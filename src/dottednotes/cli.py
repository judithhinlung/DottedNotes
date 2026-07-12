import argparse
import sys
from pathlib import Path

from .parser.braille_parser import BrailleParser
from .parser.ensemble_parser import EnsembleParser, extract_measure_number
from .parser.tokenizer import BrailleTokenizer
from .parser.input_pipeline import InputPipeline
from .bana_symbols import WORD_SIGN, END_WORD_SIGN


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="dottednotes",
        description="Convert braille music notation (.brf) to LilyPond.",
    )
    parser.add_argument("input", help="Path to a .brf braille music file")
    parser.add_argument("-o", "--output", help="Output .ly file path (default: stdout)")
    args = parser.parse_args()

    text = InputPipeline(args.input).read()

    # Determine if it's an ensemble score by checking for an instrument list header
    lines = text.splitlines()
    has_ensemble_header = False
    for line in lines:
        m_num, _ = extract_measure_number(line)
        if m_num is None and WORD_SIGN in line and END_WORD_SIGN in line:
            has_ensemble_header = True
            break

    if has_ensemble_header:
        score = EnsembleParser().parse(text)
    else:
        tokens = BrailleTokenizer().tokenize(text)
        score = BrailleParser(tokens=tokens).parse()

    rendered = score.to_lilypond()

    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
        print(f"Written to {args.output}", file=sys.stderr)
    else:
        print(rendered)


if __name__ == "__main__":
    main()
