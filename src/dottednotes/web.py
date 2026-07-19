from __future__ import annotations

import asyncio
import io
import os
import re
import shutil
import subprocess
import tempfile
import time
import uuid
import zipfile
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional, Union

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .exceptions import DottedNotesError, LilyPondCompileError
from .parser.braille_parser import BrailleParser
from .parser.ensemble_parser import EnsembleParser, has_ensemble_header
from .parser.input_pipeline import BRLInputPipeline
from .parser.lilypond_parser import LilypondParser
from .parser.tokenizer import BrailleTokenizer
from .validation.validator import BANAValidator

JOBS_DIR = Path("/tmp/dottednotes-jobs")

# Render Starter's 512MB is tight enough that a single large conversion request
# can threaten the whole process's memory budget once music21 builds an
# in-memory object graph from the parsed MusicXML. This is the ceiling on the
# actual MusicXML/braille content a request may hand to the parsers -- for a
# .mxl upload that means the *decompressed* size (see
# `_check_mxl_decompressed_size` below), since checking only the compressed
# upload size would let a small file expand well past this cap once unzipped.
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB


def _check_mxl_decompressed_size(contents: bytes, max_bytes: int) -> None:
    """Reject a .mxl (compressed MusicXML) upload whose decompressed content
    would exceed max_bytes, without actually decompressing it -- ZipInfo's
    file_size comes from the zip's central directory."""
    try:
        with zipfile.ZipFile(io.BytesIO(contents)) as archive:
            total_decompressed = sum(info.file_size for info in archive.infolist())
    except zipfile.BadZipFile:
        raise HTTPException(
            status_code=400,
            detail="File is not a valid compressed MusicXML (.mxl) archive.",
        )
    if total_decompressed > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Compressed MusicXML archive decompresses to more than the "
                f"{max_bytes // (1024 * 1024)}MB limit."
            ),
        )

def _parse_score(text: str, category_override: str | None = None):
    if category_override == "Lead Sheet":
        from .parser.lead_sheet_parser import parse_lead_sheet
        return parse_lead_sheet(text)
    if has_ensemble_header(text):
        return EnsembleParser(category_override=category_override).parse(text)
    tokens = BrailleTokenizer().tokenize(text)
    return BrailleParser(tokens=tokens, category_override=category_override).parse()

def _parse_format(format_str: str) -> dict[str, Union[float, str]]:
    overrides = {}
    valid_keys = {"paper_size", "margin_mm", "staff_size"}
    for part in format_str.split(","):
        if not part.strip():
            continue
        subparts = part.split("=")
        if len(subparts) != 2:
            raise DottedNotesError(f"Invalid format option '{part}'. Must be in key=value format.")
        key, val = subparts[0].strip(), subparts[1].strip()
        if key not in valid_keys:
            raise DottedNotesError(f"Unknown/invalid format key: '{key}'.")
        if key == "paper_size":
            overrides[key] = val
        else:
            try:
                overrides[key] = float(val)
            except ValueError:
                raise DottedNotesError(f"Invalid float value for {key}: '{val}'")
    return overrides

def compile_with_lilypond(ly_path: Path) -> None:
    if not shutil.which("lilypond"):
        raise LilyPondCompileError(
            "Could not compile: 'lilypond' binary not found on PATH. "
            "Please make sure LilyPond is installed and available."
        )
    try:
        res = subprocess.run(
            ["lilypond", "-o", str(ly_path.parent), str(ly_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30.0,
        )
    except subprocess.TimeoutExpired:
        raise LilyPondCompileError("lilypond compilation timed out after 30 seconds.")

    if res.returncode != 0:
        raise LilyPondCompileError(
            f"lilypond exited with code {res.returncode}",
            stderr=res.stderr
        )

async def clean_old_jobs():
    while True:
        try:
            now = time.time()
            if JOBS_DIR.exists():
                for job_path in JOBS_DIR.iterdir():
                    if job_path.is_dir():
                        mtime = job_path.stat().st_mtime
                        if now - mtime > 3600:  # 1 hour
                            shutil.rmtree(job_path, ignore_errors=True)
        except Exception:
            pass
        await asyncio.sleep(600)  # run every 10 minutes

@asynccontextmanager
async def lifespan(app: FastAPI):
    JOBS_DIR.mkdir(parents=True, exist_ok=True)
    cleanup_task = asyncio.create_task(clean_old_jobs())
    yield
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass

app = FastAPI(
    title="DottedNotes Web API",
    description="Web service for bidirectional conversion and reformatting of braille music.",
    version="0.1.0",
    lifespan=lifespan,
)

# Serves static assets for the client app
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def read_root():
    index_file = static_dir / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="Frontend files not found.")
    return FileResponse(index_file)

@app.post("/api/convert")
async def convert_file(
    file: UploadFile = File(...),
    target_format: str = Form("lilypond"),  # "lilypond", "brf", "brl", "musicxml"
    category: Optional[str] = Form(None),   # "Solo Piano", "Art Song", "Chamber", "Orchestral", "Lead Sheet"
    format_overrides: Optional[str] = Form(None),  # e.g., "paper_size=a4,margin_mm=12"
    compression: str = Form("full"),        # "none", "minimal", "full"
    profile: str = Form("standard"),        # "standard", "strict"
    measure_numbers: bool = Form(False),
):
    contents = await file.read(MAX_UPLOAD_SIZE + 1)
    if len(contents) > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds the {MAX_UPLOAD_SIZE // (1024 * 1024)}MB limit.",
        )

    job_id = str(uuid.uuid4())
    job_dir = JOBS_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    input_filename = Path(file.filename or "input.brf").name
    if not input_filename or input_filename in (".", ".."):
        input_filename = "input.brf"
    input_path = job_dir / input_filename

    ext = input_path.suffix.lower()
    if ext == ".mxl":
        _check_mxl_decompressed_size(contents, MAX_UPLOAD_SIZE)

    input_path.write_bytes(contents)

    input_type = "braille"
    if ext in (".musicxml", ".xml", ".mxl"):
        input_type = "musicxml"
    elif ext == ".ly":
        input_type = "lilypond"

    # Category validation
    valid_categories = {"Solo Piano", "Art Song", "Chamber", "Orchestral", "Lead Sheet"}
    if category and category not in valid_categories:
        raise HTTPException(status_code=400, detail=f"Invalid category. Must be one of {valid_categories}")

    # Compression validation
    if compression not in {"none", "minimal", "full"}:
        raise HTTPException(status_code=400, detail="Invalid compression level. Must be 'none', 'minimal', or 'full'.")

    # Profile validation
    if profile not in {"standard", "strict"}:
        raise HTTPException(status_code=400, detail="Invalid profile. Must be 'standard' or 'strict'.")

    try:
        # 1. Parse Input to Score
        raw_brl_text = None
        if input_type == "musicxml":
            from .parser.musicxml_parser import load_musicxml
            score = load_musicxml(str(input_path))
        elif input_type == "lilypond":
            raw_ly = input_path.read_text(encoding="utf-8", errors="replace")
            score = LilypondParser().parse(raw_ly)
        else:
            raw_brl_text = BRLInputPipeline().load(str(input_path))
            score = _parse_score(raw_brl_text, category_override=category)

        # 2. Run BANA validation
        validator = BANAValidator(profile=profile)
        val_result = validator.validate(score, raw_brl_text=raw_brl_text)
        corrections = [c.to_dict() for c in val_result.corrections]

        # 3. Render Output format
        available_files = {}
        compile_success = None
        compile_error = None

        if target_format == "lilypond":
            parsed_format_overrides = _parse_format(format_overrides) if format_overrides else None
            rendered = score.to_lilypond(
                category_override=category,
                format_overrides=parsed_format_overrides,
                measure_numbers=measure_numbers
            )
            output_ly = job_dir / f"{input_path.stem}.ly"
            output_ly.write_text(rendered, encoding="utf-8")
            available_files["ly"] = f"/api/jobs/{job_id}/ly"

            # Attempt PDF & MIDI compilation if LilyPond binary is installed
            if shutil.which("lilypond"):
                try:
                    compile_with_lilypond(output_ly)
                    compile_success = True
                    if (job_dir / f"{input_path.stem}.pdf").exists():
                        available_files["pdf"] = f"/api/jobs/{job_id}/pdf"
                    if (job_dir / f"{input_path.stem}.midi").exists():
                        available_files["midi"] = f"/api/jobs/{job_id}/midi"
                    elif (job_dir / f"{input_path.stem}.mid").exists():
                        # sometimes extension is .mid instead of .midi
                        (job_dir / f"{input_path.stem}.mid").rename(job_dir / f"{input_path.stem}.midi")
                        available_files["midi"] = f"/api/jobs/{job_id}/midi"
                except LilyPondCompileError as ce:
                    compile_success = False
                    compile_error = str(ce)
                    if ce.stderr:
                        compile_error += f"\nDetails:\n{ce.stderr}"
            else:
                compile_success = False
                compile_error = "LilyPond binary not installed. PDF/MIDI compilation skipped."

        elif target_format in ("braille", "brf", "brl"):
            from .renderers.brf_writer import BRFWriter
            writer = BRFWriter(
                line_width=40,
                show_measure_numbers=measure_numbers,
                compression_level=compression
            )
            if target_format == "brl":
                output_brl = job_dir / f"{input_path.stem}_output.brl"
                writer.write_unicode(score, output_brl)
                available_files["brl"] = f"/api/jobs/{job_id}/brl"
            else:
                output_brf = job_dir / f"{input_path.stem}_output.brf"
                writer.write(score, output_brf)
                available_files["brf"] = f"/api/jobs/{job_id}/brf"

        elif target_format == "musicxml":
            output_xml = job_dir / f"{input_path.stem}.musicxml"
            from .renderers.musicxml_renderer import export_musicxml
            export_musicxml(score, str(output_xml))
            available_files["musicxml"] = f"/api/jobs/{job_id}/musicxml"

        else:
            raise HTTPException(status_code=400, detail=f"Unsupported target format: '{target_format}'")

        return {
            "job_id": job_id,
            "input_type": input_type,
            "target_format": target_format,
            "validation_report": corrections,
            "files": available_files,
            "compile_success": compile_success,
            "compile_error": compile_error,
        }

    except DottedNotesError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal conversion error: {str(e)}")

@app.get("/api/jobs/{job_id}/{file_type}")
def get_job_file(job_id: str, file_type: str):
    # Sanitize inputs: job IDs are always our own uuid4() strings, so no
    # path separators or other special characters are ever legitimate here.
    if not re.fullmatch(r"[A-Za-z0-9-]+", job_id):
        raise HTTPException(status_code=400, detail="Invalid job ID format.")
    
    job_dir = JOBS_DIR / job_id
    if not job_dir.exists() or not job_dir.is_dir():
        raise HTTPException(status_code=404, detail="Job directory not found or expired.")

    # Find the file with the expected suffix
    valid_suffixes = {
        "ly": (".ly", "text/plain"),
        "pdf": (".pdf", "application/pdf"),
        "midi": (".midi", "audio/midi"),
        "brf": (".brf", "text/plain"),
        "brl": (".brl", "text/plain"),
        "musicxml": (".musicxml", "application/xml"),
    }

    if file_type not in valid_suffixes:
        raise HTTPException(status_code=400, detail=f"Invalid file type requested. Valid types: {list(valid_suffixes.keys())}")

    suffix, media_type = valid_suffixes[file_type]
    
    # Locate output file matching suffix in the job directory
    matching_files = [f for f in job_dir.iterdir() if f.suffix.lower() == suffix]
    if not matching_files:
        raise HTTPException(status_code=404, detail=f"Requested file type '{file_type}' was not generated for this job.")

    target_file = None
    if file_type in ("brf", "brl"):
        expected_suffix = f"_output.{file_type}"
        for f in matching_files:
            if f.name.endswith(expected_suffix):
                target_file = f
                break
    if not target_file:
        target_file = matching_files[0]
        
    return FileResponse(
        path=target_file,
        media_type=media_type,
        filename=target_file.name
    )
