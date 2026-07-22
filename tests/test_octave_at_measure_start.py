"""Tests for the "octave_mark_every_measure" setting -- an additive reader
preference (Sao Mai Braille-inspired) that forces the octave mark on every
measure's first note, not just measures that start a new braille line. Must
never suppress the already-required BANA 3.2.1 trigger points (line start,
after a word sign/numeric indicator).
"""
from dottednotes.models.note import Note
from dottednotes.models.duration import Duration
from dottednotes.models.measure import Measure
from dottednotes.models.staff import Staff
from dottednotes.models.score import Score
from dottednotes.models.text_marking import TextMarking, TextMarkingType
from dottednotes.renderers.braille_renderer import BrailleRenderer


def _note(name="C", octave=4, value=4):
    return Note(dots=frozenset(), category=None, raw_brl="", note_name=name, octave=octave, duration=Duration(value))


def _solo_score(measures_notes: list[list]) -> Score:
    staff = Staff(name="Violin", clef=None, key_signature=None, time_signature=None)
    staff.measures = [Measure(number=i + 1, notes=notes) for i, notes in enumerate(measures_notes)]
    return Score(title="", staves=[staff])


def test_default_off_no_forced_mark_mid_line():
    # Two measures fitting on one line; 2nd measure's note (D) is a step
    # from the 1st measure's last note (C) -- BANA 3.2.2(a) doesn't require
    # a mark here, and the setting is off by default, so none is forced.
    score = _solo_score([[_note("C")], [_note("D")]])
    output = BrailleRenderer(line_width=40, octave_mark_every_measure=False).render(score)
    # ⠐ = octave 4 mark. Should appear exactly once (measure 1's forced
    # line-start mark), not before the D in measure 2.
    assert output.count("⠐") == 1


def test_flag_on_forces_mark_on_every_measure():
    score = _solo_score([[_note("C")], [_note("D")]])
    output = BrailleRenderer(line_width=40, octave_mark_every_measure=True).render(score)
    assert output.count("⠐") == 2


def test_line_start_measure_unaffected_by_flag():
    # A measure that starts a NEW physical line always gets the mark
    # regardless of the setting -- confirm identical output on/off when
    # a narrow width forces each measure onto its own line.
    score = _solo_score([[_note("C")], [_note("D")]])
    off = BrailleRenderer(line_width=6, octave_mark_every_measure=False).render(score)
    on = BrailleRenderer(line_width=6, octave_mark_every_measure=True).render(score)
    assert off == on
    assert off.count("⠐") == 2


def test_word_sign_forced_mark_unaffected_by_flag():
    # A note immediately following a mid-piece word-sign expression already
    # gets a forced octave mark (BANA 3.2.1) regardless of this setting --
    # confirm the flag doesn't double up or otherwise change that output.
    m1 = Measure(number=1, notes=[_note("C"), _note("D")])
    m2 = Measure(number=2)
    m2.text_markings = [TextMarking(text="rit.", type=TextMarkingType.EXPRESSION)]
    m2.add_note(_note("E"))
    staff = Staff(name="Violin", clef=None, key_signature=None, time_signature=None)
    staff.measures = [m1, m2]
    score = Score(title="", staves=[staff])

    off = BrailleRenderer(line_width=40, octave_mark_every_measure=False).render(score)
    on = BrailleRenderer(line_width=40, octave_mark_every_measure=True).render(score)
    assert off == on


def test_piano_mode_forces_mark_on_every_measure_both_hands():
    rh = Staff(name="piano right hand", clef=None, key_signature=None, time_signature=None)
    rh.measures = [Measure(number=1, notes=[_note("C")]), Measure(number=2, notes=[_note("D")])]
    lh = Staff(name="piano left hand", clef=None, key_signature=None, time_signature=None)
    lh.measures = [Measure(number=1, notes=[_note("C", octave=2)]), Measure(number=2, notes=[_note("D", octave=2)])]
    score = Score(title="", staves=[rh, lh])

    off = BrailleRenderer(line_width=40, octave_mark_every_measure=False).render(score)
    on = BrailleRenderer(line_width=40, octave_mark_every_measure=True).render(score)
    assert off.count("⠐") == 1  # RH measure 1 only (LH octave 2 uses ⠘, not ⠐)
    assert on.count("⠐") == 2   # RH measures 1 and 2


def test_ensemble_mode_forces_mark_on_every_measure():
    staves = []
    for name in ("Violin I", "Violin II", "Viola"):
        s = Staff(name=name, clef=None, key_signature=None, time_signature=None)
        s.measures = [Measure(number=1, notes=[_note("C")]), Measure(number=2, notes=[_note("D")])]
        staves.append(s)
    score = Score(title="", staves=staves)

    off = BrailleRenderer(line_width=40, octave_mark_every_measure=False).render(score)
    on = BrailleRenderer(line_width=40, octave_mark_every_measure=True).render(score)
    # Count the mark immediately followed by the C-quarter note cell (⠹),
    # not a bare octave-mark count -- the ensemble instrument-list header
    # reuses the same dot-5 cell as a guide-dot column filler (BANA
    # 33.2(d)), which would otherwise contaminate a plain "⠐" count.
    # Each of the 3 staves gets exactly one forced mark (measure 1, C)
    # when off, and two (measures 1 and 2 -- but only measure 1 is C) when on;
    # measure 2 (D) forced marks are counted separately via "⠐⠱".
    assert off.count("⠐⠹") == 3
    assert off.count("⠐⠱") == 0
    assert on.count("⠐⠹") == 3
    assert on.count("⠐⠱") == 3
