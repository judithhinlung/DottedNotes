"""Tests for the "Measure numbering" setting (auto / print_score) and the
explicit TranscriptionMode dispatch it rides on (BrailleRenderer). See
CLAUDE.md / TICKETS.md for the BANA citations backing margin-number
placement and the numeral-sign convention this setting must not disturb:
BANA 24.1.1 (solo), 29.3(b) (keyboard bar-over-bar), 33.4.6 (ensemble
heading).
"""
import tempfile
from pathlib import Path

import music21
import pytest

from dottednotes.models.note import Note
from dottednotes.models.duration import Duration
from dottednotes.models.measure import Measure
from dottednotes.models.staff import Staff
from dottednotes.models.score import Score
from dottednotes.renderers.braille_renderer import BrailleRenderer, _INT_TO_LITERARY_DIGIT
from dottednotes.parser.musicxml_parser import load_musicxml


def _digit_str(n: int) -> str:
    """Encode an int as the braille literary-digit cells BrailleRenderer
    uses for margin/heading measure numbers (no numeral sign)."""
    return "".join(_INT_TO_LITERARY_DIGIT[int(d)] for d in str(n))


def _note(name="C", octave=4, value=4):
    return Note(dots=frozenset(), category=None, raw_brl="", note_name=name, octave=octave, duration=Duration(value))


def _solo_score(measure_numbers: list[int]) -> Score:
    """A single-staff (solo) score, one measure per entry in
    `measure_numbers`, using that exact `Measure.number` -- deliberately
    decoupled from position so auto vs. print_score are distinguishable."""
    staff = Staff(name="Violin", clef=None, key_signature=None, time_signature=None)
    staff.measures = [Measure(number=n, notes=[_note()]) for n in measure_numbers]
    return Score(title="", staves=[staff])


def _ensemble_score(measure_numbers: list[int]) -> Score:
    """A 3-staff score (staff count alone is enough to trigger ENSEMBLE
    detection), one measure per entry, same number across all staves
    (a valid parallel) so there is exactly one system/heading to check."""
    staves = []
    for name in ("Violin I", "Violin II", "Viola"):
        staff = Staff(name=name, clef=None, key_signature=None, time_signature=None)
        staff.measures = [Measure(number=n, notes=[_note()]) for n in measure_numbers]
        staves.append(staff)
    return Score(title="", staves=staves)


# ---------------------------------------------------------------------------
# Solo mode
# ---------------------------------------------------------------------------

def test_solo_mode_auto_numbering_ignores_source_number():
    # Source says measure 99; "auto" must show the sequential position (1),
    # not the source's own number.
    score = _solo_score([99])
    output = BrailleRenderer(measure_numbering="auto").render(score)
    assert output.startswith("⠼" + _digit_str(1) + " ")
    assert _digit_str(99) not in output


def test_solo_mode_print_score_numbering_uses_source_number():
    score = _solo_score([99])
    output = BrailleRenderer(measure_numbering="print_score").render(score)
    assert output.startswith("⠼" + _digit_str(99) + " ")


def test_solo_mode_auto_numbering_default():
    # "auto" is the default -- no explicit measure_numbering needed.
    score = _solo_score([5, 6])
    output = BrailleRenderer(line_width=6).render(score)
    lines = output.strip("\n").split("\n")
    assert lines[0].startswith("⠼" + _digit_str(1) + " ")
    assert lines[1].startswith("⠼" + _digit_str(2) + " ")


# ---------------------------------------------------------------------------
# Ensemble mode
# ---------------------------------------------------------------------------

def test_ensemble_mode_auto_numbering_ignores_source_number():
    score = _ensemble_score([57])
    output = BrailleRenderer(measure_numbering="auto").render(score)
    assert "⠼" + _digit_str(1) in output
    assert "⠼" + _digit_str(57) not in output


def test_ensemble_mode_print_score_numbering_uses_source_number():
    score = _ensemble_score([57])
    output = BrailleRenderer(measure_numbering="print_score").render(score)
    assert "⠼" + _digit_str(57) in output


# ---------------------------------------------------------------------------
# Irregular / non-sequential print numbering (MusicXML), print_score mode
# ---------------------------------------------------------------------------

def _write_musicxml_with_irregular_numbers(tmp_path: Path) -> Path:
    """A single-part MusicXML score whose print measure numbers are
    irregular: a pickup measure numbered 0, then a jump from 1 straight to
    21 (e.g. a rehearsal-letter-driven renumbering) -- exactly the kind of
    source print_score is supposed to preserve rather than "correct"."""
    part = music21.stream.Part()
    part.partName = "Flute"

    pickup = music21.stream.Measure(number=0)
    pickup.append(music21.note.Note("C5", quarterLength=1))
    part.append(pickup)

    m1 = music21.stream.Measure(number=1)
    m1.append(music21.meter.TimeSignature("4/4"))
    m1.append(music21.note.Note("D5", quarterLength=4))
    part.append(m1)

    m21 = music21.stream.Measure(number=21)
    m21.append(music21.note.Note("E5", quarterLength=4))
    part.append(m21)

    score = music21.stream.Score()
    score.insert(0, part)

    out_path = tmp_path / "irregular_numbers.musicxml"
    score.write("musicxml", fp=str(out_path))
    return out_path


def test_print_score_mode_preserves_irregular_musicxml_measure_numbers(tmp_path):
    xml_path = _write_musicxml_with_irregular_numbers(tmp_path)
    score = load_musicxml(str(xml_path))

    numbers = [m.number for m in score.staves[0].measures]
    assert numbers == [0, 1, 21]

    output = BrailleRenderer(measure_numbering="print_score", line_width=6).render(score)
    lines = [l for l in output.strip("\n").split("\n") if l]
    # Each measure is its own line at this width; the pickup (0), 1, and the
    # jump straight to 21 must all appear exactly as in the source -- never
    # "corrected" to 1, 2, 3.
    assert any(line.startswith("⠼" + _digit_str(0)) for line in lines)
    assert any(line.startswith("⠼" + _digit_str(1) + " ") for line in lines)
    assert any(line.startswith("⠼" + _digit_str(21)) for line in lines)


def test_auto_mode_renumbers_irregular_musicxml_measure_numbers_sequentially(tmp_path):
    # Contrast case: "auto" ignores the same irregular source numbers and
    # renumbers sequentially from 1 instead.
    xml_path = _write_musicxml_with_irregular_numbers(tmp_path)
    score = load_musicxml(str(xml_path))

    output = BrailleRenderer(measure_numbering="auto", line_width=6).render(score)
    lines = [l for l in output.strip("\n").split("\n") if l]
    music_lines = lines[1:]  # lines[0] is the title (music21's default movement name)
    assert any(line.startswith("⠼" + _digit_str(1) + " ") for line in music_lines)
    assert any(line.startswith("⠼" + _digit_str(2) + " ") for line in music_lines)
    assert any(line.startswith("⠼" + _digit_str(3) + " ") for line in music_lines)
    assert "⠼" + _digit_str(21) not in output


def test_invalid_measure_numbering_mode_rejected():
    with pytest.raises(ValueError):
        BrailleRenderer(measure_numbering="bogus")
