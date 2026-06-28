from dottednotes.models import (
    Articulation,
    ArticulationType,
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


def test_duration_to_lilypond():
    assert Duration(4).to_lilypond() == "4"
    assert Duration(4, dots=1).to_lilypond() == "4."
    assert Duration(8, dots=2).to_lilypond() == "8.."
    assert Duration(1).to_lilypond() == "1"


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
