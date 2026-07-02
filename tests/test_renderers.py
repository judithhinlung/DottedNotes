from dottednotes.bana_symbols import SymbolCategory
from dottednotes.models import Duration, Measure, Note, Score, Staff
from dottednotes.renderers import LilypondRenderer


def _make_note(note_name, octave, duration_value):
    return Note(
        dots=frozenset(),
        category=SymbolCategory.NOTE,
        raw_brl='⠀',
        note_name=note_name,
        octave=octave,
        duration=Duration(value=duration_value),
    )


def test_render_includes_version():
    output = LilypondRenderer().render(Score())
    assert '\\version' in output


def test_render_empty_score_no_header():
    output = LilypondRenderer().render(Score())
    assert '\\header' not in output


def test_render_header_when_title_set():
    score = Score(title="Moonlight Sonata", composer="Beethoven")
    output = LilypondRenderer().render(score)
    assert "Moonlight Sonata" in output
    assert "Beethoven" in output


def test_render_single_quarter_note():
    score = Score()
    staff = Staff(name="rh")
    measure = Measure(number=1)
    measure.add_note(_make_note('C', 4, 4))
    staff.add_measure(measure)
    score.add_staff(staff)
    output = LilypondRenderer().render(score)
    assert "c'4" in output


def test_render_note_octave_5():
    score = Score()
    staff = Staff(name="rh")
    measure = Measure(number=1)
    measure.add_note(_make_note('G', 5, 8))
    staff.add_measure(measure)
    score.add_staff(staff)
    output = LilypondRenderer().render(score)
    assert "g''8" in output
