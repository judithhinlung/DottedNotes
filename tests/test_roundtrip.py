import pytest
from pathlib import Path
from dottednotes.parser.lilypond_parser import LilypondParser
from dottednotes.renderers.brf_writer import BRFWriter, unicode_to_ascii_braille


def test_roundtrip_g_major_scale():
    # 1. Read LilyPond file
    ly_path = Path(__file__).parent / "fixtures" / "g_major_scale.ly"
    ly_content = ly_path.read_text(encoding="utf-8")

    # 2. Parse to Score
    parser = LilypondParser()
    score = parser.parse(ly_content)

    # 3. Render to ASCII Braille
    writer = BRFWriter(line_width=40, page_height=25, show_measure_numbers=False)
    rendered_unicode = writer.render_to_string(score)
    rendered_ascii = unicode_to_ascii_braille(rendered_unicode)

    # 4. Compare with reference BRF
    brf_path = Path(__file__).parent / "fixtures" / "g_major_scale.brf"
    expected_ascii = brf_path.read_text(encoding="utf-8")

    # Clean whitespace for comparison (ignoring differences in indentation of the signature line if any)
    rendered_lines = [line.strip() for line in rendered_ascii.splitlines() if line.strip()]
    expected_lines = [line.strip() for line in expected_ascii.splitlines() if line.strip()]

    assert rendered_lines == expected_lines
