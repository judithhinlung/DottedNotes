from pathlib import Path

import pytest

from dottednotes.bana_symbols import BAR_LINE_CELLS, SymbolCategory
from dottednotes.models import Score
from dottednotes.parser import BRLInputPipeline, BrailleParser, BrailleToken, BrailleTokenizer, InputPipeline


def test_braille_parser_returns_score():
    score = BrailleParser().parse("")
    assert isinstance(score, Score)


def test_braille_parser_empty_input_empty_score():
    score = BrailleParser().parse("")
    assert score.staves == []


def test_input_pipeline_read(tmp_path: Path):
    brf = tmp_path / "sample.brf"
    brf.write_text("⠀⠼⠙⠲", encoding="utf-8")
    pipeline = InputPipeline(brf)
    assert pipeline.read() == "⠀⠼⠙⠲"


def test_input_pipeline_lines(tmp_path: Path):
    brf = tmp_path / "sample.brf"
    brf.write_text("line one\nline two", encoding="utf-8")
    pipeline = InputPipeline(brf)
    assert pipeline.lines() == ["line one", "line two"]


def test_input_pipeline_missing_file():
    pipeline = InputPipeline("/nonexistent/path.brf")
    with pytest.raises(FileNotFoundError):
        pipeline.read()


# --- BRLInputPipeline tests ---

FIXTURES = Path(__file__).parent / "fixtures"


def test_brl_detect_unicode_encoding():
    pipeline = BRLInputPipeline()
    assert pipeline._detect_encoding("⠁⠃") == "unicode"


def test_brl_detect_ascii_encoding():
    pipeline = BRLInputPipeline()
    assert pipeline._detect_encoding("ABC") == "ascii"


def test_brl_detect_unknown_encoding():
    pipeline = BRLInputPipeline()
    assert pipeline._detect_encoding("   \n  ") == "unknown"


def test_brl_ascii_to_unicode_dot1():
    # 'A' in BRF = dot 1 = U+2801
    pipeline = BRLInputPipeline()
    assert pipeline._ascii_to_unicode("A") == "⠁"


def test_brl_ascii_to_unicode_number_sign():
    # '#' in BRF = dots 3,4,5,6 = U+283C
    pipeline = BRLInputPipeline()
    assert pipeline._ascii_to_unicode("#") == "⠼"


def test_brl_ascii_to_unicode_preserves_newlines():
    pipeline = BRLInputPipeline()
    result = pipeline._ascii_to_unicode("A\nB")
    assert result == "⠁\n⠃"


def test_brl_same_content_both_encodings():
    # ASCII 'A' and Unicode U+2801 both represent dot 1 (braille C quarter note).
    pipeline = BRLInputPipeline()
    ascii_result = pipeline._ascii_to_unicode("A")
    assert ascii_result == "⠁"


def test_brl_load_unicode_file(tmp_path: Path):
    brf = tmp_path / "sample.brf"
    brf.write_text("⠁⠃", encoding="utf-8")
    pipeline = BRLInputPipeline()
    result = pipeline.load(brf)
    assert result == "⠁⠃"


def test_brl_load_ascii_file(tmp_path: Path):
    brf = tmp_path / "sample.brf"
    brf.write_text("AB", encoding="utf-8")
    pipeline = BRLInputPipeline()
    result = pipeline.load(brf)
    assert result == "⠁⠃"


def test_brl_load_missing_file():
    pipeline = BRLInputPipeline()
    with pytest.raises(FileNotFoundError):
        pipeline.load("/nonexistent/path.brf")


def test_brl_load_fengyang_fixture():
    pipeline = BRLInputPipeline()
    result = pipeline.load(FIXTURES / "fengyang_flower_drum.brf")
    assert isinstance(result, str)
    assert len(result) > 0


# --- BrailleTokenizer tests ---

def test_tokenizer_returns_list():
    tokens = BrailleTokenizer().tokenize("")
    assert isinstance(tokens, list)


def test_tokenizer_empty_input():
    tokens = BrailleTokenizer().tokenize("")
    assert tokens == []


def test_tokenizer_note_cell_c_quarter():
    # ⠹ = C quarter note (dots 1,4,5,6)
    tokens = BrailleTokenizer().tokenize('⠹')
    assert len(tokens) == 1
    assert tokens[0].category == SymbolCategory.NOTE
    assert tokens[0].character == '⠹'


def test_tokenizer_note_cell_g_half():
    # ⠗ = G half note (dots 1,2,3,5)
    tokens = BrailleTokenizer().tokenize('⠗')
    assert len(tokens) == 1
    assert tokens[0].category == SymbolCategory.NOTE


def test_tokenizer_rest_cell():
    # ⠍ = whole/16th rest (dots 1,3,4)
    tokens = BrailleTokenizer().tokenize('⠍')
    assert len(tokens) == 1
    assert tokens[0].category == SymbolCategory.REST


def test_tokenizer_octave_mark():
    # ⠐ = octave 4 (dot 5)
    tokens = BrailleTokenizer().tokenize('⠐')
    assert len(tokens) == 1
    assert tokens[0].category == SymbolCategory.OCTAVE_MARK


def test_tokenizer_accidental_flat():
    # ⠣ = flat (dots 1,2,6)
    tokens = BrailleTokenizer().tokenize('⠣')
    assert len(tokens) == 1
    assert tokens[0].category == SymbolCategory.ACCIDENTAL


def test_tokenizer_accidental_sharp():
    # ⠩ = sharp (dots 1,4,6)
    tokens = BrailleTokenizer().tokenize('⠩')
    assert len(tokens) == 1
    assert tokens[0].category == SymbolCategory.ACCIDENTAL


def test_tokenizer_unknown_cell():
    # ⠬ = dots 3,4,6 — not a note, rest, octave, accidental, or bar line
    tokens = BrailleTokenizer().tokenize('⠬')
    assert len(tokens) == 1
    assert tokens[0].category == SymbolCategory.UNKNOWN


def test_tokenizer_unknown_does_not_raise():
    # Any unrecognized cell must produce UNKNOWN, never raise
    tokens = BrailleTokenizer().tokenize('⠿⠬⠻')
    assert any(t.category == SymbolCategory.UNKNOWN for t in tokens)  # ⠬ is unrecognized


def test_tokenizer_bar_line_cell():
    # In BANA braille music, measures are separated by a blank braille cell
    # (U+2800, no dots) — plain whitespace, not a special symbol.
    tokens = BrailleTokenizer().tokenize('⠀')
    assert len(tokens) == 1
    assert tokens[0].category == SymbolCategory.BAR_LINE


def test_tokenizer_position_tracking():
    # ⠐⠹ = octave mark then C quarter note
    tokens = BrailleTokenizer().tokenize('⠐⠹')
    assert tokens[0].position == 0
    assert tokens[1].position == 1


def test_tokenizer_line_tracking():
    # Two notes on separate lines
    tokens = BrailleTokenizer().tokenize('⠹\n⠱')
    assert tokens[0].line == 1
    assert tokens[1].line == 2


def test_tokenizer_newline_not_a_token():
    tokens = BrailleTokenizer().tokenize('⠹\n⠱')
    assert len(tokens) == 2  # newline does not produce a token


def test_tokenizer_sequence_categories():
    # octave 4, C quarter, flat accidental, B half
    text = '⠐⠹⠣⠞'
    tokens = BrailleTokenizer().tokenize(text)
    assert len(tokens) == 4
    assert tokens[0].category == SymbolCategory.OCTAVE_MARK
    assert tokens[1].category == SymbolCategory.NOTE
    assert tokens[2].category == SymbolCategory.ACCIDENTAL
    assert tokens[3].category == SymbolCategory.NOTE


def test_tokenizer_token_is_dataclass():
    tokens = BrailleTokenizer().tokenize('⠹')
    t = tokens[0]
    assert isinstance(t, BrailleToken)
    assert hasattr(t, 'character')
    assert hasattr(t, 'category')
    assert hasattr(t, 'position')
    assert hasattr(t, 'line')
