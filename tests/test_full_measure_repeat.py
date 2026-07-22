"""Tests for the "full_measure_repeat" (off/single-voice/multi-voice) and
"min_repeated_measures" settings controlling BANA Par. 18.2 whole-measure
repeat-sign compression, decoupled from --compression's unrelated
articulation-carry shorthand.
"""
from dottednotes.models.note import Note, Rest
from dottednotes.models.in_accord import InAccord
from dottednotes.models.measure import Measure
from dottednotes.models.duration import Duration
from dottednotes.models.staff import Staff
from dottednotes.models.score import Score
from dottednotes.renderers.braille_renderer import BrailleRenderer

REPEAT_SIGN = "⠶"


def _note(name="C", octave=4, value=4):
    return Note(dots=frozenset(), category=None, raw_brl="", note_name=name, octave=octave, duration=Duration(value))


def _plain_measures(n: int, note_name="C") -> list[Measure]:
    return [Measure(number=i + 1, notes=[_note(note_name)]) for i in range(n)]


def _in_accord_measures(n: int, note_name="C") -> list[Measure]:
    return [
        Measure(number=i + 1, notes=[InAccord(parts=[[_note(note_name)], [_note(note_name, octave=3)]])])
        for i in range(n)
    ]


def _solo_score(measures: list[Measure]) -> Score:
    staff = Staff(name="Violin", clef=None, key_signature=None, time_signature=None)
    staff.measures = measures
    return Score(title="", staves=[staff])


def test_off_disables_repeat_compression_entirely():
    score = _solo_score(_plain_measures(3))
    output = BrailleRenderer(full_measure_repeat="off").render(score)
    assert REPEAT_SIGN not in output


def test_default_single_voice_compresses_plain_measures():
    # Regression parity with the pre-existing (unconfigured) behavior:
    # 3 identical plain measures -> measures 2 and 3 become repeat signs.
    score = _solo_score(_plain_measures(3))
    output = BrailleRenderer().render(score)
    assert output.count(REPEAT_SIGN) == 2


def test_single_voice_does_not_compress_in_accord_measures():
    score = _solo_score(_in_accord_measures(3))
    output = BrailleRenderer(full_measure_repeat="single-voice").render(score)
    assert REPEAT_SIGN not in output


def test_multi_voice_compresses_in_accord_measures():
    score = _solo_score(_in_accord_measures(3))
    output = BrailleRenderer(full_measure_repeat="multi-voice").render(score)
    assert output.count(REPEAT_SIGN) == 2


def test_min_repeated_measures_boundary_two_not_compressed_three_is():
    # Exactly 2 identical measures: not compressed under min=3.
    score2 = _solo_score(_plain_measures(2))
    output2 = BrailleRenderer(min_repeated_measures=3).render(score2)
    assert REPEAT_SIGN not in output2

    # Exactly 3 identical measures: the last two compress under min=3.
    score3 = _solo_score(_plain_measures(3))
    output3 = BrailleRenderer(min_repeated_measures=3).render(score3)
    assert output3.count(REPEAT_SIGN) == 2


def test_whole_measure_rest_never_compressed():
    measures = [
        Measure(number=i + 1, notes=[Rest(dots=frozenset(), category=None, raw_brl="", duration=Duration(4), is_full_measure=True)])
        for i in range(3)
    ]
    score = _solo_score(measures)
    for mode in ("single-voice", "multi-voice"):
        for min_n in (2, 3):
            output = BrailleRenderer(full_measure_repeat=mode, min_repeated_measures=min_n).render(score)
            assert REPEAT_SIGN not in output


def test_back_to_back_distinct_runs_compress_independently():
    # [C, C, C, D, D, D] -- two independent runs, neither bleeds into the other.
    measures = _plain_measures(3, "C") + [
        Measure(number=i + 4, notes=[_note("D")]) for i in range(3)
    ]
    score = _solo_score(measures)
    output = BrailleRenderer(min_repeated_measures=3).render(score)
    assert output.count(REPEAT_SIGN) == 4  # 2 from each run


def test_ensemble_restores_compressed_measure_starting_a_new_system():
    # BANA 33.4.3: a repeat sign is only valid when the original passage it
    # refers to is on the SAME braille line/system. 6 musically-identical
    # measures across 3 staves, narrow enough that measure 4 starts a new
    # system -- _compress_measure_repeats ran before line-breaking was
    # known and would have made measure 4 a repeat sign too, but
    # _render_ensemble must restore it to real content since its "original"
    # (measure 1) is now on a different line. Measures 5-6 may still
    # validly stay repeat signs, since their "original" is the (restored)
    # measure 4 on their own line.
    staves = []
    for name in ("Violin I", "Violin II", "Viola"):
        s = Staff(name=name, clef=None, key_signature=None, time_signature=None)
        s.measures = [Measure(number=i + 1, notes=[_note()]) for i in range(6)]
        staves.append(s)
    score = Score(title="", staves=staves)

    output = BrailleRenderer(line_width=16).render(score)
    lines = output.split("\n")
    # The system-2 heading line ("⠼⠙" = measure 4's numeral-sign heading)
    # precedes the system whose first measure must show real content.
    heading_idx = next(i for i, line in enumerate(lines) if "⠼⠙" in line)
    system2_staff_line = lines[heading_idx + 1]
    assert "⠐⠹" in system2_staff_line  # real octave mark + note, not a repeat sign
    # Per staff: 2 repeat signs in system 1 (measures 2, 3) + 2 in system 2
    # (measures 5, 6, now chained from the restored measure 4) = 4 per
    # staff, across 3 staves = 12 total, not 15 (which measure 4 staying
    # compressed on all 3 staves would produce).
    assert output.count(REPEAT_SIGN) == 12


def test_invalid_full_measure_repeat_mode_rejected():
    import pytest
    with pytest.raises(ValueError):
        BrailleRenderer(full_measure_repeat="bogus")


def test_invalid_min_repeated_measures_rejected():
    import pytest
    with pytest.raises(ValueError):
        BrailleRenderer(min_repeated_measures=1)
