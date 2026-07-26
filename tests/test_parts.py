from __future__ import annotations

import io
import json
import re
import pytest
import music21
from pathlib import Path
from fastapi.testclient import TestClient

from dottednotes.models import Score, Staff
from dottednotes.exceptions import DottedNotesError
from dottednotes.cli import main
from dottednotes.web import app, SCORE_CACHE

client = TestClient(app)


def _write_flute_and_horn_musicxml(tmp_path: Path) -> Path:
    """A two-part MusicXML score: a non-transposing Flute and a Horn in F
    (down a perfect 5th) -- used to verify that individual-part output uses
    the horn player's written (transposed) pitch, not concert pitch."""
    flute = music21.stream.Part()
    flute.partName = "Flute"
    fm = music21.stream.Measure(number=1)
    fm.append(music21.meter.TimeSignature("4/4"))
    fm.append(music21.note.Note("C5", quarterLength=4))
    flute.append(fm)

    horn = music21.stream.Part()
    inst = music21.instrument.Horn()
    inst.partName = "Horn in F"
    inst.transposition = music21.interval.Interval('P-5')
    horn.insert(0, inst)
    hm = music21.stream.Measure(number=1)
    hm.append(music21.note.Note("C5", quarterLength=4))
    horn.append(hm)

    m21_score = music21.stream.Score()
    m21_score.insert(0, flute)
    m21_score.insert(0, horn)

    out_path = tmp_path / "flute_horn.musicxml"
    m21_score.write("musicxml", fp=str(out_path))
    return out_path


def test_score_extract_part_index():
    score = Score(title="Duo", composer="Bach")
    staff1 = Staff(name="Violin")
    staff2 = Staff(name="Cello")
    score.add_staff(staff1)
    score.add_staff(staff2)

    part1 = score.extract_part(0)
    assert len(part1.staves) == 1
    assert part1.staves[0].name == "Violin"
    assert part1.title == "Duo - Violin"
    assert part1.composer == "Bach"

    part2 = score.extract_part(1)
    assert len(part2.staves) == 1
    assert part2.staves[0].name == "Cello"
    assert part2.title == "Duo - Cello"


def test_score_extract_part_populates_midi_instrument():
    # Regression: OrchestraScore's full-score renderer computes each staff's
    # MIDI instrument on the fly from its name and never stores it on the
    # Staff object -- extracting a part into a plain Score bypasses that
    # renderer entirely, so without this fix an extracted part's .midi
    # silently falls back to Acoustic Grand Piano regardless of instrument.
    score = Score(title="Duo", composer="Bach")
    score.add_staff(Staff(name="Violin"))
    score.add_staff(Staff(name="Cello"))

    assert score.extract_part(0).staves[0].midi_instrument == "violin"
    assert score.extract_part(1).staves[0].midi_instrument == "cello"


def test_score_extract_part_leaves_unresolvable_name_alone():
    # A solo score's placeholder staff names ("right hand"/"left hand")
    # don't resolve to a GM instrument -- must stay None (no behavior
    # change for plain piano scores, which already default to piano).
    score = Score()
    score.add_staff(Staff(name="right hand"))
    assert score.extract_part(0).staves[0].midi_instrument is None


def test_score_extract_part_does_not_override_explicit_instrument():
    # A prior S12-3 instrument selection (web.py's _apply_instrument) must
    # win over the name-based fallback.
    score = Score()
    staff = Staff(name="Violin")
    staff.midi_instrument = "trumpet"
    score.add_staff(staff)
    assert score.extract_part(0).staves[0].midi_instrument == "trumpet"


def test_score_extract_part_name():
    score = Score(title="Choral")
    staff1 = Staff(name="Soprano")
    staff2 = Staff(name="Alto")
    score.add_staff(staff1)
    score.add_staff(staff2)

    part_sop = score.extract_part("Soprano")
    assert len(part_sop.staves) == 1
    assert part_sop.staves[0].name == "Soprano"

    part_alto = score.extract_part("alto")  # test case-insensitivity
    assert len(part_alto.staves) == 1
    assert part_alto.staves[0].name == "Alto"


def test_score_extract_part_string_instrument_keeps_treble_clef_despite_low_register():
    # Regression test (S10d-12): a Violin II staff whose first written note
    # sits below middle C must still render in treble clef when extracted
    # as a standalone part -- see Staff._resolve_clef()'s instrument-table
    # lookup, which now takes priority over the old register-only heuristic.
    from dottednotes.models import Measure, Note, Duration

    score = Score(title="Duo")
    v1 = Staff(name="Violin I")
    v1.add_measure(Measure(number=1, notes=[
        Note(dots=frozenset(), category=None, raw_brl="", note_name="C", octave=5, duration=Duration(4))
    ]))
    v2 = Staff(name="Violin II")
    v2.add_measure(Measure(number=1, notes=[
        Note(dots=frozenset(), category=None, raw_brl="", note_name="G", octave=3, duration=Duration(4))
    ]))
    score.add_staff(v1)
    score.add_staff(v2)

    part = score.extract_part(1)
    ly = part.to_lilypond(concert_pitch=False)
    assert r'\clef treble' in ly
    assert r'\clef bass' not in ly


def test_score_extract_part_with_ensemble_resolved_chord_keeps_ensemble_transcription():
    # S10d-13: an extracted part containing a Chord resolved under BANA
    # 33.4.2's ensemble "read upward" rule must not silently render under
    # SOLO's clef-based-direction convention -- that would have a reader
    # reconstruct the wrong pitch letter for the interval note, not just
    # the wrong octave (see Chord.resolved_ensemble_upward's docstring).
    from dottednotes.models import Measure, Chord, Note, Duration
    from dottednotes.parser.ensemble_parser import EnsembleParser

    score = Score(title="Duo")
    v1 = Staff(name="Violin I")
    written = Note(dots=frozenset(), category=None, raw_brl="", note_name="C", octave=4, duration=Duration(4))
    # A 3rd above C4 = E4 under the ensemble-upward rule this chord was
    # resolved under (same pitch pair as test_ensemble_treble_clef_interval_reads_upward
    # in test_parser.py) -- treble-clef SOLO convention would instead read
    # this interval sign as a 3rd *below*, reconstructing A3.
    interval_note = Note(dots=frozenset(), category=None, raw_brl="", note_name="E", octave=4, duration=Duration(4))
    chord = Chord(notes=[written, interval_note], resolved_ensemble_upward=True)
    v1.add_measure(Measure(number=1, notes=[chord]))
    v2 = Staff(name="Violin II")
    v2.add_measure(Measure(number=1, notes=[
        Note(dots=frozenset(), category=None, raw_brl="", note_name="G", octave=3, duration=Duration(4))
    ]))
    score.add_staff(v1)
    score.add_staff(v2)

    part0 = score.extract_part(0)
    out0 = part0.to_braille()
    # ENSEMBLE layout: a one-row instrument-list header naming "Violin I"
    # and its Table 29 abbreviation, not a bare SOLO margin-number line.
    assert '⠠⠧⠊⠕⠇⠊⠝' in out0  # "Violin" (capitalized)
    assert '⠜⠧⠂⠄' in out0      # ⠜ + "v1" (Table 29) + ⠄

    # Round-trips correctly when re-parsed standalone: the interval note
    # is still E4, not A3 (what SOLO/clef-based reading would produce).
    reparsed = EnsembleParser().parse(out0)
    reparsed_chord = reparsed.staves[0].measures[0].notes[0]
    assert reparsed_chord.notes[1].note_name == 'E'
    assert reparsed_chord.notes[1].octave == 4

    # A part with no ensemble-resolved shorthand content (Violin II here,
    # a plain melodic note) is unaffected -- still renders as plain SOLO.
    part1 = score.extract_part(1)
    out1 = part1.to_braille()
    assert '⠜⠧⠆⠄' not in out1
    assert '⠼⠁⠀' in out1  # plain SOLO margin-number prefix, no instrument header


def test_score_extract_part_invalid():
    score = Score()
    staff = Staff(name="Violin")
    score.add_staff(staff)

    with pytest.raises(DottedNotesError) as exc:
        score.extract_part(2)
    assert "Invalid part index 3" in str(exc.value)

    with pytest.raises(DottedNotesError) as exc2:
        score.extract_part("Oboe")
    assert "Part 'Oboe' not found" in str(exc2.value)


# CLI Tests
def _run_main(monkeypatch: pytest.MonkeyPatch, args: list[str]) -> None:
    monkeypatch.setattr("sys.argv", ["dottednotes", *args])
    main()


def test_cli_list_parts(monkeypatch, tmp_path, capsys):
    # Setup a simple multi-staff score using an ensemble header
    brf_file = tmp_path / "ensemble.brf"
    brf_file.write_text(
        '⠠⠋⠇⠥⠞⠑⠀⠐⠐⠐⠐⠐⠀⠀⠜⠋⠇⠄\n'
        '⠠⠧⠊⠕⠇⠊⠝⠀⠐⠐⠀⠀⠀⠜⠧⠇⠄\n'
        '⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠣⠣⠣⠼⠙⠲\n'
        '⠁⠀⠀⠜⠋⠇⠄⠐⠹⠱⠫⠻⠀⠐⠳⠪⠺⠹\n'
        '⠀⠀⠀⠜⠧⠇⠄⠸⠳⠪⠺⠹⠀⠸⠹⠱⠫⠻\n',
        encoding="utf-8"
    )

    with pytest.raises(SystemExit) as exc:
        _run_main(monkeypatch, ["convert", str(brf_file), "--list-parts"])
    assert exc.value.code == 0

    captured = capsys.readouterr()
    assert "Available parts:" in captured.err
    assert "1. Flute" in captured.err
    assert "2. Violin" in captured.err


def test_cli_part_by_index(monkeypatch, tmp_path):
    brf_file = tmp_path / "ensemble.brf"
    brf_file.write_text(
        '⠠⠋⠇⠥⠞⠑⠀⠐⠐⠐⠐⠐⠀⠀⠜⠋⠇⠄\n'
        '⠠⠧⠊⠕⠇⠊⠝⠀⠐⠐⠀⠀⠀⠜⠧⠇⠄\n'
        '⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠣⠣⠣⠼⠙⠲\n'
        '⠁⠀⠀⠜⠋⠇⠄⠐⠹⠱⠫⠻⠀⠐⠳⠪⠺⠹\n'
        '⠀⠀⠀⠜⠧⠇⠄⠸⠳⠪⠺⠹⠀⠸⠹⠱⠫⠻\n',
        encoding="utf-8"
    )
    out = tmp_path / "part2.ly"
    _run_main(monkeypatch, ["convert", str(brf_file), str(out), "--part", "2"])

    content = out.read_text(encoding="utf-8")
    # Should only contain Violin part, not Flute or the Piano/StaffGroup layout
    # Key signature is 3 flats (B, E, A). Flute starts C D E F (c4 d ees f).
    # Violin starts G A B C (g3 a b c -> g'4 aes4 bes4 c4).
    assert "g'4 aes4 bes4 c4" in content.lower()
    assert "StaffGroup" not in content


def test_cli_part_by_name(monkeypatch, tmp_path):
    brf_file = tmp_path / "ensemble.brf"
    brf_file.write_text(
        '⠠⠋⠇⠥⠞⠑⠀⠐⠐⠐⠐⠐⠀⠀⠜⠋⠇⠄\n'
        '⠠⠧⠊⠕⠇⠊⠝⠀⠐⠐⠀⠀⠀⠜⠧⠇⠄\n'
        '⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠣⠣⠣⠼⠙⠲\n'
        '⠁⠀⠀⠜⠋⠇⠄⠐⠹⠱⠫⠻⠀⠐⠳⠪⠺⠹\n'
        '⠀⠀⠀⠜⠧⠇⠄⠸⠳⠪⠺⠹⠀⠸⠹⠱⠫⠻\n',
        encoding="utf-8"
    )
    out = tmp_path / "part_flute.ly"
    _run_main(monkeypatch, ["convert", str(brf_file), str(out), "--part", "Flute"])

    content = out.read_text(encoding="utf-8")
    # Key signature is 3 flats (B, E, A), so the Flute's E is flatted.
    assert "c4 d4 ees4 f4" in content.lower()
    assert "g'4 aes4 bes4 c4" not in content.lower()


def test_cli_part_of_transposing_instrument_uses_written_pitch(monkeypatch, tmp_path):
    # Regression test: an individual player's part for a transposing
    # instrument must show written (transposed) pitch, not concert pitch --
    # see Score.to_lilypond's concert_pitch docstring.
    xml_path = _write_flute_and_horn_musicxml(tmp_path)

    full_out = tmp_path / "full.ly"
    _run_main(monkeypatch, ["convert", str(xml_path), str(full_out)])
    full_content = full_out.read_text(encoding="utf-8")
    assert r"\transpose" in full_content  # full score defaults to concert pitch

    horn_out = tmp_path / "horn_part.ly"
    _run_main(monkeypatch, ["convert", str(xml_path), str(horn_out), "--part", "Horn in F"])
    horn_content = horn_out.read_text(encoding="utf-8")
    assert r"\transpose" not in horn_content
    assert "c1" in horn_content.lower()  # written pitch, untouched


# Web API Tests
def test_web_convert_returns_parts_list():
    brf_content = (
        '⠠⠋⠇⠥⠞⠑⠀⠐⠐⠐⠐⠐⠀⠀⠜⠋⠇⠄\n'
        '⠠⠧⠊⠕⠇⠊⠝⠀⠐⠐⠀⠀⠀⠜⠧⠇⠄\n'
        '⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠣⠣⠣⠼⠙⠲\n'
        '⠁⠀⠀⠜⠋⠇⠄⠐⠹⠱⠫⠻⠀⠐⠳⠪⠺⠹\n'
        '⠀⠀⠀⠜⠧⠇⠄⠸⠳⠪⠺⠹⠀⠸⠹⠱⠫⠻\n'
    ).encode("utf-8")
    file_obj = io.BytesIO(brf_content)

    response = client.post(
        "/api/convert",
        files={"file": ("ensemble.brf", file_obj, "text/plain")},
        data={
            "target_format": "lilypond",
            "category": "Chamber",
            "profile": "standard"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "parts" in data
    assert [p["name"] for p in data["parts"]] == ["Flute", "Violin"]
    assert all(not p["needs_instrument"] for p in data["parts"])


def test_web_part_rendering_endpoint():
    brf_content = (
        '⠠⠋⠇⠥⠞⠑⠀⠐⠐⠐⠐⠐⠀⠀⠜⠋⠇⠄\n'
        '⠠⠧⠊⠕⠇⠊⠝⠀⠐⠐⠀⠀⠀⠜⠧⠇⠄\n'
        '⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠣⠣⠣⠼⠙⠲\n'
        '⠁⠀⠀⠜⠋⠇⠄⠐⠹⠱⠫⠻⠀⠐⠳⠪⠺⠹\n'
        '⠀⠀⠀⠜⠧⠇⠄⠸⠳⠪⠺⠹⠀⠸⠹⠱⠫⠻\n'
    ).encode("utf-8")
    file_obj = io.BytesIO(brf_content)

    response = client.post(
        "/api/convert",
        files={"file": ("ensemble.brf", file_obj, "text/plain")},
        data={
            "target_format": "lilypond",
            "category": "Chamber",
            "profile": "standard"
        }
    )
    assert response.status_code == 200
    job_id = response.json()["job_id"]

    # 1. Download part 0 (Flute). Key signature is 3 flats (B, E, A), so the
    # Flute's E is flatted.
    part0_response = client.get(f"/api/jobs/{job_id}/parts/0/ly")
    assert part0_response.status_code == 200
    assert "c4 d4 ees4 f4" in part0_response.text.lower()
    assert "g'4 aes4 bes4 c4" not in part0_response.text.lower()
    # Regression: an extracted ensemble part must carry its own MIDI
    # instrument, not silently fall back to piano.
    assert '\\set Staff.midiInstrument = "flute"' in part0_response.text

    # 2. Download part 1 (Violin)
    part1_response = client.get(f"/api/jobs/{job_id}/parts/1/ly")
    assert part1_response.status_code == 200
    assert "g'4 aes4 bes4 c4" in part1_response.text.lower()
    assert '\\set Staff.midiInstrument = "violin"' in part1_response.text

    # 3. Download part 0 (Flute) as BRF with measure numbers
    response_mn = client.post(
        "/api/convert",
        files={"file": ("ensemble.brf", io.BytesIO(brf_content), "text/plain")},
        data={
            "target_format": "lilypond",
            "category": "Chamber",
            "profile": "standard",
            "measure_numbers": "true"
        }
    )
    assert response_mn.status_code == 200
    job_id_mn = response_mn.json()["job_id"]

    part0_brf_response = client.get(f"/api/jobs/{job_id_mn}/parts/0/brf")
    assert part0_brf_response.status_code == 200
    # In BRF/ASCII Braille, measure numbers in solo format are prepended with #
    # Measure 1 should be #A, Measure 2 should be #B
    assert "#A " in part0_brf_response.text

    # 4. Test caching and fallback re-parsing
    # Evict score from cache to verify fallback
    if job_id in SCORE_CACHE:
        del SCORE_CACHE[job_id]

    part1_response_fallback = client.get(f"/api/jobs/{job_id}/parts/1/ly")
    assert part1_response_fallback.status_code == 200
    assert "g'4 aes4 bes4 c4" in part1_response_fallback.text.lower()


def test_web_part_of_transposing_instrument_uses_written_pitch(tmp_path):
    # Regression test: the per-part download endpoint must render a
    # transposing instrument's individual part in written pitch, not
    # concert pitch -- see Score.to_lilypond's concert_pitch docstring.
    xml_path = _write_flute_and_horn_musicxml(tmp_path)

    with open(xml_path, "rb") as f:
        response = client.post(
            "/api/convert",
            files={"file": ("flute_horn.musicxml", f, "application/xml")},
            data={"target_format": "lilypond"},
        )
    assert response.status_code == 200
    data = response.json()
    assert [p["name"] for p in data["parts"]] == ["Flute", "Horn in F"]
    job_id = data["job_id"]

    full_response = client.get(f"/api/jobs/{job_id}/ly")
    assert full_response.status_code == 200
    assert r"\transpose" in full_response.text  # full score defaults to concert pitch

    horn_response = client.get(f"/api/jobs/{job_id}/parts/1/ly")
    assert horn_response.status_code == 200
    assert r"\transpose" not in horn_response.text
    assert "c1" in horn_response.text.lower()  # written pitch, untouched
