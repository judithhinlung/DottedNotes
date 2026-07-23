from __future__ import annotations

import asyncio
import io
import json
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
from .models.score import Score
from .parser.braille_parser import BrailleParser
from .parser.ensemble_parser import EnsembleParser, has_ensemble_header
from .parser.input_pipeline import BRLInputPipeline
from .parser.lilypond_parser import LilypondParser
from .parser.tokenizer import BrailleTokenizer
from .validation.validator import BANAValidator

JOBS_DIR = Path("/tmp/dottednotes-jobs")

SCORE_CACHE: dict[str, Score] = {}
CACHE_KEYS_FIFO: list[str] = []
MAX_CACHE_SIZE = 50

def cache_score(job_id: str, score: Score) -> None:
    if job_id in SCORE_CACHE:
        SCORE_CACHE[job_id] = score
        return
    if len(SCORE_CACHE) >= MAX_CACHE_SIZE:
        oldest = CACHE_KEYS_FIFO.pop(0)
        SCORE_CACHE.pop(oldest, None)
    SCORE_CACHE[job_id] = score
    CACHE_KEYS_FIFO.append(job_id)

def get_cached_score(job_id: str) -> Optional[Score]:
    return SCORE_CACHE.get(job_id)

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

def _get_or_parse_score(job_id: str) -> Score:
    score = get_cached_score(job_id)
    if score is not None:
        return score

    job_dir = JOBS_DIR / job_id
    meta_path = job_dir / "metadata.json"
    if not meta_path.exists():
        raise HTTPException(status_code=404, detail="Job metadata not found.")
    
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    
    input_path = job_dir / meta["input_filename"]
    category = meta.get("category")
    
    ext = input_path.suffix.lower()
    if ext in (".musicxml", ".xml", ".mxl"):
        from .parser.musicxml_parser import load_musicxml
        score = load_musicxml(str(input_path))
    elif ext == ".ly":
        from .parser.lilypond_parser import LilypondParser
        raw_ly = input_path.read_text(encoding="utf-8", errors="replace")
        score = LilypondParser().parse(raw_ly)
    else:
        from .parser.input_pipeline import BRLInputPipeline
        raw_brl_text = BRLInputPipeline().load(str(input_path))
        score = _parse_score(raw_brl_text, category_override=category)
        
    cache_score(job_id, score)
    return score

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
    page_numbers: bool = Form(True),
    measure_numbering: str = Form("auto"),  # "auto", "print_score"
    octave_mark_every_measure: bool = Form(False),
    full_measure_repeat: str = Form("single-voice"),  # "off", "single-voice", "multi-voice"
    min_repeated_measures: int = Form(2),
    include_clef_sign: bool = Form(False),
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

    meta = {
        "input_filename": input_filename,
        "category": category,
        "format_overrides": format_overrides,
        "compression": compression,
        "profile": profile,
        "measure_numbers": measure_numbers,
        "page_numbers": page_numbers,
        "measure_numbering": measure_numbering,
        "octave_mark_every_measure": octave_mark_every_measure,
        "full_measure_repeat": full_measure_repeat,
        "min_repeated_measures": min_repeated_measures,
        "include_clef_sign": include_clef_sign,
    }
    with open(job_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(meta, f)

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

    # Measure numbering validation
    if measure_numbering not in {"auto", "print_score"}:
        raise HTTPException(status_code=400, detail="Invalid measure numbering mode. Must be 'auto' or 'print_score'.")

    # Full-measure repeat validation
    if full_measure_repeat not in {"off", "single-voice", "multi-voice"}:
        raise HTTPException(status_code=400, detail="Invalid full_measure_repeat mode. Must be 'off', 'single-voice', or 'multi-voice'.")
    if min_repeated_measures < 2:
        raise HTTPException(status_code=400, detail="min_repeated_measures must be >= 2.")

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

        cache_score(job_id, score)

        # 2. Run BANA validation
        # For MusicXML/LilyPond input there is no source braille text at
        # all -- render one so line-length/page-layout rules and real
        # line-number reporting work for these input types too, not just
        # BRF/BRL (which keeps validating the literal source text, the
        # correct semantics there).
        report_text = raw_brl_text if raw_brl_text else score.to_braille()
        validator = BANAValidator(profile=profile)
        val_result = validator.validate(score, raw_brl_text=report_text)
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
                compression_level=compression,
                page_numbers=page_numbers,
                measure_numbering=measure_numbering,
                octave_mark_every_measure=octave_mark_every_measure,
                full_measure_repeat=full_measure_repeat,
                min_repeated_measures=min_repeated_measures,
                include_clef_sign=include_clef_sign,
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
            "parts": [staff.name for staff in score.staves],
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

@app.get("/api/jobs/{job_id}/parts/{part_idx}/{file_type}")
def get_part_file(job_id: str, part_idx: int, file_type: str):
    if not re.fullmatch(r"[A-Za-z0-9-]+", job_id):
        raise HTTPException(status_code=400, detail="Invalid job ID format.")
    
    job_dir = JOBS_DIR / job_id
    meta_path = job_dir / "metadata.json"
    if not meta_path.exists():
        raise HTTPException(status_code=404, detail="Job directory not found or expired.")
        
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
        
    # Get the base score
    score = _get_or_parse_score(job_id)
    
    # Extract the requested part
    try:
        part_score = score.extract_part(part_idx)
    except DottedNotesError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    # Determine target filename and output path for this specific part
    part_dir = job_dir / "parts" / str(part_idx)
    part_dir.mkdir(parents=True, exist_ok=True)
    
    input_stem = Path(meta["input_filename"]).stem
    
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
    
    # Output file name: append part name (slugified)
    part_name_slug = re.sub(r"[^a-zA-Z0-9_-]", "_", part_score.staves[0].name)
    output_filename = f"{input_stem}_{part_name_slug}{suffix}"
    if file_type in ("brf", "brl"):
        output_filename = f"{input_stem}_{part_name_slug}_output{suffix}"
        
    output_path = part_dir / output_filename
    
    # Check if already generated
    if output_path.exists():
        return FileResponse(path=output_path, media_type=media_type, filename=output_filename)
        
    # Otherwise, render it on-demand!
    try:
        if file_type == "ly":
            parsed_format_overrides = _parse_format(meta["format_overrides"]) if meta.get("format_overrides") else None
            rendered = part_score.to_lilypond(
                category_override=meta.get("category"),
                format_overrides=parsed_format_overrides,
                measure_numbers=meta.get("measure_numbers", False)
            )
            output_path.write_text(rendered, encoding="utf-8")
            
        elif file_type == "pdf":
            # We first need the .ly file to compile
            ly_filename = f"{input_stem}_{part_name_slug}.ly"
            ly_path = part_dir / ly_filename
            if not ly_path.exists():
                parsed_format_overrides = _parse_format(meta["format_overrides"]) if meta.get("format_overrides") else None
                rendered = part_score.to_lilypond(
                    category_override=meta.get("category"),
                    format_overrides=parsed_format_overrides,
                    measure_numbers=meta.get("measure_numbers", False)
                )
                ly_path.write_text(rendered, encoding="utf-8")
            
            compile_with_lilypond(ly_path)
            # Find generated PDF
            if not output_path.exists():
                raise HTTPException(status_code=500, detail="PDF compilation failed to produce output file.")
                
        elif file_type == "midi":
            # We first need the .ly file to compile
            ly_filename = f"{input_stem}_{part_name_slug}.ly"
            ly_path = part_dir / ly_filename
            if not ly_path.exists():
                parsed_format_overrides = _parse_format(meta["format_overrides"]) if meta.get("format_overrides") else None
                rendered = part_score.to_lilypond(
                    category_override=meta.get("category"),
                    format_overrides=parsed_format_overrides,
                    measure_numbers=meta.get("measure_numbers", False)
                )
                ly_path.write_text(rendered, encoding="utf-8")
            
            compile_with_lilypond(ly_path)
            # Find generated MIDI
            midi_path = part_dir / f"{input_stem}_{part_name_slug}.midi"
            mid_path = part_dir / f"{input_stem}_{part_name_slug}.mid"
            if mid_path.exists() and not midi_path.exists():
                mid_path.rename(midi_path)
            
            if not midi_path.exists():
                raise HTTPException(status_code=500, detail="MIDI compilation failed to produce output file.")
            
        elif file_type in ("brf", "brl"):
            from .renderers.brf_writer import BRFWriter
            writer = BRFWriter(
                line_width=40,
                show_measure_numbers=meta.get("measure_numbers", False),
                compression_level=meta.get("compression", "full"),
                page_numbers=meta.get("page_numbers", True),
                measure_numbering=meta.get("measure_numbering", "auto"),
                octave_mark_every_measure=meta.get("octave_mark_every_measure", False),
                full_measure_repeat=meta.get("full_measure_repeat", "single-voice"),
                min_repeated_measures=meta.get("min_repeated_measures", 2),
                include_clef_sign=meta.get("include_clef_sign", False),
            )
            if file_type == "brl":
                writer.write_unicode(part_score, output_path)
            else:
                writer.write(part_score, output_path)
                
        elif file_type == "musicxml":
            from .renderers.musicxml_renderer import export_musicxml
            export_musicxml(part_score, str(output_path))
            
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: '{file_type}'")
            
        return FileResponse(path=output_path, media_type=media_type, filename=output_filename)
        
    except DottedNotesError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal part conversion error: {str(e)}")
