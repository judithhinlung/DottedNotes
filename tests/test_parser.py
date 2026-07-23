import warnings
from pathlib import Path

import pytest

from dottednotes.bana_symbols import BAR_LINE_CELLS, BAR_LINE_SEQUENCES, SymbolCategory, TABLE_29_ENGLISH
from dottednotes.models import Articulation, ArticulationType, Clef, ClefType, Dynamic, DynamicLevel, KeySignature, Ornament, OrnamentType, Score, TimeSignature
from dottednotes.parser import BRLInputPipeline, BrailleParser, BrailleToken, BrailleTokenizer, parse_instrument_list, resolve_abbreviation
from dottednotes.parser.instrument_list import _decode_abbreviation


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
    # ⠐ = octave 4, ⠹ = C quarter, ⠱ = D quarter (no new octave mark).
    # C4 -> D is a 2nd (BANA Sec. 3.2.2(a)), so the unmarked note resolves
    # to the same octave as the previous one -- not because unmarked notes
    # are always "sticky" to whatever octave was last set (they aren't; see
    # test_octave_leap_without_mark_resolves_nearest below), but because a
    # 2nd/3rd interval's nearest reading always happens to land there.
    notes = _parse('⠐⠹⠱')
    assert notes[0].note_name == 'C'
    assert notes[0].octave == 4
    assert notes[1].note_name == 'D'
    assert notes[1].octave == 4


def test_octave_leap_without_mark_resolves_nearest_descending():
    # ⠐ = octave 4, ⠹ = C quarter, ⠺ = B quarter (no mark). A same-octave
    # reading would put B a 7th above C -- BANA Sec. 3.2.2 instead resolves
    # to the nearest B, a 2nd below (B3), not B4 (the S8b-10 motivating bug).
    notes = _parse('⠐⠹⠺')
    assert notes[0].note_name == 'C'
    assert notes[0].octave == 4
    assert notes[1].note_name == 'B'
    assert notes[1].octave == 3


def test_octave_leap_without_mark_resolves_nearest_ascending():
    # ⠘ = octave 2, ⠺ = B quarter, ⠹ = C quarter (no mark). A same-octave
    # reading would put C a 7th below B -- BANA Sec. 3.2.2 instead resolves
    # to the nearest C, a 2nd above (octave 3), the symmetric ascending case.
    notes = _parse('⠘⠺⠹')
    assert notes[0].note_name == 'B'
    assert notes[0].octave == 2
    assert notes[1].note_name == 'C'
    assert notes[1].octave == 3


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
    # ⠙ = C 8th-note cell (dots 1,4,5); must be mid-line (after an octave mark)
    # so the tokenizer does not mistake it for a measure-number digit at line start.
    tokens = BrailleTokenizer().tokenize('⠐⠙')
    note_tokens = [t for t in tokens if t.category == SymbolCategory.NOTE]
    assert len(note_tokens) == 1
    assert note_tokens[0].character == '⠙'


def test_all_eighth_note_cells_tokenized_as_note():
    # All 7 8th-note cells should classify as NOTE when mid-line (not at line start).
    # Prefix with octave mark to move them past the at-line-start position.
    tokens = BrailleTokenizer().tokenize('⠐⠙⠑⠋⠛⠓⠊⠚')
    note_tokens = [t for t in tokens if t.category == SymbolCategory.NOTE]
    assert len(note_tokens) == 7
    assert all(t.category == SymbolCategory.NOTE for t in note_tokens)


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
    # A quarter (base_4) ends the run/individual adjacency context, so the
    # trailing base_1 cell has no run/individual signal of its own (S5-6
    # Bug B). But treating it as a whole note would total 5.5 beats in a
    # 4/4 measure (0.25+0.25+1+4) — an impossible overflow, so the
    # beat-budget check re-resolves it as a 16th instead. This replaces the
    # previous (buggy) expectation that a cell with "no qualifying
    # successor" always defaults to whole regardless of fit.
    #
    # Note: this trailing cell isn't part of a genuine 4-note (or 6-note
    # triplet) 16th-note run — a real run needs that many notes to total a
    # full beat, and a lone 16th like this one can't. Bug B is deliberately
    # scoped to the overflow check only (validated against
    # children_s_piece.brf) and doesn't validate beat-grouping completeness;
    # that's a separate, unresolved question, not something this test
    # should be read as endorsing as valid BANA notation.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse('⠐⠽⠙⠹⠽')  # 16th, run-continuation, quarter, 16th (was: whole)
    assert notes[0].duration.value == 16
    assert notes[1].duration.value == 16
    assert notes[2].duration.value == 4
    assert notes[3].duration.value == 16   # overflow-corrected, not whole


# --- S5-6: augmentation dots and beat-budget resolution of standalone
#     ambiguous whole/16th cells ---


def test_tokenizer_classifies_dot3_after_note_as_augmentation_dot():
    tokens = BrailleTokenizer().tokenize('⠐⠹⠄')  # octave4, C quarter, dot-3
    assert tokens[-1].category == SymbolCategory.AUGMENTATION_DOT
    assert tokens[-1].character == '⠄'


def test_dotted_quarter_note_has_one_dot():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse('⠐⠹⠄')  # C quarter + augmentation dot
    assert notes[0].duration.value == 4
    assert notes[0].duration.dots == 1


def test_dotted_half_note_has_one_dot():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse('⠐⠝⠄')  # C half/32nd-ambiguous + augmentation dot
    assert notes[0].duration.value == 2
    assert notes[0].duration.dots == 1


def test_dotted_eighth_note_has_one_dot():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse('⠐⠙⠄')  # C eighth (genuine, unambiguous) + dot
    assert notes[0].duration.value == 8
    assert notes[0].duration.dots == 1


def test_dotted_rest_has_one_dot():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse('⠐⠧⠄')  # quarter rest + augmentation dot
    assert notes[0].duration.value == 4
    assert notes[0].duration.dots == 1


def test_augmentation_dots_cap_at_two():
    # The exact BANA encoding for a double-dot (whether it's really two
    # consecutive dot-3 cells) hasn't been confirmed with the developer —
    # this only verifies the implementation's defensive cap, not that this
    # input is genuine double-dot notation.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse('⠐⠹⠄⠄⠄')  # C quarter + three augmentation-dot cells
    assert notes[0].duration.dots == 2


def test_augmentation_dot_with_no_preceding_note_warns():
    tokens = [_make_token('⠄', SymbolCategory.AUGMENTATION_DOT)]
    with pytest.warns(UserWarning, match="Augmentation dot"):
        BrailleParser(tokens=tokens).parse()


def test_measure1_pattern_matches_children_s_piece_ground_truth():
    # Mirrors children_s_piece.brf measure 1's developer-confirmed notation:
    # g8. b16 d4-. g4-. in 3/4 time. Should resolve with NO beat-count
    # warning: 0.75 (dotted 8th) + 0.25 (16th) + 1 + 1 = 3.0 exactly.
    tokens = [
        _make_token('⠼⠉⠲', SymbolCategory.TIME_SIGNATURE),
        _make_token('⠐', SymbolCategory.OCTAVE_MARK),
        _make_token('⠓', SymbolCategory.NOTE),               # G, base_8
        _make_token('⠄', SymbolCategory.AUGMENTATION_DOT),
        _make_token('⠾', SymbolCategory.NOTE),               # B, base_1 (ambiguous)
        _make_token('⠱', SymbolCategory.NOTE),               # D, base_4
        _make_token('⠳', SymbolCategory.NOTE),               # G, base_4
        _make_token('⠀', SymbolCategory.BAR_LINE),
    ]
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        score = BrailleParser(tokens=tokens).parse()
    notes = score.staves[0].measures[0].notes
    assert [n.duration.value for n in notes] == [8, 16, 4, 4]
    assert notes[0].duration.dots == 1
    assert not caught  # exact fit — no beat-count mismatch warning


def test_standalone_whole_note_exactly_filling_measure_is_unaffected():
    # Equality (not overflow) must not trigger the Bug B re-check.
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        notes = _parse('⠐⠽')  # single whole/16th cell, fills 4/4 exactly
    assert notes[0].duration.value == 1
    assert not caught


# --- BANA Sec. 5.1: a lone ambiguous whole/16th rest cell (⠍) is always a
#     whole-measure rest, regardless of time signature, except in 4/2 time ---


def test_lone_ambiguous_rest_is_full_measure_in_3_4():
    # Before the fix: Bug B's overflow check (built for notes) treated a
    # literal "whole rest" as 4 beats, which overflows a 3/4 measure, so it
    # silently demoted this to a 16th rest instead of a dotted-half
    # full-measure rest.
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        notes = _parse('⠼⠉⠲⠍')  # 3/4 time, lone ⠍ rest
    assert notes[0].duration.value == 2
    assert notes[0].duration.dots == 1
    assert notes[0].is_full_measure is True
    assert not caught  # no beat-count mismatch warning


def test_lone_ambiguous_rest_is_full_measure_in_6_8():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        notes = _parse('⠼⠋⠦⠍')  # 6/8 time, lone ⠍ rest
    assert notes[0].duration.value == 2
    assert notes[0].duration.dots == 1
    assert notes[0].is_full_measure is True
    assert not caught


def test_lone_ambiguous_rest_is_full_measure_in_2_4():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        notes = _parse('⠼⠃⠲⠍')  # 2/4 time, lone ⠍ rest
    assert notes[0].duration.value == 2
    assert notes[0].duration.dots == 0
    assert notes[0].is_full_measure is True
    assert not caught


def test_lone_ambiguous_rest_still_whole_measure_in_4_4():
    # 4/4 already worked before the fix, by coincidence (a literal whole
    # rest's tick length happens to equal a 4/4 measure's) -- must still work.
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        notes = _parse('⠼⠙⠲⠍')  # 4/4 time, lone ⠍ rest
    assert notes[0].duration.value == 1
    assert notes[0].is_full_measure is True
    assert not caught


def test_lone_ambiguous_rest_in_4_2_keeps_prior_ambiguity_resolution():
    # BANA Sec. 5.1's stated exception: in 4/2 time the ambiguity is real,
    # so the ordinary note-style whole/16th state machine (not a full-
    # measure-rest override) still applies -- unlike every other time
    # signature. A literal whole rest (4 beats) doesn't overflow an 8-beat
    # 4/2 measure, so Bug B leaves it as a plain (non-full-measure) whole
    # rest here, same as before this fix.
    notes = _parse('⠼⠙⠆⠍')  # 4/2 time, lone ⠍ rest
    assert notes[0].duration.value == 1
    assert notes[0].is_full_measure is False


def test_rest_run_adjacency_unaffected_by_full_measure_rule():
    # The full-measure-rest override only applies to a *lone* rest
    # (len(pending) == 1) -- it must not interfere with the existing
    # run/individual adjacency resolution for consecutive ambiguous cells.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse('⠼⠉⠲⠍⠭')  # 3/4 time, ⠍ followed by ⠭ (genuine 8th) -> run
    assert notes[0].duration.value == 16
    assert notes[0].is_full_measure is False


# --- S5-8: single-cell triplet sign (BANA 8.4) ---


def test_tokenizer_classifies_triplet_indicator():
    tokens = BrailleTokenizer().tokenize('⠐⠹⠆')  # octave4, C quarter, triplet sign
    assert tokens[-1].category == SymbolCategory.TRIPLET_INDICATOR
    assert tokens[-1].character == '⠆'


def test_eighth_triplet_totals_one_beat():
    from dottednotes.models.tuplet import Tuplet

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse('⠐⠆⠙⠑⠋')  # triplet sign, C D E eighths
    assert len(notes) == 1
    tup = notes[0]
    assert isinstance(tup, Tuplet)
    assert [n.duration.value for n in tup.items] == [8, 8, 8]
    assert all(n.duration.is_triplet for n in tup.items)
    assert [n.duration.duration_in_ticks() for n in tup.items] == [8, 8, 8]
    assert sum(n.duration.duration_in_ticks() for n in tup.items) == 24  # 1 beat


def test_quarter_triplet_totals_two_beats():
    from dottednotes.models.tuplet import Tuplet

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse('⠐⠆⠹⠫⠱')  # triplet sign, C E D quarters
    tup = notes[0]
    assert isinstance(tup, Tuplet)
    assert [n.duration.value for n in tup.items] == [4, 4, 4]
    assert [n.duration.duration_in_ticks() for n in tup.items] == [16, 16, 16]
    assert sum(n.duration.duration_in_ticks() for n in tup.items) == 48  # 2 beats


def test_16th_class_triplet_via_leader_and_continuations():
    # A 16th-class triplet reuses the same leader (base_1) + continuation
    # (base_8) cells as a normal run (S2-4/S5-7), but the group is exactly
    # 3 notes long, not beat-bounded — the confirmed interaction from S5-8.
    from dottednotes.models.tuplet import Tuplet

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse('⠐⠆⠷⠙⠑')  # triplet sign, G(ambiguous 16th) C D (continuations)
    tup = notes[0]
    assert isinstance(tup, Tuplet)
    assert [n.duration.value for n in tup.items] == [16, 16, 16]
    assert [n.duration.duration_in_ticks() for n in tup.items] == [4, 4, 4]
    assert sum(n.duration.duration_in_ticks() for n in tup.items) == 12  # 0.5 beat


def test_doubled_triplet_sign_opens_unbounded_groups_until_single_sign_closes():
    # Doubled sign -> two auto-continuing groups of 3 (no repeated sign
    # needed) -> a single sign marks the final group -> a plain note after
    # that is not a triplet.
    from dottednotes.models.tuplet import Tuplet

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse('⠐⠆⠆⠙⠑⠋⠛⠓⠊⠆⠚⠙⠑⠋')
    assert len(notes) == 4
    assert isinstance(notes[0], Tuplet)
    assert [n.note_name for n in notes[0].items] == ['C', 'D', 'E']
    assert isinstance(notes[1], Tuplet)
    assert [n.note_name for n in notes[1].items] == ['F', 'G', 'A']
    assert isinstance(notes[2], Tuplet)
    assert [n.note_name for n in notes[2].items] == ['B', 'C', 'D']
    assert all(n.duration.is_triplet for group in notes[:3] for n in group.items)
    assert not isinstance(notes[3], Tuplet)
    assert notes[3].note_name == 'E'
    assert notes[3].duration.is_triplet is False
    assert notes[3].duration.value == 8


def test_triplet_to_lilypond_uses_tuplet_syntax():
    from dottednotes.models.tuplet import Tuplet

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse('⠐⠆⠙⠑⠋')
    tup = notes[0]
    assert isinstance(tup, Tuplet)
    ly, _ = tup.to_relative_lilypond(60)
    assert ly == r'\tuplet 3/2 { c8 d8 e8 }'


# --- S5-9: mixed-value notes within triplet groups (BANA 8.4) ---


def test_mixed_value_two_note_group_closes_by_duration_not_note_count():
    from dottednotes.models.tuplet import Tuplet

    # triplet sign, C quarter, D eighth, E eighth (plain, not under the sign)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse('⠐⠆⠹⠑⠋')
    assert len(notes) == 2
    tup = notes[0]
    assert isinstance(tup, Tuplet)
    assert [n.duration.value for n in tup.items] == [4, 8]
    assert [n.duration.duration_in_ticks() for n in tup.items] == [16, 8]
    assert sum(n.duration.duration_in_ticks() for n in tup.items) == 24
    # The larger note's duration is twice the smaller note's (developer-
    # confirmed two-note rule).
    ticks = [n.duration.duration_in_ticks() for n in tup.items]
    assert ticks[0] == 2 * ticks[1]
    # The third note was never swept into the triplet — old note-counting
    # would have incorrectly consumed it as the group's "third" member.
    assert not isinstance(notes[1], Tuplet)
    assert notes[1].note_name == 'E'
    assert notes[1].duration.is_triplet is False
    assert notes[1].duration.value == 8


def test_triplet_overshoot_raises_hard_error():
    from dottednotes.parser.braille_parser import TripletDurationError

    # triplet sign, C eighth, D eighth, E quarter: 8+8=16 (target 24 so
    # far), then +16 = 32, overshooting the target implied by the
    # smallest note (8) — developer-confirmed this is a hard error.
    with pytest.raises(TripletDurationError):
        _parse('⠐⠆⠙⠑⠫')


def test_undoubled_single_sign_uses_duration_based_closing_too():
    # Developer-confirmed: duration-based closing applies to every triplet
    # group, not just doubled-sign blocks — the quarter+eighth example
    # itself was under a single (undoubled) sign.
    from dottednotes.models.tuplet import Tuplet

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse('⠐⠆⠹⠑')  # triplet sign, C quarter, D eighth (no 3rd note)
    assert len(notes) == 1
    assert isinstance(notes[0], Tuplet)
    assert len(notes[0].items) == 2


def test_a_single_triplet_group_cannot_span_a_bar_line():
    # Developer-confirmed: a triplet *group*'s own notes must complete
    # within one measure. A quarter in one measure and an eighth in the
    # next cannot combine into one eighth-note-triplet group, even though
    # each alone is a valid partial duration.
    from dottednotes.parser.braille_parser import TripletDurationError

    tokens = BrailleTokenizer().tokenize('⠐⠆⠹⠀⠑')  # sign, C quarter | D eighth
    with pytest.raises(TripletDurationError):
        BrailleParser(tokens=tokens).parse()


def test_triplet_block_can_span_a_bar_line_via_separate_self_contained_groups():
    # Developer-confirmed: a doubled-sign *block* may span a bar line —
    # three eighths in one measure, then three more in the next, marked
    # within one triplet block, is fine, because each group is complete
    # within its own measure (unlike the quarter+eighth case above).
    from dottednotes.models.tuplet import Tuplet

    tokens = BrailleTokenizer().tokenize('⠐⠆⠆⠙⠑⠋⠀⠛⠓⠊')  # doubled sign, CDE | FGA
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        score = BrailleParser(tokens=tokens).parse()
    measures = score.staves[0].measures
    assert len(measures) == 2
    assert len(measures[0].notes) == 1
    assert isinstance(measures[0].notes[0], Tuplet)
    assert [n.note_name for n in measures[0].notes[0].items] == ['C', 'D', 'E']
    assert len(measures[1].notes) == 1
    assert isinstance(measures[1].notes[0], Tuplet)
    assert [n.note_name for n in measures[1].notes[0].items] == ['F', 'G', 'A']


def test_unclosed_triplet_group_at_end_of_input_raises():
    # End-of-input is an implicit final bar line for this purpose: a group
    # left mid-flight there is just as malformed as at a real bar line.
    from dottednotes.parser.braille_parser import TripletDurationError

    tokens = BrailleTokenizer().tokenize('⠐⠆⠹')  # sign, C quarter — never closes
    with pytest.raises(TripletDurationError):
        BrailleParser(tokens=tokens).parse()


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
    # ⠸⠇ = octave-3 mark (⠸ dots 4,5,6) followed by an unrecognized cell
    # (⠇ dots 1,2,3 — not a note, rest, accidental, bar line, articulation,
    # ornament, slur, interval, or any other classified symbol)
    tokens = BrailleTokenizer().tokenize('⠸⠇')  # dots 4,5,6 + dots 1,2,3
    # The second cell (⠇ dots 1,2,3) is unrecognized
    unknown_tokens = [t for t in tokens if t.category == SymbolCategory.UNKNOWN]
    assert len(unknown_tokens) >= 1


def test_tokenizer_unknown_does_not_raise():
    # Any unrecognized cell must produce UNKNOWN, never raise.
    # ⠅ (dots 1,3) is not in any symbol table.
    tokens = BrailleTokenizer().tokenize('⠅')
    assert len(tokens) == 1
    assert tokens[0].category == SymbolCategory.UNKNOWN


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
    # Two notes on separate lines — newline emits an implicit BAR_LINE token
    tokens = BrailleTokenizer().tokenize('⠹\n⠱')
    assert tokens[0].line == 1   # first note
    assert tokens[1].line == 1   # implicit bar line at the newline position
    assert tokens[2].line == 2   # second note on line 2


def test_tokenizer_newline_produces_implicit_bar_line():
    # A newline following a note (not at a measure start) acts as a measure
    # separator and produces an implicit BAR_LINE token.  This matches BANA
    # braille music layout where each physical line holds one segment of measures.
    tokens = BrailleTokenizer().tokenize('⠹\n⠱')
    assert len(tokens) == 3
    assert tokens[1].category == SymbolCategory.BAR_LINE


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


# --- S5b-2: measure repeat (BANA Table 18, dots 2,3,5,6) ---

def test_tokenizer_classifies_measure_repeat_sign():
    tokens = BrailleTokenizer().tokenize('⠶')
    assert len(tokens) == 1
    assert tokens[0].category == SymbolCategory.REPEAT


def test_whole_measure_repeat_expands_previous_measure():
    # octave4, C D E F quarters (one full 4/4 measure), bar, single repeat sign
    measures = _parse_measures('⠐⠹⠱⠫⠻⠀⠶')
    assert [n.note_name for n in measures[1].notes] == ['C', 'D', 'E', 'F']
    assert [n.duration.value for n in measures[1].notes] == [4, 4, 4, 4]
    # A materialized copy, not the same objects as the original measure.
    assert measures[1].notes[0] is not measures[0].notes[0]


def test_whole_measure_repeat_sign_twice_duplicates_original_twice():
    # Two repeat signs together in the same measure: each one independently
    # repeats the *original* previous measure (BANA 18.2.1), not a cascading
    # repeat-of-a-repeat, so this is 2 copies of the 4-note original (8
    # notes), not a growing chain.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # 8 beats in a 4/4 measure — expected here
        measures = _parse_measures('⠐⠹⠱⠫⠻⠀⠶⠶')
    assert [n.note_name for n in measures[1].notes] == \
        ['C', 'D', 'E', 'F', 'C', 'D', 'E', 'F']


def test_part_measure_repeat_three_signs_totals_four_statements():
    # octave4, C8 D8 (1 beat) + 3 repeat signs, default 4/4: the pair is
    # played a total of 4 times (original + 3 repeats) to fill 4 beats.
    notes = _parse('⠐⠙⠑⠶⠶⠶')
    assert [n.note_name for n in notes] == ['C', 'D'] * 4
    assert all(n.duration.value == 8 for n in notes)
    assert len(notes) == 8


def test_whole_measure_repeat_with_no_previous_measure_raises():
    from dottednotes.parser.braille_parser import MeasureRepeatError

    tokens = BrailleTokenizer().tokenize('⠶')
    with pytest.raises(MeasureRepeatError):
        BrailleParser(tokens=tokens).parse()


# --- S8-5: braille numeral repeats (BANA Sec. 19) raise instead of parsing ---
# Table 19's own ASCII examples, decoded via NUMBER_SIGN/LITERARY_DIGITS/
# LOWER_DIGIT_CELLS/LITERARY_HYPHEN (all already-verified cells, see
# bana_symbols.py): conjunct "#b", disjunct "#e#d", single "#2", range "#2-4".

def test_tokenizer_recognizes_conjunct_backward_numeral_repeat():
    tokens = BrailleTokenizer().tokenize('⠼⠃')  # "#b" — digit 2
    assert len(tokens) == 1
    assert tokens[0].category == SymbolCategory.NUMERAL_REPEAT
    assert tokens[0].character == '⠼⠃'


def test_tokenizer_recognizes_disjunct_backward_numeral_repeat():
    tokens = BrailleTokenizer().tokenize('⠼⠑⠼⠙')  # "#e#d" — digits 5, 4
    assert len(tokens) == 1
    assert tokens[0].category == SymbolCategory.NUMERAL_REPEAT
    assert tokens[0].character == '⠼⠑⠼⠙'


def test_tokenizer_recognizes_single_measure_number_repeat():
    tokens = BrailleTokenizer().tokenize('⠼⠆')  # "#2"
    assert len(tokens) == 1
    assert tokens[0].category == SymbolCategory.NUMERAL_REPEAT
    assert tokens[0].character == '⠼⠆'


def test_tokenizer_recognizes_inclusive_measure_number_repeat():
    tokens = BrailleTokenizer().tokenize('⠼⠆⠤⠲')  # "#2-4"
    assert len(tokens) == 1
    assert tokens[0].category == SymbolCategory.NUMERAL_REPEAT
    assert tokens[0].character == '⠼⠆⠤⠲'


def test_backward_numeral_repeat_raises_braille_parse_error():
    from dottednotes.exceptions import BrailleParseError
    from dottednotes.parser.braille_parser import NumeralRepeatError

    tokens = BrailleTokenizer().tokenize('⠼⠃')
    assert issubclass(NumeralRepeatError, BrailleParseError)
    with pytest.raises(NumeralRepeatError, match="numeral repeat"):
        BrailleParser(tokens=tokens).parse()


def test_measure_number_repeat_raises_braille_parse_error():
    from dottednotes.parser.braille_parser import NumeralRepeatError

    tokens = BrailleTokenizer().tokenize('⠼⠆⠤⠲')
    with pytest.raises(NumeralRepeatError, match="numeral repeat"):
        BrailleParser(tokens=tokens).parse()


def test_numeral_repeat_mid_piece_raises_after_prior_measures_parsed():
    # A numeral repeat encountered after real measures have already been
    # parsed still raises -- it is never silently skipped or ignored
    # regardless of how much valid content precedes it.
    from dottednotes.parser.braille_parser import NumeralRepeatError

    tokens = BrailleTokenizer().tokenize('⠐⠹⠱⠫⠻⠀⠼⠆')
    with pytest.raises(NumeralRepeatError):
        BrailleParser(tokens=tokens).parse()


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
# S2-8: Measure number parsing — margin tokens and Measure.number assignment
# ---------------------------------------------------------------------------

_NUMBERED_FIXTURE = FIXTURES / 'simple_melody_with_measure_numbers.brf'


def _parse_numbered() -> list:
    """Return Measure objects from the numbered fixture."""
    pipeline = BRLInputPipeline()
    text = pipeline.load(_NUMBERED_FIXTURE)
    tokens = BrailleTokenizer().tokenize(text)
    return BrailleParser(tokens=tokens).parse().staves[0].measures


def test_literary_digits_table_populated():
    """LITERARY_DIGITS must cover all ten digits 0-9."""
    from dottednotes.bana_symbols import LITERARY_DIGITS
    assert set(LITERARY_DIGITS.values()) == set(range(10))


def test_measure_number_category_exists():
    """SymbolCategory must have MEASURE_NUMBER."""
    assert hasattr(SymbolCategory, 'MEASURE_NUMBER')


def test_measure_number_token_at_line_start():
    """A literary-digit cell at the very start of a line is a MEASURE_NUMBER token."""
    # Line 2 of the numbered fixture begins with 'A' (digit 1).
    pipeline = BRLInputPipeline()
    text = pipeline.load(_NUMBERED_FIXTURE)
    tokens = BrailleTokenizer().tokenize(text)
    mn_tokens = [t for t in tokens if t.category == SymbolCategory.MEASURE_NUMBER]
    assert len(mn_tokens) >= 1
    assert mn_tokens[0].character == '1'


def test_two_system_measure_numbers():
    """Fixture has two systems with explicit measure numbers: 1 and 5."""
    pipeline = BRLInputPipeline()
    text = pipeline.load(_NUMBERED_FIXTURE)
    tokens = BrailleTokenizer().tokenize(text)
    mn_tokens = [t for t in tokens if t.category == SymbolCategory.MEASURE_NUMBER]
    assert len(mn_tokens) == 2
    assert mn_tokens[0].character == '1'
    assert mn_tokens[1].character == '5'


def test_number_sign_prefixed_margin_number_followed_by_music_is_measure_number():
    # BANA 24.1.1: single-line solo margin numbers carry the number sign
    # (⠼), unlike a keyboard bar-over-bar margin number (BANA 29.3(b)).
    # Real content (a note) follows the margin here, disambiguating it from
    # the BANA Sec. 19 numeral-repeat shorthand, which uses the same shape.
    tokens = BrailleTokenizer().tokenize('⠼⠁⠀⠐⠹')
    assert tokens[0].category == SymbolCategory.MEASURE_NUMBER
    assert tokens[0].character == '1'


def test_bare_number_sign_digit_with_no_following_content_is_still_numeral_repeat():
    # Without real content after it, "#1" alone stays a BANA Sec. 19
    # numeral-repeat token (unsupported -- BrailleParser rejects it), not a
    # margin measure number -- a margin number is never the last thing in
    # the piece with nothing after it.
    tokens = BrailleTokenizer().tokenize('⠼⠁')
    assert len(tokens) == 1
    assert tokens[0].category == SymbolCategory.NUMERAL_REPEAT


def test_measure_number_not_parsed_mid_line():
    """Literary digit cells that appear mid-line are not parsed as MEASURE_NUMBER."""
    # ⠐⠹⠑ = octave-4 mark, C-quarter, D-eighth (⠑ = dots 1,5 = digit 5 mid-line)
    tokens = BrailleTokenizer().tokenize('⠐⠹⠑')
    cats = [t.category for t in tokens]
    assert SymbolCategory.MEASURE_NUMBER not in cats
    assert SymbolCategory.NOTE in cats


def test_measure_number_assigned_to_measure_objects():
    """Measure.number reflects the explicit margin number from the fixture."""
    measures = _parse_numbered()
    # System 1 starts at measure 1; system 2 starts at measure 5.
    assert measures[0].number == 1
    assert measures[4].number == 5


def test_sequential_measure_numbers_assigned():
    """All 8 measures should be numbered 1-8 sequentially."""
    measures = _parse_numbered()
    assert [m.number for m in measures] == list(range(1, 9))


def test_two_digit_measure_number_tokenized():
    """Two consecutive literary-digit cells at line start produce a single token."""
    # 'A' (digit 1) + 'J' (digit 0) = measure 10; followed by space then a note.
    text = '⠁⠚⠀⠐⠹'  # digits 1,0 + blank + octave4 + C-quarter
    tokens = BrailleTokenizer().tokenize(text)
    mn_tokens = [t for t in tokens if t.category == SymbolCategory.MEASURE_NUMBER]
    assert len(mn_tokens) == 1
    assert mn_tokens[0].character == '10'


def test_measure_number_continuity_warning():
    """Non-sequential margin measure numbers produce a plain text warning."""
    # Manually construct tokens: MEASURE_NUMBER(1) then notes then MEASURE_NUMBER(3)
    # (skipping 2 — should warn).
    # Build a minimal two-system BRF string with a skipped number.
    # System 1 starts at 1: ⠁ (digit 1) + ⠀ + ⠐⠹⠀ (octave C quarter bar)
    # Newline (→ implicit bar + at_line_start)
    # System 2 starts at 3 instead of 2: ⠉ (digit 3) + ⠀ + ⠐⠹⠀
    text = '⠁⠀⠐⠹⠀\n⠉⠀⠐⠹⠀'
    tokens = BrailleTokenizer().tokenize(text)
    with pytest.warns(UserWarning, match='measure number 3.*expected 2'):
        BrailleParser(tokens=tokens).parse()


def test_no_measure_numbers_assigns_sequentially():
    """A score with no margin numbers assigns sequential numbers from 1."""
    # Simple two-measure melody with no measure number tokens.
    text = '⠐⠹⠱⠫⠻⠀⠐⠳⠪⠺⠹⠀'
    tokens = BrailleTokenizer().tokenize(text)
    assert all(t.category != SymbolCategory.MEASURE_NUMBER for t in tokens)
    score = BrailleParser(tokens=tokens).parse()
    measures = score.staves[0].measures
    assert measures[0].number == 1
    assert measures[1].number == 2


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
# S8b-2: Bowing marks (down-bow / up-bow)
# BANA Music Braille Code 2015, Table 24(B), Sec. 25.3 -- down-bow "<b" = ⠣⠃,
# up-bow "<'" = ⠣⠄ (decoded via ASCII_TO_DOTS). Reuses the existing
# articulation carry/doubling mechanism (_handle_articulation) wholesale, so
# these tests mirror the staccato tests above one-for-one.
# ---------------------------------------------------------------------------

def test_tokenizer_down_bow_two_cells():
    tokens = BrailleTokenizer().tokenize('⠣⠃')
    assert len(tokens) == 1
    assert tokens[0].category == SymbolCategory.ARTICULATION
    assert tokens[0].character == '⠣⠃'


def test_tokenizer_up_bow_two_cells():
    tokens = BrailleTokenizer().tokenize('⠣⠄')
    assert len(tokens) == 1
    assert tokens[0].category == SymbolCategory.ARTICULATION
    assert tokens[0].character == '⠣⠄'


def test_tokenizer_flat_accidental_still_works_alongside_bowing_cells():
    # ⠣ alone (not followed by ⠃ or ⠄) must remain a flat ACCIDENTAL --
    # regression check that adding ⠣⠃/⠣⠄ to ARTICULATION_CELLS didn't
    # shadow the pre-existing flat-accidental fallthrough.
    tokens = BrailleTokenizer().tokenize('⠣⠐⠹')
    assert tokens[0].category == SymbolCategory.ACCIDENTAL
    assert tokens[1].category == SymbolCategory.OCTAVE_MARK
    assert tokens[2].category == SymbolCategory.NOTE


def test_parser_down_bow_attaches_to_note():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse('⠣⠃⠐⠹')
    assert len(notes[0].articulations) == 1
    assert notes[0].articulations[0].type == ArticulationType.DOWN_BOW


def test_parser_up_bow_attaches_to_note():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse('⠣⠄⠐⠹')
    assert notes[0].articulations[0].type == ArticulationType.UP_BOW


def test_parser_down_bow_does_not_carry_forward():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse('⠣⠃⠐⠹⠹')
    assert len(notes[0].articulations) == 1
    assert len(notes[1].articulations) == 0


def test_parser_doubled_down_bow_applies_to_all_following_notes():
    # BANA Sec. 25.3 / 1.12: doubled two-cell bowing sign continues across
    # 4+ successive notes.
    notes = _parse('⠣⠃⠣⠃⠐⠹⠹⠹⠹')
    assert all(len(n.articulations) == 1 for n in notes)
    assert all(n.articulations[0].type == ArticulationType.DOWN_BOW for n in notes)


def test_parser_doubled_up_bow_ends_on_terminator_sign():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse('⠣⠄⠣⠄⠐⠹⠹⠹⠣⠄⠹⠹')
    assert notes[0].articulations[0].type == ArticulationType.UP_BOW  # carry
    assert notes[1].articulations[0].type == ArticulationType.UP_BOW  # carry
    assert notes[2].articulations[0].type == ArticulationType.UP_BOW  # carry
    assert notes[3].articulations[0].type == ArticulationType.UP_BOW  # terminator note
    assert notes[4].articulations == []                                # carry ended


def test_parser_down_bow_renders_to_lilypond():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse('⠣⠃⠐⠹')
    assert r'\downbow' in notes[0].to_lilypond()


def test_parser_up_bow_renders_to_lilypond():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse('⠣⠄⠐⠹')
    assert r'\upbow' in notes[0].to_lilypond()


def test_parser_down_bow_renders_on_chord():
    # Bowing on the written note of a chord renders via Chord.to_lilypond()'s
    # existing _chord_extras (reads notes[0].articulations) -- no bowing-
    # specific code needed there.
    from dottednotes.models import Chord
    items = _parse_chords('⠣⠃⠐⠹⠬')
    assert isinstance(items[0], Chord)
    ly = items[0].to_relative_lilypond(60)[0]
    assert r'\downbow' in ly


def test_parser_wind_mute_and_open():
    from dottednotes.models.instrument import InstrumentInfo
    from dottednotes.models.articulation import ArticulationType
    
    # ⠣⠃ = mute sign, ⠐⠹ = C4 quarter note, ⠅ = open sign (after the note)
    brf = '⠣⠃⠐⠹⠅'
    tokens = BrailleTokenizer().tokenize(brf)
    
    # Wind instrument (Horn = Brass)
    inst_wind = InstrumentInfo(name="Horn", abbreviation="Hn")
    parser_wind = BrailleParser(tokens=tokens, active_instrument=inst_wind)
    score_wind = parser_wind.parse()
    notes_wind = score_wind.staves[0].measures[0].notes
    
    assert len(notes_wind[0].articulations) == 2
    assert notes_wind[0].articulations[0].type == ArticulationType.STOPPED
    assert notes_wind[0].articulations[1].type == ArticulationType.OPEN
    assert r'\stopped' in notes_wind[0].to_lilypond()
    assert r'\open' in notes_wind[0].to_lilypond()


def test_parser_bowed_string_open():
    from dottednotes.models.instrument import InstrumentInfo
    from dottednotes.models.articulation import ArticulationType
    
    # ⠣⠃ = down-bow sign, ⠐⠹ = C4 quarter note, ⠅ = open string sign (after the note)
    brf = '⠣⠃⠐⠹⠅'
    tokens = BrailleTokenizer().tokenize(brf)
    
    # Bowed String instrument (Violin = String)
    inst_str = InstrumentInfo(name="Violin I", abbreviation="Vln I")
    parser_str = BrailleParser(tokens=tokens, active_instrument=inst_str)
    score_str = parser_str.parse()
    notes_str = score_str.staves[0].measures[0].notes
    
    assert len(notes_str[0].articulations) == 2
    assert notes_str[0].articulations[0].type == ArticulationType.DOWN_BOW
    assert notes_str[0].articulations[1].type == ArticulationType.OPEN
    assert r'\downbow' in notes_str[0].to_lilypond()
    assert r'\open' in notes_str[0].to_lilypond()


def test_parser_plucked_string_and_keyboard_treat_dots_13_as_fingering():
    from dottednotes.models.instrument import InstrumentInfo
    from dottednotes.models.articulation import ArticulationType
    
    # ⠣⠃ = down-bow/mute sign, ⠐⠹ = C4 quarter note, ⠅ = dots 1-3
    brf = '⠣⠃⠐⠹⠅'
    tokens = BrailleTokenizer().tokenize(brf)
    
    # Plucked String instrument (Guitar = PluckedString)
    inst_guitar = InstrumentInfo(name="Guitar", abbreviation="Gtr")
    parser_guitar = BrailleParser(tokens=tokens, active_instrument=inst_guitar)
    score_guitar = parser_guitar.parse()
    notes_guitar = score_guitar.staves[0].measures[0].notes
    
    assert len(notes_guitar[0].articulations) == 1
    assert notes_guitar[0].articulations[0].type == ArticulationType.DOWN_BOW  # default
    assert len(notes_guitar[0].fingerings) == 1
    assert notes_guitar[0].fingerings[0].finger == 5
    
    # Keyboard instrument (Piano = KeyboardHarp)
    inst_piano = InstrumentInfo(name="Piano right hand", abbreviation="Prh")
    parser_piano = BrailleParser(tokens=tokens, active_instrument=inst_piano)
    score_piano = parser_piano.parse()
    notes_piano = score_piano.staves[0].measures[0].notes
    
    assert len(notes_piano[0].articulations) == 1
    assert notes_piano[0].articulations[0].type == ArticulationType.DOWN_BOW  # default
    assert len(notes_piano[0].fingerings) == 1
    assert notes_piano[0].fingerings[0].finger == 5


def test_parser_wind_mute_doubled_carry():
    from dottednotes.models.instrument import InstrumentInfo
    from dottednotes.models.articulation import ArticulationType
    
    # ⠣⠃⠣⠃ = doubled mute, ⠐⠹ = C4, ⠹ = C4, ⠹ = C4, ⠣⠃ = terminator, ⠹ = C4, ⠹ = C4
    brf = '⠣⠃⠣⠃⠐⠹⠹⠹⠣⠃⠹⠹'
    tokens = BrailleTokenizer().tokenize(brf)
    inst_wind = InstrumentInfo(name="Trumpet", abbreviation="Tpt")
    parser_wind = BrailleParser(tokens=tokens, active_instrument=inst_wind)
    score = parser_wind.parse()
    notes = score.staves[0].measures[0].notes
    
    # Check carry and termination
    assert notes[0].articulations[0].type == ArticulationType.STOPPED
    assert notes[1].articulations[0].type == ArticulationType.STOPPED
    assert notes[2].articulations[0].type == ArticulationType.STOPPED
    assert notes[3].articulations[0].type == ArticulationType.STOPPED # terminator note
    assert len(notes[4].articulations) == 0 # carry ended


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


# ---------------------------------------------------------------------------
# S4-6: Integration test — sprint_4_melody with all Sprint 4 elements
# ---------------------------------------------------------------------------

import functools

from dottednotes.models.note import Note
from dottednotes.models import TextMarkingType


@functools.lru_cache(maxsize=1)
def _sprint4_result():
    """Parse sprint_4_melody.brf once and cache for all S4-6 tests."""
    pipeline = BRLInputPipeline()
    text = pipeline.load(FIXTURES / 'sprint_4_melody.brf')
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        score = BrailleParser(tokens=BrailleTokenizer().tokenize(text)).parse()
    staff = score.staves[0]
    all_notes = [n for m in staff.measures for n in m.notes if isinstance(n, Note)]
    all_text_markings = [tm for m in staff.measures for tm in m.text_markings]
    return score, staff, all_notes, all_text_markings


def test_sprint4_melody_parses_without_error():
    score, staff, all_notes, _ = _sprint4_result()
    assert len(score.staves) == 1
    assert len(staff.measures) == 25


def test_sprint4_melody_header_tempo():
    _, staff, _, _ = _sprint4_result()
    assert staff.tempo is not None
    assert staff.tempo.text == 'Allegro moderato'
    assert staff.tempo.type == TextMarkingType.TEMPO


def test_sprint4_melody_key_and_time():
    _, staff, _, _ = _sprint4_result()
    assert staff.key_signature is not None
    assert staff.key_signature.sharps_or_flats == 1  # G major
    assert staff.time_signature is not None
    assert staff.time_signature.numerator == 4
    assert staff.time_signature.denominator == 4


def test_sprint4_melody_contains_articulations():
    _, _, all_notes, _ = _sprint4_result()
    assert any(n.articulations for n in all_notes)


def test_sprint4_melody_contains_dynamics():
    _, _, all_notes, _ = _sprint4_result()
    assert any(n.dynamics for n in all_notes)


def test_sprint4_melody_contains_ornament():
    _, _, all_notes, _ = _sprint4_result()
    assert any(n.ornaments for n in all_notes)


def test_sprint4_melody_contains_grace_note():
    _, _, all_notes, _ = _sprint4_result()
    assert any(n.grace_note is not None for n in all_notes)


def test_sprint4_melody_contains_slur():
    # slur_end is confirmed set; slur_start is affected by a pre-existing
    # grace-note carry-slur state bug and is not yet reliable across line breaks
    _, _, all_notes, _ = _sprint4_result()
    assert any(n.slur_end for n in all_notes)


def test_sprint4_melody_contains_tie():
    _, _, all_notes, _ = _sprint4_result()
    assert any(n.tie for n in all_notes)


def test_sprint4_melody_mid_piece_dolce():
    _, _, _, all_text_markings = _sprint4_result()
    assert any(tm.text == 'dolce' for tm in all_text_markings)


def test_sprint4_melody_renders_to_lilypond():
    score, _, _, _ = _sprint4_result()
    ly = score.to_lilypond()
    assert r'\version' in ly
    assert r'\relative' in ly
    assert r'\tempo "Allegro moderato"' in ly
    assert r'\key g \major' in ly
    assert r'\time 4/4' in ly
    assert '->' in ly       # accent
    assert '-.' in ly       # staccato
    assert '--' in ly       # tenuto
    assert r'\f' in ly      # forte
    assert r'\p' in ly      # piano
    assert r'\trill' in ly
    assert r'\grace' in ly  # grace notes


def test_sprint4_melody_lilypond_compiles():
    import shutil
    import subprocess
    if not shutil.which('lilypond'):
        pytest.skip('lilypond not installed')
    score, _, _, _ = _sprint4_result()
    result = subprocess.run(
        ['lilypond', '--silent', '-'],
        input=score.to_lilypond(),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f'LilyPond failed:\n{result.stderr}'


# ---------------------------------------------------------------------------
# Sprint 5 — Chord and Interval Parsing
# ---------------------------------------------------------------------------

from dottednotes.bana_symbols import INTERVAL_CELLS
from dottednotes.models import Chord


def _parse_chords(text: str) -> list:
    """Helper: tokenize and parse braille text, return items from first measure."""
    from dottednotes.parser import BrailleParser, BrailleTokenizer
    tokens = BrailleTokenizer().tokenize(text)
    score = BrailleParser(tokens=tokens).parse()
    return score.staves[0].measures[0].notes


# --- Tokenizer: interval cell classification ---

def test_interval_cells_in_bana_symbols():
    assert '⠌' in INTERVAL_CELLS and INTERVAL_CELLS['⠌'] == 2   # 2nd, dots 3,4
    assert '⠬' in INTERVAL_CELLS and INTERVAL_CELLS['⠬'] == 3   # 3rd, dots 3,4,6
    assert '⠼' in INTERVAL_CELLS and INTERVAL_CELLS['⠼'] == 4   # 4th, dots 3,4,5,6
    assert '⠔' in INTERVAL_CELLS and INTERVAL_CELLS['⠔'] == 5   # 5th, dots 3,5
    assert '⠴' in INTERVAL_CELLS and INTERVAL_CELLS['⠴'] == 6   # 6th, dots 3,5,6
    assert '⠒' in INTERVAL_CELLS and INTERVAL_CELLS['⠒'] == 7   # 7th, dots 2,5
    assert '⠤' in INTERVAL_CELLS and INTERVAL_CELLS['⠤'] == 8   # 8th (octave), dots 3,6


def test_tokenizer_classifies_interval_cells():
    from dottednotes.parser import BrailleTokenizer
    # ⠐⠹ = octave-4 C-quarter (puts us mid-measure); ⠬ = 3rd interval
    tokens = BrailleTokenizer().tokenize('⠐⠹⠬')
    interval_tokens = [t for t in tokens if t.category == SymbolCategory.INTERVAL]
    assert len(interval_tokens) == 1
    assert interval_tokens[0].character == '⠬'


def test_tokenizer_fourth_interval_mid_measure():
    """⠼ mid-measure (after a note) is a 4th interval, not a NUMBER_SIGN."""
    from dottednotes.parser import BrailleTokenizer
    tokens = BrailleTokenizer().tokenize('⠐⠹⠼')
    interval_tokens = [t for t in tokens if t.category == SymbolCategory.INTERVAL]
    assert len(interval_tokens) == 1
    assert interval_tokens[0].character == '⠼'


def test_tokenizer_number_sign_at_measure_start_is_time_sig():
    """⠼ at measure start is still a time/key signature prefix, not an interval."""
    from dottednotes.parser import BrailleTokenizer
    # ⠼⠙⠲ = 4/4 time signature
    tokens = BrailleTokenizer().tokenize('⠼⠙⠲')
    time_tokens = [t for t in tokens if t.category == SymbolCategory.TIME_SIGNATURE]
    assert len(time_tokens) == 1


def test_tokenizer_swell_2cell_takes_priority_over_octave_interval():
    """⠤⠄ (swell) must still be classified as ARTICULATION, not as ⠤ (8th interval) + ⠄."""
    from dottednotes.parser import BrailleTokenizer
    tokens = BrailleTokenizer().tokenize('⠐⠹⠤⠄')
    art_tokens = [t for t in tokens if t.category == SymbolCategory.ARTICULATION]
    interval_tokens = [t for t in tokens if t.category == SymbolCategory.INTERVAL]
    assert len(art_tokens) == 1
    assert len(interval_tokens) == 0


# --- Parser: basic chord building (treble clef, descending intervals) ---

def test_single_interval_creates_chord():
    """A note followed by one interval sign produces a Chord, not a Note."""
    # ⠐⠹ = octave-4 C-quarter; ⠬ = 3rd interval (treble → 3rd below C4 = A3)
    items = _parse_chords('⠐⠹⠬')
    assert len(items) == 1
    assert isinstance(items[0], Chord)


def test_chord_written_note_is_first():
    """The first note in a Chord is the written (top) note."""
    items = _parse_chords('⠐⠹⠬')
    chord = items[0]
    assert chord.notes[0].note_name == 'C'
    assert chord.notes[0].octave == 4


def test_third_below_c4_treble_is_a3():
    """3rd below C4 in treble clef (C major) = A3."""
    items = _parse_chords('⠐⠹⠬')
    chord = items[0]
    assert len(chord.notes) == 2
    assert chord.notes[1].note_name == 'A'
    assert chord.notes[1].octave == 3


def test_sixth_below_c5_treble_eb_major_is_eflat4():
    """6th below C5 in treble clef, Eb major key sig → E♭4."""
    # ⠣⠣⠣ = 3 flats (Eb major); ⠼⠉⠲ = 3/4; newline separates header from music;
    # ⠨⠹ = C5 quarter; ⠴ = 6th interval
    items = _parse_chords('⠣⠣⠣⠼⠉⠲\n⠨⠹⠴')
    chord = items[0]
    assert chord.notes[0].note_name == 'C'
    assert chord.notes[0].octave == 5
    interval_note = chord.notes[1]
    assert interval_note.note_name == 'E'
    assert interval_note.octave == 4
    assert interval_note.accidental is not None
    from dottednotes.models import AccidentalType
    assert interval_note.accidental.type == AccidentalType.FLAT


def test_fifth_below_c4_treble_is_f3():
    """5th below C4 in treble clef (C major) = F3."""
    items = _parse_chords('⠐⠹⠔')
    chord = items[0]
    assert chord.notes[1].note_name == 'F'
    assert chord.notes[1].octave == 3


def test_octave_interval_below_c5():
    """8th (octave) below C5 = C4."""
    items = _parse_chords('⠨⠹⠤')
    chord = items[0]
    assert chord.notes[1].note_name == 'C'
    assert chord.notes[1].octave == 4


def test_second_interval_below_e4():
    """2nd below E4 = D4."""
    # ⠐⠫ = octave-4 E-quarter; ⠌ = 2nd interval
    items = _parse_chords('⠐⠫⠌')
    chord = items[0]
    assert chord.notes[1].note_name == 'D'
    assert chord.notes[1].octave == 4


def test_seventh_below_g4():
    """7th below G4 = A3."""
    # ⠐⠳ = octave-4 G-quarter; ⠒ = 7th interval
    items = _parse_chords('⠐⠳⠒')
    chord = items[0]
    assert chord.notes[1].note_name == 'A'
    assert chord.notes[1].octave == 3


# --- Parser: multiple intervals on one note ---

def test_two_intervals_makes_three_note_chord():
    # ⠐⠹ = C4 quarter; ⠬ = 3rd (A3); ⠔ = 5th (F3)
    items = _parse_chords('⠐⠹⠬⠔')
    assert len(items) == 1
    chord = items[0]
    assert len(chord.notes) == 3
    assert chord.notes[0].note_name == 'C'
    assert chord.notes[1].note_name == 'A'
    assert chord.notes[2].note_name == 'F'


# --- Parser: intervals with explicit accidentals ---

def test_explicit_accidental_before_interval():
    """An accidental before an interval overrides the key signature."""
    # In G major (1 sharp: F#), a 3rd below A4 would be F#4 by key sig.
    # Adding a natural before the 3rd interval sign makes it F natural.
    # ⠩ = G major (1 sharp); ⠼⠙⠲ = 4/4; ⠐⠪ = A4 quarter;
    # ⠡ = natural accidental; ⠬ = 3rd interval
    items = _parse_chords('⠩⠼⠙⠲⠐⠪⠡⠬')
    chord = items[0]
    interval_note = chord.notes[1]
    assert interval_note.note_name == 'F'
    from dottednotes.models import AccidentalType
    assert interval_note.accidental is not None
    assert interval_note.accidental.type == AccidentalType.NATURAL


# --- Parser: bass clef (ascending intervals) ---

def test_bass_clef_third_above_e2():
    """Bass clef: 3rd above E2 = G2."""
    # ⠜⠼⠇ = bass clef; ⠼⠙⠲ = 4/4; ⠘⠫ = E2 (octave-2) quarter; ⠬ = 3rd interval
    items = _parse_chords('⠜⠼⠇⠼⠙⠲⠘⠫⠬')
    chord = items[0]
    assert chord.notes[0].note_name == 'E'
    assert chord.notes[0].octave == 2
    assert chord.notes[1].note_name == 'G'
    assert chord.notes[1].octave == 2


def test_bass_clef_sixth_above_e2():
    """Bass clef: 6th above E2 = C3."""
    # ⠼⠙⠲ = 4/4 time sig; newline separates header from music;
    # ⠜⠼⠇ = bass clef; ⠘⠫ = E2 quarter; ⠴ = 6th interval
    items = _parse_chords('⠼⠙⠲\n⠜⠼⠇⠘⠫⠴')
    chord = items[0]
    assert chord.notes[1].note_name == 'C'
    assert chord.notes[1].octave == 3


# --- S5b-3: ensemble scores read intervals upward regardless of clef ---

from dottednotes.models.instrument import InstrumentInfo


def _parse_chords_ensemble(text: str, instruments=None) -> list:
    """Like _parse_chords, but supplies an instrument list (BANA §33.2
    header) so BrailleParser treats the piece as an ensemble score."""
    from dottednotes.parser import BrailleParser, BrailleTokenizer
    if instruments is None:
        instruments = [InstrumentInfo(name='Violin I', abbreviation='vln', part_number='1')]
    tokens = BrailleTokenizer().tokenize(text)
    score = BrailleParser(tokens=tokens, instruments=instruments).parse()
    return score.staves[0].measures[0].notes


def test_no_instruments_keeps_clef_based_direction():
    """Regression: an empty/omitted instrument list must not change
    existing (non-ensemble) behavior — same input as
    test_third_below_c4_treble_is_a3, still 3rd *below* C4 = A3."""
    items = _parse_chords_ensemble('⠐⠹⠬', instruments=[])
    chord = items[0]
    assert chord.notes[1].note_name == 'A'
    assert chord.notes[1].octave == 3


def test_ensemble_treble_clef_interval_reads_upward():
    """BANA 33.4.2: with an instrument list present, intervals read upward
    in every part — treble clef no longer means "downward." Same input as
    test_third_below_c4_treble_is_a3 (3rd below C4 = A3 there); here the
    3rd above C4 = E4."""
    items = _parse_chords_ensemble('⠐⠹⠬')
    chord = items[0]
    assert chord.notes[1].note_name == 'E'
    assert chord.notes[1].octave == 4


def test_ensemble_alto_clef_interval_reads_upward():
    """Alto clef would normally also read downward (like treble); an
    ensemble score overrides that too."""
    # ⠜⠬⠇ = alto clef; ⠐⠹ = C4 quarter; ⠬ = 3rd interval
    items = _parse_chords_ensemble('⠜⠬⠇⠐⠹⠬')
    chord = items[0]
    assert chord.notes[1].note_name == 'E'
    assert chord.notes[1].octave == 4


def test_ensemble_bass_clef_interval_still_reads_upward():
    """Bass clef already reads upward outside ensembles (BANA general
    rule); an ensemble score must not flip that to downward. Same
    expectation as test_bass_clef_third_above_e2."""
    items = _parse_chords_ensemble('⠜⠼⠇⠼⠙⠲⠘⠫⠬')
    chord = items[0]
    assert chord.notes[1].note_name == 'G'
    assert chord.notes[1].octave == 2


# --- S5b-3: divisi-in-octaves voice reconstruction (BANA 33.4.2) ---
#
# Trigger confirmed against the real BANA Example 33.4.2-2 (decoded via
# the tokenizer from the manual's own braille-ASCII text): a WORD_SIGN
# "div" token, followed by a note, followed by a doubled octave-interval
# (⠤⠤) sign. That doubling already activates ordinary interval carry
# (S5-... interval doubling) — S5b-3 only changes what the carry produces
# once "div" was seen: two independent voices instead of a chord per note.
#
# ⠜⠙⠊⠧⠄ = word sign + d + i + v + end word sign ("div")
# ⠐⠹⠤⠤  = octave4, C4 quarter, doubled 8th (octave) interval -> divisi trigger
# ⠱⠫⠻   = D4, E4, F4 quarters (carried divisi voice; completes measure 1)
# ⠀      = bar line (carry must survive this, per BANA 33.4.2/existing carry rules)
# ⠳⠪    = G4, A4 quarters (still carried divisi voice, in measure 2)
# ⠤      = single terminating octave sign (clears carry, no new voice note)
# ⠺⠨⠹   = B4 quarter, octave5 C5 quarter (plain notes, divisi already ended)

def _divisi_measures(text: str):
    from dottednotes.parser import BrailleParser, BrailleTokenizer
    instruments = [InstrumentInfo(name='Violin I', abbreviation='vln', part_number='1')]
    tokens = BrailleTokenizer().tokenize(text)
    score = BrailleParser(tokens=tokens, instruments=instruments).parse()
    return score.staves[0].measures


def test_divisi_octave_reconstructs_two_voices_spanning_a_bar_line():
    measures = _divisi_measures('⠜⠙⠊⠧⠄⠐⠹⠤⠤⠱⠫⠻⠀⠳⠪⠤⠺⠨⠹')

    m1 = measures[0]
    assert len(m1.notes) == 1
    voice = m1.notes[0]
    assert isinstance(voice, InAccord)
    assert voice.in_accord_type == 'divisi_octave'
    # Treble clef (default, no explicit clef cell) -> highest voice first.
    higher, lower = voice.parts
    assert [n.note_name for n in lower] == ['C', 'D', 'E', 'F']
    assert [n.octave for n in lower] == [4, 4, 4, 4]
    assert [n.note_name for n in higher] == ['C', 'D', 'E', 'F']
    assert [n.octave for n in higher] == [5, 5, 5, 5]

    m2 = measures[1]
    # Divisi voice continues from measure 1 (G4/A4), then terminates and
    # B4/C5 are plain notes, not part of any InAccord.
    assert len(m2.notes) == 3
    voice2 = m2.notes[0]
    assert isinstance(voice2, InAccord)
    higher2, lower2 = voice2.parts
    assert [n.note_name for n in lower2] == ['G', 'A']
    assert [n.note_name for n in higher2] == ['G', 'A']
    assert [n.octave for n in higher2] == [5, 5]
    assert m2.notes[1].note_name == 'B' and m2.notes[1].octave == 4
    assert m2.notes[2].note_name == 'C' and m2.notes[2].octave == 5


def test_octave_doubling_without_div_marking_still_builds_chords():
    """Control: the same doubled-octave-interval pattern without a
    preceding 'div' word-sign must keep today's behavior (a Chord per
    note via ordinary interval-carry), matching Example 33.4.2-1's plain
    double/octave stops — 'div' is what makes it a voice split, not the
    doubled sign alone."""
    from dottednotes.models import Chord
    measures = _divisi_measures('⠐⠹⠤⠤⠱⠫⠻⠀⠳⠪⠤⠺⠨⠹')
    m1 = measures[0]
    assert all(isinstance(item, Chord) for item in m1.notes)
    assert [c.notes[0].note_name for c in m1.notes] == ['C', 'D', 'E', 'F']
    assert [c.notes[1].octave for c in m1.notes] == [5, 5, 5, 5]


# --- LilyPond rendering ---

def test_chord_lilypond_format():
    """C4 quarter + 3rd below (A3) renders as '<c a>4': correct notes, duration, structure."""
    # ⠐⠹⠬ = C4 quarter + 3rd below (A3) in C major
    items = _parse_chords('⠐⠹⠬')
    chord = items[0]
    ly = chord.to_relative_lilypond(60)[0]
    # Outer structure: angle brackets wrap both pitch names
    assert ly.startswith('<')
    assert '>4' in ly
    # Pitch names inside the brackets
    inner = ly[1:ly.index('>')]
    assert inner == 'c a'
    # Duration appears once after '>', not inside the brackets
    assert '4' not in inner


# --- Interval doubling (carry mode) ---

def test_interval_doubling_carry_mode():
    """Interval sign after note1 then doubled activates carry for 4 successive notes.

    Sequence: ⠐⠹ = C4; ⠬ = 3rd applied to C4; ⠬ = doubled → carry;
    ⠱⠐⠫⠳ = D4 E4 G4 (each gets 3rd from carry); ⠬ = terminator after G4.
    Expected intervals (3rd below, treble, C major):
      C4 → A3, D4 → B3, E4 → C4, G4 → E4
    """
    text = '⠐⠹⠬⠬⠱⠐⠫⠳⠬'
    items = _parse_chords(text)
    # All four notes become chords via carry
    assert all(isinstance(item, Chord) for item in items)
    # C4 + 3rd below = A3
    assert items[0].notes[1].note_name == 'A'
    # D4 + 3rd below = B3 (carry)
    assert items[1].notes[1].note_name == 'B'
    # G4 + 3rd below = E4 (last carried note, also the terminator note)
    assert items[3].notes[1].note_name == 'E'


def test_interval_doubling_terminates_at_final_bar():
    """Active doublings terminate at a final double bar."""
    # ⠐⠹⠬⠬ = C4 with 3rd applied + carry; ⠱⠐⠫⠳ = three carry notes; ⠣⠅ = final bar
    # After the bar, a plain note (no interval) should just be a Note, not a Chord
    text = '⠐⠹⠬⠬⠱⠐⠫⠳⠣⠅\n⠐⠹'
    from dottednotes.parser import BrailleParser, BrailleTokenizer
    tokens = BrailleTokenizer().tokenize(text)
    score = BrailleParser(tokens=tokens).parse()
    staff = score.staves[0]
    # First measure: four chords (carry active)
    assert isinstance(staff.measures[0].notes[0], Chord)
    # Second measure: plain note (carry terminated by final bar)
    assert isinstance(staff.measures[1].notes[0], Note)


def test_interval_doubling_terminator_note_has_exactly_one_interval():
    """Terminator sign must not add a duplicate interval to the last carried note."""
    # G4 gets E4 via carry; terminator ⠬ clears carry without re-applying the interval.
    text = '⠐⠹⠬⠬⠱⠐⠫⠳⠬'
    items = _parse_chords(text)
    # G4 should be a 2-note chord (G4 + E4), NOT 3-note (G4 + E4 + E4)
    assert len(items[3].notes) == 2


def test_multiple_doublings_terminated_together():
    """BANA 9.3.3: terminating one interval doubling terminates all active doublings."""
    # ⠐⠹ = C4; ⠬⠬ = 3rd doubled; ⠔⠔ = 5th doubled
    # ⠱⠐⠫⠳ = D4 E4 G4 (carry applies both 3rd and 5th)
    # ⠬ = terminator for 3rd → clears 3rd AND 5th simultaneously (BANA 9.3.3)
    # ⠵ = A4 (plain note, no intervals)
    text = '⠐⠹⠬⠬⠔⠔⠱⠐⠫⠳⠬⠵'
    items = _parse_chords(text)
    assert len(items[0].notes) == 3   # C4 + A3 (3rd) + F3 (5th)
    assert len(items[1].notes) == 3   # D4 + B3 (3rd) + G3 (5th)
    assert len(items[2].notes) == 3   # E4 + C4 (3rd) + A3 (5th)
    assert len(items[3].notes) == 3   # G4 + E4 (3rd) + C4 (5th)
    assert isinstance(items[4], Note)  # A4: both carries ended (BANA 9.3.3)


# =============================================================================
# S8b-4: Chord ties (BANA Music Braille Code 2015, Table 10, Sec. 10.2)
# =============================================================================

_CHORD_TIE = '⠨⠉'  # dots 4,6 + dots 1,4 — placed after a tied chord


# --- Tokenizer: chord-tie cell recognition ---

def test_tokenizer_chord_tie_is_slur_category():
    tokens = BrailleTokenizer().tokenize('⠐⠹⠬' + _CHORD_TIE + '⠐⠹⠬')
    slur_tokens = [t for t in tokens if t.category == SymbolCategory.SLUR]
    assert len(slur_tokens) == 1
    assert slur_tokens[0].character == _CHORD_TIE


def test_tokenizer_chord_tie_not_split_into_octave_mark_plus_slur():
    # ⠨ (dots 4,6) is octave mark 5; before this fix, ⠨⠉ mis-tokenized as
    # octave-mark-5 + plain slur instead of one chord-tie SLUR token.
    tokens = BrailleTokenizer().tokenize('⠐⠹⠬' + _CHORD_TIE + '⠐⠹⠬')
    octave_tokens = [t for t in tokens if t.category == SymbolCategory.OCTAVE_MARK]
    assert all(t.character == '⠐' for t in octave_tokens)
    stray_slurs = [t for t in tokens if t.character == '⠉' and t.category == SymbolCategory.SLUR]
    assert stray_slurs == []


# --- Parser: chord tie ---

def test_parser_chord_tie_attaches_to_first_chord_only():
    """A single chord-tie sign ties exactly the chord pair it sits between."""
    items = _parse_chords('⠐⠹⠬' + _CHORD_TIE + '⠐⠹⠬')
    assert items[0].notes[0].tie is True
    assert items[1].notes[0].tie is False


def test_parser_chord_tie_renders_tilde_in_lilypond():
    items = _parse_chords('⠐⠹⠬' + _CHORD_TIE + '⠐⠹⠬')
    ly0 = items[0].to_relative_lilypond(60)[0]
    ly1 = items[1].to_relative_lilypond(60)[0]
    assert ly0.count('~') == 1
    assert ly0.index('~') > ly0.index('>')  # placed after the chord's closing bracket
    assert '~' not in ly1


def test_chord_tie_doubling_carry_mode():
    """Doubled chord-tie sign (⠨⠉⠉) ties 4 successive chords via carry; a
    single terminator restatement ends the carry for the chord after it
    (BANA Sec. 10.2.2, mirrors test_interval_doubling_carry_mode /
    test_parser_doubled_staccato_ends_on_third_sign's shape).
    """
    text = ('⠐⠹⠬' + _CHORD_TIE + '⠉' + '⠱⠬' + '⠐⠫⠬' + '⠳⠬'
            + _CHORD_TIE + '⠐⠹⠬')
    items = _parse_chords(text)
    assert len(items) == 5
    assert all(isinstance(item, Chord) for item in items)
    assert items[0].notes[0].tie is True
    assert items[1].notes[0].tie is True
    assert items[2].notes[0].tie is True
    assert items[3].notes[0].tie is True   # terminator chord, also carried
    assert items[4].notes[0].tie is False  # carry ended


def test_chord_tie_carry_terminates_at_final_bar():
    """Active chord-tie carry terminates at a final double bar (BANA Sec. 10.1.2,
    mirrors test_interval_doubling_terminates_at_final_bar)."""
    text = ('⠐⠹⠬' + _CHORD_TIE + '⠉' + '⠱⠬' + '⠐⠫⠬' + '⠳⠬' + '⠣⠅\n⠐⠹⠬')
    tokens = BrailleTokenizer().tokenize(text)
    score = BrailleParser(tokens=tokens).parse()
    staff = score.staves[0]
    assert staff.measures[0].notes[3].notes[0].tie is True    # last carried chord
    assert staff.measures[1].notes[0].notes[0].tie is False   # carry ended by bar


def test_chord_tie_does_not_interrupt_interval_doubling_carry():
    """BANA Sec. 10.2.1: an active interval-doubling carry must not be
    interrupted by a chord tie occurring between carried chords."""
    # ⠐⠹⠬⠬ = C4 with 3rd applied + carry; a chord tie then ties this chord
    # to the next; ⠱⠐⠫⠳ = three more notes, each still carrying the 3rd
    # interval independently of the (single, non-carrying) chord-tie sign.
    text = '⠐⠹⠬⠬' + _CHORD_TIE + '⠱⠐⠫⠳'
    items = _parse_chords(text)
    assert len(items) == 4
    assert all(isinstance(item, Chord) for item in items)
    # Interval carry still applies to every chord (BANA 9.3 unaffected).
    assert items[1].notes[1].note_name == 'B'  # D4 + 3rd below (carry)
    assert items[3].notes[1].note_name == 'E'  # G4 + 3rd below (carry)
    # A single (non-doubled) chord tie only ties the first pair.
    assert items[0].notes[0].tie is True
    assert items[1].notes[0].tie is False


def test_regression_plain_slur_without_preceding_chord_tie_still_works():
    """An ordinary bare slur cell, not preceded by a chord-tie sign, is unaffected."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse('⠐⠹' + '⠉' + '⠹')
    assert notes[0].tie is False
    assert notes[1].tie is False


# =============================================================================
# S5-2: In-accord parsing
# =============================================================================

from dottednotes.bana_symbols import IN_ACCORD_CELLS
from dottednotes.models.in_accord import InAccord
from dottednotes.models.note import Note
from dottednotes.models.accidental import Accidental, AccidentalType


# --- Symbol table ---

def test_in_accord_cells_contains_all_three_signs():
    assert '⠣⠜' in IN_ACCORD_CELLS and IN_ACCORD_CELLS['⠣⠜'] == 'full_measure'
    assert '⠐⠂' in IN_ACCORD_CELLS and IN_ACCORD_CELLS['⠐⠂'] == 'part_measure'
    assert '⠨⠅' in IN_ACCORD_CELLS and IN_ACCORD_CELLS['⠨⠅'] == 'measure_division'


# --- Tokenizer: in-accord sign classification ---

def test_tokenizer_classifies_full_measure_in_accord():
    tokens = BrailleTokenizer().tokenize('⠣⠜')
    assert len(tokens) == 1
    assert tokens[0].category == SymbolCategory.IN_ACCORD
    assert tokens[0].character == '⠣⠜'


def test_tokenizer_classifies_part_measure_in_accord():
    tokens = BrailleTokenizer().tokenize('⠐⠂')
    assert len(tokens) == 1
    assert tokens[0].category == SymbolCategory.IN_ACCORD
    assert tokens[0].character == '⠐⠂'


def test_tokenizer_classifies_measure_division():
    tokens = BrailleTokenizer().tokenize('⠨⠅')
    assert len(tokens) == 1
    assert tokens[0].category == SymbolCategory.IN_ACCORD
    assert tokens[0].character == '⠨⠅'


def test_tokenizer_in_accord_not_confused_with_flat_accidental():
    # ⠣⠜ must be IN_ACCORD, not ACCIDENTAL (flat) followed by something else
    tokens = BrailleTokenizer().tokenize('⠣⠜')
    assert tokens[0].category == SymbolCategory.IN_ACCORD
    assert tokens[0].category != SymbolCategory.ACCIDENTAL


def test_tokenizer_in_accord_not_confused_with_octave4_mark():
    # ⠐⠂ must be IN_ACCORD, not OCTAVE_MARK (⠐) followed by UNKNOWN (⠂)
    tokens = BrailleTokenizer().tokenize('⠐⠂')
    assert len(tokens) == 1
    assert tokens[0].category == SymbolCategory.IN_ACCORD


def test_tokenizer_in_accord_not_confused_with_octave5_mark():
    # ⠨⠅ must be IN_ACCORD, not OCTAVE_MARK (⠨) followed by UNKNOWN (⠅)
    tokens = BrailleTokenizer().tokenize('⠨⠅')
    assert len(tokens) == 1
    assert tokens[0].category == SymbolCategory.IN_ACCORD


def test_tokenizer_flat_alone_still_accidental():
    # ⠣ alone (not followed by ⠜) should still be ACCIDENTAL in mid-measure context.
    # Use ⠐⠹⠣⠱ (C4 quarter, flat accidental, D quarter) — ⠣ is not followed by ⠜.
    tokens = BrailleTokenizer().tokenize('⠐⠹⠣⠱')
    in_accord_toks = [t for t in tokens if t.category == SymbolCategory.IN_ACCORD]
    accidental_toks = [t for t in tokens if t.category == SymbolCategory.ACCIDENTAL]
    assert len(in_accord_toks) == 0
    assert len(accidental_toks) == 1


def test_tokenizer_octave4_mark_alone_still_octave_mark():
    # ⠐ alone (not followed by ⠂) should still be OCTAVE_MARK.
    tokens = BrailleTokenizer().tokenize('⠐⠹')
    assert tokens[0].category == SymbolCategory.OCTAVE_MARK
    assert tokens[0].character == '⠐'


def test_tokenizer_octave5_mark_alone_still_octave_mark():
    # ⠨ alone (not followed by ⠅) should still be OCTAVE_MARK.
    # Use ⠨⠦ (accent articulation) to ensure ⠨ isn't consumed as in-accord.
    tokens = BrailleTokenizer().tokenize('⠨⠦')
    assert tokens[0].category == SymbolCategory.ARTICULATION
    assert tokens[0].character == '⠨⠦'


# --- Parser: full-measure in-accord ---

# Braille sequence: voice1 (C4 D4 E4 F4) + full-measure in-accord + voice2 (G4 A4 B4 C4) + bar
_FULL_ACCORD = '⠐⠹⠱⠫⠻⠣⠜⠐⠳⠪⠺⠹⠀'


def _parse_in_accord(text: str) -> list:
    """Helper: parse braille text, return notes from first measure."""
    tokens = BrailleTokenizer().tokenize(text)
    score = BrailleParser(tokens=tokens).parse()
    return score.staves[0].measures[0].notes


def test_parser_full_measure_in_accord_parses_correctly():
    items = _parse_in_accord(_FULL_ACCORD)
    assert len(items) == 1
    ia = items[0]
    assert isinstance(ia, InAccord)
    assert len(ia.parts) == 2
    assert [(n.note_name, n.octave) for n in ia.parts[0]] == [
        ('C', 4), ('D', 4), ('E', 4), ('F', 4)
    ]
    # Voice 2's last note (C, unmarked after B4) resolves to C5, not C4:
    # BANA Sec. 3.2.2 -- an unmarked note a 7th away in the same octave is
    # always the 2nd-away complement in the adjacent octave instead.
    assert [(n.note_name, n.octave) for n in ia.parts[1]] == [
        ('G', 4), ('A', 4), ('B', 4), ('C', 5)
    ]


def test_parser_in_accord_accidental_does_not_carry_across_boundary():
    # Voice 1 ends with a sharp-F4; voice 2 starts after the in-accord sign.
    # BANA 11.2: the sharp must not carry into voice 2.
    # ⠩⠻ = sharp F4 quarter
    # After ⠣⠜, the first note of voice 2 (G4) should have no accidental.
    text = '⠐⠹⠱⠫⠩⠻⠣⠜⠐⠳⠪⠺⠹⠀'
    items = _parse_in_accord(text)
    voice1 = items[0].parts[0]
    voice2 = items[0].parts[1]
    # Voice 1: F4 should have a sharp
    assert voice1[3].accidental is not None
    assert voice1[3].accidental.type == AccidentalType.SHARP
    # Voice 2: G4 should have no accidental carried from voice 1
    assert voice2[0].accidental is None


def test_parser_in_accord_type_is_full():
    items = _parse_in_accord(_FULL_ACCORD)
    assert items[0].in_accord_type == 'full_measure'


def test_parser_in_accord_across_two_measures():
    # Two measures: first has in-accord, second is plain.
    text = _FULL_ACCORD + '⠐⠹⠀'
    tokens = BrailleTokenizer().tokenize(text)
    score = BrailleParser(tokens=tokens).parse()
    staff = score.staves[0]
    assert len(staff.measures) == 2
    assert isinstance(staff.measures[0].notes[0], InAccord)
    assert isinstance(staff.measures[1].notes[0], Note)


# --- Parser: part-measure in-accord (BANA 11.1.2) ---

# 4/4 measure: [half C] part-measure-sign [quarter E, quarter F]
# measure-division-sign [quarter G, quarter A] bar
# Section 1 has two voices covering the first half of the measure (2 beats
# each); section 2 is a single voice covering the second half (2 beats).
_PART_MEASURE_ACCORD = '⠐⠝⠐⠂⠫⠻⠨⠅⠳⠪⠀'


def test_part_measure_two_voices_first_half():
    items = _parse_in_accord(_PART_MEASURE_ACCORD)
    assert len(items) == 3
    ia = items[0]
    assert isinstance(ia, InAccord)
    assert ia.in_accord_type == 'part_measure'
    assert len(ia.parts) == 2
    assert [(n.note_name, n.octave, n.duration.value) for n in ia.parts[0]] == [
        ('C', 4, 2)
    ]
    assert [(n.note_name, n.octave, n.duration.value) for n in ia.parts[1]] == [
        ('E', 4, 4), ('F', 4, 4)
    ]
    assert isinstance(items[1], Note) and items[1].note_name == 'G'
    assert isinstance(items[2], Note) and items[2].note_name == 'A'


def test_part_measure_division_creates_sections():
    # The measure-division sign closes section 1 (two voices) before
    # section 2 (single voice) begins.
    items = _parse_in_accord(_PART_MEASURE_ACCORD)
    ia = items[0]
    assert len(ia.parts) == 2  # section 1 only — section 2 is single-voice


def test_part_measure_accidental_does_not_carry_across_part_sign():
    # Sharp before the part-measure sign (on voice 1's only note) must not
    # carry into voice 2's first note (BANA 11.2).
    text = '⠐⠩⠝⠐⠂⠫⠻⠨⠅⠳⠪⠀'
    items = _parse_in_accord(text)
    ia = items[0]
    assert ia.parts[0][0].accidental is not None
    assert ia.parts[0][0].accidental.type == AccidentalType.SHARP
    assert ia.parts[1][0].accidental is None


def test_part_measure_accidental_does_not_carry_across_division_sign():
    # Sharp before the measure-division sign (on the last note of section 1)
    # must not carry into section 2's first note (BANA 11.2).
    text = '⠐⠝⠐⠂⠫⠩⠻⠨⠅⠳⠪⠀'
    items = _parse_in_accord(text)
    ia = items[0]
    assert ia.parts[1][1].accidental is not None
    assert ia.parts[1][1].accidental.type == AccidentalType.SHARP
    assert items[1].accidental is None


def test_single_voice_section_adds_notes_directly():
    # Section 2 has only one voice, so its notes are added flat to the
    # measure rather than wrapped in an InAccord.
    items = _parse_in_accord(_PART_MEASURE_ACCORD)
    assert not isinstance(items[1], InAccord)
    assert not isinstance(items[2], InAccord)


def test_part_measure_renders_lilypond():
    tokens = BrailleTokenizer().tokenize(_PART_MEASURE_ACCORD)
    score = BrailleParser(tokens=tokens).parse()
    ly_out = score.staves[0].to_lilypond()
    assert '<< { c2 } \\\\ { e4 f4 } >>' in ly_out
    assert 'g' in ly_out and 'a4' in ly_out


# --- InAccord model: to_relative_lilypond ---

def test_in_accord_to_relative_lilypond_structure():
    ia = _parse_in_accord(_FULL_ACCORD)[0]
    ly, _ = ia.to_relative_lilypond(60)
    assert ly.startswith('<<')
    assert ly.endswith('>>')
    assert ly.count('\\\\') == 1  # exactly one separator for two voices


def test_in_accord_to_relative_lilypond_prev_midi_advances_through_last_voice():
    # LilyPond's \relative pitch tracking treats '<<', '\\', and '>>' as
    # complete no-ops -- a purely sequential/textual chain through the
    # token stream (verified against real `lilypond`'s `\displayLilyMusic`
    # output; see test_lilypond_parser.py's in-accord tests for the
    # disambiguating cases). So prev_midi must advance through voice 1
    # (C4 D4 E4 F4, ending at F4=65) and then through voice 2, which
    # chains from voice 1's F4 rather than resetting to the original
    # prev_midi=60: G4=67, A4=69, B4=71, C5=72.
    items = _parse_in_accord(_FULL_ACCORD)
    ia = items[0]
    _, new_midi = ia.to_relative_lilypond(60)
    # C5 = MIDI 72
    assert new_midi == 72


def test_in_accord_renders_inside_measure_to_lilypond():
    # Measure.to_lilypond() should delegate to InAccord.to_relative_lilypond().
    tokens = BrailleTokenizer().tokenize(_FULL_ACCORD)
    score = BrailleParser(tokens=tokens).parse()
    staff = score.staves[0]
    ly_out = staff.to_lilypond()
    assert '<<' in ly_out
    assert '\\\\' in ly_out
    assert '>>' in ly_out


# Voice 1: C4 D4 E4 F4, voice 2: G4 A4 B4 C5, voice 3: E4 F4 G4 A4 (all quarter notes)
_THREE_VOICE_ACCORD = '⠐⠹⠱⠫⠻⠣⠜⠐⠳⠪⠺⠹⠣⠜⠐⠫⠻⠳⠪⠀'


def test_three_voice_in_accord_parses_correctly():
    items = _parse_in_accord(_THREE_VOICE_ACCORD)
    assert len(items) == 1
    ia = items[0]
    assert isinstance(ia, InAccord)
    assert len(ia.parts) == 3
    assert [(n.note_name, n.octave) for n in ia.parts[0]] == [
        ('C', 4), ('D', 4), ('E', 4), ('F', 4)
    ]
    # Voice 2's last note (C, unmarked after B4) resolves to C5 -- see
    # test_parser_full_measure_in_accord_parses_correctly for why.
    assert [(n.note_name, n.octave) for n in ia.parts[1]] == [
        ('G', 4), ('A', 4), ('B', 4), ('C', 5)
    ]
    assert [(n.note_name, n.octave) for n in ia.parts[2]] == [
        ('E', 4), ('F', 4), ('G', 4), ('A', 4)
    ]


def test_in_accord_voice_with_transcriber_added_rest():
    # Transcriber-added rests use dot 5 (⠐) as a prefix before the rest cell.
    # The dot 5 is also the octave-4 mark; before a rest it is harmlessly consumed.
    # Voice 1: C4 D4 E4 F4 quarter notes
    # Voice 2: ⠐⠍ = dot-5 prefix + whole-rest cell → whole-measure rest
    from dottednotes.models.note import Rest
    text = '⠐⠹⠱⠫⠻⠣⠜⠐⠍⠀'
    items = _parse_in_accord(text)
    ia = items[0]
    assert len(ia.parts) == 2
    voice2 = ia.parts[1]
    assert len(voice2) == 1
    assert isinstance(voice2[0], Rest)
    assert voice2[0].is_full_measure is True


# --- S5-4: hand signs and staff assembly ---

from dottednotes.bana_symbols import HAND_SIGN_CELLS


def test_hand_sign_cells_contains_both_signs():
    assert '⠨⠜' in HAND_SIGN_CELLS and HAND_SIGN_CELLS['⠨⠜'] == 'right'
    assert '⠸⠜' in HAND_SIGN_CELLS and HAND_SIGN_CELLS['⠸⠜'] == 'left'


# --- Tokenizer: hand-sign classification ---

def test_tokenizer_classifies_right_hand_sign():
    tokens = BrailleTokenizer().tokenize('⠨⠜')
    assert len(tokens) == 1
    assert tokens[0].category == SymbolCategory.HAND_SIGN
    assert tokens[0].character == 'right'


def test_tokenizer_classifies_left_hand_sign():
    tokens = BrailleTokenizer().tokenize('⠸⠜')
    assert len(tokens) == 1
    assert tokens[0].category == SymbolCategory.HAND_SIGN
    assert tokens[0].character == 'left'


def test_tokenizer_hand_sign_not_confused_with_octave5_mark():
    # ⠨ alone (not followed by ⠜) should still be OCTAVE_MARK.
    tokens = BrailleTokenizer().tokenize('⠨⠹')
    assert tokens[0].category == SymbolCategory.OCTAVE_MARK
    assert tokens[0].character == '⠨'


def test_tokenizer_hand_sign_not_confused_with_octave3_mark():
    # ⠸ alone (not followed by ⠜) should still be OCTAVE_MARK.
    tokens = BrailleTokenizer().tokenize('⠸⠹')
    assert tokens[0].category == SymbolCategory.OCTAVE_MARK
    assert tokens[0].character == '⠸'


def test_tokenizer_right_hand_sign_not_confused_with_measure_division():
    # ⠨⠅ (measure_division) must stay IN_ACCORD, not HAND_SIGN, despite sharing ⠨.
    tokens = BrailleTokenizer().tokenize('⠨⠅')
    assert tokens[0].category == SymbolCategory.IN_ACCORD
    assert tokens[0].character == '⠨⠅'


def test_tokenizer_hand_sign_consumes_disambiguator_when_present():
    # ⠝ (half/32nd C) contains dot 1 — the disambiguator (⠄, dot 3) is present
    # in the source and must be silently consumed, not emitted as a token.
    tokens = BrailleTokenizer().tokenize('⠨⠜⠄⠝⠹')
    assert [t.category for t in tokens] == [
        SymbolCategory.HAND_SIGN, SymbolCategory.NOTE, SymbolCategory.NOTE,
    ]
    assert tokens[1].position == 3  # 2 cells for the hand sign + 1 disambiguator


def test_tokenizer_hand_sign_no_disambiguator_when_absent():
    tokens = BrailleTokenizer().tokenize('⠨⠜⠝⠹')
    assert [t.category for t in tokens] == [
        SymbolCategory.HAND_SIGN, SymbolCategory.NOTE, SymbolCategory.NOTE,
    ]
    assert tokens[1].position == 2  # 2 cells for the hand sign, no disambiguator


# --- Parser: staff routing ---

# Two systems: right hand (C D E F | C D E F), left hand (G A B C | G A B C).
_TWO_HAND_SNIPPET = (
    '⠨⠜⠐⠹⠱⠫⠻⠀'
    '⠸⠜⠸⠳⠪⠺⠹⠀'
    '⠨⠜⠐⠹⠱⠫⠻⠀'
    '⠸⠜⠸⠳⠪⠺⠹⠀'
)


def test_parser_routes_measures_to_two_staves():
    tokens = BrailleTokenizer().tokenize(_TWO_HAND_SNIPPET)
    score = BrailleParser(tokens=tokens).parse()
    assert len(score.staves) == 2
    assert score.staves[0].name == 'right hand'
    assert score.staves[1].name == 'left hand'
    assert len(score.staves[0].measures) == 2
    assert len(score.staves[1].measures) == 2


def test_parser_staff_routing_note_content():
    tokens = BrailleTokenizer().tokenize(_TWO_HAND_SNIPPET)
    score = BrailleParser(tokens=tokens).parse()
    right_notes = [n.note_name for n in score.staves[0].measures[0].notes]
    left_notes = [n.note_name for n in score.staves[1].measures[0].notes]
    assert right_notes == ['C', 'D', 'E', 'F']
    assert left_notes == ['G', 'A', 'B', 'C']


def test_parser_staff_routing_measure_numbers_match():
    tokens = BrailleTokenizer().tokenize(_TWO_HAND_SNIPPET)
    score = BrailleParser(tokens=tokens).parse()
    right_numbers = [m.number for m in score.staves[0].measures]
    left_numbers = [m.number for m in score.staves[1].measures]
    assert right_numbers == [1, 2]
    assert left_numbers == [1, 2]


def test_parser_no_hand_sign_still_produces_one_staff():
    # Backward compatibility: files with no hand signs at all route everything
    # to a single staff, now named "right hand" instead of "".
    text = '⠐⠹⠱⠫⠻⠀'
    tokens = BrailleTokenizer().tokenize(text)
    score = BrailleParser(tokens=tokens).parse()
    assert len(score.staves) == 1
    assert score.staves[0].name == 'right hand'
    assert len(score.staves[0].measures) == 1


def test_parser_staff_clef_heuristic_differs_by_hand():
    tokens = BrailleTokenizer().tokenize(_TWO_HAND_SNIPPET)
    score = BrailleParser(tokens=tokens).parse()
    assert r'\clef treble' in score.staves[0].to_lilypond()
    assert r'\clef bass' in score.staves[1].to_lilypond()


# --- Score.to_lilypond(): PianoStaff wrapping for two staves ---

def test_score_to_lilypond_two_staves_uses_piano_staff():
    tokens = BrailleTokenizer().tokenize(_TWO_HAND_SNIPPET)
    score = BrailleParser(tokens=tokens).parse()
    ly = score.to_lilypond()
    assert r'\new PianoStaff <<' in ly
    assert ly.count(r'\new Staff {') == 2
    assert '>>' in ly


def test_score_to_lilypond_single_staff_unchanged():
    tokens = BrailleTokenizer().tokenize('⠐⠹⠱⠫⠻⠀')
    score = BrailleParser(tokens=tokens).parse()
    ly = score.to_lilypond()
    assert r'\new PianoStaff' not in ly
    assert "\\relative c' {" in ly


def test_score_to_lilypond_empty_score_unchanged():
    ly = Score().to_lilypond()
    assert r'\version "2.26.0"' in ly
    assert r'#(set-global-staff-size 20.0)' in ly
    assert r'\paper {' in ly


# --- S5-5: integration test — two-hand piano piece ---
#
# As of S5-7 (16th-note runs end once they complete the current beat,
# accounting for beat space already consumed before the run's leader),
# children_s_piece.brf parses with zero _validate_measure_beat_count
# warnings — see test_children_s_piece_has_no_remaining_warnings below.


def test_children_s_piece_has_two_correctly_named_staves():
    pipeline = BRLInputPipeline()
    text = pipeline.load(FIXTURES / 'children_s_piece.brf')
    tokens = BrailleTokenizer().tokenize(text)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        score = BrailleParser(tokens=tokens).parse()
    assert len(score.staves) == 2
    assert score.staves[0].name == 'right hand'
    assert score.staves[1].name == 'left hand'


def test_children_s_piece_staves_have_matching_measure_numbers():
    pipeline = BRLInputPipeline()
    text = pipeline.load(FIXTURES / 'children_s_piece.brf')
    tokens = BrailleTokenizer().tokenize(text)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        score = BrailleParser(tokens=tokens).parse()
    right_numbers = [m.number for m in score.staves[0].measures]
    left_numbers = [m.number for m in score.staves[1].measures]
    assert right_numbers == left_numbers
    assert right_numbers == list(range(1, 42))  # 41 measures


def test_children_s_piece_clefs_resolve_by_hand():
    pipeline = BRLInputPipeline()
    text = pipeline.load(FIXTURES / 'children_s_piece.brf')
    tokens = BrailleTokenizer().tokenize(text)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        score = BrailleParser(tokens=tokens).parse()
    assert r'\clef treble' in score.staves[0].to_lilypond()
    assert r'\clef bass' in score.staves[1].to_lilypond()


def test_children_s_piece_renders_piano_staff_lilypond():
    pipeline = BRLInputPipeline()
    text = pipeline.load(FIXTURES / 'children_s_piece.brf')
    tokens = BrailleTokenizer().tokenize(text)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        score = BrailleParser(tokens=tokens).parse()
    ly = score.to_lilypond()
    assert r'\version' in ly
    assert r'\new PianoStaff <<' in ly
    assert ly.count(r'\new Staff {') == 2
    # Each staff's \relative anchor matches its register (S6 follow-up):
    # the upper/treble staff opens on c' (its first bare, non-chord/in-accord
    # note is the B in measure 4, which BANA Sec. 3.2.2 resolves to octave 4 --
    # confirmed against Children_s_Piece.ly, the hand-authored ground truth,
    # by decoding its absolute pitches via real lilypond) and the lower/bass
    # staff opens on plain c -- not a uniform \relative c' for both.
    assert "\\relative c' {" in ly
    assert "\\relative c'' {" not in ly
    assert "\\relative c {" in ly


def test_children_s_piece_measure1_matches_lilypond_ground_truth():
    # Children_s_Piece.ly measure 1: <<{g8.\mf b16 d4-. g4-.}\\{d,4\mf g4 g4}>>
    # No beat-count warning expected: 0.75+0.25+1+1 = 3.0 exactly (S5-6 Bug B).
    from dottednotes.models.in_accord import InAccord

    pipeline = BRLInputPipeline()
    text = pipeline.load(FIXTURES / 'children_s_piece.brf')
    tokens = BrailleTokenizer().tokenize(text)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        score = BrailleParser(tokens=tokens).parse()
    m1 = score.staves[0].measures[0]
    in_accord = m1.notes[0]
    assert isinstance(in_accord, InAccord)
    part0, part1 = in_accord.parts
    assert [(n.note_name, n.duration.value, n.duration.dots) for n in part0] == [
        ('G', 8, 1), ('B', 16, 0), ('D', 4, 0), ('G', 4, 0),
    ]
    assert [(n.note_name, n.duration.value) for n in part1] == [
        ('D', 4), ('G', 4), ('G', 4),
    ]
    assert not any("Measure 1:" in str(w.message) for w in caught)


def test_children_s_piece_measure22_right_hand_matches_lilypond_ground_truth():
    # Children_s_Piece.ly measure 22 upper: four eighth-note chords + a
    # closing quarter chord (<cis g e>8 <d a fis>8 <e b g>8 <fis cis a>8
    # <g d b>4) — 3.0 beats exactly, no dots. See
    # test_children_s_piece_measure22_left_hand_matches_lilypond_ground_truth
    # for the left hand (S5-7's primary regression case).
    from dottednotes.models.chord import Chord

    pipeline = BRLInputPipeline()
    text = pipeline.load(FIXTURES / 'children_s_piece.brf')
    tokens = BrailleTokenizer().tokenize(text)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        score = BrailleParser(tokens=tokens).parse()
    m22 = score.staves[0].measures[21]
    assert all(isinstance(item, Chord) for item in m22.notes)
    assert [n.notes[0].duration.value for n in m22.notes] == [8, 8, 8, 8, 4]
    assert all(n.notes[0].duration.dots == 0 for n in m22.notes)


def test_children_s_piece_has_no_remaining_warnings():
    # As of S5-7 (run ends once it completes the current beat, accounting
    # for beat space already consumed before the run's leader),
    # children_s_piece.brf parses with zero _validate_measure_beat_count
    # warnings. If this regresses, check whether a real bug was
    # introduced — don't silently loosen this assertion.
    pipeline = BRLInputPipeline()
    text = pipeline.load(FIXTURES / 'children_s_piece.brf')
    tokens = BrailleTokenizer().tokenize(text)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        BrailleParser(tokens=tokens).parse()
    assert caught == []


def test_children_s_piece_measure22_left_hand_matches_lilypond_ground_truth():
    # Children_s_Piece.ly measure 22 lower: g8.\< fis16 e8 fis8 e4 — a
    # dotted-8th (0.75 beat) + a single 16th completing that beat exactly,
    # then two genuine eighths (1 beat), then a quarter (1 beat) = 3.0.
    # This is S5-7's primary regression case: the run must stop after just
    # one 16th (not continue sweeping the following two eighths into it).
    pipeline = BRLInputPipeline()
    text = pipeline.load(FIXTURES / 'children_s_piece.brf')
    tokens = BrailleTokenizer().tokenize(text)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        score = BrailleParser(tokens=tokens).parse()
    m22 = score.staves[1].measures[21]
    assert [(n.note_name, n.duration.value, n.duration.dots) for n in m22.notes] == [
        ('G', 8, 1), ('F', 16, 0), ('E', 8, 0), ('F', 8, 0), ('E', 4, 0),
    ]
    assert not any("Measure 22:" in str(w.message) for w in caught)


def test_16th_run_splits_into_two_beat_groups():
    # A run of 8 consecutive 16th-class notes across two beats needs a
    # fresh leader cell for the second beat (S5-7): once the first run
    # completes a beat, a plain base-8 cell right after is a genuine
    # eighth, not an automatic continuation.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse('⠐⠽⠙⠙⠙⠽⠙⠙⠙')  # leader,cont,cont,cont x2
    assert [n.duration.value for n in notes] == [16] * 8


def test_16th_run_without_fresh_leader_does_not_continue_past_a_beat():
    # Same 8-cell shape, but only ONE leader for both groups: the run ends
    # after 4 notes (1 beat); the remaining base-8 cells have no active run
    # to continue and no leader of their own, so they resolve as genuine
    # eighths — not a silent continuation.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        notes = _parse('⠐⠽⠙⠙⠙⠙⠙⠙⠙')  # 1 leader + 7 continuations
    assert [n.duration.value for n in notes] == [16, 16, 16, 16, 8, 8, 8, 8]


# ---------------------------------------------------------------------------
# S5b-1: instrument abbreviation lookup table and §33.2 header parsing
# ---------------------------------------------------------------------------

def test_table_29_english_matches_bana_manual():
    # Spot-check against Music_Braille_Code_2015.pdf Table 29(A), p.28.
    assert TABLE_29_ENGLISH['Flute'] == 'fl'
    assert TABLE_29_ENGLISH['Violin I'] == 'v1'
    assert TABLE_29_ENGLISH['Violin II'] == 'v2'
    assert TABLE_29_ENGLISH['Viola'] == 'vl'
    assert TABLE_29_ENGLISH['Violoncello'] == 'vc'
    assert TABLE_29_ENGLISH['Double bass'] == 'db'
    assert TABLE_29_ENGLISH['Bassoon'] == 'b'


def test_decode_abbreviation_simple():
    # "fl" — no §33.2.2 numbering.
    cells = BRLInputPipeline()._ascii_to_unicode('FL')
    assert _decode_abbreviation(cells) == ('fl', None, None)


def test_decode_abbreviation_with_part_number():
    # "v1" — Violin I, §33.2.2 lower-cell numbering digit.
    cells = BRLInputPipeline()._ascii_to_unicode('V1')
    assert _decode_abbreviation(cells) == ('v', '1', None)


def test_decode_abbreviation_with_sub_number():
    # "v1a" — a further-divided part (e.g. "Violins I-1"), §33.2.2's
    # upper-cell digit after the lower-cell part number.
    cells = BRLInputPipeline()._ascii_to_unicode('V1A')
    assert _decode_abbreviation(cells) == ('v', '1', '1')


def test_parse_instrument_list_synthetic():
    pipeline = BRLInputPipeline()
    raw = (
        ',GLOCKENSPIEL """"""  >GLO\'\n'
        ",VIOLIN ,I    >V1'\n"
        ",VIOLIN ,,II  >V2'\n"
    )
    text = pipeline._ascii_to_unicode(raw)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        entries = parse_instrument_list(text)
    assert [e.name for e in entries] == ['Glockenspiel', 'Violin I', 'Violin II']
    assert [e.abbreviation for e in entries] == ['glo', 'v', 'v']
    assert [e.part_number for e in entries] == [None, '1', '2']
    # Glockenspiel isn't in Table 29 (transcriber-devised abbreviation, §33.2.1)
    # so no mismatch check applies to it; the Violin I/II entries match exactly.
    assert caught == []


def test_parse_instrument_list_warns_on_table_29_mismatch():
    pipeline = BRLInputPipeline()
    raw = ',FLUTE """""  >FLT\'\n'  # wrong abbreviation for a Table 29 instrument
    text = pipeline._ascii_to_unicode(raw)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        entries = parse_instrument_list(text)
    assert entries[0].abbreviation == 'flt'
    assert any("does not match Table 29" in str(w.message) for w in caught)


def test_parse_instrument_list_skips_non_header_lines():
    pipeline = BRLInputPipeline()
    raw = (
        "             ,FENGYANG ,FLOWER ,DRUM\n"
        ',FLUTE """""  >FL\'\n'
        "              ALLEGRO <<<#D4\n"
    )
    text = pipeline._ascii_to_unicode(raw)
    entries = parse_instrument_list(text)
    # The title and tempo lines have no WORD_SIGN...END_WORD_SIGN abbreviation
    # and are skipped rather than misparsed.
    assert [e.name for e in entries] == ['Flute']


def test_parse_instrument_list_skips_title_with_apostrophe():
    # "Children's Piece" -- the apostrophe is END_WORD_SIGN's own dot-3
    # pattern, which previously fooled _parse_line into treating the whole
    # title line as a bogus one-instrument header (S11-bug: caused
    # children_s_piece.brf to route to EnsembleParser and render as nothing
    # but a run of r16 rests). A genuine abbreviation always starts with a
    # real WORD_SIGN, which this title line never has.
    pipeline = BRLInputPipeline()
    raw = (
        "              ,CHILDREN'S ,PIECE\n"
        ',FLUTE """""  >FL\'\n'
    )
    text = pipeline._ascii_to_unicode(raw)
    entries = parse_instrument_list(text)
    assert [e.name for e in entries] == ['Flute']


def test_parse_instrument_list_fengyang_real_header():
    pipeline = BRLInputPipeline()
    text = pipeline.load(FIXTURES / 'fengyang_flower_drum.brf')
    header_lines = text.splitlines()[1:7]  # instrument-list block: title above, tempo below
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        entries = parse_instrument_list('\n'.join(header_lines))
    assert [e.name for e in entries] == [
        'Flute', 'Violin I', 'Violin II', 'Viola', 'Violoncello', 'Double bass',
    ]
    assert [e.abbreviation for e in entries] == ['fl', 'v', 'v', 'vl', 'vc', 'db']
    assert [e.part_number for e in entries] == [None, '1', '2', None, None, None]
    # Every entry's own abbreviation matches Table 29(A) exactly.
    assert caught == []


def test_resolve_abbreviation_table_29():
    assert resolve_abbreviation('Flute') == 'fl'


def test_resolve_abbreviation_override():
    assert resolve_abbreviation('Glockenspiel', overrides={'Glockenspiel': 'glo'}) == 'glo'


def test_resolve_abbreviation_raises_without_override():
    with pytest.raises(ValueError, match="Glockenspiel"):
        resolve_abbreviation('Glockenspiel')


def test_multi_measure_rest_parsing():
    from dottednotes.parser.tokenizer import BrailleTokenizer
    from dottednotes.parser.braille_parser import BrailleParser

    pipeline = BRLInputPipeline()

    # 1. Two-measure rest (⠍⠍)
    text1 = pipeline._ascii_to_unicode('MM')
    tokens1 = BrailleTokenizer().tokenize(text1)
    score1 = BrailleParser(tokens=tokens1).parse()
    assert len(score1.staves[0].measures) == 2
    # Verification of compressed LilyPond output
    ly1 = score1.to_lilypond()
    assert 'R1*2' in ly1

    # 2. Three-measure rest (⠍⠍⠍)
    text2 = pipeline._ascii_to_unicode('MMM')
    tokens2 = BrailleTokenizer().tokenize(text2)
    score2 = BrailleParser(tokens=tokens2).parse()
    assert len(score2.staves[0].measures) == 3
    ly2 = score2.to_lilypond()
    assert 'R1*3' in ly2

    # 3. Four-measure rest (⠼⠙⠍)
    text3 = pipeline._ascii_to_unicode('#DM')
    tokens3 = BrailleTokenizer().tokenize(text3)
    score3 = BrailleParser(tokens=tokens3).parse()
    assert len(score3.staves[0].measures) == 4
    ly3 = score3.to_lilypond()
    assert 'R1*4' in ly3

    # 4. Multi-measure rest in non-default time signature (3/4 time signature)
    # Time sig = #C4 (3/4), followed by space, followed by #DM (4-measure rest)
    text4 = pipeline._ascii_to_unicode('#C4 #DM')
    tokens4 = BrailleTokenizer().tokenize(text4)
    score4 = BrailleParser(tokens=tokens4).parse()
    assert len(score4.staves[0].measures) == 4
    ly4 = score4.to_lilypond()
    # 3/4 full-measure rest in LilyPond is R2.
    assert 'R2.*4' in ly4


def test_ensemble_omission_rest_reconstruction():
    from dottednotes.parser.tokenizer import BrailleTokenizer
    from dottednotes.parser.braille_parser import BrailleParser
    from dottednotes.models.instrument import InstrumentInfo

    # Create two parts: flute and violin
    # Measure 1: both play. Measure 2: only flute plays (violin is omitted).
    # Since ensemble=True (or instruments are supplied), violin should get a reconstructed rest for Measure 2.
    raw = (
        '⠨⠜⠐⠹⠱⠫⠻⠀⠐⠹⠱⠫⠻\n'  # 2 measures for flute/right hand
        '⠸⠜⠸⠳⠪⠺⠹\n'             # Only 1 measure for violin/left hand
    )
    tokens = BrailleTokenizer().tokenize(raw)
    
    # Enable ensemble mode explicitly
    score = BrailleParser(tokens=tokens, ensemble=True).parse()
    
    assert len(score.staves) == 2
    # Both staves should now have exactly 2 measures
    assert len(score.staves[0].measures) == 2
    assert len(score.staves[1].measures) == 2
    
    # Staff 1 Measure 2 should have notes/pitch
    assert len(score.staves[0].measures[1].notes) == 4  # C D E F
    # Staff 2 Measure 2 should have been reconstructed as a full-measure rest
    assert len(score.staves[1].measures[1].notes) == 1
    assert score.staves[1].measures[1].notes[0].is_full_measure

