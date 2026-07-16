import pytest
from dottednotes.parser.lilypond_parser import LilypondParser, tokenize_lilypond, _skip_balanced_block
from dottednotes.models.score import Score
from dottednotes.models.orchestra_score import OrchestraScore
from dottednotes.models.staff import Staff
from dottednotes.models.measure import Measure
from dottednotes.models.note import Note, Rest
from dottednotes.models.chord import Chord
from dottednotes.models.duration import Duration


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


def test_tokenize_punctuation_articulations_and_dynamics():
    assert tokenize_lilypond("c4-.") == ['c', '4', '-.']
    assert tokenize_lilypond("c4-!") == ['c', '4', '-!']
    assert tokenize_lilypond("c4-_") == ['c', '4', '-_']
    assert tokenize_lilypond("c4--") == ['c', '4', '--']
    assert tokenize_lilypond("c4->") == ['c', '4', '->']
    assert tokenize_lilypond("c4-^") == ['c', '4', '-^']
    assert tokenize_lilypond("e4\\<") == ['e', '4', '\\<']
    assert tokenize_lilypond("e4\\>") == ['e', '4', '\\>']
    assert tokenize_lilypond("e4\\!") == ['e', '4', '\\!']


def test_parse_multi_measure_rest():
    ly_content = """
    \\version "2.24.0"
    \\score {
      \\relative c' {
        R1*8 c4
      }
    }
    """
    parser = LilypondParser()
    score = parser.parse(ly_content)
    rest = score.staves[0].measures[0].notes[0]
    assert isinstance(rest, Rest)
    assert rest.is_full_measure is True
    assert rest.duration.value == 1
    assert rest.multi_measure_count == 8


def test_parse_full_measure_rest_without_multiplier_defaults_to_one():
    ly_content = """
    \\version "2.24.0"
    \\score {
      \\relative c' {
        R1 c4
      }
    }
    """
    parser = LilypondParser()
    score = parser.parse(ly_content)
    rest = score.staves[0].measures[0].notes[0]
    assert isinstance(rest, Rest)
    assert rest.multi_measure_count == 1


def test_skip_balanced_block_handles_nested_braces():
    tokens = tokenize_lilypond('{ a b { c } d }')
    start = tokens.index('{')
    end_idx = _skip_balanced_block(tokens, start)
    assert end_idx == len(tokens)
    assert tokens[end_idx - 1] == '}'


def test_skip_balanced_block_returns_unchanged_for_non_brace():
    tokens = tokenize_lilypond('foo bar')
    assert _skip_balanced_block(tokens, 0) == 0


def test_parse_generated_solo_score_survives_paper_block():
    # Regression test for the \paper{} block (always emitted by
    # Score.to_lilypond() before \score) being misparsed as a top-level
    # variable definition and silently swallowing the \score block.
    staff = Staff(name="Melody")
    m = Measure(number=1, notes=[
        Note(dots=frozenset(), category=None, raw_brl="", note_name="C", octave=4, duration=Duration(value=4, dots=0)),
        Note(dots=frozenset(), category=None, raw_brl="", note_name="D", octave=4, duration=Duration(value=4, dots=0)),
    ])
    staff.measures.append(m)
    score = Score(staves=[staff])
    ly_content = score.to_lilypond()
    assert '\\paper' in ly_content  # sanity check the fixture actually exercises the bug

    parsed = LilypondParser().parse(ly_content)
    assert len(parsed.staves) == 1
    assert len(parsed.staves[0].measures) == 1
    notes = parsed.staves[0].measures[0].notes
    assert [(n.note_name, n.octave) for n in notes] == [("C", 4), ("D", 4)]


def test_parse_generated_orchestra_score_survives_paper_block():
    def make_staff(name, note_name):
        s = Staff(name=name)
        s.measures.append(Measure(number=1, notes=[
            Note(dots=frozenset(), category=None, raw_brl="", note_name=note_name, octave=4, duration=Duration(value=4, dots=0)),
        ]))
        return s

    score = OrchestraScore(staves=[make_staff("Piano right hand", "C"), make_staff("Piano left hand", "G")])
    ly_content = score.to_lilypond()

    parsed = LilypondParser().parse(ly_content)
    assert len(parsed.staves) == 2
    assert parsed.staves[0].name == "Piano right hand"
    assert parsed.staves[1].name == "Piano left hand"


def test_chord_written_note_sorted_highest_first_for_treble():
    ly_content = """
    \\version "2.24.0"
    \\score {
      \\relative c' {
        <c e g>4
      }
    }
    """
    score = LilypondParser().parse(ly_content)
    chord = score.staves[0].measures[0].notes[0]
    assert isinstance(chord, Chord)
    assert chord.notes[0].note_name == "G"
    assert chord.notes[-1].note_name == "C"


def test_chord_written_note_sorted_lowest_first_for_bass_clef():
    ly_content = """
    \\version "2.24.0"
    \\score {
      \\relative c' {
        \\clef bass
        <c e g>4
      }
    }
    """
    score = LilypondParser().parse(ly_content)
    chord = score.staves[0].measures[0].notes[0]
    assert isinstance(chord, Chord)
    assert chord.notes[0].note_name == "C"
    assert chord.notes[-1].note_name == "G"


def test_chord_sort_does_not_break_relative_pitch_chain():
    # The note following the chord must resolve relative to the note as
    # literally written first in the LilyPond source (C), not the
    # BANA-sorted written note (G) -- otherwise \relative octave tracking
    # would silently regress.
    ly_content = """
    \\version "2.24.0"
    \\score {
      \\relative c' {
        <c e g>4 a4
      }
    }
    """
    score = LilypondParser().parse(ly_content)
    notes = score.staves[0].measures[0].notes
    following_note = notes[1]
    assert (following_note.note_name, following_note.octave) == ("A", 3)
