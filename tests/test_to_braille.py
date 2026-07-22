import pytest
from dottednotes.models.accidental import Accidental, AccidentalType
from dottednotes.models.articulation import Articulation, ArticulationType
from dottednotes.models.dynamic import Dynamic, DynamicLevel
from dottednotes.models.ornament import Ornament, OrnamentType, GraceNote
from dottednotes.models.fingering import Fingering
from dottednotes.models.clef import Clef, ClefType
from dottednotes.models.key_signature import KeySignature
from dottednotes.models.time_signature import TimeSignature
from dottednotes.models.text_marking import TextMarking, TextMarkingType
from dottednotes.models.note import Note, Rest
from dottednotes.models.chord import Chord
from dottednotes.models.tuplet import Tuplet
from dottednotes.models.in_accord import InAccord
from dottednotes.models.measure_repeat import MeasureRepeat
from dottednotes.models.duration import Duration
from dottednotes.models.measure import Measure


def test_accidental_to_braille():
    assert Accidental(dots=frozenset(), category=None, raw_brl="", type=AccidentalType.SHARP).to_braille() == '⠩'
    assert Accidental(dots=frozenset(), category=None, raw_brl="", type=AccidentalType.FLAT).to_braille() == '⠣'
    assert Accidental(dots=frozenset(), category=None, raw_brl="", type=AccidentalType.NATURAL).to_braille() == '⠡'


def test_articulation_to_braille():
    assert Articulation(type=ArticulationType.STACCATO).to_braille() == '⠦'
    assert Articulation(type=ArticulationType.STACCATISSIMO).to_braille() == '⠠⠦'
    assert Articulation(type=ArticulationType.TENUTO).to_braille() == '⠸⠦'


def test_dynamic_to_braille():
    assert Dynamic(level=DynamicLevel.P).to_braille() == '⠜⠏'
    assert Dynamic(level=DynamicLevel.MF).to_braille() == '⠜⠍⠋'
    assert Dynamic(level=DynamicLevel.CRESCENDO_START).to_braille() == '⠜⠉'


def test_fingering_to_braille():
    assert Fingering(dots=frozenset(), category=None, raw_brl="", finger=1).to_braille() == '⠁'
    assert Fingering(dots=frozenset(), category=None, raw_brl="", finger=2, change_to=3).to_braille() == '⠃⠉⠇'
    assert Fingering(dots=frozenset(), category=None, raw_brl="", finger=1, alternative=2).to_braille() == '⠁⠃'


def test_clef_to_braille():
    assert Clef(dots=frozenset(), category=None, raw_brl="", clef_type=ClefType.TREBLE).to_braille() == '⠜⠌⠇'
    assert Clef(dots=frozenset(), category=None, raw_brl="", clef_type=ClefType.BASS).to_braille() == '⠜⠼⠇'


def test_key_signature_to_braille():
    assert KeySignature(dots=frozenset(), category=None, raw_brl="", sharps_or_flats=1).to_braille() == '⠩'
    assert KeySignature(dots=frozenset(), category=None, raw_brl="", sharps_or_flats=-2).to_braille() == '⠣⠣'


def test_time_signature_to_braille():
    assert TimeSignature(dots=frozenset(), category=None, raw_brl="", numerator=4, denominator=4).to_braille() == '⠼⠙⠲'
    assert TimeSignature(dots=frozenset(), category=None, raw_brl="", numerator=6, denominator=8).to_braille() == '⠼⠋⠦'


def test_text_marking_to_braille():
    assert TextMarking(text="Allegro", type=TextMarkingType.TEMPO).to_braille() == '⠠⠁⠇⠇⠑⠛⠗⠕⠲'


def test_note_and_rest_to_braille():
    n = Note(dots=frozenset(), category=None, raw_brl="", note_name="C", octave=4, duration=Duration(value=4, dots=0))
    # Standard C4 quarter note with octave mark at start of measure
    assert n.to_braille(is_measure_start=True) == '⠐⠹'
    
    r = Rest(dots=frozenset(), category=None, raw_brl="", duration=Duration(value=4, dots=0))
    assert r.to_braille() == '⠧'


def test_full_measure_rest_always_uses_whole_rest_sign_regardless_of_time_signature():
    # BANA Music Braille Code 2015, Par. 5.1: "A measure of silence is
    # indicated in the print by a whole rest, whatever the time signature
    # may be, except that in 4/2 time the double whole rest may sometimes
    # be found." A full-measure rest in 2/4 time has duration.value == 2
    # (the "half rest" value musically), but must still braille as the
    # whole-rest sign (⠍, dots 1,3,4), not the half-rest sign (⠥).
    for value in (1, 2, 4, 8, 16, 32, 64):
        r = Rest(dots=frozenset(), category=None, raw_brl="", duration=Duration(value=value, dots=0), is_full_measure=True)
        assert r.to_braille() == '⠍', f"duration.value={value} should still be the whole-rest sign"

    # A non-full-measure rest of the same values is unaffected -- only
    # is_full_measure changes the rule.
    assert Rest(dots=frozenset(), category=None, raw_brl="", duration=Duration(value=2, dots=0)).to_braille() == '⠥'


def test_full_measure_rest_drops_augmentation_dots():
    # A full-measure rest's own `duration` (value/dots) only exists to
    # satisfy the beat count a full measure of that time signature adds
    # up to -- e.g. a 3/4 measure of rest computes internally to
    # value=2, dots=1 (a "dotted half", matching LilyPond's R2.), found
    # via a real 3/4 passage in the Bartok fixture. Since Par. 5.1 fixes
    # the braille sign regardless of that value, the augmentation dot(s)
    # must not be added either -- otherwise the rest would still
    # (wrongly) look like a specific dotted note value.
    r = Rest(dots=frozenset(), category=None, raw_brl="", duration=Duration(value=2, dots=1), is_full_measure=True)
    assert r.to_braille() == '⠍'

    # A non-full-measure dotted rest is unaffected -- only is_full_measure
    # suppresses the dot.
    assert Rest(dots=frozenset(), category=None, raw_brl="", duration=Duration(value=2, dots=1)).to_braille() == '⠥⠄'


def test_full_measure_breve_rest_keeps_double_whole_rest_sign():
    # BANA Par. 5.1's narrow exception: "in 4/2 time the double whole
    # rest may sometimes be found" -- a genuine breve (duration.value=0)
    # full-measure rest keeps its own double-whole-rest sign (⠍⠅) rather
    # than being forced to the plain whole-rest sign.
    r = Rest(dots=frozenset(), category=None, raw_brl="", duration=Duration(value=0, dots=0), is_full_measure=True)
    assert r.to_braille() == '⠍⠅'


def test_chord_to_braille():
    n1 = Note(dots=frozenset(), category=None, raw_brl="", note_name="C", octave=4, duration=Duration(value=4, dots=0))
    n2 = Note(dots=frozenset(), category=None, raw_brl="", note_name="E", octave=4, duration=Duration(value=4, dots=0))
    n3 = Note(dots=frozenset(), category=None, raw_brl="", note_name="G", octave=4, duration=Duration(value=4, dots=0))
    # Chord C E G (in treble clef descending: G is highest/written note)
    c = Chord(notes=[n3, n2, n1])
    # Interval cells per the authoritative INTERVAL_CELLS table (bana_symbols.py):
    # E is a 3rd below G ('⠬'), C is a 5th below G ('⠔').
    assert c.to_braille(is_measure_start=True) == '⠐⠳⠬⠔'


def test_chord_interval_cells_match_bana_symbols():
    from dottednotes.bana_symbols import INTERVAL_CELLS
    _NAMES = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
    written = Note(dots=frozenset(), category=None, raw_brl="", note_name="C", octave=5, duration=Duration(value=4, dots=0))
    written_diatonic = written.octave * 7 + _NAMES.index(written.note_name)
    expected = {v: k for k, v in INTERVAL_CELLS.items()}
    for steps in range(1, 8):
        # An interval note `steps` diatonic scale-steps below the written note
        # (steps=1 -> a 2nd, ..., steps=7 -> an octave).
        target_diatonic = written_diatonic - steps
        octave, idx = divmod(target_diatonic, 7)
        interval_note = Note(dots=frozenset(), category=None, raw_brl="", note_name=_NAMES[idx], octave=octave, duration=Duration(value=4, dots=0))
        c = Chord(notes=[written, interval_note])
        brl = c.to_braille(is_measure_start=True)
        assert expected[steps + 1] in brl, f"interval {steps + 1} should render {expected[steps + 1]!r}, got {brl!r}"


def test_measure_repeat_to_braille():
    assert MeasureRepeat(count=1, line=0).to_braille() == '⠶'
    assert MeasureRepeat(count=3, line=0).to_braille() == '⠶⠶⠶'


def test_measure_with_rest_to_braille_does_not_raise():
    r = Rest(dots=frozenset(), category=None, raw_brl="", duration=Duration(value=4, dots=0))
    m = Measure(number=1, notes=[r])
    brl, _ = m.to_braille(is_measure_start=True)
    assert r.to_braille() in brl


def test_measure_with_chord_to_braille_does_not_raise():
    n1 = Note(dots=frozenset(), category=None, raw_brl="", note_name="C", octave=4, duration=Duration(value=4, dots=0))
    n2 = Note(dots=frozenset(), category=None, raw_brl="", note_name="E", octave=4, duration=Duration(value=4, dots=0))
    n3 = Note(dots=frozenset(), category=None, raw_brl="", note_name="G", octave=4, duration=Duration(value=4, dots=0))
    c = Chord(notes=[n3, n2, n1])
    m = Measure(number=1, notes=[c])
    brl, _ = m.to_braille(is_measure_start=True)
    assert brl


def test_tuplet_with_rest_to_braille_does_not_raise():
    # Regression test: a triplet containing a rest (e.g. an eighth-note
    # triplet with a rest for one of its three slots, common in orchestral
    # scores) crashed Tuplet.to_braille() because it passed prev_note/
    # is_measure_start/time_signature to every item uniformly, but
    # Rest.to_braille() takes no arguments at all -- Measure's own
    # item-rendering loop already special-cases Rest for this reason,
    # Tuplet's did not.
    n1 = Note(dots=frozenset(), category=None, raw_brl="", note_name="C", octave=4, duration=Duration(value=8, dots=0))
    r = Rest(dots=frozenset(), category=None, raw_brl="", duration=Duration(value=8, dots=0))
    n2 = Note(dots=frozenset(), category=None, raw_brl="", note_name="E", octave=4, duration=Duration(value=8, dots=0))
    t = Tuplet(items=[n1, r, n2])
    m = Measure(number=1, notes=[t])
    brl, _ = m.to_braille(is_measure_start=True)
    assert brl


def test_tuplet_ending_in_rest_does_not_crash_next_notes_octave_logic():
    # Regression test (found via a real OMR-sourced MusicXML solo flute
    # piece, gerhard_roberto_capriccio2_for_flute.xml, measure 7): when a
    # Tuplet's LAST item is a Rest, _render_note_list_to_braille's
    # curr_prev tracking (models/measure.py) used to fall back to
    # assigning the Rest object itself as "the previous note" -- fine
    # until the NEXT note's octave-interval comparison unconditionally
    # accessed prev_note.octave/note_name, crashing with AttributeError:
    # 'Rest' object has no attribute 'octave'. The correct previous note
    # is the tuplet's last REAL note (skipping the trailing rest), not
    # the rest itself.
    n1 = Note(dots=frozenset(), category=None, raw_brl="", note_name="C", octave=4, duration=Duration(value=8, dots=0))
    r = Rest(dots=frozenset(), category=None, raw_brl="", duration=Duration(value=8, dots=0))
    t = Tuplet(items=[n1, r])
    n2 = Note(dots=frozenset(), category=None, raw_brl="", note_name="D", octave=4, duration=Duration(value=4, dots=0))
    m = Measure(number=1, notes=[t, n2])
    brl, last_note = m.to_braille(is_measure_start=True)
    assert brl
    assert last_note is n2


def test_measure_with_measure_repeat_to_braille_does_not_raise():
    mr = MeasureRepeat(count=2, line=0)
    m = Measure(number=1, notes=[mr])
    brl, _ = m.to_braille(is_measure_start=True)
    assert brl.count('⠶') == 2
