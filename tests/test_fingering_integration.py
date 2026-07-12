import warnings
from pathlib import Path

from dottednotes.parser.input_pipeline import BRLInputPipeline
from dottednotes.parser.tokenizer import BrailleTokenizer
from dottednotes.parser.braille_parser import BrailleParser
from dottednotes.models.chord import Chord

FIXTURES = Path(__file__).parent / "fixtures"


def _parse_fixture(name, record_warnings=False):
    pipeline = BRLInputPipeline()
    text = pipeline.load(FIXTURES / name)
    tokens = BrailleTokenizer().tokenize(text)
    if record_warnings:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            score = BrailleParser(tokens=tokens).parse()
        return score, caught
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        score = BrailleParser(tokens=tokens).parse()
    return score


# --- fingering_test_suite.brf: synthetic single-staff fixture exercising
# --- every fingering idiom in isolation (S6-1 through S6-4) ---


def test_fingering_test_suite_has_eight_measures():
    score = _parse_fixture("fingering_test_suite.brf")
    assert len(score.staves) == 1
    assert len(score.staves[0].measures) == 8


def test_fingering_test_suite_measure1_basic_fingerings():
    score = _parse_fixture("fingering_test_suite.brf")
    notes = score.staves[0].measures[0].notes
    assert [n.note_name for n in notes] == ['C', 'C', 'C']
    assert [n.fingerings[0].finger for n in notes] == [1, 2, 3]
    assert [n.to_lilypond() for n in notes] == ["c'4-1", "c'4-2", "c'2-3"]


def test_fingering_test_suite_measure2_remaining_basic_fingers_and_unfingered_note():
    score = _parse_fixture("fingering_test_suite.brf")
    notes = score.staves[0].measures[1].notes
    assert [n.fingerings[0].finger for n in notes[:2]] == [4, 5]
    # D half note carries no fingering at all.
    assert notes[2].note_name == 'D'
    assert notes[2].fingerings == []
    assert [n.to_lilypond() for n in notes] == ["c'4-4", "c'4-5", "d'2"]


def test_fingering_test_suite_measure3_fingering_on_plain_quarter_and_beats_balance():
    # Fixed: measure 3 used to be dotted-E-quarter(1.5) + 3 quarters = 4.5
    # beats, overflowing 4/4 by half a beat. The dot has been removed, so
    # this is now four plain quarters (E-1, E, D, C) = 4.0 beats exactly,
    # and no beat-count warning should fire.
    score, caught = _parse_fixture("fingering_test_suite.brf", record_warnings=True)
    notes = score.staves[0].measures[2].notes
    assert notes[0].duration.dots == 0
    assert notes[0].fingerings[0].finger == 1
    assert [n.to_lilypond() for n in notes] == ["e'4-1", "e'4", "d'4", "c'4"]
    assert not any("Measure 3" in str(w.message) for w in caught)


def test_fingering_test_suite_measure4_change_of_fingering_and_alternative_both_present():
    score = _parse_fixture("fingering_test_suite.brf")
    notes = score.staves[0].measures[3].notes

    change = notes[0].fingerings[0]
    assert (change.finger, change.change_to) == (1, 2)
    assert notes[0].to_lilypond() == "c'4-1-2"

    alt = notes[1].fingerings[0]
    assert (alt.finger, alt.alternative) == (1, 2)
    assert notes[1].to_lilypond() == 'c\'4-\\markup \\center-column { "2" "1" }'

    assert notes[2].fingerings == []
    assert notes[2].to_lilypond() == "c'2"


def test_fingering_test_suite_measure5_alternative_first_omitted():
    score = _parse_fixture("fingering_test_suite.brf")
    notes = score.staves[0].measures[4].notes
    f = notes[0].fingerings[0]
    assert f.first_omitted is True
    assert f.alternative == 2
    assert notes[0].to_lilypond() == 'c\'4-\\markup \\center-column { "2" "" }'
    # Remaining notes in the measure are unfingered scale motion.
    assert [n.note_name for n in notes[1:]] == ['D', 'E', 'F']
    assert all(n.fingerings == [] for n in notes[1:])


def test_fingering_test_suite_measure6_octave_mark_unaffected_by_fingering_parsing():
    # Regression check: an octave-up mark shortly after fingered notes
    # still applies correctly -- fingering lookahead must not consume or
    # confuse octave-mark tokens.
    score = _parse_fixture("fingering_test_suite.brf")
    notes = score.staves[0].measures[5].notes
    assert [(n.note_name, n.octave) for n in notes] == [
        ('G', 4), ('A', 4), ('B', 4), ('C', 5),
    ]
    assert notes[-1].to_lilypond() == "c''4"


def test_fingering_test_suite_measures7_and_8_plain_notes_regress_cleanly():
    # Plain, unfingered notes surrounding the fingering-heavy measures
    # must be completely unaffected by fingering support.
    score = _parse_fixture("fingering_test_suite.brf")
    m7 = score.staves[0].measures[6].notes
    m8 = score.staves[0].measures[7].notes
    assert all(n.fingerings == [] for n in m7 + m8)
    assert [n.to_lilypond() for n in m7] == ["c'4"] * 4
    assert [n.to_lilypond() for n in m8] == ["c'4", "c'4", "c'2"]


def test_fingering_test_suite_ends_with_final_bar_line():
    score = _parse_fixture("fingering_test_suite.brf")
    ly = score.staves[0].to_lilypond()
    assert r'\bar "|."' in ly


# --- fingering_melody.brf: real two-hand piano piece with known-correct
# --- LilyPond output in fingering_melody.ly (ground truth, same role
# --- children_s_piece.brf's ground truth .ly played for S5-5). ---


def test_fingering_melody_has_two_correctly_named_staves():
    score = _parse_fixture("fingering_melody.brf")
    assert len(score.staves) == 2
    assert score.staves[0].name == 'right hand'
    assert score.staves[1].name == 'left hand'


def test_fingering_melody_staves_have_matching_measure_numbers():
    score = _parse_fixture("fingering_melody.brf")
    right_numbers = [m.number for m in score.staves[0].measures]
    left_numbers = [m.number for m in score.staves[1].measures]
    assert right_numbers == left_numbers == [1, 2, 3, 4]


def test_fingering_melody_has_no_beat_count_warnings():
    _, caught = _parse_fixture("fingering_melody.brf", record_warnings=True)
    assert caught == []


def test_fingering_melody_right_hand_matches_lilypond_ground_truth():
    # fingering_melody.ly pianoRightHand:
    # %1 c4-1 d4-2 e4-3 f4-4 |
    # %2 g2.-5-4 a8-5( g8) |
    # %3 g4-\markup \center-column { "5" "4" } f4-4 e4-3 d4-2 |
    # %4 c2-1 c'2-5 \bar "|." |
    score = _parse_fixture("fingering_melody.brf")
    m1, m2, m3, m4 = score.staves[0].measures

    assert [n.to_lilypond() for n in m1.notes] == [
        "c'4-1", "d'4-2", "e'4-3", "f'4-4",
    ]

    # Measure 2: change-of-fingering on a dotted half, then a slurred pair
    # of eighths (the slur must not interfere with fingering rendering).
    assert m2.notes[0].fingerings[0].finger == 5
    assert m2.notes[0].fingerings[0].change_to == 4
    assert m2.notes[0].to_lilypond() == "g'2.-5-4"
    ly_m2 = score.staves[0].to_lilypond()
    assert "a8-5( g8)" in ly_m2

    # Measure 3: alternative fingering (both present) stacked markup.
    assert m3.notes[0].to_lilypond() == \
        'g\'4-\\markup \\center-column { "5" "4" }'
    assert [n.to_lilypond() for n in m3.notes[1:]] == [
        "f'4-4", "e'4-3", "d'4-2",
    ]

    # Measure 4: octave jump between the two half notes, each fingered.
    assert [n.to_lilypond() for n in m4.notes] == ["c'2-1", "c''2-5"]


def test_fingering_melody_left_hand_matches_lilypond_ground_truth():
    # fingering_melody.ly pianoLeftHand:
    # %1 c4-5 g'4-1 d4-4 g4-1 |
    # %2 c,4-5 e4-3 g4-1 f8-2( e8-3) |
    # %3 c4-5 d4-4 e4-3 f4-2 |
    # %4 <c-5 e-3 g-1>1 \bar "|." |
    score = _parse_fixture("fingering_melody.brf")
    m1, m2, m3, m4 = score.staves[1].measures

    assert [n.fingerings[0].finger for n in m1.notes] == [5, 1, 4, 1]
    assert [n.fingerings[0].finger for n in m3.notes] == [5, 4, 3, 2]

    # Measure 4 collapses to a single triad, and every member note carries
    # its own fingering (S6-1: fingerings attach per-note within a chord).
    chord = m4.notes[0]
    assert isinstance(chord, Chord)
    assert len(chord.notes) == 3
    assert [n.fingerings[0].finger for n in chord.notes] == [5, 3, 1]
    assert chord.to_lilypond() == "<c-5 e-3 g-1>1"


def test_fingering_melody_full_score_renders_as_piano_staff_with_final_bar():
    score = _parse_fixture("fingering_melody.brf")
    ly = score.to_lilypond()
    assert r'\new PianoStaff <<' in ly
    assert ly.count(r'\new Staff {') == 2
    assert ly.count(r'\bar "|."') == 2
