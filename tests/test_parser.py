from pathlib import Path

import pytest

from dottednotes.bana_symbols import BAR_LINE_CELLS, SymbolCategory
from dottednotes.models import Score
from dottednotes.parser import BRLInputPipeline, BrailleParser, BrailleToken, BrailleTokenizer, InputPipeline


def test_braille_parser_returns_score():
    score = BrailleParser(tokens=[]).parse()
    assert isinstance(score, Score)


def test_braille_parser_empty_input_empty_score():
    score = BrailleParser(tokens=[]).parse()
    assert score.staves == []


def test_braille_parser_accepts_token_list():
    tokens = BrailleTokenizer().tokenize('⠐⠹')
    parser = BrailleParser(tokens=tokens)
    result = parser.parse()
    assert isinstance(result, Score)


def test_braille_parser_default_octave():
    parser = BrailleParser(tokens=[])
    parser._reset_state()
    assert parser._current_octave == 4


def test_braille_parser_default_key_signature():
    parser = BrailleParser(tokens=[])
    parser._reset_state()
    assert parser._key_signature == 0  # C major


def test_braille_parser_default_time_signature():
    parser = BrailleParser(tokens=[])
    parser._reset_state()
    assert parser._time_signature == (4, 4)


def test_braille_parser_state_resets_between_parses():
    parser = BrailleParser(tokens=[])
    parser.parse()
    parser._current_octave = 6  # simulate mid-parse mutation
    parser.parse()
    assert parser._current_octave == 4  # reset on second parse


# --- S2-3: octave mark recognition and tracking ---

def _parse(text: str) -> list:
    """Helper: tokenize and parse braille text, return notes from first measure."""
    tokens = BrailleTokenizer().tokenize(text)
    score = BrailleParser(tokens=tokens).parse()
    return score.staves[0].measures[0].notes


def test_octave_mark_sets_octave():
    # ⠨ = octave 5 mark, ⠹ = C quarter note
    notes = _parse('⠨⠹')
    assert notes[0].note_name == 'C'
    assert notes[0].octave == 5


def test_octave_mark_octave4():
    # ⠐ = octave 4, ⠹ = C quarter
    notes = _parse('⠐⠹')
    assert notes[0].octave == 4


def test_octave_persists_without_mark():
    # ⠐ = octave 4, ⠹ = C quarter, ⠱ = D quarter (no new octave mark)
    notes = _parse('⠐⠹⠱')
    assert notes[0].note_name == 'C'
    assert notes[0].octave == 4
    assert notes[1].note_name == 'D'
    assert notes[1].octave == 4  # octave persists


def test_octave_mark_changes_midstream():
    # ⠐ = octave 4, ⠹ = C, ⠨ = octave 5, ⠱ = D
    notes = _parse('⠐⠹⠨⠱')
    assert notes[0].octave == 4
    assert notes[1].octave == 5


def test_all_octave_marks():
    # One note per octave mark, verify each is tracked correctly
    # ⠈=oct1, ⠘=oct2, ⠸=oct3, ⠐=oct4, ⠨=oct5, ⠰=oct6, ⠠=oct7
    # Use C quarter (⠹) after each mark
    cases = [('⠈', 1), ('⠘', 2), ('⠸', 3), ('⠐', 4), ('⠨', 5), ('⠰', 6), ('⠠', 7)]
    for mark, expected_octave in cases:
        notes = _parse(mark + '⠹')
        assert notes[0].octave == expected_octave, (
            f"Octave mark {mark!r} should give octave {expected_octave}"
        )


def test_note_without_preceding_mark_uses_default_octave():
    # No octave mark — parser default is octave 4
    notes = _parse('⠹')
    assert notes[0].octave == 4


def test_note_name_from_note_cell():
    # Verify all 7 natural note names are correctly parsed from their cells
    # Using quarter-note cells, octave 4 for simplicity
    # ⠐=oct4, cells: C=⠹ D=⠱ E=⠫ F=⠻ G=⠳ A=⠪ B=⠺
    text = '⠐⠹⠱⠫⠻⠳⠪⠺'
    notes = _parse(text)
    assert [n.note_name for n in notes] == ['C', 'D', 'E', 'F', 'G', 'A', 'B']


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
