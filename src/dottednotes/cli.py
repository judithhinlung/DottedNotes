from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
import warnings
from importlib.metadata import version as _pkg_version
from pathlib import Path

from .exceptions import DottedNotesError, LilyPondCompileError
from .parser.braille_parser import BrailleParser
from .parser.ensemble_parser import EnsembleParser, has_ensemble_header
from .parser.lead_sheet_parser import parse_lead_sheet
from .parser.strophic_song_parser import parse_strophic_song
from .parser.tokenizer import BrailleTokenizer
from .parser.input_pipeline import BRLInputPipeline


def _parse_score(text: str, category_override: str | None = None):
    """Parse normalized Unicode braille text into a Score, choosing the
    lead-sheet, strophic-song, ensemble, or solo parser.

    An explicit `category_override == "Lead Sheet"` always wins and routes
    to `parse_lead_sheet()` (BANA Sec. 27's two-line melody/chord-symbol
    parallel); `category_override == "Strophic Song"` routes to
    `parse_strophic_song()` (BANA Secs. 35/36's solo vocal lyric/chord/
    melody format) -- there's no unambiguous structural marker to
    auto-detect either format the way an instrument-list header marks an
    ensemble score, so the caller must ask for them explicitly. Otherwise,
    choose the ensemble or solo parser based on whether an instrument-list
    header (BANA §33.2) is present.
    """
    if category_override == "Lead Sheet":
        return parse_lead_sheet(text)
    if category_override == "Strophic Song":
        return parse_strophic_song(text)
    if has_ensemble_header(text):
        return EnsembleParser(category_override=category_override).parse(text)
    tokens = BrailleTokenizer().tokenize(text)
    return BrailleParser(tokens=tokens, category_override=category_override).parse()


def _print_verbose_trace(input_path: str, text: str) -> None:
    """Print a plain-text diagnostic trace to stderr: detected input
    encoding, every token the tokenizer produced for the top-level text,
    and category/raw braille character for each. Ensemble scores are
    tokenized further, per-instrument, inside EnsembleParser itself --
    this trace only covers the top-level pass every input goes through,
    which is still the most useful single view for diagnosing why a cell
    was mis-tokenized.
    """
    pipeline = BRLInputPipeline()
    raw = Path(input_path).read_text(encoding="utf-8", errors="replace")
    print(f"Detected encoding: {pipeline._detect_encoding(raw)}", file=sys.stderr)

    for token in BrailleTokenizer().tokenize(text):
        print(f"Token: {token.category.name} {token.raw}", file=sys.stderr)


def _compile_with_lilypond(ly_path: Path) -> None:
    """Invoke the `lilypond` binary on `ly_path`, writing PDF/MIDI output
    next to it. Raises LilyPondCompileError (caught centrally in main())
    if the binary is missing or compilation fails -- never exits directly,
    so callers other than the CLI (e.g. tests) can handle the failure too.
    """
    if shutil.which("lilypond") is None:
        raise LilyPondCompileError(
            "the 'lilypond' program is not installed or not on your PATH. "
            "Install LilyPond to use --compile."
        )

    output_basename = ly_path.with_suffix("")
    result = subprocess.run(
        ["lilypond", "-o", str(output_basename), str(ly_path)],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode != 0:
        raise LilyPondCompileError("lilypond compilation failed", stderr=result.stderr)

    print(
        f"Compiled {output_basename}.pdf and {output_basename}.midi",
        file=sys.stderr,
    )


def _parse_format(format_str: str) -> dict:
    """Parse comma-separated key=value pairs into a dictionary of formatting overrides."""
    if not format_str.strip():
        return {}

    overrides = {}
    valid_keys = {"paper_size", "margin_mm", "staff_size", "basic_distance", "padding"}

    parts = format_str.split(",")
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if "=" not in part:
            raise DottedNotesError(f"Invalid format option '{part}'. Must be in key=value format.")

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


def _run_convert(args: argparse.Namespace) -> None:
    input_path = Path(args.input)
    is_musicxml_input = input_path.suffix.lower() in (".musicxml", ".xml", ".mxl")
    is_lilypond_input = input_path.suffix.lower() == ".ly"

    category_override = args.category
    valid_categories = {"Solo Piano", "Art Song", "Chamber", "Orchestral", "Lead Sheet", "Strophic Song"}
    if category_override is not None and category_override not in valid_categories:
        raise DottedNotesError(
            f"Invalid category: '{category_override}'. Must be one of {sorted(list(valid_categories))}"
        )

    format_overrides = None
    if args.format is not None:
        format_overrides = _parse_format(args.format)

    if is_musicxml_input:
        from dottednotes.parser.musicxml_parser import load_musicxml
        score = load_musicxml(args.input)
        text = ""
    elif is_lilypond_input:
        from dottednotes.parser.lilypond_parser import LilypondParser
        raw_ly = Path(args.input).read_text(encoding="utf-8")
        try:
            score = LilypondParser().parse(raw_ly)
        except Exception as e:
            # LilypondParser is a restricted parser -- it only needs to
            # round-trip LilyPond that DottedNotes itself generated, not
            # arbitrary hand-authored LilyPond (see CLAUDE.md's "Restricted
            # LilyPond parser" design note). A failure here is an expected,
            # documented scope limitation, not a mystery internal bug, so
            # it gets a plain-text DottedNotesError like any other
            # malformed/unsupported input -- never a raw traceback.
            raise DottedNotesError(
                f"Could not parse LilyPond input '{args.input}': {e}. "
                "This parser only supports LilyPond that DottedNotes itself "
                "generated, not arbitrary hand-authored LilyPond."
            ) from e
        text = ""
    else:
        text = BRLInputPipeline().load(args.input)
        if args.verbose:
            _print_verbose_trace(args.input, text)
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                score = _parse_score(text, category_override=category_override)
            for w in caught:
                print(f"Warning: {w.message}", file=sys.stderr)
        else:
            score = _parse_score(text, category_override=category_override)

    if getattr(args, 'report', False):
        from dottednotes.validation.validator import BANAValidator
        # For MusicXML/LilyPond input there is no source braille text at
        # all (`text` is "") -- render one so line-length/page-layout
        # rules (S9b-4/S11c-2) and real line-number reporting work for
        # these input types too, not just BRF/BRL. For BRF/BRL input,
        # keep validating the literal source text as before (that is the
        # correct semantics there -- checking what the user actually
        # wrote, not a freshly re-rendered version of it).
        report_text = text if text else score.to_braille()
        validator = BANAValidator(profile=args.profile)
        result = validator.validate(score, raw_brl_text=report_text)
        for c in result.corrections:
            msg = ""
            if c.line_number > 0:
                msg += f"Line {c.line_number}: "
            if c.measure_number > 0:
                msg += f"Measure {c.measure_number}: "
            msg += c.message
            print(msg, file=sys.stderr)

    output_path = args.output
    is_musicxml_output = output_path is not None and Path(output_path).suffix.lower() in (".musicxml", ".mxl", ".xml")
    is_braille_output = output_path is not None and Path(output_path).suffix.lower() in (".brf", ".brl")

    if is_musicxml_output:
        if args.compile:
            raise DottedNotesError(
                "--compile requires LilyPond (.ly) output, not a .musicxml/.mxl output path."
            )
        from dottednotes.renderers.musicxml_renderer import export_musicxml
        export_musicxml(score, output_path)
        print(f"Written to {output_path}", file=sys.stderr)
    else:
        if is_braille_output:
            if args.compile:
                raise DottedNotesError(
                    "--compile requires LilyPond (.ly) output, not a .brf/.brl output path."
                )
            from dottednotes.renderers.brf_writer import BRFWriter, unicode_to_ascii_braille
            writer = BRFWriter(
                line_width=40,
                show_measure_numbers=args.measure_numbers,
                compression_level=args.compression,
                page_numbers=not args.no_page_numbers,
                measure_numbering=args.measure_numbering,
                octave_mark_every_measure=args.octave_mark_every_measure,
                full_measure_repeat=args.full_measure_repeat,
                min_repeated_measures=args.min_repeated_measures,
            )
            is_brl = output_path is not None and Path(output_path).suffix.lower() == ".brl"
            if is_brl:
                rendered = writer.render_to_string(score)
            else:
                brl_content = writer.render_to_string(score)
                rendered = unicode_to_ascii_braille(brl_content)
        else:
            rendered = score.to_lilypond(
                category_override=category_override,
                format_overrides=format_overrides,
                measure_numbers=args.measure_numbers,
            )

        if args.compile and output_path is None:
            # lilypond compiles a file, not stdin -- an output path is required
            # to compile even when the caller didn't ask to keep the .ly file.
            tmp_dir = Path(tempfile.mkdtemp(prefix="dottednotes-"))
            output_path = str(tmp_dir / (Path(args.input).stem + ".ly"))

        if output_path:
            Path(output_path).write_text(rendered, encoding="utf-8")
            print(f"Written to {output_path}", file=sys.stderr)
        else:
            print(rendered)

    if args.compile:
        _compile_with_lilypond(Path(output_path))


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="dottednotes",
        description="Convert braille music notation (.brf/.brl) to LilyPond.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"dottednotes {_pkg_version('dottednotes')}",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    convert_parser = subparsers.add_parser(
        "convert", help="Convert a .brf/.brl file to LilyPond"
    )
    convert_parser.add_argument("input", help="Path to a .brf or .brl braille music file")
    convert_parser.add_argument(
        "output", nargs="?",
        help="Output file path (default: stdout, as LilyPond). A .ly path (or "
             "no path) produces LilyPond; a .brf/.brl path produces compressed "
             "braille instead (see --compression).",
    )
    convert_parser.add_argument(
        "--compile",
        action="store_true",
        help="Compile the output to PDF and MIDI using the lilypond binary",
    )
    convert_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print a diagnostic trace (encoding, tokens, validation "
             "warnings) to stderr",
    )
    convert_parser.add_argument(
        "--category",
        help="Override the layout category (e.g. Solo Piano, Art Song, Chamber, "
             "Orchestral, Lead Sheet, Strophic Song). \"Lead Sheet\" and "
             "\"Strophic Song\" also switch the parser itself: \"Lead Sheet\" to "
             "BANA Sec. 27's two-line melody/chord-symbol format, \"Strophic "
             "Song\" to BANA Secs. 35/36's solo vocal lyric/chord/melody format.",
    )
    convert_parser.add_argument(
        "--format",
        help="Comma-separated formatting overrides (e.g. paper_size=a4,margin_mm=12)",
    )
    convert_parser.add_argument(
        "--report",
        action="store_true",
        help="Print BANA correction/validation report to stderr",
    )
    convert_parser.add_argument(
        "--measure-numbers",
        action="store_true",
        help="Show measure numbers: in LilyPond output, prefix each measure's "
             "line with a '%% N' comment giving its real BANA margin number, "
             "for faster screen-reader navigation back from a validation "
             "warning to the line it refers to; in .brf/.brl output, show "
             "the BANA margin number/heading itself (see --measure-numbering "
             "for which number is shown). Off by default in both.",
    )
    convert_parser.add_argument(
        "--measure-numbering",
        choices=["auto", "print_score"],
        default="auto",
        help="For .brf/.brl output, which measure numbers to show when "
             "--measure-numbers is on: 'auto' (default) renumbers "
             "sequentially from 1, ignoring any measure numbers in the "
             "source file; 'print_score' reads and keeps the source "
             "MusicXML/LilyPond file's own measure numbers (e.g. a pickup "
             "measure numbered 0, or a non-sequential renumbering), rather "
             "than recalculating them. Has no effect on .ly output.",
    )
    convert_parser.add_argument(
        "--compression",
        choices=["none", "minimal", "full"],
        default="full",
        help="Set repeat and shorthand compression level (none, minimal, full) "
             "for .brf/.brl output; has no effect on .ly output",
    )
    convert_parser.add_argument(
        "--octave-mark-every-measure",
        action="store_true",
        help="For .brf/.brl output, force the octave mark on every "
             "measure's first note, not just measures that start a new "
             "braille line. Additive on top of the required BANA 3.2.1 "
             "trigger points (line start, after a word sign/numeric "
             "indicator) -- never suppresses a mark that would already be "
             "shown. Off by default; has no effect on .ly output.",
    )
    convert_parser.add_argument(
        "--full-measure-repeat",
        choices=["off", "single-voice", "multi-voice"],
        default="single-voice",
        help="Control whole-measure repeat-sign compression (BANA Par. "
             "18.2) for .brf/.brl output, independent of --compression's "
             "articulation-carry shorthand: 'off' disables repeat-sign "
             "compression entirely; 'single-voice' (default) compresses "
             "only measures with no in-accord (multi-voice) content; "
             "'multi-voice' also allows compressing in-accord-containing "
             "measures. Has no effect if --compression is 'none' (that "
             "remains a hard override disabling all compression) or on "
             ".ly output.",
    )
    convert_parser.add_argument(
        "--min-repeated-measures",
        type=int,
        default=2,
        help="Minimum number of consecutive musically-identical measures "
             "required before they are compressed into a repeat sign, for "
             ".brf/.brl output (default 2, the smallest possible repeat: "
             "one original plus one repetition). Has no effect if "
             "--full-measure-repeat is 'off' or on .ly output.",
    )
    convert_parser.add_argument(
        "--no-page-numbers",
        action="store_true",
        help="For .brf/.brl output, skip BANA running-head pagination "
             "(title + braille page number on every page after the first) "
             "and emit the music as one continuous stream instead. Page "
             "numbers are included by default; has no effect on .ly output.",
    )
    convert_parser.add_argument(
        "--profile",
        choices=["standard", "strict"],
        default="standard",
        help="Set the validation profile (standard, strict) for formatting checks",
    )
    convert_parser.set_defaults(func=_run_convert)

    args = parser.parse_args()
    try:
        args.func(args)
    except DottedNotesError as e:
        print(f"Error: {e}", file=sys.stderr)
        if isinstance(e, LilyPondCompileError) and e.stderr:
            print(e.stderr, file=sys.stderr)
        sys.exit(1)
    except OSError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
