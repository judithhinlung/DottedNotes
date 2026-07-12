import argparse
import shutil
import subprocess
import sys
import tempfile
from importlib.metadata import version as _pkg_version
from pathlib import Path

from .exceptions import DottedNotesError, LilyPondCompileError
from .parser.braille_parser import BrailleParser
from .parser.ensemble_parser import EnsembleParser, has_ensemble_header
from .parser.tokenizer import BrailleTokenizer
from .parser.input_pipeline import BRLInputPipeline


def _parse_score(text: str):
    """Parse normalized Unicode braille text into a Score, choosing the
    ensemble or solo parser based on whether an instrument-list header
    (BANA §33.2) is present.
    """
    if has_ensemble_header(text):
        return EnsembleParser().parse(text)
    tokens = BrailleTokenizer().tokenize(text)
    return BrailleParser(tokens=tokens).parse()


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
    )
    if result.returncode != 0:
        raise LilyPondCompileError("lilypond compilation failed", stderr=result.stderr)

    print(
        f"Compiled {output_basename}.pdf and {output_basename}.midi",
        file=sys.stderr,
    )


def _run_convert(args: argparse.Namespace) -> None:
    text = BRLInputPipeline().load(args.input)
    score = _parse_score(text)
    rendered = score.to_lilypond()

    output_path = args.output
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
        "output", nargs="?", help="Output .ly file path (default: stdout)"
    )
    convert_parser.add_argument(
        "--compile",
        action="store_true",
        help="Compile the output to PDF and MIDI using the lilypond binary",
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
