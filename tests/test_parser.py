import warnings
from pathlib import Path

import pytest

from dottednotes.bana_symbols import BAR_LINE_CELLS, BAR_LINE_SEQUENCES, SymbolCategory
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


# --- S2-4: note value ambiguity resolution (measure-level) ---
#
# The parser buffers all notes in a measure, then resolves each ambiguous
# group at the measure boundary:
#   base_duration 1 (whole/16th): if count * 4 beats > measure beats → 16th
#   base_duration 2 (half/32nd):  if count * 2 beats > measure beats → 32nd
#   base_duration 4:              always quarter
#
# Tests use ⠽=C whole/16th, ⠝=C half/32nd, ⠹=C quarter.


def test_single_whole_cell_resolves_as_whole():
    # 1 whole-class note in 4/4: 1 * 4 = 4 == 4 beats → whole (1)
    notes = _parse('⠐⠽')
    assert notes[0].duration.value == 1


def test_two_whole_cells_resolve_as_16th():
    # 2 whole-class notes in 4/4: 2 * 4 = 8 > 4 beats → 16th (16)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse('⠐⠽⠽')
    assert notes[0].duration.value == 16
    assert notes[1].duration.value == 16


def test_two_half_cells_resolve_as_half():
    # 2 half-class notes in 4/4: 2 * 2 = 4 == 4 beats → half (2)
    notes = _parse('⠐⠝⠝')
    assert notes[0].duration.value == 2
    assert notes[1].duration.value == 2


def test_three_half_cells_resolve_as_32nd():
    # 3 half-class notes in 4/4: 3 * 2 = 6 > 4 beats → 32nd (32)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse('⠐⠝⠝⠝')
    assert all(n.duration.value == 32 for n in notes)


def test_four_quarter_cells_resolve_as_quarter():
    # quarter-class notes (base_duration 4) always resolve to 4
    notes = _parse('⠐⠹⠹⠹⠹')
    assert all(n.duration.value == 4 for n in notes)


def test_quarter_note_duration_in_parsed_output():
    # ⠐=oct4, ⠹=C quarter — base_duration 4 → always 4
    notes = _parse('⠐⠹')
    assert notes[0].duration.value == 4


def test_whole_note_duration_in_parsed_output():
    # ⠐=oct4, ⠽=C whole — single note fills 4/4 exactly → whole (1)
    notes = _parse('⠐⠽')
    assert notes[0].duration.value == 1


def test_half_note_duration_in_parsed_output():
    # ⠐=oct4, ⠝=C half — single half note in 4/4 → half (2)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse('⠐⠝')
    assert notes[0].duration.value == 2


def test_validate_measure_no_warning_when_correct():
    # 4 quarter notes fills 4/4 exactly — no warning expected
    tokens = BrailleTokenizer().tokenize('⠐⠹⠹⠹⠹')
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        BrailleParser(tokens=tokens).parse()


def test_validate_measure_warns_on_mismatch():
    # 3 quarter notes in 4/4 = 3 beats, expected 4 → UserWarning
    tokens = BrailleTokenizer().tokenize('⠐⠹⠹⠹')
    with pytest.warns(UserWarning, match="Measure 1"):
        BrailleParser(tokens=tokens).parse()


# --- 8th note cells and 16th-note run detection ---
#
# 8th note cells use the bare pitch base (no dots 3 or 6).
# They default to genuine 8th notes but become 16th-note run continuations
# when they directly follow a whole/16th cell that resolved to a 16th note.
# Cells: ⠙=C ⠑=D ⠋=E ⠛=F ⠓=G ⠊=A ⠚=B (all 8th-note class, base_duration=8)


def test_eighth_note_cell_c_tokenized_as_note():
    # ⠙ = C 8th-note cell (dots 1,4,5)
    tokens = BrailleTokenizer().tokenize('⠙')
    assert tokens[0].category == SymbolCategory.NOTE


def test_all_eighth_note_cells_tokenized_as_note():
    # All 7 8th-note cells should classify as NOTE, not UNKNOWN
    tokens = BrailleTokenizer().tokenize('⠙⠑⠋⠛⠓⠊⠚')
    assert all(t.category == SymbolCategory.NOTE for t in tokens)


def test_eight_eighth_notes_resolve_to_eighth():
    # 8 × 8th note = 4 beats in 4/4 → fills measure, no ambiguity
    notes = _parse('⠐⠙⠙⠙⠙⠙⠙⠙⠙')
    assert all(n.duration.value == 8 for n in notes)


def test_eighth_note_names_all_pitch_cells():
    # Verify each 8th-note cell maps to the correct note name
    # 7 notes × 0.5 beats = 3.5 ≠ 4/4 → suppress beat-count warning
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse('⠐⠙⠑⠋⠛⠓⠊⠚')
    assert [n.note_name for n in notes] == ['C', 'D', 'E', 'F', 'G', 'A', 'B']


def test_eighth_before_16th_group_stays_eighth():
    # 2 whole/16th cells → count_1=2, 2*4=8>4 → resolve_1=16.
    # The 8th cell precedes both 16th cells, so it is a genuine 8th note.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse('⠐⠙⠽⠽')  # 8th, 16th, 16th
    assert notes[0].duration.value == 8   # genuine 8th (no preceding 16th)
    assert notes[1].duration.value == 16  # first 16th-note cell


def test_eighth_after_single_16th_cell_is_run_continuation():
    # A single base_1 cell followed by base_8 cells is a 16th-note run.
    # All four notes here are 16th notes.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse('⠐⠽⠙⠙⠙')  # 16th (run leader), run-16th × 3
    assert all(n.duration.value == 16 for n in notes)


def test_eighth_after_two_consecutive_16th_cells_is_genuine():
    # Two consecutive base_1 cells are individual 16th notes (INDIVIDUAL state).
    # A base_8 cell that follows is a genuine 8th note, not a run continuation.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse('⠐⠽⠽⠙⠙')  # 16th, 16th (individual), 8th, 8th
    assert notes[0].duration.value == 16
    assert notes[1].duration.value == 16
    assert notes[2].duration.value == 8   # genuine 8th
    assert notes[3].duration.value == 8   # genuine 8th


def test_run_ends_at_quarter_cell():
    # A single base_1 starts a run; the following base_8 is a continuation.
    # A quarter note (base_4) ends the run; the next base_8 is a genuine 8th.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse('⠐⠽⠙⠹⠙')  # 16th (run leader), run-16th, quarter, 8th
    assert notes[0].duration.value == 16  # run leader
    assert notes[1].duration.value == 16  # run continuation
    assert notes[2].duration.value == 4   # quarter ends the run
    assert notes[3].duration.value == 8   # genuine 8th after run ends


def test_single_16th_cell_starts_run_with_eighth_cells():
    # A single base_1 cell followed by base_8 cells is a 16th-note run.
    # The old count-based check (1 * 4 == 4, not > 4) would have wrongly
    # resolved the base_1 as a whole note.  The sequential rule is correct.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse('⠐⠽⠙⠙⠙')  # 16th + 3 run continuations
    assert all(n.duration.value == 16 for n in notes)


def test_consecutive_16th_cells_without_eighth_cells():
    # Three consecutive base_1 cells → all 16th notes (no base_8 needed).
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse('⠐⠽⠽⠽')
    assert all(n.duration.value == 16 for n in notes)


def test_16th_context_does_not_bleed_past_quarter():
    # A quarter (base_4) ends the 16th context; a base_1 cell after it
    # with no qualifying successor is a whole note.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse('⠐⠽⠙⠹⠽')  # 16th, run-16th, quarter, whole
    assert notes[0].duration.value == 16
    assert notes[1].duration.value == 16
    assert notes[2].duration.value == 4
    assert notes[3].duration.value == 1   # whole, not 16th


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


# --- S2-5: multi-cell bar line tokenization ---

def test_tokenizer_section_double_bar():
    # ⠣⠅⠄ (dots 1,2,6 + dots 1,3 + dot 3) → single BAR_LINE token
    tokens = BrailleTokenizer().tokenize('⠣⠅⠄')
    assert len(tokens) == 1
    assert tokens[0].category == SymbolCategory.BAR_LINE
    assert tokens[0].character == '⠣⠅⠄'


def test_tokenizer_final_double_bar():
    # ⠣⠅ (dots 1,2,6 + dots 1,3) → single BAR_LINE token
    tokens = BrailleTokenizer().tokenize('⠣⠅')
    assert len(tokens) == 1
    assert tokens[0].category == SymbolCategory.BAR_LINE
    assert tokens[0].character == '⠣⠅'


def test_tokenizer_forward_repeat():
    # ⠣⠶ (dots 1,2,6 + dots 2,3,5,6) → single BAR_LINE token
    tokens = BrailleTokenizer().tokenize('⠣⠶')
    assert len(tokens) == 1
    assert tokens[0].category == SymbolCategory.BAR_LINE
    assert tokens[0].character == '⠣⠶'


def test_tokenizer_end_repeat():
    # ⠣⠆ (dots 1,2,6 + dots 2,3) → single BAR_LINE token
    tokens = BrailleTokenizer().tokenize('⠣⠆')
    assert len(tokens) == 1
    assert tokens[0].category == SymbolCategory.BAR_LINE
    assert tokens[0].character == '⠣⠆'


def test_section_double_bar_preferred_over_final_double_bar():
    # ⠣⠅⠄ must resolve as the 3-cell section_double_bar, not ⠣⠅ + lone ⠄
    tokens = BrailleTokenizer().tokenize('⠣⠅⠄')
    assert len(tokens) == 1
    assert tokens[0].character == '⠣⠅⠄'


def test_flat_sign_not_misread_as_bar_line():
    # ⠣ followed by a note cell (not a bar line second cell) → ACCIDENTAL, not BAR_LINE
    tokens = BrailleTokenizer().tokenize('⠣⠽')  # flat + C whole/16th
    assert tokens[0].category == SymbolCategory.ACCIDENTAL
    assert all(t.category != SymbolCategory.BAR_LINE for t in tokens)


def test_flat_at_end_of_input_is_accidental():
    # ⠣ with no following cell → ACCIDENTAL
    tokens = BrailleTokenizer().tokenize('⠣')
    assert len(tokens) == 1
    assert tokens[0].category == SymbolCategory.ACCIDENTAL


def test_tokenizer_position_after_two_cell_bar_line():
    # After consuming a 2-cell forward repeat, the next token's position should be 2
    tokens = BrailleTokenizer().tokenize('⠣⠶⠐')  # forward_repeat + octave mark
    assert len(tokens) == 2
    assert tokens[0].character == '⠣⠶'
    assert tokens[0].position == 0
    assert tokens[1].category == SymbolCategory.OCTAVE_MARK
    assert tokens[1].position == 2


def test_tokenizer_position_after_three_cell_bar_line():
    # After consuming a 3-cell bar line, the next token's position should be 3
    tokens = BrailleTokenizer().tokenize('⠣⠅⠄⠐')  # section_double_bar + octave mark
    assert len(tokens) == 2
    assert tokens[0].character == '⠣⠅⠄'
    assert tokens[0].position == 0
    assert tokens[1].category == SymbolCategory.OCTAVE_MARK
    assert tokens[1].position == 3


# --- S2-5: bar_line_type on Measure objects ---

def _parse_measures(text: str) -> list:
    """Helper: tokenize and parse braille text, return all measures from first staff."""
    tokens = BrailleTokenizer().tokenize(text)
    score = BrailleParser(tokens=tokens).parse()
    return score.staves[0].measures


def test_measure_default_bar_line_type_is_measure_separator():
    # A measure ended by a blank cell has bar_line_type 'measure_separator'
    measures = _parse_measures('⠐⠹⠀⠐⠹')  # C quarter, blank bar, C quarter
    assert measures[0].bar_line_type == 'measure_separator'


def test_final_double_bar_sets_bar_line_type():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        measures = _parse_measures('⠐⠹⠣⠅')  # C quarter then final double bar
    assert measures[0].bar_line_type == 'final_double_bar'


def test_section_double_bar_sets_bar_line_type():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        measures = _parse_measures('⠐⠹⠣⠅⠄')  # C quarter then section double bar
    assert measures[0].bar_line_type == 'section_double_bar'


def test_forward_repeat_sets_bar_line_type():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        measures = _parse_measures('⠐⠹⠣⠶')  # C quarter then forward repeat
    assert measures[0].bar_line_type == 'forward_repeat'


def test_end_repeat_sets_bar_line_type():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        measures = _parse_measures('⠐⠹⠣⠆')  # C quarter then end repeat
    assert measures[0].bar_line_type == 'end_repeat'


def test_bar_line_sequences_dict_has_all_four_types():
    assert 'section_double_bar' in BAR_LINE_SEQUENCES.values()
    assert 'final_double_bar' in BAR_LINE_SEQUENCES.values()
    assert 'forward_repeat' in BAR_LINE_SEQUENCES.values()
    assert 'end_repeat' in BAR_LINE_SEQUENCES.values()
