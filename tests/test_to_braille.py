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


def test_measure_with_measure_repeat_to_braille_does_not_raise():
    mr = MeasureRepeat(count=2, line=0)
    m = Measure(number=1, notes=[mr])
    brl, _ = m.to_braille(is_measure_start=True)
    assert brl.count('⠶') == 2
