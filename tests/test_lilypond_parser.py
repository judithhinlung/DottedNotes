from pathlib import Path

import pytest
from dottednotes.parser.lilypond_parser import LilypondParser, tokenize_lilypond, _skip_balanced_block

FIXTURES = Path(__file__).parent / "fixtures"
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


# --- Regression: LilypondParser input support and in-accord (<<{...}\\{...}>>)
#     two-voice parsing. Both bugs were found via `dottednotes convert` on a
#     real .ly file producing garbled/crashing output -- see test_e2e_cli.py
#     for the CLI-level reproduction. ---


def test_tokenizer_recognizes_voice_separator():
    # The bare '\\' voice separator (distinct from '\\<'/'\\>'/'\\!'
    # hairpin/dynamic tokens) was previously dropped entirely by the token
    # regex, silently merging both voices of every in-accord group into one
    # flat token stream.
    tokens = tokenize_lilypond("<< { c4 } \\\\ { e,4 } >>")
    assert tokens == ['<<', '{', 'c', '4', '}', '\\\\', '{', 'e,', '4', '}', '>>']


def test_dynamic_marking_does_not_crash():
    # Dynamic(dots=..., category=..., raw_brl=..., level=...) used to raise
    # TypeError: Dynamic.__init__() got an unexpected keyword argument
    # 'dots' -- Dynamic (unlike Note) only has a `level` field. This crashed
    # on any real piece using so much as a single \mf/\p/\f marking.
    ly_content = """
    \\version "2.24.0"
    \\score {
      \\relative c' {
        c4\\mf d4\\p
      }
    }
    """
    score = LilypondParser().parse(ly_content)
    notes = score.staves[0].measures[0].notes
    assert notes[0].dynamics[0].level.name == "MF"
    assert notes[1].dynamics[0].level.name == "P"


def test_in_accord_parses_two_independent_voices():
    # Real DottedNotes-generated two-hand-on-one-staff BANA in-accord
    # notation (InAccord.to_relative_lilypond()): voice 1 g'8. b16 d4 g4,
    # voice 2 d4 g4 g4 -- both voices must come back as two separate lists
    # of real notes, not silently merged into one 7-note sequence.
    ly_content = """
    \\version "2.24.0"
    \\score {
      \\relative c' {
        << { g'8. b16 d4 g4 } \\\\ { d4 g4 g4 } >>
      }
    }
    """
    score = LilypondParser().parse(ly_content)
    from dottednotes.models.in_accord import InAccord
    ia = score.staves[0].measures[0].notes[0]
    assert isinstance(ia, InAccord)
    assert len(ia.parts) == 2
    assert [(n.note_name, n.duration.value) for n in ia.parts[0]] == \
        [("G", 8), ("B", 16), ("D", 4), ("G", 4)]
    assert [(n.note_name, n.duration.value) for n in ia.parts[1]] == \
        [("D", 4), ("G", 4), ("G", 4)]


def test_in_accord_voices_track_octave_independently():
    # Each voice inside << >> must reset to the SAME pre-block relative
    # reference (InAccord.to_relative_lilypond()'s documented contract) --
    # not chain from whatever the previous voice's last note was. Before
    # the fix, voice 2's notes were computed relative to voice 1's *last*
    # note (since both voices were parsed as one merged stream), causing a
    # cumulative octave drift across many in-accord groups that eventually
    # produced an invalid octave and crashed.
    ly_content = """
    \\version "2.24.0"
    \\score {
      \\relative c' {
        << { g'8. b16 d4 g4 } \\\\ { d4 g4 g4 } >>
      }
    }
    """
    score = LilypondParser().parse(ly_content)
    ia = score.staves[0].measures[0].notes[0]
    voice1_octaves = [n.octave for n in ia.parts[0]]
    voice2_octaves = [n.octave for n in ia.parts[1]]
    # Voice 1: relative to c'(octave 4) -- g'8. reads as G4 (nearest-4th),
    # b16 as B4, d4 as D5, g4 as G5.
    assert voice1_octaves == [4, 4, 5, 5]
    # Voice 2 independently resets to the same c'(octave 4) reference --
    # d4 as D4, g4 as G4, g4 as G4 -- NOT continuing from voice 1's G5.
    assert voice2_octaves == [4, 4, 4]


def test_relative_reference_after_in_accord_uses_primary_voice():
    # After the << >> block closes, the ongoing relative-pitch reference
    # for what follows must advance to voice 0's (the primary voice's)
    # final note -- matching InAccord.to_relative_lilypond()'s documented
    # rule -- not voice 1's last note or some other value.
    ly_content = """
    \\version "2.24.0"
    \\score {
      \\relative c' {
        << { g'8. b16 d4 g4 } \\\\ { d4 g4 g4 } >> c4
      }
    }
    """
    score = LilypondParser().parse(ly_content)
    notes = score.staves[0].measures[0].notes
    following_note = notes[1]
    # Voice 0's last note is G5; an unmarked "c" immediately after should
    # read as the nearest C to G5, i.e. C6 (a 4th up), not C5 or C4.
    assert (following_note.note_name, following_note.octave) == ("C", 6)


def test_self_generated_piano_piece_round_trips_without_crashing():
    # Regression for the actual reported crash, using the scenario
    # LilypondParser is actually documented to support (CLAUDE.md: "only
    # needs to parse LilyPond that DottedNotes itself generated, not
    # arbitrary LilyPond written by humans") -- a real 41-measure two-hand
    # piano piece's OWN generated .ly, fed straight back in. Before the
    # fix, its many in-accord groups' real (non-monotonic) melodic contour
    # accumulated octave error across voices (see
    # test_in_accord_voices_track_octave_independently) until a note's
    # computed octave fell outside Note's valid 0-8 range partway through
    # and raised an uncaught ValueError.
    from dottednotes.parser.input_pipeline import BRLInputPipeline
    from dottednotes.parser.braille_parser import BrailleParser
    from dottednotes.parser.tokenizer import BrailleTokenizer

    brf_text = BRLInputPipeline().load(FIXTURES / "children_s_piece.brf")
    original_score = BrailleParser(tokens=BrailleTokenizer().tokenize(brf_text)).parse()
    generated_ly = original_score.to_lilypond()

    round_tripped = LilypondParser().parse(generated_ly)  # must not raise
    assert len(round_tripped.staves) == 2
    assert len(round_tripped.staves[0].measures) == 41
    assert len(round_tripped.staves[1].measures) == 41


def test_grace_note_attaches_to_following_note_and_chains_octave():
    # \grace {a8(} g4 -- Note.to_relative_lilypond()'s own documented
    # contract: the grace note chains into the relative-pitch reference
    # like an ordinary note, and the main note that follows it is relative
    # to the grace note, not to whatever preceded the \grace block.
    ly_content = """
    \\version "2.24.0"
    \\score {
      \\relative c' {
        b'4 \\grace {a8(} g4
      }
    }
    """
    score = LilypondParser().parse(ly_content)
    notes = score.staves[0].measures[0].notes
    main_note = notes[1]
    assert main_note.note_name == "G"
    assert main_note.grace_note is not None
    assert [(n.note_name, n.octave) for n in main_note.grace_note.notes] == [("A", 4)]
    # "g4" with no mark, relative to the grace note A4, reads as G4 (a step
    # down), not G3 or G5.
    assert main_note.octave == 4
