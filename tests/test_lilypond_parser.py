import pytest
from dottednotes.parser.lilypond_parser import LilypondParser
from dottednotes.models.score import Score
from dottednotes.models.orchestra_score import OrchestraScore
from dottednotes.models.note import Note, Rest
from dottednotes.models.chord import Chord


def test_parse_single_staff():
    ly_content = """
    \\version "2.24.0"
    \\header {
      title = "Test Solo"
      composer = "A. Composer"
    }
    \\score {
      \\relative c' {
        \\tempo "Andante" \\key g \\major \\time 3/4
        c4 d8 e f4 | g2 r4
      }
    }
    """
    parser = LilypondParser()
    score = parser.parse(ly_content)

    assert isinstance(score, Score)
    assert not isinstance(score, OrchestraScore)
    assert score.title == "Test Solo"
    assert score.composer == "A. Composer"

    assert len(score.staves) == 1
    staff = score.staves[0]
    assert staff.name == "Melody"

    # Measures
    assert len(staff.measures) == 2
    
    m1 = staff.measures[0]
    assert len(m1.notes) == 4
    # c4
    assert isinstance(m1.notes[0], Note)
    assert m1.notes[0].note_name == "C"
    assert m1.notes[0].octave == 4
    assert m1.notes[0].duration.value == 4
    
    # d8
    assert m1.notes[1].note_name == "D"
    assert m1.notes[1].duration.value == 8
    
    m2 = staff.measures[1]
    assert len(m2.notes) == 2
    assert isinstance(m2.notes[1], Rest)


def test_parse_piano():
    ly_content = """
    \\version "2.24.0"
    rhMusic = \\relative c' {
      c4 e g2
    }
    lhMusic = \\relative c {
      c2 e4 g
    }
    \\score {
      \\new PianoStaff <<
        \\new Staff \\with { instrumentName = "Piano right hand" } { \\rhMusic }
        \\new Staff \\with { instrumentName = "Piano left hand" } { \\lhMusic }
      >>
    }
    """
    parser = LilypondParser()
    score = parser.parse(ly_content)

    assert isinstance(score, OrchestraScore)
    assert len(score.staves) == 2
    assert score.staves[0].name == "Piano right hand"
    assert score.staves[1].name == "Piano left hand"

    # RH first measure
    assert len(score.staves[0].measures) == 1
    # LH first measure
    assert len(score.staves[1].measures) == 1
