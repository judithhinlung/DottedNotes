import pytest
from dottednotes.models.score import Score
from dottednotes.models.orchestra_score import OrchestraScore
from dottednotes.models.staff import Staff
from dottednotes.models.measure import Measure
from dottednotes.models.note import Note, Rest
from dottednotes.models.duration import Duration
from dottednotes.renderers.braille_renderer import BrailleRenderer


def test_solo_renderer():
    score = Score(title="Solo Piece")
    staff = Staff(name="Flute")
    m = Measure(number=1)
    # Add a C4 quarter note
    m.add_note(Note(dots=frozenset(), category=None, raw_brl="", note_name="C", octave=4, duration=Duration(value=4, dots=0)))
    staff.add_measure(m)
    score.add_staff(staff)

    renderer = BrailleRenderer(line_width=40)
    output = renderer.render(score)
    # Check that it contains title and measure 1
    # Title "Solo Piece" -> '⠠⠎⠕⠇⠕⠀⠠⠏⠊⠑⠉⠑⠲'
    assert '⠠⠎⠕⠇⠕⠀⠠⠏⠊⠑⠉⠑⠲' in output
    assert '⠁ ⠐⠹' in output


def test_piano_renderer():
    score = Score(title="Piano Piece")
    # Piano staves
    rh = Staff(name="Piano right hand")
    lh = Staff(name="Piano left hand")
    
    m1 = Measure(number=1)
    m1.add_note(Note(dots=frozenset(), category=None, raw_brl="", note_name="C", octave=4, duration=Duration(value=4, dots=0)))
    rh.add_measure(m1)
    
    m2 = Measure(number=1)
    m2.add_note(Note(dots=frozenset(), category=None, raw_brl="", note_name="C", octave=3, duration=Duration(value=4, dots=0)))
    lh.add_measure(m2)
    
    score.add_staff(rh)
    score.add_staff(lh)

    renderer = BrailleRenderer(line_width=40)
    output = renderer.render(score)
    # RH line: starts with '⠁ ' (measure 1 prefix) followed by RH hand sign '⠨⠜' and note
    assert '⠁ ⠨⠜⠐⠹' in output
    # LH line: starts with spaces, followed by LH hand sign '⠸⠜' and note
    # Prefix '⠁ ' is 2 chars, so LH line starts with 2 spaces
    assert '  ⠸⠜⠸⠹' in output
