import pytest
from dottednotes.parser.tokenizer import BrailleTokenizer
from dottednotes.parser.braille_parser import BrailleParser
from dottednotes.models import Note, Chord, Fingering


def _parse(text: str) -> list:
    """Helper: tokenize and parse braille text, return notes from first measure."""
    tokens = BrailleTokenizer().tokenize(text)
    score = BrailleParser(tokens=tokens).parse()
    return score.staves[0].measures[0].notes


def test_parse_single_fingerings():
    # ⠐ = octave 4, ⠹ = C quarter.
    # ⠁, ⠃, ⠇, ⠂, ⠅ are fingers 1 to 5.
    for finger_char, finger_val in [('⠁', 1), ('⠃', 2), ('⠇', 3), ('⠂', 4), ('⠅', 5)]:
        notes = _parse(f'⠐⠹{finger_char}')
        assert len(notes) == 1
        note = notes[0]
        assert isinstance(note, Note)
        assert len(note.fingerings) == 1
        assert note.fingerings[0].finger == finger_val
        assert note.fingerings[0].change_to is None
        assert note.fingerings[0].alternative is None


def test_parse_fingering_after_dotted_note():
    # ⠐⠹ = C4 quarter, ⠄ = dot, ⠁ = finger 1
    notes = _parse('⠐⠹⠄⠁')
    assert len(notes) == 1
    note = notes[0]
    assert note.duration.dots == 1
    assert len(note.fingerings) == 1
    assert note.fingerings[0].finger == 1
    assert note.to_lilypond() == "c'4.-1"


def test_parse_fingering_on_tied_note():
    # ⠐⠹ = C4 quarter, ⠁ = finger 1, ⠈⠉ = tie, ⠹ = C4 quarter
    notes = _parse('⠐⠹⠁⠈⠉⠹')
    assert len(notes) == 2
    assert notes[0].tie is True
    assert len(notes[0].fingerings) == 1
    assert notes[0].fingerings[0].finger == 1
    assert notes[0].to_lilypond() == "c'4-1~"


def test_parse_change_of_fingering():
    # ⠐⠹ = C4 quarter, ⠁ = finger 1, ⠉ = change sign, ⠃ = finger 2
    notes = _parse('⠐⠹⠁⠉⠃')
    assert len(notes) == 1
    note = notes[0]
    assert len(note.fingerings) == 1
    f = note.fingerings[0]
    assert f.finger == 1
    assert f.change_to == 2
    assert f.to_lilypond() == "-1-2"
    assert note.to_lilypond() == "c'4-1-2"


def test_parse_alternative_fingerings_both_present():
    # ⠐⠹ = C4 quarter, ⠁ = finger 1, ⠃ = finger 2
    notes = _parse('⠐⠹⠁⠃')
    assert len(notes) == 1
    note = notes[0]
    assert len(note.fingerings) == 1
    f = note.fingerings[0]
    assert f.finger == 1
    assert f.alternative == 2
    assert f.first_omitted is False
    assert f.second_omitted is False
    assert note.to_lilypond() == 'c\'4-\\markup \\center-column { "2" "1" }'


def test_parse_alternative_fingerings_first_omitted():
    # ⠐⠹ = C4 quarter, ⠠ = first omitted, ⠃ = finger 2
    notes = _parse('⠐⠹⠠⠃')
    assert len(notes) == 1
    note = notes[0]
    assert len(note.fingerings) == 1
    f = note.fingerings[0]
    assert f.finger is None
    assert f.alternative == 2
    assert f.first_omitted is True
    assert f.second_omitted is False
    assert note.to_lilypond() == 'c\'4-\\markup \\center-column { "2" "" }'


def test_parse_alternative_fingerings_second_omitted():
    # ⠐⠹ = C4 quarter, ⠁ = finger 1, ⠄ = second omitted
    notes = _parse('⠐⠹⠁⠄')
    assert len(notes) == 1
    note = notes[0]
    assert len(note.fingerings) == 1
    f = note.fingerings[0]
    assert f.finger == 1
    assert f.alternative is None
    assert f.first_omitted is False
    assert f.second_omitted is True
    assert note.to_lilypond() == 'c\'4-\\markup \\center-column { "" "1" }'


def test_parse_chord_fingerings():
    # ⠐⠹ = C4 quarter, ⠁ = finger 1, ⠬ = interval third (E4 descending to A3 in Treble clef), ⠃ = finger 2
    notes = _parse('⠐⠹⠁⠬⠃')
    assert len(notes) == 1
    chord = notes[0]
    assert isinstance(chord, Chord)
    assert len(chord.notes) == 2
    
    # Written note C4
    n1 = chord.notes[0]
    assert n1.note_name == 'C'
    assert len(n1.fingerings) == 1
    assert n1.fingerings[0].finger == 1
    
    # Interval note A3
    n2 = chord.notes[1]
    assert n2.note_name == 'A'
    assert len(n2.fingerings) == 1
    assert n2.fingerings[0].finger == 2
    
    assert chord.to_lilypond() == "<c-1 a-2>4"
