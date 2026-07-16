"""S8b-10: real-fixture, real-compile integration tests combining breve
(S8b-1), bowing (S8b-2), sustain pedal (S8b-3), chord ties and doubled
intervals (S8b-4), and glissando/wind mute (S8b-6) in one hand-authored,
multi-staff score -- see tests/fixtures/README.md.

instrumental_techniques_test.brf covers: a breve note and a breve rest; both
up-bow and down-bow, including a down-bow carried across six consecutive
violin notes; a sustain pedal down/release pair plus a same-note pedal
change; a four-chord doubled chord-tie carry (BANA Sec. 10.2.2) running
concurrently with an active doubled-interval carry (Sec. 10.2.1) in the
piano-right-hand part; a glissando between two violin notes; and a wind-mute
stopped/open pair on the flute part.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from dottednotes.parser.ensemble_parser import EnsembleParser
from dottednotes.parser.input_pipeline import BRLInputPipeline

FIXTURES = Path(__file__).parent / "fixtures"


def _compile_and_check_no_warnings(ly_output: str, tmp_path: Path, basename: str) -> Path:
    """Same convention as test_lilypond_formatter.py / test_vocal.py /
    test_lead_sheet_integration.py: compile with the real `lilypond` binary
    (no --silent, so its full log is available), assert success and a
    non-empty PDF, and assert the compile log contains no "warning" text --
    a clean exit code alone doesn't mean LilyPond was happy with the
    engraving.
    """
    ly_file = tmp_path / f"{basename}.ly"
    ly_file.write_text(ly_output, encoding="utf-8")
    result = subprocess.run(
        ["lilypond", "-o", str(tmp_path / basename), str(ly_file)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"LilyPond compilation failed:\n{result.stderr}"

    combined_log = (result.stdout + result.stderr).lower()
    assert "warning" not in combined_log, (
        f"LilyPond reported a warning during compilation:\n{result.stdout}\n{result.stderr}"
    )

    pdf_path = tmp_path / f"{basename}.pdf"
    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 0
    return pdf_path


def test_sprint8b_fixture_parses_without_warnings(recwarn):
    text = BRLInputPipeline().load(FIXTURES / "instrumental_techniques_test.brf")
    EnsembleParser().parse(text)

    messages = [str(w.message) for w in recwarn.list]
    assert messages == []


def test_sprint8b_fixture_matches_ground_truth_ly():
    text = BRLInputPipeline().load(FIXTURES / "instrumental_techniques_test.brf")
    score = EnsembleParser().parse(text)

    ly_output = score.to_lilypond()
    ground_truth = (FIXTURES / "instrumental_techniques_test.ly").read_text(encoding="utf-8")
    assert ly_output == ground_truth


def test_sprint8b_fixture_compiles_cleanly(tmp_path: Path):
    if not shutil.which("lilypond"):
        pytest.skip("lilypond binary not found; skipping compile test")

    text = BRLInputPipeline().load(FIXTURES / "instrumental_techniques_test.brf")
    score = EnsembleParser().parse(text)

    ly_output = score.to_lilypond()
    _compile_and_check_no_warnings(ly_output, tmp_path, "instrumental_techniques_test")


def test_sprint8b_fixture_renders_expected_markup():
    text = BRLInputPipeline().load(FIXTURES / "instrumental_techniques_test.brf")
    score = EnsembleParser().parse(text)

    ly_output = score.to_lilypond()

    assert r"\breve" in ly_output
    assert r"\downbow" in ly_output
    assert r"\upbow" in ly_output
    assert r"\sustainOn" in ly_output
    assert r"\sustainOff" in ly_output
    assert r"\glissando" in ly_output
    assert r"\stopped" in ly_output
    assert r"\open" in ly_output
    # Chord ties render as '~' right after the chord's duration.
    assert "g>4~" in ly_output
    assert r"\breve~" in ly_output
