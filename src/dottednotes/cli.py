import argparse
import sys
from pathlib import Path

from .parser.braille_parser import BrailleParser
from .parser.input_pipeline import InputPipeline
from .renderers.lilypond_renderer import LilypondRenderer


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="dottednotes",
        description="Convert braille music notation (.brf) to LilyPond.",
    )
    parser.add_argument("input", help="Path to a .brf braille music file")
    parser.add_argument("-o", "--output", help="Output .ly file path (default: stdout)")
    args = parser.parse_args()

    text = InputPipeline(args.input).read()
    score = BrailleParser().parse(text)
    rendered = LilypondRenderer().render(score)

    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
        print(f"Written to {args.output}", file=sys.stderr)
    else:
        print(rendered)


if __name__ == "__main__":
    main()
