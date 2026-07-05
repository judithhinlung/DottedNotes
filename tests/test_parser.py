import warnings
from pathlib import Path

import pytest

from dottednotes.bana_symbols import BAR_LINE_CELLS, BAR_LINE_SEQUENCES, SymbolCategory
from dottednotes.models import Articulation, ArticulationType, Clef, ClefType, Dynamic, DynamicLevel, KeySignature, Ornament, OrnamentType, Score, TimeSignature
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
    assert parser._key_signature.sharps_or_flats == 0  # C major


def test_braille_parser_default_time_signature():
    parser = BrailleParser(tokens=[])
    parser._reset_state()
    assert parser._time_signature.as_tuple() == (4, 4)


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
    # ⠠ (dots 6) acts as a literary capital indicator only in the piece header
    # (before the first key sig / time sig / note).  Once musical content appears,
    # ⠠ is the octave-7 mark as normal.
    cases = [('⠈', 1), ('⠘', 2), ('⠸', 3), ('⠐', 4), ('⠨', 5), ('⠰', 6), ('⠠', 7)]
    for mark, expected_octave in cases:
        # Precede each mark with a note in the SAME measure to ensure header_active
        # is False before the mark is seen, so ⠠ is treated as the octave-7 mark.
        notes = _parse('⠐⠹' + mark + '⠹')
        assert notes[1].octave == expected_octave, (
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
    # ⠣ after a note (not at measure start) → ACCIDENTAL, not KEY_SIGNATURE
    # At measure start ⠣ becomes KEY_SIGNATURE (1 flat); a preceding note clears that.
    tokens = BrailleTokenizer().tokenize('⠹⠣')  # C quarter, then flat accidental
    assert tokens[1].category == SymbolCategory.ACCIDENTAL


def test_tokenizer_accidental_sharp():
    # ⠩ after a note (not at measure start) → ACCIDENTAL, not KEY_SIGNATURE
    tokens = BrailleTokenizer().tokenize('⠹⠩')  # C quarter, then sharp accidental
    assert tokens[1].category == SymbolCategory.ACCIDENTAL


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
    # ⠣ between notes (after measure-start is cleared) → ACCIDENTAL, not BAR_LINE
    tokens = BrailleTokenizer().tokenize('⠹⠣⠽')  # note + flat accidental + note
    assert tokens[1].category == SymbolCategory.ACCIDENTAL
    assert all(t.category != SymbolCategory.BAR_LINE for t in tokens)


def test_flat_at_end_of_input_is_accidental():
    # ⠣ after a note (not at measure start) → ACCIDENTAL
    tokens = BrailleTokenizer().tokenize('⠹⠣')  # C quarter then flat
    assert tokens[1].category == SymbolCategory.ACCIDENTAL


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


# --- S2-6: integration test — parse simple_melody.brf ---
#
# simple_melody.brf: 8 measures, 4/4, C major, quarter and half notes only.
# Braille layout (Unicode):
#   M1  ⠐⠹⠹⠝   = oct4, C-qtr, C-qtr, C-half     (c c c2)
#   M2  ⠹⠹⠕    = C-qtr, C-qtr, D-half             (c c d2)
#   M3  ⠫⠫⠱⠹  = E-qtr, E-qtr, D-qtr, C-qtr       (e e d c)
#   M4  ⠹⠹⠝    = C-qtr, C-qtr, C-half             (c c c2)
#   M5  ⠹⠱⠫⠻  = C-qtr, D-qtr, E-qtr, F-qtr       (c d e f)
#   M6  ⠳⠪⠺⠨⠹ = G-qtr, A-qtr, B-qtr, oct5, C-qtr (g a b c5)
#   M7  ⠐⠹⠹⠹⠹ = oct4, C-qtr x4                   (c c c c)
#   M8  ⠹⠹⠝⠣⠅ = C-qtr, C-qtr, C-half, final bar  (c c c2 "|.")


def test_parse_simple_melody():
    pipeline = BRLInputPipeline()
    text = pipeline.load(FIXTURES / 'simple_melody.brf')
    tokens = BrailleTokenizer().tokenize(text)
    score = BrailleParser(tokens=tokens).parse()

    assert len(score.staves) == 1
    assert len(score.staves[0].measures) == 8

    first_note = score.staves[0].measures[0].notes[0]
    assert first_note.note_name == 'C'
    assert first_note.octave == 4
    assert first_note.duration.value == 4  # quarter note


def test_parse_simple_melody_measure_note_counts():
    pipeline = BRLInputPipeline()
    text = pipeline.load(FIXTURES / 'simple_melody.brf')
    score = BrailleParser(tokens=BrailleTokenizer().tokenize(text)).parse()
    measures = score.staves[0].measures

    assert len(measures[0].notes) == 3   # c c c2
    assert len(measures[1].notes) == 3   # c c d2
    assert len(measures[2].notes) == 4   # e e d c
    assert len(measures[5].notes) == 4   # g a b c5
    assert len(measures[6].notes) == 4   # c c c c


def test_parse_simple_melody_octave_jump_to_5():
    pipeline = BRLInputPipeline()
    text = pipeline.load(FIXTURES / 'simple_melody.brf')
    score = BrailleParser(tokens=BrailleTokenizer().tokenize(text)).parse()
    measures = score.staves[0].measures

    # Measure 6: last note is C in octave 5 (octave mark ⠨ precedes it)
    last_note_m6 = measures[5].notes[-1]
    assert last_note_m6.note_name == 'C'
    assert last_note_m6.octave == 5


def test_parse_simple_melody_octave_return_to_4():
    pipeline = BRLInputPipeline()
    text = pipeline.load(FIXTURES / 'simple_melody.brf')
    score = BrailleParser(tokens=BrailleTokenizer().tokenize(text)).parse()
    measures = score.staves[0].measures

    # Measure 7: octave mark ⠐ resets to 4; all notes are C4
    for note in measures[6].notes:
        assert note.note_name == 'C'
        assert note.octave == 4


def test_parse_simple_melody_final_bar_type():
    pipeline = BRLInputPipeline()
    text = pipeline.load(FIXTURES / 'simple_melody.brf')
    score = BrailleParser(tokens=BrailleTokenizer().tokenize(text)).parse()

    assert score.staves[0].measures[-1].bar_line_type == 'final_double_bar'


def test_parse_simple_melody_no_beat_count_warnings():
    # All 8 measures fill 4/4 exactly; no UserWarning should be emitted
    pipeline = BRLInputPipeline()
    text = pipeline.load(FIXTURES / 'simple_melody.brf')
    tokens = BrailleTokenizer().tokenize(text)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        BrailleParser(tokens=tokens).parse()


# --- S2-7: integration test — render parsed simple_melody to LilyPond ---


def test_simple_melody_renders_to_lilypond():
    pipeline = BRLInputPipeline()
    text = pipeline.load(FIXTURES / 'simple_melody.brf')
    score = BrailleParser(tokens=BrailleTokenizer().tokenize(text)).parse()

    ly_output = score.to_lilypond()

    assert isinstance(ly_output, str)
    assert len(ly_output) > 0
    assert r'\version' in ly_output
    assert r'\relative' in ly_output


def test_simple_melody_lilypond_contains_all_measures():
    pipeline = BRLInputPipeline()
    text = pipeline.load(FIXTURES / 'simple_melody.brf')
    score = BrailleParser(tokens=BrailleTokenizer().tokenize(text)).parse()

    ly_output = score.to_lilypond()
    # 8 measure barlines: 7 '|' separators + final \bar "|."
    assert ly_output.count('|') >= 8


def test_simple_melody_lilypond_relative_mode_octave_jump():
    """C5 in measure 6 must render without explicit octave marks (stepwise from B4)."""
    pipeline = BRLInputPipeline()
    text = pipeline.load(FIXTURES / 'simple_melody.brf')
    score = BrailleParser(tokens=BrailleTokenizer().tokenize(text)).parse()

    ly_output = score.to_lilypond()
    # Measure 6 stepwise ascent should contain 'g4 a4 b4 c4' (no extra ' on the c)
    assert 'g4 a4 b4 c4' in ly_output


def test_simple_melody_lilypond_relative_mode_octave_descent():
    """C4 in measure 7 (returning from C5) must render as 'c,' in relative mode."""
    pipeline = BRLInputPipeline()
    text = pipeline.load(FIXTURES / 'simple_melody.brf')
    score = BrailleParser(tokens=BrailleTokenizer().tokenize(text)).parse()

    ly_output = score.to_lilypond()
    assert 'c,4' in ly_output


def test_simple_melody_lilypond_final_bar():
    pipeline = BRLInputPipeline()
    text = pipeline.load(FIXTURES / 'simple_melody.brf')
    score = BrailleParser(tokens=BrailleTokenizer().tokenize(text)).parse()

    ly_output = score.to_lilypond()
    assert r'\bar "|."' in ly_output


def test_simple_melody_lilypond_compiles(tmp_path: Path):
    """If the lilypond binary is installed, the rendered output must compile cleanly."""
    import shutil
    import subprocess

    pipeline = BRLInputPipeline()
    text = pipeline.load(FIXTURES / 'simple_melody.brf')
    score = BrailleParser(tokens=BrailleTokenizer().tokenize(text)).parse()
    ly_output = score.to_lilypond()

    if not shutil.which('lilypond'):
        pytest.skip('lilypond binary not found; skipping compile test')

    ly_file = tmp_path / 'simple_melody.ly'
    ly_file.write_text(ly_output, encoding='utf-8')
    result = subprocess.run(
        ['lilypond', '--silent', '-o', str(tmp_path / 'simple_melody'), str(ly_file)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"LilyPond compilation failed:\n{result.stderr}"
    )


# ---------------------------------------------------------------------------
# S3-4: Key / time / clef tokenization and parser state
# ---------------------------------------------------------------------------

# --- Tokenizer: key signature ---

def test_tokenizer_key_sig_1_sharp_at_start():
    tokens = BrailleTokenizer().tokenize('⠩')   # G major (1 sharp)
    assert len(tokens) == 1
    assert tokens[0].category == SymbolCategory.KEY_SIGNATURE
    assert tokens[0].character == '⠩'


def test_tokenizer_key_sig_2_sharps_at_start():
    tokens = BrailleTokenizer().tokenize('⠩⠩')   # D major (2 sharps)
    assert len(tokens) == 1
    assert tokens[0].category == SymbolCategory.KEY_SIGNATURE
    assert tokens[0].character == '⠩⠩'


def test_tokenizer_key_sig_3_sharps_at_start():
    tokens = BrailleTokenizer().tokenize('⠩⠩⠩')   # A major (3 sharps)
    assert len(tokens) == 1
    assert tokens[0].category == SymbolCategory.KEY_SIGNATURE
    assert tokens[0].character == '⠩⠩⠩'


def test_tokenizer_key_sig_4_sharps():
    # ⠼⠙⠩ = E major (4 sharps), number-sign prefix
    tokens = BrailleTokenizer().tokenize('⠼⠙⠩')
    assert len(tokens) == 1
    assert tokens[0].category == SymbolCategory.KEY_SIGNATURE
    assert tokens[0].character == '⠼⠙⠩'


def test_tokenizer_key_sig_1_flat_at_start():
    tokens = BrailleTokenizer().tokenize('⠣')   # F major (1 flat), at piece start
    assert len(tokens) == 1
    assert tokens[0].category == SymbolCategory.KEY_SIGNATURE


def test_tokenizer_key_sig_3_flats_at_start():
    tokens = BrailleTokenizer().tokenize('⠣⠣⠣')   # Eb major (3 flats)
    assert len(tokens) == 1
    assert tokens[0].category == SymbolCategory.KEY_SIGNATURE
    assert tokens[0].character == '⠣⠣⠣'


def test_tokenizer_key_sig_4_flats():
    # ⠼⠙⠣ = Ab major (4 flats)
    tokens = BrailleTokenizer().tokenize('⠼⠙⠣')
    assert len(tokens) == 1
    assert tokens[0].category == SymbolCategory.KEY_SIGNATURE
    assert tokens[0].character == '⠼⠙⠣'


# --- Tokenizer: time signature ---

def test_tokenizer_time_sig_4_4():
    # ⠼⠙⠲ = 4/4
    tokens = BrailleTokenizer().tokenize('⠼⠙⠲')
    assert len(tokens) == 1
    assert tokens[0].category == SymbolCategory.TIME_SIGNATURE
    assert tokens[0].character == '⠼⠙⠲'


def test_tokenizer_time_sig_6_8():
    # ⠼⠋⠦ = 6/8
    tokens = BrailleTokenizer().tokenize('⠼⠋⠦')
    assert len(tokens) == 1
    assert tokens[0].category == SymbolCategory.TIME_SIGNATURE


def test_tokenizer_number_sign_distinguishes_key_from_time():
    # ⠼⠙⠩ = E major key sig, ⠼⠙⠲ = 4/4 time sig — same digits, different third cell
    ks = BrailleTokenizer().tokenize('⠼⠙⠩')
    ts = BrailleTokenizer().tokenize('⠼⠙⠲')
    assert ks[0].category == SymbolCategory.KEY_SIGNATURE
    assert ts[0].category == SymbolCategory.TIME_SIGNATURE


# --- Tokenizer: clef ---

def test_tokenizer_treble_clef():
    tokens = BrailleTokenizer().tokenize('⠜⠌⠇')   # G clef
    assert len(tokens) == 1
    assert tokens[0].category == SymbolCategory.CLEF
    assert tokens[0].character == '⠜⠌⠇'


def test_tokenizer_bass_clef():
    tokens = BrailleTokenizer().tokenize('⠜⠼⠇')   # F clef
    assert len(tokens) == 1
    assert tokens[0].category == SymbolCategory.CLEF


def test_tokenizer_alto_clef():
    tokens = BrailleTokenizer().tokenize('⠜⠬⠇')   # C clef (alto)
    assert len(tokens) == 1
    assert tokens[0].category == SymbolCategory.CLEF
    assert tokens[0].character == '⠜⠬⠇'


def test_tokenizer_tenor_clef():
    # Tenor clef is 4 cells: ⠜⠬⠐⠇ (dots 3,4,5 + 3,4,6 + 5 + 1,2,3)
    tokens = BrailleTokenizer().tokenize('⠜⠬⠐⠇')
    assert len(tokens) == 1
    assert tokens[0].category == SymbolCategory.CLEF
    assert tokens[0].character == '⠜⠬⠐⠇'


def test_tokenizer_tenor_not_confused_with_alto():
    # Alto = 3 cells ⠜⠬⠇; tenor = 4 cells ⠜⠬⠐⠇ — longest match wins
    alto = BrailleTokenizer().tokenize('⠜⠬⠇')
    tenor = BrailleTokenizer().tokenize('⠜⠬⠐⠇')
    assert alto[0].character == '⠜⠬⠇'
    assert tenor[0].character == '⠜⠬⠐⠇'


# --- Tokenizer: sharp/flat as accidental after a note ---

def test_sharp_after_note_is_accidental_not_key_sig():
    # at_measure_start is False after a note, so ⠩ → ACCIDENTAL
    tokens = BrailleTokenizer().tokenize('⠐⠗⠩⠙')  # octave + G-half + sharp + C-8th
    cats = [t.category for t in tokens]
    assert SymbolCategory.ACCIDENTAL in cats
    assert SymbolCategory.KEY_SIGNATURE not in cats


def test_flat_after_note_is_accidental_not_key_sig():
    tokens = BrailleTokenizer().tokenize('⠐⠗⠣⠙')  # octave + G-half + flat + C-8th
    cats = [t.category for t in tokens]
    assert SymbolCategory.ACCIDENTAL in cats
    assert SymbolCategory.KEY_SIGNATURE not in cats


# --- Parser state after parsing key/time/clef tokens ---

def _make_token(char: str, category: SymbolCategory) -> BrailleToken:
    return BrailleToken(character=char, category=category, position=0, line=1)


def test_parser_reads_1_sharp_key_signature():
    # Feed a G-major key sig token + a note so the staff is non-empty
    tokens = [
        _make_token('⠩', SymbolCategory.KEY_SIGNATURE),
        _make_token('⠐', SymbolCategory.OCTAVE_MARK),
        _make_token('⠹', SymbolCategory.NOTE),
        _make_token('⠀', SymbolCategory.BAR_LINE),
    ]
    parser = BrailleParser(tokens=tokens)
    parser.parse()
    assert parser._key_signature_parsed
    assert parser._key_signature.sharps_or_flats == 1


def test_parser_reads_4_sharp_key_signature():
    tokens = [
        _make_token('⠼⠙⠩', SymbolCategory.KEY_SIGNATURE),
        _make_token('⠐', SymbolCategory.OCTAVE_MARK),
        _make_token('⠹', SymbolCategory.NOTE),
        _make_token('⠀', SymbolCategory.BAR_LINE),
    ]
    parser = BrailleParser(tokens=tokens)
    parser.parse()
    assert parser._key_signature.sharps_or_flats == 4


def test_parser_reads_time_signature_3_4():
    tokens = [
        _make_token('⠼⠉⠲', SymbolCategory.TIME_SIGNATURE),
        _make_token('⠐', SymbolCategory.OCTAVE_MARK),
        _make_token('⠹', SymbolCategory.NOTE),
        _make_token('⠀', SymbolCategory.BAR_LINE),
    ]
    parser = BrailleParser(tokens=tokens)
    parser.parse()
    assert parser._time_signature_parsed
    assert parser._time_signature.numerator == 3
    assert parser._time_signature.denominator == 4


def test_parser_reads_treble_clef():
    tokens = [
        _make_token('⠜⠌⠇', SymbolCategory.CLEF),
        _make_token('⠐', SymbolCategory.OCTAVE_MARK),
        _make_token('⠹', SymbolCategory.NOTE),
        _make_token('⠀', SymbolCategory.BAR_LINE),
    ]
    parser = BrailleParser(tokens=tokens)
    parser.parse()
    assert parser._clef_parsed
    assert parser._clef.clef_type == ClefType.TREBLE


def test_parser_reads_bass_clef():
    tokens = [
        _make_token('⠜⠼⠇', SymbolCategory.CLEF),
        _make_token('⠐', SymbolCategory.OCTAVE_MARK),
        _make_token('⠹', SymbolCategory.NOTE),
        _make_token('⠀', SymbolCategory.BAR_LINE),
    ]
    parser = BrailleParser(tokens=tokens)
    parser.parse()
    assert parser._clef.clef_type == ClefType.BASS


# --- Staff header directives in to_lilypond() ---

def test_staff_emits_key_directive_for_non_c_major():
    tokens = [
        _make_token('⠩', SymbolCategory.KEY_SIGNATURE),       # 1 sharp (G major)
        _make_token('⠼⠙⠲', SymbolCategory.TIME_SIGNATURE),   # 4/4
        _make_token('⠐', SymbolCategory.OCTAVE_MARK),
        _make_token('⠹', SymbolCategory.NOTE),
        _make_token('⠀', SymbolCategory.BAR_LINE),
    ]
    score = BrailleParser(tokens=tokens).parse()
    ly = score.to_lilypond()
    assert r'\key g \major' in ly
    assert r'\time 4/4' in ly


def test_staff_omits_key_directive_for_c_major():
    # No key sig token → staff.key_signature is None → no \key line emitted
    tokens = [
        _make_token('⠐', SymbolCategory.OCTAVE_MARK),
        _make_token('⠹', SymbolCategory.NOTE),
        _make_token('⠀', SymbolCategory.BAR_LINE),
    ]
    score = BrailleParser(tokens=tokens).parse()
    ly = score.to_lilypond()
    assert r'\key' not in ly


def test_staff_omits_time_directive_when_not_in_file():
    tokens = [
        _make_token('⠐', SymbolCategory.OCTAVE_MARK),
        _make_token('⠹', SymbolCategory.NOTE),
        _make_token('⠀', SymbolCategory.BAR_LINE),
    ]
    score = BrailleParser(tokens=tokens).parse()
    ly = score.to_lilypond()
    assert r'\time' not in ly


def test_staff_emits_clef_directive_for_bass():
    tokens = [
        _make_token('⠜⠼⠇', SymbolCategory.CLEF),
        _make_token('⠐', SymbolCategory.OCTAVE_MARK),
        _make_token('⠹', SymbolCategory.NOTE),
        _make_token('⠀', SymbolCategory.BAR_LINE),
    ]
    score = BrailleParser(tokens=tokens).parse()
    ly = score.to_lilypond()
    assert r'\clef bass' in ly


def test_staff_emits_treble_clef_for_explicit_treble_clef():
    # Explicit treble clef cell in the BRF → \clef treble emitted
    tokens = [
        _make_token('⠜⠌⠇', SymbolCategory.CLEF),
        _make_token('⠐', SymbolCategory.OCTAVE_MARK),
        _make_token('⠹', SymbolCategory.NOTE),
        _make_token('⠀', SymbolCategory.BAR_LINE),
    ]
    score = BrailleParser(tokens=tokens).parse()
    ly = score.to_lilypond()
    assert r'\clef treble' in ly


def test_staff_emits_treble_clef_heuristic_for_octave_4():
    # No explicit clef cell; first note at octave 4 (middle C) → heuristic → treble
    tokens = [
        _make_token('⠐', SymbolCategory.OCTAVE_MARK),   # octave 4
        _make_token('⠹', SymbolCategory.NOTE),
        _make_token('⠀', SymbolCategory.BAR_LINE),
    ]
    score = BrailleParser(tokens=tokens).parse()
    ly = score.to_lilypond()
    assert r'\clef treble' in ly


def test_staff_emits_bass_clef_heuristic_for_octave_3():
    # No explicit clef cell; first note at octave 3 → heuristic → bass
    tokens = [
        _make_token('⠸', SymbolCategory.OCTAVE_MARK),   # octave 3
        _make_token('⠹', SymbolCategory.NOTE),
        _make_token('⠀', SymbolCategory.BAR_LINE),
    ]
    score = BrailleParser(tokens=tokens).parse()
    ly = score.to_lilypond()
    assert r'\clef bass' in ly


def test_staff_emits_bass_clef_heuristic_for_octave_2():
    tokens = [
        _make_token('⠘', SymbolCategory.OCTAVE_MARK),   # octave 2
        _make_token('⠹', SymbolCategory.NOTE),
        _make_token('⠀', SymbolCategory.BAR_LINE),
    ]
    score = BrailleParser(tokens=tokens).parse()
    ly = score.to_lilypond()
    assert r'\clef bass' in ly


# --- S3-4: ⠩/⠣ disambiguation — single sharp/flat lookahead ---
#
# A single ⠩ (sharp, dots 1,4,6) or ⠣ (flat, dots 1,2,6) at a measure boundary
# is KEY_SIGNATURE only when followed by the number sign ⠼ (meaning a time
# signature follows on the same line) or by whitespace/end-of-input (key sig
# alone on its own line).  When followed by a note or octave mark it must be
# treated as a sharp/flat accidental, not a key signature.

def test_tokenizer_single_sharp_before_note_is_accidental():
    # ⠩ at measure start followed immediately by a note cell → ACCIDENTAL
    tokens = BrailleTokenizer().tokenize('⠩⠹')
    assert tokens[0].category == SymbolCategory.ACCIDENTAL
    assert tokens[1].category == SymbolCategory.NOTE


def test_tokenizer_g_major_4_4_together():
    # dots 1,4,6 + 3,4,5,6 + 1,4,5 + 2,5,6 → G major (1 sharp) + 4/4 time
    # ⠩ is followed by ⠼ (number sign) → classified as KEY_SIGNATURE
    tokens = BrailleTokenizer().tokenize('⠩⠼⠙⠲')
    assert len(tokens) == 2
    assert tokens[0].category == SymbolCategory.KEY_SIGNATURE
    assert tokens[0].character == '⠩'
    assert tokens[1].category == SymbolCategory.TIME_SIGNATURE
    assert tokens[1].character == '⠼⠙⠲'


def test_parser_g_major_4_4_together():
    # Full integration: ⠩⠼⠙⠲ → G major (sharps_or_flats=1) + 4/4 time
    parser = BrailleParser(tokens=BrailleTokenizer().tokenize('⠩⠼⠙⠲'))
    parser.parse()
    assert parser._key_signature_parsed
    assert parser._key_signature.sharps_or_flats == 1
    assert parser._time_signature_parsed
    assert parser._time_signature.as_tuple() == (4, 4)


def test_tokenizer_f_major_2_4_together():
    # dots 1,2,6 + 3,4,5,6 + 1,2 + 2,5,6 → F major (1 flat) + 2/4 time
    # ⠣ is followed by ⠼ (number sign) → classified as KEY_SIGNATURE
    tokens = BrailleTokenizer().tokenize('⠣⠼⠃⠲')
    assert len(tokens) == 2
    assert tokens[0].category == SymbolCategory.KEY_SIGNATURE
    assert tokens[0].character == '⠣'
    assert tokens[1].category == SymbolCategory.TIME_SIGNATURE
    assert tokens[1].character == '⠼⠃⠲'


def test_parser_f_major_2_4_together():
    # Full integration: ⠣⠼⠃⠲ → F major (sharps_or_flats=-1) + 2/4 time
    parser = BrailleParser(tokens=BrailleTokenizer().tokenize('⠣⠼⠃⠲'))
    parser.parse()
    assert parser._key_signature_parsed
    assert parser._key_signature.sharps_or_flats == -1
    assert parser._time_signature_parsed
    assert parser._time_signature.as_tuple() == (2, 4)


# --- Accidental attachment to notes ---
#
# In BANA braille, an accidental cell immediately precedes the note it modifies.
# dots 1,2,6 + dots 1,2,4,6 = flat (⠣) + E quarter (⠫) = E-flat quarter note.
# The parser buffers a pending accidental and attaches it to the next NOTE seen.
# After that note the pending accidental is cleared (it does not carry forward).

def test_accidental_flat_attaches_to_following_note():
    # ⠣⠫ (flat + E quarter) at piece start → E-flat quarter, not F-major key sig
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse('⠣⠫')
    assert notes[0].note_name == 'E'
    assert notes[0].accidental is not None
    assert notes[0].accidental.type.name == 'FLAT'


def test_accidental_sharp_attaches_to_following_note():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse('⠐⠩⠫')   # octave 4 + sharp + E quarter → E-sharp quarter
    assert notes[0].note_name == 'E'
    assert notes[0].accidental.type.name == 'SHARP'


def test_accidental_natural_attaches_to_following_note():
    # ⠡ = natural (dots 1,6)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse('⠐⠡⠫')   # octave 4 + natural + E quarter
    assert notes[0].note_name == 'E'
    assert notes[0].accidental.type.name == 'NATURAL'


def test_e_flat_quarter_renders_as_ees_in_lilypond():
    # E-flat uses LilyPond's 'es' suffix: E + 'es' = 'ees'
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse('⠐⠣⠫')   # octave 4 + flat + E quarter
    assert notes[0].to_lilypond().startswith('ees')


def test_accidental_does_not_carry_forward_to_next_note():
    # After the flat E, the following E note should carry no accidental
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse('⠐⠣⠫⠫')   # octave 4, flat E, plain E
    assert notes[0].accidental is not None   # first note: E-flat
    assert notes[1].accidental is None       # second note: plain E


def test_note_without_preceding_accidental_has_none():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse('⠐⠫')   # octave 4 + plain E quarter
    assert notes[0].accidental is None


# ---------------------------------------------------------------------------
# S3-5: Integration test — parse a non-C-major piece (G major scale)
# ---------------------------------------------------------------------------
#
# g_major_scale.brf: 2 measures, 4/4, G major (1 sharp), all quarter notes.
# Line 1 (header):  leading blank cells + ⠩ (G major key sig) + ⠼⠙⠲ (4/4)
# Line 2 (music):   ⠐⠳⠪⠺⠹ ⠀ ⠱⠫⠩⠻⠳ ⠣⠅
#   Measure 1: oct4, G-qtr, A-qtr, B-qtr, C-qtr
#   Measure 2: D-qtr, E-qtr, F#-qtr (explicit sharp accidental), G-qtr, final bar


def test_parse_g_major_scale():
    pipeline = BRLInputPipeline()
    text = pipeline.load(FIXTURES / 'g_major_scale.brf')
    score = BrailleParser(tokens=BrailleTokenizer().tokenize(text)).parse()

    assert len(score.staves) == 1
    staff = score.staves[0]

    assert staff.key_signature.sharps_or_flats == 1

    assert staff.time_signature.numerator == 4
    assert staff.time_signature.denominator == 4

    assert len(staff.measures) == 2
    assert len(staff.measures[0].notes) == 4
    assert len(staff.measures[1].notes) == 4

    first_note = staff.measures[0].notes[0]
    assert first_note.note_name == 'G'
    assert first_note.octave == 4
    assert first_note.duration.value == 4


def test_parse_g_major_scale_all_notes():
    pipeline = BRLInputPipeline()
    text = pipeline.load(FIXTURES / 'g_major_scale.brf')
    score = BrailleParser(tokens=BrailleTokenizer().tokenize(text)).parse()
    staff = score.staves[0]

    m1_names = [n.note_name for n in staff.measures[0].notes]
    m2_names = [n.note_name for n in staff.measures[1].notes]
    assert m1_names == ['G', 'A', 'B', 'C']
    assert m2_names == ['D', 'E', 'F', 'G']

    fsharp = staff.measures[1].notes[2]
    assert fsharp.note_name == 'F'
    assert fsharp.accidental is not None
    assert fsharp.accidental.type.name == 'SHARP'


def test_parse_g_major_scale_final_bar():
    pipeline = BRLInputPipeline()
    text = pipeline.load(FIXTURES / 'g_major_scale.brf')
    score = BrailleParser(tokens=BrailleTokenizer().tokenize(text)).parse()
    assert score.staves[0].measures[-1].bar_line_type == 'final_double_bar'


def test_parse_g_major_scale_no_beat_count_warnings():
    pipeline = BRLInputPipeline()
    text = pipeline.load(FIXTURES / 'g_major_scale.brf')
    tokens = BrailleTokenizer().tokenize(text)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        BrailleParser(tokens=tokens).parse()


def test_g_major_scale_renders_to_lilypond():
    pipeline = BRLInputPipeline()
    text = pipeline.load(FIXTURES / 'g_major_scale.brf')
    score = BrailleParser(tokens=BrailleTokenizer().tokenize(text)).parse()

    ly = score.to_lilypond()

    assert isinstance(ly, str)
    assert len(ly) > 0
    assert r'\version' in ly
    assert r'\key g \major' in ly
    assert r'\time 4/4' in ly
    assert r'\clef treble' in ly
    assert 'fis' in ly


def test_g_major_scale_lilypond_compiles(tmp_path: Path):
    """If the lilypond binary is installed, the rendered output must compile cleanly."""
    import shutil
    import subprocess

    pipeline = BRLInputPipeline()
    text = pipeline.load(FIXTURES / 'g_major_scale.brf')
    score = BrailleParser(tokens=BrailleTokenizer().tokenize(text)).parse()
    ly_output = score.to_lilypond()

    if not shutil.which('lilypond'):
        pytest.skip('lilypond binary not found; skipping compile test')

    ly_file = tmp_path / 'g_major_scale.ly'
    ly_file.write_text(ly_output, encoding='utf-8')
    result = subprocess.run(
        ['lilypond', '--silent', '-o', str(tmp_path / 'g_major_scale'), str(ly_file)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"LilyPond compilation failed:\n{result.stderr}"
    )


# ---------------------------------------------------------------------------
# S4-1: Articulation tokenization and parsing
# ---------------------------------------------------------------------------

# --- Tokenizer: articulation cells ---

def test_tokenizer_staccato_single_cell():
    # ⠦ = dots 2,3,6 — staccato (single cell)
    tokens = BrailleTokenizer().tokenize('⠦')
    assert len(tokens) == 1
    assert tokens[0].category == SymbolCategory.ARTICULATION
    assert tokens[0].character == '⠦'


def test_tokenizer_staccatissimo_two_cells():
    # ⠠⠦ = dots 6 + dots 2,3,6 — staccatissimo
    tokens = BrailleTokenizer().tokenize('⠠⠦')
    assert len(tokens) == 1
    assert tokens[0].category == SymbolCategory.ARTICULATION
    assert tokens[0].character == '⠠⠦'


def test_tokenizer_mezzo_staccato_two_cells():
    # ⠐⠦ = dots 5 + dots 2,3,6 — mezzo staccato
    # ⠐ is also octave 4 mark; the 2-cell pair must be preferred.
    tokens = BrailleTokenizer().tokenize('⠐⠦')
    assert len(tokens) == 1
    assert tokens[0].category == SymbolCategory.ARTICULATION
    assert tokens[0].character == '⠐⠦'


def test_tokenizer_tenuto_two_cells():
    # ⠸⠦ = dots 4,5,6 + dots 2,3,6 — tenuto
    # ⠸ is also octave 3 mark; the 2-cell pair must be preferred.
    tokens = BrailleTokenizer().tokenize('⠸⠦')
    assert len(tokens) == 1
    assert tokens[0].category == SymbolCategory.ARTICULATION
    assert tokens[0].character == '⠸⠦'


def test_tokenizer_accent_two_cells():
    # ⠨⠦ = dots 4,6 + dots 2,3,6 — accent
    # ⠨ is also octave 5 mark; the 2-cell pair must be preferred.
    tokens = BrailleTokenizer().tokenize('⠨⠦')
    assert len(tokens) == 1
    assert tokens[0].category == SymbolCategory.ARTICULATION
    assert tokens[0].character == '⠨⠦'


def test_tokenizer_expressive_accent_two_cells():
    # ⠘⠦ = dots 4,5 + dots 2,3,6 — expressive accent
    # ⠘ is also octave 2 mark; the 2-cell pair must be preferred.
    tokens = BrailleTokenizer().tokenize('⠘⠦')
    assert len(tokens) == 1
    assert tokens[0].category == SymbolCategory.ARTICULATION
    assert tokens[0].character == '⠘⠦'


def test_tokenizer_swell_two_cells():
    # ⠤⠄ = dots 3,6 + dot 3 — swell
    tokens = BrailleTokenizer().tokenize('⠤⠄')
    assert len(tokens) == 1
    assert tokens[0].category == SymbolCategory.ARTICULATION
    assert tokens[0].character == '⠤⠄'


def test_tokenizer_octave_mark_alone_still_works():
    # ⠐ alone (not followed by ⠦) must remain an OCTAVE_MARK, not ARTICULATION
    tokens = BrailleTokenizer().tokenize('⠐⠹')
    assert tokens[0].category == SymbolCategory.OCTAVE_MARK
    assert tokens[1].category == SymbolCategory.NOTE


def test_tokenizer_articulation_before_note():
    # ⠦⠐⠹ = staccato + octave 4 + C quarter
    tokens = BrailleTokenizer().tokenize('⠦⠐⠹')
    assert tokens[0].category == SymbolCategory.ARTICULATION
    assert tokens[1].category == SymbolCategory.OCTAVE_MARK
    assert tokens[2].category == SymbolCategory.NOTE


# --- Parser: single articulation applied to one note ---

def test_parser_staccato_attaches_to_note():
    # ⠦ staccato + octave 4 + C quarter
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse('⠦⠐⠹')
    assert len(notes[0].articulations) == 1
    assert notes[0].articulations[0].type == ArticulationType.STACCATO


def test_parser_staccato_does_not_carry_forward():
    # Single staccato applies to one note only; second note has no articulation.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse('⠦⠐⠹⠹')
    assert len(notes[0].articulations) == 1
    assert len(notes[1].articulations) == 0


def test_parser_tenuto_attaches_to_note():
    # ⠸⠦ tenuto + octave 4 + C quarter
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse('⠸⠦⠐⠹')
    assert notes[0].articulations[0].type == ArticulationType.TENUTO


def test_parser_accent_attaches_to_note():
    # ⠨⠦ accent + octave 4 + C quarter
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse('⠨⠦⠐⠹')
    assert notes[0].articulations[0].type == ArticulationType.ACCENT


def test_parser_note_with_no_articulation():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse('⠐⠹')
    assert notes[0].articulations == []


# --- Parser: doubled articulation sign activates carry mode ---

def test_parser_doubled_staccato_applies_to_all_following_notes():
    # ⠦⠦ (doubled staccato) then four C quarters in 4/4 — all should be staccato.
    notes = _parse('⠦⠦⠐⠹⠹⠹⠹')
    assert all(len(n.articulations) == 1 for n in notes)
    assert all(n.articulations[0].type == ArticulationType.STACCATO for n in notes)


def test_parser_doubled_staccato_ends_on_third_sign():
    # ⠦⠦ C C C ⠦ C C: carry on first 4 Cs (including terminator C), then off.
    # notes[0..2]: carry, notes[3]: terminator note, notes[4]: no staccato
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse('⠦⠦⠐⠹⠹⠹⠦⠹⠹')
    assert notes[0].articulations[0].type == ArticulationType.STACCATO  # carry
    assert notes[1].articulations[0].type == ArticulationType.STACCATO  # carry
    assert notes[2].articulations[0].type == ArticulationType.STACCATO  # carry
    assert notes[3].articulations[0].type == ArticulationType.STACCATO  # terminator note
    assert notes[4].articulations == []                                  # carry ended


# --- Parser: articulation renders to LilyPond ---

def test_parser_staccato_renders_to_lilypond():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse('⠦⠐⠹')
    assert '-.' in notes[0].to_lilypond()


def test_parser_tenuto_renders_to_lilypond():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse('⠸⠦⠐⠹')
    assert '--' in notes[0].to_lilypond()


# ---------------------------------------------------------------------------
# S4-2: Dynamic tokenization and parsing
# ---------------------------------------------------------------------------

# Verified BANA dynamic sequences (word sign ⠜ + dynamic letters):
_DYN_P   = '⠜⠏'     # p   — word sign + p (dots 1,2,3,4)
_DYN_PP  = '⠜⠏⠏'   # pp  — word sign + p + p
_DYN_PPP = '⠜⠏⠏⠏' # ppp — word sign + p + p + p
_DYN_F   = '⠜⠋'     # f   — word sign + f (dots 1,2,4)
_DYN_FF  = '⠜⠋⠋'   # ff  — word sign + f + f
_DYN_FFF = '⠜⠋⠋⠋' # fff — word sign + f + f + f
_DYN_MP  = '⠜⠍⠏'   # mp  — word sign + m + p
_DYN_MF  = '⠜⠍⠋'   # mf  — word sign + m + f
_DYN_SF  = '⠜⠎⠋'   # sf  — word sign + s + f
_DYN_SFZ = '⠜⠎⠋⠵' # sfz — word sign + s + f + z
_DYN_FP  = '⠜⠋⠏'   # fp  — word sign + f + p
_DYN_CRESC_START  = '⠜⠉'  # crescendo start  — word sign + c (dots 1,4)
_DYN_DECRESC_START = '⠜⠙' # decrescendo start — word sign + d (dots 1,4,5)
_DYN_CRESC_END    = '⠜⠒'  # crescendo end    — word sign + lower c (dots 2,5)
_DYN_DECRESC_END  = '⠜⠲'  # decrescendo end  — word sign + lower d (dots 2,5,6)
_END_WORD_SIGN = '⠄'        # dot 3 — terminator before a note starting with dots 1,2,3


# --- Tokenizer: dynamic cell recognition ---

def test_tokenizer_dynamic_p():
    tokens = BrailleTokenizer().tokenize(_DYN_P)
    assert len(tokens) == 1
    assert tokens[0].category == SymbolCategory.DYNAMIC
    assert tokens[0].character == _DYN_P


def test_tokenizer_dynamic_pp():
    tokens = BrailleTokenizer().tokenize(_DYN_PP)
    assert len(tokens) == 1
    assert tokens[0].category == SymbolCategory.DYNAMIC
    assert tokens[0].character == _DYN_PP


def test_tokenizer_dynamic_ppp():
    tokens = BrailleTokenizer().tokenize(_DYN_PPP)
    assert len(tokens) == 1
    assert tokens[0].category == SymbolCategory.DYNAMIC
    assert tokens[0].character == _DYN_PPP


def test_tokenizer_dynamic_f():
    tokens = BrailleTokenizer().tokenize(_DYN_F)
    assert len(tokens) == 1
    assert tokens[0].category == SymbolCategory.DYNAMIC


def test_tokenizer_dynamic_ff():
    tokens = BrailleTokenizer().tokenize(_DYN_FF)
    assert len(tokens) == 1
    assert tokens[0].category == SymbolCategory.DYNAMIC
    assert tokens[0].character == _DYN_FF


def test_tokenizer_dynamic_fff():
    tokens = BrailleTokenizer().tokenize(_DYN_FFF)
    assert len(tokens) == 1
    assert tokens[0].category == SymbolCategory.DYNAMIC
    assert tokens[0].character == _DYN_FFF


def test_tokenizer_dynamic_mp():
    tokens = BrailleTokenizer().tokenize(_DYN_MP)
    assert len(tokens) == 1
    assert tokens[0].category == SymbolCategory.DYNAMIC
    assert tokens[0].character == _DYN_MP


def test_tokenizer_dynamic_mf():
    tokens = BrailleTokenizer().tokenize(_DYN_MF)
    assert len(tokens) == 1
    assert tokens[0].category == SymbolCategory.DYNAMIC


def test_tokenizer_dynamic_sfz():
    tokens = BrailleTokenizer().tokenize(_DYN_SFZ)
    assert len(tokens) == 1
    assert tokens[0].category == SymbolCategory.DYNAMIC
    assert tokens[0].character == _DYN_SFZ


def test_tokenizer_dynamic_crescendo_start():
    tokens = BrailleTokenizer().tokenize(_DYN_CRESC_START)
    assert len(tokens) == 1
    assert tokens[0].category == SymbolCategory.DYNAMIC
    assert tokens[0].character == _DYN_CRESC_START


def test_tokenizer_dynamic_decrescendo_start():
    tokens = BrailleTokenizer().tokenize(_DYN_DECRESC_START)
    assert len(tokens) == 1
    assert tokens[0].category == SymbolCategory.DYNAMIC
    assert tokens[0].character == _DYN_DECRESC_START


def test_tokenizer_dynamic_crescendo_end():
    tokens = BrailleTokenizer().tokenize(_DYN_CRESC_END)
    assert len(tokens) == 1
    assert tokens[0].category == SymbolCategory.DYNAMIC
    assert tokens[0].character == _DYN_CRESC_END


def test_tokenizer_dynamic_decrescendo_end():
    tokens = BrailleTokenizer().tokenize(_DYN_DECRESC_END)
    assert len(tokens) == 1
    assert tokens[0].category == SymbolCategory.DYNAMIC
    assert tokens[0].character == _DYN_DECRESC_END


def test_tokenizer_dynamic_with_end_word_sign():
    # ⠜⠏⠄ — piano followed by end word sign; the ⠄ is consumed, result is one DYNAMIC token
    tokens = BrailleTokenizer().tokenize(_DYN_P + _END_WORD_SIGN)
    assert len(tokens) == 1
    assert tokens[0].category == SymbolCategory.DYNAMIC
    assert tokens[0].character == _DYN_P


def test_tokenizer_dynamic_end_word_sign_before_note():
    # ⠜⠏⠄⠐⠹ — piano + end word sign + octave 4 + C quarter
    tokens = BrailleTokenizer().tokenize(_DYN_P + _END_WORD_SIGN + '⠐⠹')
    cats = [t.category for t in tokens]
    assert cats == [SymbolCategory.DYNAMIC, SymbolCategory.OCTAVE_MARK, SymbolCategory.NOTE]


def test_tokenizer_dynamic_ppp_preferred_over_pp():
    # Longest match: ⠜⠏⠏⠏ must be a single ppp token, not pp + stray ⠏
    tokens = BrailleTokenizer().tokenize(_DYN_PPP)
    assert len(tokens) == 1
    assert tokens[0].character == _DYN_PPP


def test_tokenizer_dynamic_sfz_preferred_over_sf():
    # Longest match: ⠜⠎⠋⠵ must be sfz, not sf + stray ⠵
    tokens = BrailleTokenizer().tokenize(_DYN_SFZ)
    assert len(tokens) == 1
    assert tokens[0].character == _DYN_SFZ


def test_tokenizer_clef_not_confused_with_dynamic():
    # ⠜⠌⠇ must still be CLEF, not DYNAMIC
    tokens = BrailleTokenizer().tokenize('⠜⠌⠇')
    assert len(tokens) == 1
    assert tokens[0].category == SymbolCategory.CLEF


# --- Parser: dynamic attachment to notes ---

def test_parser_dynamic_p_attaches_to_note():
    # ⠜⠏ (piano) + octave 4 + C quarter
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse(_DYN_P + '⠐⠹')
    assert len(notes[0].dynamics) == 1
    assert notes[0].dynamics[0].level == DynamicLevel.P


def test_parser_dynamic_p_does_not_carry_forward():
    # Piano applies to the first note only; second note has no dynamic.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse(_DYN_P + '⠐⠹⠹')
    assert len(notes[0].dynamics) == 1
    assert notes[1].dynamics == []


def test_parser_dynamic_f_attaches_to_note():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse(_DYN_F + '⠐⠹')
    assert notes[0].dynamics[0].level == DynamicLevel.F


def test_parser_crescendo_start_attaches_to_note():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse(_DYN_CRESC_START + '⠐⠹')
    assert notes[0].dynamics[0].level == DynamicLevel.CRESCENDO_START


def test_parser_crescendo_end_attaches_to_preceding_note():
    # Token stream: C quarter, C quarter, crescendo_end, C quarter
    # The crescendo_end must attach to the SECOND C, not the third.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse('⠐⠹⠹' + _DYN_CRESC_END + _END_WORD_SIGN + '⠹')
    assert notes[1].dynamics[0].level == DynamicLevel.CRESCENDO_END
    assert notes[0].dynamics == []
    assert notes[2].dynamics == []


def test_parser_note_with_no_dynamic():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse('⠐⠹')
    assert notes[0].dynamics == []


# --- Parser: dynamic renders to LilyPond ---

def test_parser_dynamic_p_renders_to_lilypond():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse(_DYN_P + '⠐⠹')
    assert r'\p' in notes[0].to_lilypond()


def test_parser_crescendo_renders_to_lilypond():
    # Crescendo start on first note, end on second, nothing on third.
    notes = _parse(_DYN_CRESC_START + '⠐⠹⠹' + _DYN_CRESC_END + _END_WORD_SIGN + '⠹⠹')
    assert r'\<' in notes[0].to_lilypond()
    assert r'\!' in notes[1].to_lilypond()
    assert notes[2].dynamics == []


def test_parser_dynamic_with_end_word_sign_before_note():
    # ⠜⠏⠄⠐⠹ — end word sign consumed; C quarter must still receive the dynamic.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse(_DYN_P + _END_WORD_SIGN + '⠐⠹')
    assert notes[0].dynamics[0].level == DynamicLevel.P


# ---------------------------------------------------------------------------
# S4-3: Ties and slurs
# ---------------------------------------------------------------------------

# Verified BANA tie and slur cells:
_TIE          = '⠈⠉'  # dots 4 + dots 1,4 — placed after tied note
_SLUR         = '⠉'    # dots 1,4 — between notes (simple) or doubled for carry
_PHRASE_OPEN  = '⠰⠃'  # dots 5,6 + dots 1,2 — before first phrased note
_PHRASE_CLOSE = '⠘⠆'  # dots 4,5 + dots 2,3 — after last phrased note


# --- Tokenizer: tie / slur cell recognition ---

def test_tokenizer_tie_is_slur_category():
    tokens = BrailleTokenizer().tokenize('⠐⠹' + _TIE + '⠹')
    slur_tokens = [t for t in tokens if t.category == SymbolCategory.SLUR]
    assert len(slur_tokens) == 1
    assert slur_tokens[0].character == _TIE


def test_tokenizer_simple_slur_is_slur_category():
    tokens = BrailleTokenizer().tokenize('⠐⠹' + _SLUR + '⠹')
    slur_tokens = [t for t in tokens if t.category == SymbolCategory.SLUR]
    assert len(slur_tokens) == 1
    assert slur_tokens[0].character == _SLUR


def test_tokenizer_slur_bracket_open_is_slur_category():
    tokens = BrailleTokenizer().tokenize(_PHRASE_OPEN + '⠐⠹')
    slur_tokens = [t for t in tokens if t.category == SymbolCategory.SLUR]
    assert len(slur_tokens) == 1
    assert slur_tokens[0].character == _PHRASE_OPEN


def test_tokenizer_slur_bracket_close_is_slur_category():
    tokens = BrailleTokenizer().tokenize('⠐⠹' + _PHRASE_CLOSE)
    slur_tokens = [t for t in tokens if t.category == SymbolCategory.SLUR]
    assert len(slur_tokens) == 1
    assert slur_tokens[0].character == _PHRASE_CLOSE


def test_tokenizer_tie_not_classified_as_octave_mark():
    # ⠈ (dots 4) is the octave 1 mark; ⠈⠉ must produce a SLUR token, not an OCTAVE_MARK.
    tokens = BrailleTokenizer().tokenize('⠐⠹' + _TIE + '⠹')
    octave_tokens = [t for t in tokens if t.category == SymbolCategory.OCTAVE_MARK]
    assert all(t.character == '⠐' for t in octave_tokens)  # only the initial octave 4 mark


def test_tokenizer_slur_bracket_open_not_classified_as_octave_six():
    # ⠰ (dots 5,6) is the octave 6 mark; ⠰⠃ must produce a SLUR token, not an OCTAVE_MARK.
    tokens = BrailleTokenizer().tokenize(_PHRASE_OPEN + '⠐⠹')
    octave_tokens = [t for t in tokens if t.category == SymbolCategory.OCTAVE_MARK]
    assert all(t.character == '⠐' for t in octave_tokens)  # only the octave 4 mark


def test_tokenizer_slur_bracket_close_not_classified_as_octave_two():
    # ⠘ (dots 4,5) is octave 2 and also starts expressive_accent ⠘⠦;
    # ⠘⠆ must be SLUR, not octave mark or articulation.
    tokens = BrailleTokenizer().tokenize('⠐⠹' + _PHRASE_CLOSE)
    octave_tokens = [t for t in tokens if t.category == SymbolCategory.OCTAVE_MARK]
    assert all(t.character == '⠐' for t in octave_tokens)


def test_tokenizer_slur_bracket_close_vs_expressive_accent():
    # ⠘⠦ (expressive accent) and ⠘⠆ (phrase slur close) share the ⠘ prefix;
    # make sure both are classified by their 2-cell pair, not by ⠘ alone.
    tokens_art = BrailleTokenizer().tokenize('⠐⠹⠘⠦⠹')
    tokens_slur = BrailleTokenizer().tokenize('⠐⠹' + _PHRASE_CLOSE)
    art_cats = [t.category for t in tokens_art if t.character in ('⠘⠦', '⠘⠆')]
    slur_cats = [t.category for t in tokens_slur if t.character in ('⠘⠦', '⠘⠆')]
    assert SymbolCategory.ARTICULATION in art_cats
    assert SymbolCategory.SLUR in slur_cats


# --- Parser: tie ---

def test_parser_tie_attaches_to_first_note():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse('⠐⠹' + _TIE + '⠹')
    assert notes[0].tie is True
    assert notes[1].tie is False



def test_parser_tie_renders_tilde_in_lilypond():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse('⠐⠹' + _TIE + '⠹')
    assert '~' in notes[0].to_lilypond()
    assert '~' not in notes[1].to_lilypond()


# --- Parser: simple (two-note) slur ---

def test_parser_simple_slur_first_and_second_notes():
    notes = _parse('⠐⠹' + _SLUR + '⠹⠹')
    assert notes[0].slur_start is True
    assert notes[1].slur_end is True


def test_parser_simple_slur_third_note_has_no_marks():
    notes = _parse('⠐⠹' + _SLUR + '⠹⠹')
    assert notes[2].slur_start is False
    assert notes[2].slur_end is False


def test_parser_simple_slur_renders_parens_in_lilypond():
    notes = _parse('⠐⠹' + _SLUR + '⠹⠹')
    assert '(' in notes[0].to_lilypond()
    assert ')' in notes[1].to_lilypond()


# --- Parser: doubled (long) slur ---

def test_parser_doubled_slur():
    # NOTE SLUR SLUR NOTE NOTE NOTE SLUR NOTE
    # First note starts slur, middle notes have no marks, last note ends slur.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse('⠐⠙' + _SLUR + _SLUR + '⠙⠙⠙' + _SLUR + '⠙')
    assert notes[0].slur_start is True
    assert notes[1].slur_start is False
    assert notes[1].slur_end is False
    assert notes[2].slur_start is False
    assert notes[3].slur_end is False
    assert notes[4].slur_end is True


# --- Parser: phrasing (bracket) slur ---

def test_parser_slur_bracket():
    # ⠰⠃ ⠐⠻ ⠋ ⠑ ⠋ ⠛ ⠘⠆ — F quarter + 4 eighth notes in bracket slur
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse(_PHRASE_OPEN + '⠐⠻⠋⠑⠋⠛' + _PHRASE_CLOSE)
    assert notes[0].slur_bracket_open is True
    assert notes[1].slur_bracket_open is False
    assert notes[1].slur_bracket_close is False
    assert notes[4].slur_bracket_close is True


def test_parser_slur_bracket_renders_to_lilypond():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse(_PHRASE_OPEN + '⠐⠻⠋⠑⠋⠛' + _PHRASE_CLOSE)
    assert r'\(' in notes[0].to_lilypond()
    assert r'\)' in notes[4].to_lilypond()


# ---------------------------------------------------------------------------
# S4-4: Ornaments
# ---------------------------------------------------------------------------

# BANA ornament cells (verified with developer):
_TRILL           = '⠖'    # dots 2,3,5 — trill (also used doubled for carry mode)
_TURN            = '⠲'    # dots 2,5,6 — turn
_INV_TURN        = '⠲⠇'  # dots 2,5,6 + dots 1,2,3 — inverted turn
_UPPER_MORDENT   = '⠐⠖'  # dots 5 + dots 2,3,5 — upper mordent (prall)
_LOWER_MORDENT   = '⠐⠖⠇' # dots 5 + dots 2,3,5 + dots 1,2,3 — lower mordent
_GLISSANDO       = '⠈⠁'  # dot 4 cell + dot 1 cell — follows first note
_GRACE_SHORT     = '⠢'    # dots 2,6 — short grace note indicator (with slash → \grace)
_GRACE_LONG      = '⠐⠢'  # dots 5 + dots 2,6 — long grace note indicator (no slash → \appoggiatura)

# Octave 4 mark + note cells used in ornament tests:
_OCT4            = '⠐'    # dots 5 — octave 4 (middle C range)
_C4              = '⠐⠹'  # octave 4 + C quarter
_E4              = '⠫'    # E quarter (same octave, no mark needed after ⠐)


# --- Tokenizer: ornament cell classification ---

def test_tokenizer_trill_is_ornament_category():
    tokens = BrailleTokenizer().tokenize(_TRILL + _C4)
    orn = [t for t in tokens if t.category == SymbolCategory.ORNAMENT]
    assert len(orn) == 1
    assert orn[0].character == _TRILL


def test_tokenizer_turn_is_ornament_category():
    tokens = BrailleTokenizer().tokenize(_TURN + _C4)
    orn = [t for t in tokens if t.category == SymbolCategory.ORNAMENT]
    assert len(orn) == 1
    assert orn[0].character == _TURN


def test_tokenizer_inverted_turn_is_two_cell_ornament():
    tokens = BrailleTokenizer().tokenize(_INV_TURN + _C4)
    orn = [t for t in tokens if t.category == SymbolCategory.ORNAMENT]
    assert len(orn) == 1
    assert orn[0].character == _INV_TURN


def test_tokenizer_upper_mordent_is_two_cell_ornament():
    # ⠐⠖ must be emitted as one 2-cell ORNAMENT token, not split into octave mark + trill.
    tokens = BrailleTokenizer().tokenize(_UPPER_MORDENT + _C4)
    orn = [t for t in tokens if t.category == SymbolCategory.ORNAMENT]
    assert len(orn) == 1
    assert orn[0].character == _UPPER_MORDENT


def test_tokenizer_lower_mordent_is_three_cell_ornament():
    tokens = BrailleTokenizer().tokenize(_LOWER_MORDENT + _C4)
    orn = [t for t in tokens if t.category == SymbolCategory.ORNAMENT]
    assert len(orn) == 1
    assert orn[0].character == _LOWER_MORDENT


def test_tokenizer_upper_mordent_not_split_as_octave_mark():
    tokens = BrailleTokenizer().tokenize(_UPPER_MORDENT + _C4)
    cats = [t.category for t in tokens]
    # ⠐ must not appear as an isolated OCTAVE_MARK when it starts the mordent
    octave_marks = [t for t in tokens if t.category == SymbolCategory.OCTAVE_MARK]
    # Only the ⠐ inside _C4 should be an octave mark
    assert len(octave_marks) == 1


def test_tokenizer_short_grace_indicator_is_ornament():
    tokens = BrailleTokenizer().tokenize(_GRACE_SHORT + _OCT4 + _E4 + _C4)
    orn = [t for t in tokens if t.category == SymbolCategory.ORNAMENT]
    assert len(orn) == 1
    assert orn[0].character == _GRACE_SHORT


def test_tokenizer_long_grace_indicator_is_two_cell_ornament():
    # ⠐⠢ must be one 2-cell ORNAMENT token, not split as octave mark + short grace.
    tokens = BrailleTokenizer().tokenize(_GRACE_LONG + _OCT4 + _E4 + _C4)
    orn = [t for t in tokens if t.category == SymbolCategory.ORNAMENT]
    assert len(orn) == 1
    assert orn[0].character == _GRACE_LONG


# --- Parser: ornaments attach to the following note ---

def test_parser_trill_attaches_to_note():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse(_TRILL + _C4)
    assert len(notes[0].ornaments) == 1
    assert notes[0].ornaments[0].type == OrnamentType.TRILL


def test_parser_turn_attaches_to_note():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse(_TURN + _C4)
    assert notes[0].ornaments[0].type == OrnamentType.TURN


def test_parser_inverted_turn_attaches_to_note():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse(_INV_TURN + _C4)
    assert notes[0].ornaments[0].type == OrnamentType.INVERTED_TURN


def test_parser_upper_mordent_attaches_to_note():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse(_UPPER_MORDENT + _C4)
    assert notes[0].ornaments[0].type == OrnamentType.UPPER_MORDENT


def test_parser_lower_mordent_attaches_to_note():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse(_LOWER_MORDENT + _C4)
    assert notes[0].ornaments[0].type == OrnamentType.MORDENT


def test_parser_note_without_ornament_has_empty_list():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse(_C4)
    assert notes[0].ornaments == []


# --- Parser: ornaments render correctly to LilyPond ---

def test_parser_trill_renders_to_lilypond():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse(_TRILL + _C4)
    assert r'\trill' in notes[0].to_lilypond()


def test_parser_turn_renders_to_lilypond():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse(_TURN + _C4)
    assert r'\turn' in notes[0].to_lilypond()


def test_parser_inverted_turn_renders_to_lilypond():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse(_INV_TURN + _C4)
    assert r'\reverseturn' in notes[0].to_lilypond()


def test_parser_upper_mordent_renders_to_lilypond():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse(_UPPER_MORDENT + _C4)
    assert r'\prall' in notes[0].to_lilypond()


def test_parser_lower_mordent_renders_to_lilypond():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse(_LOWER_MORDENT + _C4)
    assert r'\mordent' in notes[0].to_lilypond()


# --- Tokenizer: glissando cell recognition ---

def test_tokenizer_glissando_is_two_cell_ornament():
    # ⠈⠁ is two separate cells (dot 4, dot 1), not the single slur cell ⠉ (dots 1,4).
    tokens = BrailleTokenizer().tokenize(_C4 + _GLISSANDO + '⠱')
    orn = [t for t in tokens if t.category == SymbolCategory.ORNAMENT]
    assert len(orn) == 1
    assert orn[0].character == _GLISSANDO


def test_tokenizer_glissando_not_confused_with_slur():
    # ⠈⠁ (glissando) and ⠉ (slur/tie) are different byte sequences.
    tokens_gliss = BrailleTokenizer().tokenize(_C4 + _GLISSANDO + '⠱')
    tokens_slur  = BrailleTokenizer().tokenize('⠐⠹⠉⠹')
    gliss_orn = [t for t in tokens_gliss if t.category == SymbolCategory.ORNAMENT]
    slur_toks = [t for t in tokens_slur if t.category == SymbolCategory.SLUR]
    assert len(gliss_orn) == 1
    assert len(slur_toks) == 1


def test_tokenizer_glissando_not_classified_as_slur():
    tokens = BrailleTokenizer().tokenize(_C4 + _GLISSANDO + '⠱')
    slur_toks = [t for t in tokens if t.category == SymbolCategory.SLUR]
    assert slur_toks == []


# --- Parser: glissando attaches to the preceding note ---

def test_parser_glissando_attaches_to_preceding_note():
    # Sequence: C4 quarter, glissando, D4 quarter
    # Glissando follows first note, so notes[0] carries it.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse(_C4 + _GLISSANDO + '⠱')
    assert len(notes[0].ornaments) == 1
    assert notes[0].ornaments[0].type == OrnamentType.GLISSANDO


def test_parser_glissando_not_on_second_note():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse(_C4 + _GLISSANDO + '⠱')
    assert notes[1].ornaments == []


def test_parser_glissando_renders_to_lilypond():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse(_C4 + _GLISSANDO + '⠱')
    assert r'\glissando' in notes[0].to_lilypond()


def test_parser_glissando_not_in_second_note_lilypond():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse(_C4 + _GLISSANDO + '⠱')
    assert r'\glissando' not in notes[1].to_lilypond()


# --- Parser: trill carry mode ---

def test_parser_doubled_trill_sign_gives_span_start():
    # Two consecutive trill signs before any note → TRILL_SPAN_START on first note.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse(_TRILL + _TRILL + _C4 + '⠹')
    assert notes[0].ornaments[0].type == OrnamentType.TRILL_SPAN_START


def test_parser_trill_span_start_renders_startTrillSpan():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse(_TRILL + _TRILL + _C4 + '⠹')
    assert r'\startTrillSpan' in notes[0].to_lilypond()


def test_parser_trill_carry_end():
    # Doubled trill before first note activates carry; single trill before last note terminates.
    # Sequence: ⠖⠖ C4 ⠖ D(same octave)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse(_TRILL + _TRILL + _C4 + _TRILL + '⠱')
    assert notes[1].ornaments[0].type == OrnamentType.TRILL_SPAN_END
    assert r'\stopTrillSpan' in notes[1].to_lilypond()


# --- Parser: grace notes ---

def test_parser_short_grace_note():
    # ⠢ E4 C4 → C4 has a short grace note (E4); grace cell is not a separate measure note.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse(_GRACE_SHORT + _OCT4 + _E4 + _C4)
    assert len(notes) == 1
    assert notes[0].grace_note is not None
    assert notes[0].grace_note.long_appoggiatura is False
    assert notes[0].grace_note.notes[0].note_name == 'E'
    assert r'\grace' in notes[0].to_lilypond()


def test_parser_long_grace_note():
    # ⠐⠢ E4 C4 → C4 has a long grace note (appoggiatura)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse(_GRACE_LONG + _OCT4 + _E4 + _C4)
    assert notes[0].grace_note is not None
    assert notes[0].grace_note.long_appoggiatura is True
    assert r'\appoggiatura' in notes[0].to_lilypond()


def test_parser_note_without_grace_has_none():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse(_C4)
    assert notes[0].grace_note is None


# --- Parser: multiple grace notes (≤3, each with its own indicator) ---
# Braille: ⠢⠐⠙ ⠢⠑ ⠢⠋ ⠐⠻ → \grace { c8 d8 e8 } f'4
# After the first octave mark, the remaining grace notes inherit octave 4.
_THREE_GRACE = _GRACE_SHORT + _OCT4 + '⠙' + _GRACE_SHORT + '⠑' + _GRACE_SHORT + '⠋' + _OCT4 + '⠻'


def test_parser_three_grace_notes_all_in_one_block():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse(_THREE_GRACE)
    assert notes[0].grace_note is not None
    assert len(notes[0].grace_note.notes) == 3


def test_parser_three_grace_note_names():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse(_THREE_GRACE)
    names = [n.note_name for n in notes[0].grace_note.notes]
    assert names == ['C', 'D', 'E']


def test_parser_three_grace_notes_only_one_measure_note():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse(_THREE_GRACE)
    assert len(notes) == 1


def test_parser_three_grace_notes_renders_single_grace_block():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse(_THREE_GRACE)
    ly = notes[0].to_lilypond()
    assert ly.startswith(r'\grace')
    assert ly.count(r'\grace') == 1  # one block, not three


def test_parser_three_grace_notes_lilypond_contains_all_pitches():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse(_THREE_GRACE)
    ly = notes[0].to_lilypond()
    assert 'c' in ly
    assert 'd' in ly
    assert 'e' in ly
    assert 'f' in ly


# --- Parser: 4+ grace notes with carry mode (doubled indicator) ---
# Braille: ⠢⠢⠐⠙ ⠑ ⠋ ⠛ ⠢⠓ ⠐⠻ → \grace { c8 d8 e8 f8 g8 } f'4
# ⠛ = F eighth, ⠓ = G eighth
_FIVE_GRACE = (
    _GRACE_SHORT + _GRACE_SHORT + _OCT4 + '⠙'  # doubled indicator + C
    + '⠑'                                        # middle: D
    + '⠋'                                        # middle: E
    + '⠛'                                        # middle: F
    + _GRACE_SHORT + '⠓'                         # terminating indicator + G
    + _OCT4 + '⠻'                               # main note: F quarter
)


def test_parser_carry_mode_five_grace_notes():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse(_FIVE_GRACE)
    assert notes[0].grace_note is not None
    assert len(notes[0].grace_note.notes) == 5


def test_parser_carry_mode_grace_note_names():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse(_FIVE_GRACE)
    names = [n.note_name for n in notes[0].grace_note.notes]
    assert names == ['C', 'D', 'E', 'F', 'G']


def test_parser_carry_mode_only_one_measure_note():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse(_FIVE_GRACE)
    assert len(notes) == 1


def test_parser_carry_mode_renders_single_grace_block():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse(_FIVE_GRACE)
    ly = notes[0].to_lilypond()
    assert ly.startswith(r'\grace')
    assert ly.count(r'\grace') == 1


# ---------------------------------------------------------------------------
# S4-5: Word sign / text marking parsing
# ---------------------------------------------------------------------------

# Braille strings for common musical terms (word sign ⠜ + literary letters).
# Generated from ASCII_TO_DOTS reverse mapping.
_WORD_SIGN            = '⠜'
_BANA_ALLEGRO         = '⠜⠁⠇⠇⠑⠛⠗⠕'  # word sign + a-l-l-e-g-r-o
_BANA_DOLCE           = '⠜⠙⠕⠇⠉⠑'     # word sign + d-o-l-c-e
_BANA_CON_MOTO        = '⠜⠉⠕⠝⠀⠍⠕⠞⠕' # word sign + c-o-n-space-m-o-t-o
_BANA_ANDANTE         = '⠜⠁⠝⠙⠁⠝⠞⠑'  # word sign + a-n-d-a-n-t-e
_C_QUARTER_OCT4       = '⠐⠹'          # octave 4 + C quarter


# --- Tokenizer: word sign token recognition ---

def test_tokenizer_word_sign_allegro_produces_word_sign_token():
    tokens = BrailleTokenizer().tokenize(_BANA_ALLEGRO + _C_QUARTER_OCT4)
    assert tokens[0].category == SymbolCategory.WORD_SIGN


def test_tokenizer_word_sign_allegro_decodes_text():
    tokens = BrailleTokenizer().tokenize(_BANA_ALLEGRO + _C_QUARTER_OCT4)
    assert tokens[0].character == 'allegro'


def test_tokenizer_word_sign_dolce_decodes_text():
    tokens = BrailleTokenizer().tokenize(_BANA_DOLCE + _C_QUARTER_OCT4)
    assert tokens[0].category == SymbolCategory.WORD_SIGN
    assert tokens[0].character == 'dolce'


def test_tokenizer_word_sign_multi_word_con_moto():
    tokens = BrailleTokenizer().tokenize(_BANA_CON_MOTO + _C_QUARTER_OCT4)
    assert tokens[0].category == SymbolCategory.WORD_SIGN
    assert tokens[0].character == 'con moto'


def test_tokenizer_word_sign_stops_at_octave_mark():
    """Octave mark after the text is left for the note parser, not consumed."""
    tokens = BrailleTokenizer().tokenize(_BANA_ALLEGRO + _C_QUARTER_OCT4)
    # tokens: WORD_SIGN, OCTAVE_MARK, NOTE
    assert tokens[1].category == SymbolCategory.OCTAVE_MARK
    assert tokens[2].category == SymbolCategory.NOTE


def test_tokenizer_word_sign_end_word_sign_consumed():
    """⠄ is consumed and not emitted as a separate token."""
    tokens = BrailleTokenizer().tokenize(_BANA_DOLCE + _END_WORD_SIGN + _C_QUARTER_OCT4)
    categories = [t.category for t in tokens]
    assert SymbolCategory.UNKNOWN not in categories
    assert tokens[0].character == 'dolce'


def test_tokenizer_dynamic_not_confused_with_word_sign():
    """Dynamic abbreviations are still classified as DYNAMIC, not WORD_SIGN."""
    tokens = BrailleTokenizer().tokenize(_DYN_P + _END_WORD_SIGN + _C_QUARTER_OCT4)
    assert tokens[0].category == SymbolCategory.DYNAMIC
    assert tokens[0].character == _DYN_P


# --- Parser: word sign → TextMarking classification ---

def _parse_score(text: str):
    """Tokenize and parse braille text; return the full Score."""
    from dottednotes.parser import BrailleParser, BrailleTokenizer
    tokens = BrailleTokenizer().tokenize(text)
    return BrailleParser(tokens=tokens).parse()


def test_parser_allegro_classified_as_tempo():
    from dottednotes.models import TextMarkingType
    score = _parse_score(_BANA_ALLEGRO + _C_QUARTER_OCT4)
    staff = score.staves[0]
    assert staff.tempo is not None
    assert staff.tempo.type == TextMarkingType.TEMPO
    assert staff.tempo.text == 'allegro'


def test_parser_dolce_classified_as_expression():
    from dottednotes.models import TextMarkingType
    score = _parse_score(_BANA_DOLCE + _C_QUARTER_OCT4)
    staff = score.staves[0]
    assert staff.tempo is not None
    assert staff.tempo.type == TextMarkingType.EXPRESSION
    assert staff.tempo.text == 'dolce'


def test_parser_con_moto_classified_as_expression():
    from dottednotes.models import TextMarkingType
    score = _parse_score(_BANA_CON_MOTO + _C_QUARTER_OCT4)
    staff = score.staves[0]
    assert staff.tempo is not None
    assert staff.tempo.text == 'con moto'


def test_parser_andante_classified_as_tempo():
    from dottednotes.models import TextMarkingType
    score = _parse_score(_BANA_ANDANTE + _C_QUARTER_OCT4)
    assert score.staves[0].tempo.type == TextMarkingType.TEMPO


def test_parser_word_sign_mid_piece_goes_to_measure_text_markings():
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        score = _parse_score(_C_QUARTER_OCT4 + '⠣⠅' + _BANA_DOLCE + _C_QUARTER_OCT4)
    assert len(score.staves[0].measures) >= 1
    last_measure = score.staves[0].measures[-1]
    assert len(last_measure.text_markings) == 1
    assert last_measure.text_markings[0].text == 'dolce'


# --- LilyPond rendering ---

def test_word_sign_tempo_renders_tempo_directive():
    score = _parse_score(_BANA_ALLEGRO + _C_QUARTER_OCT4)
    ly = score.to_lilypond()
    assert r'\tempo "allegro"' in ly


def test_word_sign_expression_renders_mark_directive():
    score = _parse_score(_BANA_DOLCE + _C_QUARTER_OCT4)
    ly = score.to_lilypond()
    assert r'\mark \markup { "dolce" }' in ly


def test_word_sign_tempo_comes_before_notes_in_lilypond():
    score = _parse_score(_BANA_ALLEGRO + _C_QUARTER_OCT4)
    ly = score.to_lilypond()
    tempo_pos = ly.index(r'\tempo')
    first_note_pos = ly.index("c4")
    assert tempo_pos < first_note_pos


# --- Capital letter indicator (⠠) — header tempo markings ---
# "Allegro moderato" encoded as capital indicator + literary braille + period:
#   ⠠ = capital indicator
#   ⠁⠇⠇⠑⠛⠗⠕ = a-l-l-e-g-r-o
#   ⠀ = space
#   ⠍⠕⠙⠑⠗⠁⠞⠕ = m-o-d-e-r-a-t-o
#   ⠲ = literary period (terminator)
_CAPITAL_ALLEGRO_MODERATO = '⠠⠁⠇⠇⠑⠛⠗⠕⠀⠍⠕⠙⠑⠗⠁⠞⠕⠲'
_CAPITAL_ANDANTE          = '⠠⠁⠝⠙⠁⠝⠞⠑⠲'   # capital + a-n-d-a-n-t-e + period
_END_WORD_SIGN            = '⠄'              # dot 3


def test_capital_indicator_produces_word_sign_token():
    tokens = BrailleTokenizer().tokenize(_CAPITAL_ALLEGRO_MODERATO)
    assert len(tokens) == 1
    assert tokens[0].category == SymbolCategory.WORD_SIGN


def test_capital_indicator_decodes_capitalized_first_letter():
    tokens = BrailleTokenizer().tokenize(_CAPITAL_ALLEGRO_MODERATO)
    assert tokens[0].character == 'Allegro moderato'


def test_capital_indicator_andante_decoded():
    tokens = BrailleTokenizer().tokenize(_CAPITAL_ANDANTE)
    assert tokens[0].category == SymbolCategory.WORD_SIGN
    assert tokens[0].character == 'Andante'


def test_capital_indicator_period_consumed_not_emitted():
    """The literary period terminates the text and is not included in the token."""
    tokens = BrailleTokenizer().tokenize(_CAPITAL_ALLEGRO_MODERATO)
    assert '.' not in tokens[0].character


def test_capital_indicator_followed_by_key_sig_leaves_key_sig_token():
    """After the text the key signature is tokenized normally."""
    _G_MAJOR = '⠩'
    tokens = BrailleTokenizer().tokenize(_CAPITAL_ALLEGRO_MODERATO + _G_MAJOR)
    assert tokens[0].category == SymbolCategory.WORD_SIGN
    assert tokens[1].category == SymbolCategory.KEY_SIGNATURE


def test_capital_indicator_staccatissimo_not_affected():
    """⠠⠦ (staccatissimo) must still tokenize as ARTICULATION, not as capital indicator."""
    _STACCATISSIMO = '⠠⠦'
    tokens = BrailleTokenizer().tokenize(_STACCATISSIMO + _C_QUARTER_OCT4)
    assert tokens[0].category == SymbolCategory.ARTICULATION


def test_capital_indicator_tempo_classified_as_tempo():
    from dottednotes.models import TextMarkingType
    score = _parse_score(_CAPITAL_ALLEGRO_MODERATO + _C_QUARTER_OCT4)
    staff = score.staves[0]
    assert staff.tempo is not None
    assert staff.tempo.type == TextMarkingType.TEMPO
    assert staff.tempo.text == 'Allegro moderato'


def test_capital_indicator_tempo_renders_in_lilypond():
    score = _parse_score(_CAPITAL_ALLEGRO_MODERATO + _C_QUARTER_OCT4)
    assert r'\tempo "Allegro moderato"' in score.to_lilypond()


def test_capital_indicator_tempo_before_first_note_in_lilypond():
    score = _parse_score(_CAPITAL_ALLEGRO_MODERATO + _C_QUARTER_OCT4)
    ly = score.to_lilypond()
    assert ly.index(r'\tempo') < ly.index('c4')
