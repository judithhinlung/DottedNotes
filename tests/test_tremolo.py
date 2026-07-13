import warnings

from dottednotes.bana_symbols import SymbolCategory
from dottednotes.models import Chord, Duration, Note
from dottednotes.models.tremolo import AlternatingTremolo, RepeatedTremolo
from dottednotes.parser import BrailleParser, BrailleTokenizer


def _parse(text: str) -> list:
    """Helper: tokenize and parse braille text, return items from first measure."""
    tokens = BrailleTokenizer().tokenize(text)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        score = BrailleParser(tokens=tokens).parse()
    return score.staves[0].measures[0].notes


def _note(name='C', octave=4, value=4, tremolo=None):
    return Note(
        dots=frozenset(),
        category=SymbolCategory.NOTE,
        raw_brl='',
        note_name=name,
        octave=octave,
        duration=Duration(value=value),
        tremolo=tremolo,
    )


# --- Model: RepeatedTremolo ---

def test_repeated_tremolo_to_lilypond_all_subdivisions():
    for subdivision in (8, 16, 32, 64, 128):
        assert RepeatedTremolo(subdivision=subdivision).to_lilypond() == f':{subdivision}'


def test_note_with_tremolo_renders_colon_after_duration():
    note = _note(tremolo=RepeatedTremolo(subdivision=16))
    assert note.to_lilypond() == "c'4:16"


def test_note_with_tremolo_and_fingering_order():
    from dottednotes.models.fingering import Fingering
    note = _note(tremolo=RepeatedTremolo(subdivision=8))
    note.fingerings.append(Fingering(dots=frozenset(), category=SymbolCategory.FINGERING, raw_brl='⠁', finger=1))
    assert note.to_lilypond() == "c'4:8-1"


def test_chord_with_tremolo_on_written_note():
    written = _note('C', 4, 4, tremolo=RepeatedTremolo(subdivision=16))
    other = _note('A', 3, 4)
    chord = Chord(notes=[written, other])
    assert chord.to_lilypond() == "<c a>4:16"


# --- Model: AlternatingTremolo ---

def test_alternating_tremolo_repeat_count_half_note_sixteenths():
    n1 = _note('C', 4, 2)
    n2 = _note('D', 4, 2)
    alt = AlternatingTremolo(items=[n1, n2], subdivision=16)
    assert alt._repeat_count() == 4


def test_alternating_tremolo_to_relative_lilypond():
    n1 = _note('C', 4, 2)
    n2 = _note('D', 4, 2)
    alt = AlternatingTremolo(items=[n1, n2], subdivision=16)
    ly, midi = alt.to_relative_lilypond(60)
    assert ly == r'\repeat tremolo 4 { c16 d16 }'
    assert midi == 62


# --- Parser: repeated-note tremolo, single sign ---

def test_parse_single_repeated_tremolo_all_subdivisions():
    signs = [('⠃', 8), ('⠇', 16), ('⠂', 32), ('⠅', 64), ('⠄', 128)]
    for value_cell, subdivision in signs:
        notes = _parse(f'⠐⠹⠘{value_cell}')
        assert len(notes) == 1
        note = notes[0]
        assert isinstance(note, Note)
        assert note.tremolo == RepeatedTremolo(subdivision=subdivision)
        assert note.to_lilypond() == f"c'4:{subdivision}"


def test_parse_repeated_tremolo_on_chord():
    # ⠐⠹⠬⠘⠇ = C4 quarter + 3rd interval (chord), 16th repeated tremolo
    notes = _parse('⠐⠹⠬⠘⠇')
    assert len(notes) == 1
    chord = notes[0]
    assert isinstance(chord, Chord)
    assert chord.notes[0].tremolo == RepeatedTremolo(subdivision=16)
    assert chord.to_lilypond() == "<c a>4:16"


def test_parse_repeated_tremolo_after_fingering():
    # ⠐⠹ = C4 quarter, ⠁ = finger 1, ⠘⠃ = 8th repeated tremolo
    notes = _parse('⠐⠹⠁⠘⠃')
    assert len(notes) == 1
    note = notes[0]
    assert note.tremolo == RepeatedTremolo(subdivision=8)
    assert len(note.fingerings) == 1
    assert note.to_lilypond() == "c'4:8-1"


# --- Parser: repeated-note tremolo doubling (4+ notes, BANA 14.2) ---

def test_parse_repeated_tremolo_doubling_carries_across_run():
    # C quarter x4; doubled 8ths sign starts the run after note 1,
    # notes 2-3 are bare, the full sign terminates the run after note 4.
    notes = _parse('⠐⠹⠃⠃⠹⠹⠹⠘⠃')
    assert len(notes) == 4
    for note in notes:
        assert note.tremolo == RepeatedTremolo(subdivision=8)
        assert note.to_lilypond() == "c'4:8"


def test_parse_repeated_tremolo_doubling_does_not_leak_past_terminator():
    # Doubled run of two 16th-tremolo notes, terminated, then a plain note.
    notes = _parse('⠐⠹⠇⠇⠹⠘⠇⠹')
    assert len(notes) == 3
    assert notes[0].tremolo == RepeatedTremolo(subdivision=16)
    assert notes[1].tremolo == RepeatedTremolo(subdivision=16)
    assert notes[2].tremolo is None


def test_doubled_fingering_same_value_not_misread_as_tremolo_collision():
    # A single note followed by a genuine (if unusual) alternative-fingering
    # pair with two DIFFERENT fingers must still parse as fingering, not
    # tremolo -- only an identical doubled cell signals tremolo doubling.
    notes = _parse('⠐⠹⠁⠃')
    assert len(notes) == 1
    note = notes[0]
    assert note.tremolo is None
    assert len(note.fingerings) == 1
    assert note.fingerings[0].finger == 1
    assert note.fingerings[0].alternative == 2


# --- Parser: alternating-note tremolo (BANA 14.3) ---

def test_parse_alternating_tremolo_notes():
    # ⠐⠝ = C4 half, ⠨⠇ = 16th alternating sign, ⠕ = D4 half
    notes = _parse('⠐⠝⠨⠇⠕')
    assert len(notes) == 1
    alt = notes[0]
    assert isinstance(alt, AlternatingTremolo)
    assert alt.subdivision == 16
    assert [n.note_name for n in alt.items] == ['C', 'D']
    assert all(n.duration.value == 2 for n in alt.items)
    ly, _ = alt.to_relative_lilypond(60)
    assert ly == r'\repeat tremolo 4 { c16 d16 }'


def test_parse_alternating_tremolo_chords():
    # ⠐⠹⠬ = C4 quarter chord (+3rd below), ⠨⠇ = 16th alternating sign,
    # ⠱⠬ = D4 quarter chord (+3rd below)
    notes = _parse('⠐⠹⠬⠨⠇⠱⠬')
    assert len(notes) == 1
    alt = notes[0]
    assert isinstance(alt, AlternatingTremolo)
    assert all(isinstance(item, Chord) for item in alt.items)
    ly, _ = alt.to_relative_lilypond(60)
    assert ly == r'\repeat tremolo 2 { <c a>16 <d b>16 }'


def test_parse_alternating_tremolo_all_subdivisions():
    signs = [('⠃', 8), ('⠇', 16), ('⠂', 32), ('⠁', 64), ('⠄', 128)]
    for value_cell, subdivision in signs:
        notes = _parse(f'⠐⠝⠨{value_cell}⠕')
        assert len(notes) == 1
        assert notes[0].subdivision == subdivision
