from __future__ import annotations

import io
import json
import re
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from dottednotes.models import Score, Staff
from dottednotes.exceptions import DottedNotesError
from dottednotes.cli import main
from dottednotes.web import app, SCORE_CACHE

client = TestClient(app)


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
    # Flute starts C D E F (c4 d e f -> c4 d4 e4 f4)
    # Violin starts G A B C (g3 a b c -> g'4 a4 b4 c4)
    assert "g'4 a4 b4 c4" in content.lower()
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
    assert "c4 d4 e4 f4" in content.lower()
    assert "g'4 a4 b4 c4" not in content.lower()


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
    assert data["parts"] == ["Flute", "Violin"]


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

    # 1. Download part 0 (Flute)
    part0_response = client.get(f"/api/jobs/{job_id}/parts/0/ly")
    assert part0_response.status_code == 200
    assert "c4 d4 e4 f4" in part0_response.text.lower()
    assert "g'4 a4 b4 c4" not in part0_response.text.lower()

    # 2. Download part 1 (Violin)
    part1_response = client.get(f"/api/jobs/{job_id}/parts/1/ly")
    assert part1_response.status_code == 200
    assert "g'4 a4 b4 c4" in part1_response.text.lower()

    # 3. Test caching and fallback re-parsing
    # Evict score from cache to verify fallback
    if job_id in SCORE_CACHE:
        del SCORE_CACHE[job_id]

    part1_response_fallback = client.get(f"/api/jobs/{job_id}/parts/1/ly")
    assert part1_response_fallback.status_code == 200
    assert "g'4 a4 b4 c4" in part1_response_fallback.text.lower()
