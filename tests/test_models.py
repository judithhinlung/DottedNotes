from dottednotes.bana_symbols import SymbolCategory
from dottednotes.models import (
    Articulation,
    ArticulationType,
    BrailleSymbol,
    Duration,
    Dynamic,
    DynamicLevel,
    Measure,
    Note,
    Ornament,
    OrnamentType,
    Score,
    Staff,
)


def test_braille_symbol_requires_to_lilypond():
    """BrailleSymbol subclasses must implement to_lilypond."""
    import pytest

    sym = BrailleSymbol(
        dots=frozenset([1, 2]),
        category=SymbolCategory.NOTE,
        raw_brl='⠃'
    )
    with pytest.raises(NotImplementedError):
        sym.to_lilypond()


def test_braille_symbol_repr():
    sym = BrailleSymbol(
        dots=frozenset([1, 2]),
        category=SymbolCategory.NOTE,
        raw_brl='⠃'
    )
    assert repr(sym) == "BrailleSymbol(dots=frozenset({1, 2}), category=NOTE)"


def test_duration_to_lilypond():
    assert Duration(4).to_lilypond() == "4"
    assert Duration(4, dots=1).to_lilypond() == "4."
    assert Duration(8, dots=2).to_lilypond() == "8.."
    assert Duration(1).to_lilypond() == "1"


def test_duration_to_lilypond_all_valid_values():
    for value in [1, 2, 4, 8, 16, 32, 64]:
        assert Duration(value).to_lilypond() == str(value)


def test_double_dotted_half():
    assert Duration(value=2, dots=2).to_lilypond() == "2.."


def test_invalid_duration_value_raises():
    import pytest
    with pytest.raises(ValueError):
        Duration(value=3)


def test_invalid_duration_value_zero_raises():
    import pytest
    with pytest.raises(ValueError):
        Duration(value=0)


def test_invalid_dot_count_raises():
    import pytest
    with pytest.raises(ValueError):
        Duration(value=4, dots=3)


def test_duration_in_beats_quarter():
    assert Duration(value=4).duration_in_beats() == 1.0


def test_duration_in_beats_dotted_quarter():
    assert Duration(value=4, dots=1).duration_in_beats() == 1.5


def test_duration_in_beats_half():
    assert Duration(value=2).duration_in_beats() == 2.0


def test_duration_in_beats_whole():
    assert Duration(value=1).duration_in_beats() == 4.0


def test_duration_in_beats_eighth():
    assert Duration(value=8).duration_in_beats() == 0.5


def test_duration_in_beats_double_dotted():
    assert Duration(value=4, dots=2).duration_in_beats() == 1.75


def test_note_defaults():
    note = Note(pitch="c", octave=4, duration=Duration(4))
    assert not note.is_rest
    assert not note.is_chord
    assert not note.tie
    assert note.articulations == []
    assert note.ornaments == []
    assert note.dynamic is None


def test_note_with_articulation():
    art = Articulation(ArticulationType.STACCATO)
    note = Note(pitch="g", octave=5, duration=Duration(8), articulations=[art])
    assert note.articulations[0].type == ArticulationType.STACCATO


def test_measure_add_note():
    measure = Measure(number=1)
    measure.add_note(Note(pitch="c", octave=4, duration=Duration(4)))
    measure.add_note(Note(pitch="e", octave=4, duration=Duration(4)))
    assert len(measure.notes) == 2


def test_staff_add_measure():
    staff = Staff(name="right hand")
    staff.add_measure(Measure(number=1))
    assert len(staff.measures) == 1


def test_score_add_staff():
    score = Score(title="Ode to Joy", composer="Beethoven")
    score.add_staff(Staff(name="right hand"))
    score.add_staff(Staff(name="left hand"))
    assert len(score.staves) == 2
    assert score.title == "Ode to Joy"
