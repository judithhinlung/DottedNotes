"""Tests for beat-boundary-aware note grouping (BANA Par. 8.1/8.1.1(a),
Table 8): "a regular group consists of three or more notes of the same
value that occupy a full beat or a natural division of a beat," and notes
"not contained entirely within the same beat" may not be grouped. A run of
16th notes spanning multiple beats must restart (a fresh full-value cell)
at each beat boundary, not just once at the start of the whole run --
mirroring BrailleParser._resolve_measure_durations' own beat-tracking
convention for the read direction, which treats one beat as one quarter
note (TICKS_PER_QUARTER).
"""
from dottednotes.models.note import Note
from dottednotes.models.duration import Duration
from dottednotes.models.measure import Measure
from dottednotes.models.measure_repeat import MeasureRepeat
from dottednotes.models.in_accord import InAccord
from dottednotes.models.time_signature import TimeSignature


def _note16(name="C", octave=4):
    return Note(dots=frozenset(), category=None, raw_brl="", note_name=name, octave=octave,
                duration=Duration(value=16))


def _time_sig(numerator=4, denominator=4):
    return TimeSignature(dots=frozenset(), category=None, raw_brl="", numerator=numerator, denominator=denominator)


def test_full_cell_count_matches_one_per_beat():
    # Exactly the reported bug: 16 sixteenth notes in 4/4 (4 beats) must
    # have a full-value cell at the start of each beat (positions 1, 5, 9,
    # 13) -- 4 full cells total, not 1 (old bug, whole run treated as one
    # group) and not 16 (no grouping at all).
    notes = [_note16("C") for _ in range(16)]
    m = Measure(number=1, notes=notes, time_signature=(4, 4))
    brl, _ = m.to_braille(is_measure_start=True, time_signature=_time_sig())

    full = _note16("C").to_braille(is_measure_start=True)[-1]
    cont = _note16("C").to_braille(is_measure_start=True, is_16th_run_continuation=True)[-1]
    assert brl.count(full) == 4
    assert brl.count(cont) == 12


def test_eight_sixteenth_notes_in_4_4_two_beat_groups():
    notes = [_note16("C") for _ in range(8)]
    m = Measure(number=1, notes=notes, time_signature=(4, 4))
    brl, _ = m.to_braille(is_measure_start=True, time_signature=_time_sig())
    full = _note16("C").to_braille(is_measure_start=True)[-1]
    assert brl.count(full) == 2


def test_run_not_starting_on_a_beat_boundary_still_splits_correctly():
    # A quarter note (1 beat) followed by 8 sixteenth notes (2 beats) in
    # 4/4: the run starts exactly at beat 2, so it should still split into
    # 2 clean groups of 4, not be misaligned by the preceding quarter note.
    quarter = Note(dots=frozenset(), category=None, raw_brl="", note_name="C", octave=4, duration=Duration(value=4))
    run = [_note16("D") for _ in range(8)]
    m = Measure(number=1, notes=[quarter] + run, time_signature=(4, 4))
    brl, _ = m.to_braille(is_measure_start=True, time_signature=_time_sig())
    full = _note16("D").to_braille(is_measure_start=True)[-1]
    assert brl.count(full) == 2


def test_run_shorter_than_three_notes_never_grouped():
    # A run of only 2 sixteenth notes is never grouped at all (Par. 8.1
    # requires "three or more"), regardless of beat position -- both
    # notes render at full value.
    notes = [_note16("C"), _note16("D")]
    m = Measure(number=1, notes=notes, time_signature=(4, 4))
    brl, _ = m.to_braille(is_measure_start=True, time_signature=_time_sig())
    full_c = _note16("C").to_braille(is_measure_start=True)[-1]
    full_d = _note16("D").to_braille(is_measure_start=True)[-1]
    assert full_c in brl
    assert full_d in brl


def test_measure_repeat_item_does_not_crash_beat_tracking():
    # Regression guard: MeasureRepeat has no .duration at all -- must not
    # crash the beat-tick accounting used for 16th-note-run splitting.
    m = Measure(number=2, notes=[MeasureRepeat(count=1, line=1)], time_signature=(4, 4))
    brl, _ = m.to_braille(is_measure_start=True, time_signature=_time_sig())
    assert brl  # renders without raising


def test_in_accord_item_does_not_crash_beat_tracking():
    # Regression guard: InAccord has no .duration of its own either.
    parts = [[_note16("C")], [_note16("E")]]
    ia = InAccord(parts=parts, in_accord_type='full_measure')
    m = Measure(number=1, notes=[ia], time_signature=(4, 4))
    brl, _ = m.to_braille(is_measure_start=True, time_signature=_time_sig())
    assert brl
