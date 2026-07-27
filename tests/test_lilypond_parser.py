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
    \\version "2.26.0"
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
    \\version "2.26.0"
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
    # R1*8 is Staff.to_lilypond()'s own compression of 8 consecutive
    # whole-measure-rest Measures into one compact token (see staff.py) --
    # the parser must expand it back into 8 real Measure objects, each a
    # single-measure rest, or the trailing c4's measure number drifts.
    ly_content = """
    \\version "2.26.0"
    \\score {
      \\relative c' {
        R1*8 c4
      }
    }
    """
    parser = LilypondParser()
    score = parser.parse(ly_content)
    measures = score.staves[0].measures
    assert len(measures) == 9
    for i, m in enumerate(measures[:8]):
        rest = m.notes[0]
        assert isinstance(rest, Rest)
        assert rest.is_full_measure is True
        assert rest.duration.value == 1
        assert rest.multi_measure_count == 1
        assert m.number == i + 1
    assert measures[8].number == 9
    assert isinstance(measures[8].notes[0], Note)


def test_parse_full_measure_rest_without_multiplier_defaults_to_one():
    ly_content = """
    \\version "2.26.0"
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
    \\version "2.26.0"
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
    \\version "2.26.0"
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
    \\version "2.26.0"
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
    \\version "2.26.0"
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
    \\version "2.26.0"
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


def test_in_accord_second_voice_chains_from_first_voices_last_note():
    # LilyPond's \relative pitch tracking treats '<<', '\\', and '>>' as
    # complete no-ops -- it is a purely sequential/textual chain through the
    # token stream, blind to the << \\ >> structure (verified against the
    # real `lilypond` binary's `\displayLilyMusic` output: `\relative c' {
    # g4 << { c,4 b'4 } \\ { d4 } >> c4 }` displays as `<< { c4 b4 } \\
    # { d'4 } >> c'4` -- voice 2's "d4" resolves to D4, which only matches
    # "continue from voice 1's LAST note" (B3); "reset to the pre-<< pitch"
    # (G3) would give D3, and "voice 1's FIRST note" (C3) would also give
    # D3). This uses the same non-degenerate shape (voice 1 ends far from
    # where it started) to pin down the same rule inside DottedNotes'
    # in-accord parsing.
    ly_content = """
    \\version "2.26.0"
    \\score {
      \\relative c' {
        g4 << { c,4 b'4 } \\\\ { d4 } >> c4
      }
    }
    """
    score = LilypondParser().parse(ly_content)
    ia = score.staves[0].measures[0].notes[1]
    assert [(n.note_name, n.octave) for n in ia.parts[0]] == [("C", 3), ("B", 3)]
    # Voice 2's "d" chains from voice 1's last note (B3), giving D4 -- not
    # D3 (which "reset to pre-<< G3" or "voice 1's first note C3" would give).
    assert [(n.note_name, n.octave) for n in ia.parts[1]] == [("D", 4)]


def test_relative_reference_after_in_accord_uses_last_voice():
    # After the << >> block closes, the ongoing relative-pitch reference
    # for what follows must continue from the LAST voice parsed (matching
    # real LilyPond's purely sequential pitch tracking -- see the comment on
    # test_in_accord_second_voice_chains_from_first_voices_last_note), not
    # voice 0's/the first voice's last note. Verified against real
    # `lilypond`'s `\displayLilyMusic`: `\relative c' { << { c'8 d8 e8 f8 g8
    # a8 b8 c8 } \\ { c,8 } >> d4 }` displays as `<< { c''8 ... c'''8 } \\
    # { c''8 } >> d''4` -- voice 1 ends on C6 ("c'''8"), voice 2 ends on C5
    # ("c''8"); the trailing "d4" resolves to D5, which matches "continue
    # from voice 2/the last voice's C5" (nearest D to C5 is D5) and rules
    # out "continue from voice 1's C6" (nearest D to C6 would be D6).
    ly_content = """
    \\version "2.26.0"
    \\score {
      \\relative c' {
        << { c'8 d8 e8 f8 g8 a8 b8 c8 } \\\\ { c,8 } >> d4
      }
    }
    """
    score = LilypondParser().parse(ly_content)
    notes = score.staves[0].measures[0].notes
    following_note = notes[1]
    assert (following_note.note_name, following_note.octave) == ("D", 5)


def test_two_consecutive_in_accord_measures_chain_through_last_voice():
    # Two << \\ >> measures back to back (as in a real two-hand piano
    # piece): the second measure's voice 1 must branch from the FIRST
    # measure's LAST voice's last note, not voice 1's. Verified against
    # real `lilypond`'s `\displayLilyMusic`: `\relative c' { << { c'8 d8 e8
    # f8 g8 a8 b8 c8 } \\ { c,8 } >> | << { d4 } \\ { e4 } >> | }` displays
    # as `<< {...c'''8} \\ {c''8} >> | << {d''4} \\ {e''4} >> |` -- voice 1
    # of measure 1 ends on C6 ("c'''8"), voice 2 ends on C5 ("c''8");
    # measure 2 voice 1's "d4" resolves to D5, matching "continue from
    # measure 1's LAST voice's C5" (nearest D to C5 is D5) and ruling out
    # "continue from voice 1's C6" (nearest D to C6 would be D6).
    ly_content = """
    \\version "2.26.0"
    \\score {
      \\relative c' {
        << { c'8 d8 e8 f8 g8 a8 b8 c8 } \\\\ { c,8 } >> |
        << { d4 } \\\\ { e4 } >> |
      }
    }
    """
    score = LilypondParser().parse(ly_content)
    ia2 = score.staves[0].measures[1].notes[0]
    assert [(n.note_name, n.octave) for n in ia2.parts[0]] == [("D", 5)]
    assert [(n.note_name, n.octave) for n in ia2.parts[1]] == [("E", 5)]


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
    \\version "2.26.0"
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


def test_lilypond_key_mode_parsing():
    # Test major key
    ly_major = """
    \\version "2.26.0"
    \\score {
      \\relative c' {
        \\key g \\major
        g4
      }
    }
    """
    score_major = LilypondParser().parse(ly_major)
    ks_major = score_major.staves[0].key_signature
    assert ks_major is not None
    assert ks_major.sharps_or_flats == 1
    assert ks_major.mode == "major"

    # Test minor key
    ly_minor = """
    \\version "2.26.0"
    \\score {
      \\relative c' {
        \\key e \\minor
        e4
      }
    }
    """
    score_minor = LilypondParser().parse(ly_minor)
    ks_minor = score_minor.staves[0].key_signature
    assert ks_minor is not None
    assert ks_minor.sharps_or_flats == 1
    assert ks_minor.mode == "minor"
