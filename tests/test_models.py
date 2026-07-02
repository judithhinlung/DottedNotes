from dottednotes.bana_symbols import SymbolCategory
from dottednotes.models import (
    Accidental,
    AccidentalType,
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
    Rest,
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


def _make_note(note_name, octave, duration_value, dots=0, accidental=None, articulations=None):
    return Note(
        dots=frozenset(),
        category=SymbolCategory.NOTE,
        raw_brl='⠀',
        note_name=note_name,
        octave=octave,
        duration=Duration(value=duration_value, dots=dots),
        accidental=accidental,
        articulations=articulations or [],
    )


def test_middle_c_quarter():
    note = _make_note('C', 4, 4)
    assert note.to_lilypond() == "c'4"


def test_b_flat_half_note():
    note = _make_note('B', 4, 2, accidental=Accidental(dots=frozenset(), category=SymbolCategory.ACCIDENTAL, raw_brl='⠣', type=AccidentalType.FLAT))
    assert note.to_lilypond() == "bes'2"


def test_f_sharp_eighth():
    note = _make_note('F', 5, 8, accidental=Accidental(dots=frozenset(), category=SymbolCategory.ACCIDENTAL, raw_brl='⠩', type=AccidentalType.SHARP))
    assert note.to_lilypond() == "fis''8"


def test_all_natural_note_names():
    expected = {
        'C': 'c', 'D': 'd', 'E': 'e', 'F': 'f',
        'G': 'g', 'A': 'a', 'B': 'b',
    }
    for name, ly in expected.items():
        note = _make_note(name, 4, 4)
        assert note.to_lilypond().startswith(ly), f"{name} should produce {ly}..."


def test_octave_marks_all_octaves():
    expected_marks = {
        1: "c,,4", 2: "c,4", 3: "c4", 4: "c'4",
        5: "c''4", 6: "c'''4", 7: "c''''4",
    }
    for octave, expected in expected_marks.items():
        note = _make_note('C', octave, 4)
        assert note.to_lilypond() == expected, f"octave {octave}: expected {expected!r}"


def test_dotted_quarter_note():
    note = _make_note('G', 4, 4, dots=1)
    assert note.to_lilypond() == "g'4."


def test_note_with_staccato():
    art = Articulation(ArticulationType.STACCATO)
    note = _make_note('D', 4, 4, articulations=[art])
    assert note.to_lilypond() == "d'4-."


def test_invalid_note_name_raises():
    import pytest
    with pytest.raises(ValueError):
        _make_note('H', 4, 4)


def test_invalid_octave_raises():
    import pytest
    with pytest.raises(ValueError):
        _make_note('C', 9, 4)


def _make_accidental(accidental_type):
    return Accidental(
        dots=frozenset(),
        category=SymbolCategory.ACCIDENTAL,
        raw_brl='⠀',
        type=accidental_type,
    )


def test_accidental_sharp():
    assert _make_accidental(AccidentalType.SHARP).to_lilypond() == 'is'


def test_accidental_flat():
    assert _make_accidental(AccidentalType.FLAT).to_lilypond() == 'es'


def test_accidental_natural():
    assert _make_accidental(AccidentalType.NATURAL).to_lilypond() == ''


def test_accidental_double_sharp():
    assert _make_accidental(AccidentalType.DOUBLE_SHARP).to_lilypond() == 'isis'


def test_accidental_double_flat():
    assert _make_accidental(AccidentalType.DOUBLE_FLAT).to_lilypond() == 'eses'


def test_quarter_rest():
    rest = Rest(
        dots=frozenset(),
        category=SymbolCategory.REST,
        raw_brl='⠀',
        duration=Duration(value=4)
    )
    assert rest.to_lilypond() == "r4"


def test_full_measure_rest():
    rest = Rest(
        dots=frozenset(),
        category=SymbolCategory.REST,
        raw_brl='⠀',
        duration=Duration(value=1),
        is_full_measure=True
    )
    assert rest.to_lilypond() == "R1"


def test_dotted_half_rest():
    rest = Rest(
        dots=frozenset(),
        category=SymbolCategory.REST,
        raw_brl='⠀',
        duration=Duration(value=2, dots=1)
    )
    assert rest.to_lilypond() == "r2."


def test_measure_add_note():
    measure = Measure(number=1)
    measure.add_note(_make_note('C', 4, 4))
    measure.add_note(_make_note('E', 4, 4))
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


def test_articulation_staccato():
    assert Articulation(ArticulationType.STACCATO).to_lilypond() == '-.'


def test_articulation_accent():
    assert Articulation(ArticulationType.ACCENT).to_lilypond() == '->'


def test_articulation_tenuto():
    assert Articulation(ArticulationType.TENUTO).to_lilypond() == '--'


def test_articulation_marcato():
    assert Articulation(ArticulationType.MARCATO).to_lilypond() == '-^'


def test_articulation_portato():
    assert Articulation(ArticulationType.PORTATO).to_lilypond() == '-_'


def test_articulation_staccatissimo():
    assert Articulation(ArticulationType.STACCATISSIMO).to_lilypond() == '-!'


def test_note_with_accent():
    art = Articulation(ArticulationType.ACCENT)
    note = _make_note('C', 4, 4, articulations=[art])
    assert note.to_lilypond() == "c'4->"


def test_note_with_multiple_articulations():
    articulations = [
        Articulation(ArticulationType.TENUTO),
        Articulation(ArticulationType.STACCATO),
    ]
    note = _make_note('G', 5, 8, articulations=articulations)
    assert note.to_lilypond() == "g''8---."


def test_dynamic_ppp():
    assert Dynamic(DynamicLevel.PPP).to_lilypond() == r'\ppp'


def test_dynamic_pp():
    assert Dynamic(DynamicLevel.PP).to_lilypond() == r'\pp'


def test_dynamic_p():
    assert Dynamic(DynamicLevel.P).to_lilypond() == r'\p'


def test_dynamic_mp():
    assert Dynamic(DynamicLevel.MP).to_lilypond() == r'\mp'


def test_dynamic_mf():
    assert Dynamic(DynamicLevel.MF).to_lilypond() == r'\mf'


def test_dynamic_f():
    assert Dynamic(DynamicLevel.F).to_lilypond() == r'\f'


def test_dynamic_ff():
    assert Dynamic(DynamicLevel.FF).to_lilypond() == r'\ff'


def test_dynamic_fff():
    assert Dynamic(DynamicLevel.FFF).to_lilypond() == r'\fff'


def test_dynamic_sf():
    assert Dynamic(DynamicLevel.SF).to_lilypond() == r'\sf'


def test_dynamic_sfz():
    assert Dynamic(DynamicLevel.SFZ).to_lilypond() == r'\sfz'


def test_dynamic_fp():
    assert Dynamic(DynamicLevel.FP).to_lilypond() == r'\fp'


def test_dynamic_crescendo_start():
    assert Dynamic(DynamicLevel.CRESCENDO_START).to_lilypond() == r'\<'


def test_dynamic_crescendo_end():
    assert Dynamic(DynamicLevel.CRESCENDO_END).to_lilypond() == r'\!'


def test_dynamic_decrescendo_start():
    assert Dynamic(DynamicLevel.DECRESCENDO_START).to_lilypond() == r'\>'


def test_dynamic_decrescendo_end():
    assert Dynamic(DynamicLevel.DECRESCENDO_END).to_lilypond() == r'\!'


def test_note_with_all_components():
    """Integration test: note with accidental, duration, and articulation."""
    note = Note(
        dots=frozenset([1, 4]),
        category=SymbolCategory.NOTE,
        raw_brl='⠉',
        note_name='B',
        octave=4,
        duration=Duration(value=4, dots=1),
        accidental=Accidental(
            dots=frozenset(),
            category=SymbolCategory.ACCIDENTAL,
            raw_brl='⠀',
            type=AccidentalType.FLAT,
        ),
        articulations=[Articulation(ArticulationType.STACCATO)],
    )
    # B-flat, octave 4, dotted quarter, staccato
    assert note.to_lilypond() == "bes'4.-."
