from dottednotes.models import Duration, Measure, Note, Score, Staff
from dottednotes.renderers import LilypondRenderer


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
    measure.add_note(Note(pitch="c", octave=4, duration=Duration(4)))
    staff.add_measure(measure)
    score.add_staff(staff)
    output = LilypondRenderer().render(score)
    assert "c" in output
    assert "4" in output


def test_render_rest():
    score = Score()
    staff = Staff(name="rh")
    measure = Measure(number=1)
    measure.add_note(Note(pitch="r", octave=4, duration=Duration(4), is_rest=True))
    staff.add_measure(measure)
    score.add_staff(staff)
    output = LilypondRenderer().render(score)
    assert "r4" in output
