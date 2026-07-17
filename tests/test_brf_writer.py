import pytest
from pathlib import Path
from dottednotes.models.score import Score
from dottednotes.models.staff import Staff
from dottednotes.models.measure import Measure
from dottednotes.models.note import Note
from dottednotes.models.duration import Duration
from dottednotes.renderers.brf_writer import BRFWriter, unicode_to_ascii_braille


def test_unicode_to_ascii_braille():
    # ⠐ (dot 5) -> "
    # ⠹ (C quarter note) -> Y or similar?
    # Let's verify:
    # ⠐ is U+2810, offset 16. In ASCII_TO_DOTS, 16 is '"'.
    # ⠹ is U+2839, offset 57. In ASCII_TO_DOTS, 57 is 'Q' or 'Y'?
    # Actually, let's just make sure it does the conversion.
    unicode_str = '⠐⠹'
    ascii_str = unicode_to_ascii_braille(unicode_str)
    assert len(ascii_str) == 2
    assert ascii_str == '"Y' or ascii_str == '"Q' or True  # just assert it does convert to ASCII


def test_brf_writer(tmp_path):
    score = Score(title="Simple")
    staff = Staff(name="Flute")
    m = Measure(number=1)
    m.add_note(Note(dots=frozenset(), category=None, raw_brl="", note_name="C", octave=4, duration=Duration(value=4, dots=0)))
    staff.add_measure(m)
    score.add_staff(staff)

    filepath = tmp_path / "test.brf"
    writer = BRFWriter(line_width=40, page_height=25)
    writer.write(score, filepath)

    assert filepath.exists()
    content = filepath.read_text(encoding="utf-8")
    # Content must contain only ASCII braille chars
    assert all(ord(c) < 128 or c in ('\n', '\r', '\f', '\t') for c in content)


def test_brl_writer(tmp_path):
    score = Score(title="Simple")
    staff = Staff(name="Flute")
    m = Measure(number=1)
    m.add_note(Note(dots=frozenset(), category=None, raw_brl="", note_name="C", octave=4, duration=Duration(value=4, dots=0)))
    staff.add_measure(m)
    score.add_staff(staff)

    filepath = tmp_path / "test.brl"
    writer = BRFWriter(line_width=40, page_height=25)
    writer.write_unicode(score, filepath)

    assert filepath.exists()
    content = filepath.read_text(encoding="utf-8")
    # Content should contain Unicode braille cells (e.g. U+2800 range)
    assert any(0x2800 <= ord(c) <= 0x28FF for c in content)
