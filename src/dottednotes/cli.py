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
from .parser.tokenizer import BrailleTokenizer
from .parser.input_pipeline import BRLInputPipeline


def _parse_score(text: str, category_override: str | None = None):
    """Parse normalized Unicode braille text into a Score, choosing the
    lead-sheet, ensemble, or solo parser.

    An explicit `category_override == "Lead Sheet"` always wins and routes
    to `parse_lead_sheet()` (BANA Sec. 27's two-line melody/chord-symbol
    parallel) -- there's no unambiguous structural marker to auto-detect a
    lead sheet the way an instrument-list header marks an ensemble score,
    so the caller must ask for it explicitly. Otherwise, choose the
    ensemble or solo parser based on whether an instrument-list header
    (BANA §33.2) is present.
    """
    if category_override == "Lead Sheet":
        return parse_lead_sheet(text)
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

    category_override = args.category
    valid_categories = {"Solo Piano", "Art Song", "Chamber", "Orchestral", "Lead Sheet"}
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
        validator = BANAValidator(profile=args.profile)
        result = validator.validate(score, raw_brl_text=text)
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
            rendered = score.to_braille(compression_level=args.compression)
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
             "Orchestral, Lead Sheet). \"Lead Sheet\" also switches the parser "
             "itself to BANA Sec. 27's two-line melody/chord-symbol format.",
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
        help="Prefix each measure's line in LilyPond output with a '%% N' "
             "comment giving its real BANA margin number, for faster "
             "screen-reader navigation back from a validation warning to "
             "the line it refers to. Has no effect on .brf/.brl output.",
    )
    convert_parser.add_argument(
        "--compression",
        choices=["none", "minimal", "full"],
        default="full",
        help="Set repeat and shorthand compression level (none, minimal, full) "
             "for .brf/.brl output; has no effect on .ly output",
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
