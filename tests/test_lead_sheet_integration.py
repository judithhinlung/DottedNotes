"""S8b-9: real-fixture, real-compile integration tests for BANA Sec. 27
lead sheets, complementing test_chord_symbols.py's isolated-string unit
tests with a full hand-authored `.brf` -- see tests/fixtures/README.md.

lead_sheet_test.brf covers: an instrumental header (time signature only,
no key signature), margin measure numbers using the lead-sheet-specific
number-sign-prefixed convention (BANA 27, confirmed by the developer --
distinct from the bare-letter convention plain solo scores use), a pickup
(anacrusis) measure numbered 0 with no coincident chord symbol, and chord
symbols covering maj7, dominant 7th, minor, sus4, and diminished, each
aligned to the first cell (including any octave-mark/accidental prefix) of
the melody note it accompanies.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from dottednotes.cli import main
from dottednotes.parser.input_pipeline import BRLInputPipeline
from dottednotes.parser.lead_sheet_parser import parse_lead_sheet

FIXTURES = Path(__file__).parent / "fixtures"


def _compile_and_check_no_warnings(ly_output: str, tmp_path: Path, basename: str) -> Path:
    """Same convention as test_lilypond_formatter.py / test_vocal.py: compile
    with the real `lilypond` binary (no --silent, so its full log is
    available), assert success and a non-empty PDF, and assert the compile
    log contains no "warning" text -- a clean exit code alone doesn't mean
    LilyPond was happy with the engraving.
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


def test_lead_sheet_fixture_parses_without_unexpected_warnings(recwarn):
    # The fixture opens with a one-beat pickup measure (measure 0) and ends
    # with a correspondingly short final measure (measure 8) -- both
    # legitimate (BANA margin numbers 0 and 5 confirmed by the developer),
    # but _validate_measure_beat_count (S5-8) always compares a measure's
    # length against a full bar, so these two specific warnings are the
    # expected result, not a parsing bug. Anything else would be a bug.
    text = BRLInputPipeline().load(FIXTURES / "lead_sheet_test.brf")
    score = parse_lead_sheet(text)

    messages = [str(w.message) for w in recwarn.list]
    assert len(messages) == 2, messages
    assert "Measure 0: expected 4.0 beats but counted 1.0" in messages[0]
    assert "Measure 8: expected 4.0 beats but counted 3.0" in messages[1]

    assert score.chord_names is not None
    assert len(score.chord_names.entries) == 26


def test_lead_sheet_fixture_matches_ground_truth_ly():
    text = BRLInputPipeline().load(FIXTURES / "lead_sheet_test.brf")
    score = parse_lead_sheet(text)

    ly_output = score.to_lilypond(category_override="Lead Sheet")
    ground_truth = (FIXTURES / "lead_sheet_test.ly").read_text(encoding="utf-8")
    assert ly_output == ground_truth


def test_lead_sheet_fixture_compiles_cleanly(tmp_path: Path):
    if not shutil.which("lilypond"):
        pytest.skip("lilypond binary not found; skipping compile test")

    text = BRLInputPipeline().load(FIXTURES / "lead_sheet_test.brf")
    score = parse_lead_sheet(text)

    ly_output = score.to_lilypond(category_override="Lead Sheet")
    assert "\\new ChordNames" in ly_output
    assert "\\partial 4" in ly_output  # the opening pickup measure

    _compile_and_check_no_warnings(ly_output, tmp_path, "lead_sheet_test")


def test_cli_convert_lead_sheet_fixture_end_to_end(monkeypatch, tmp_path):
    out = tmp_path / "lead_sheet_test.ly"
    monkeypatch.setattr(
        "sys.argv",
        [
            "dottednotes", "convert",
            str(FIXTURES / "lead_sheet_test.brf"), str(out),
            "--category", "Lead Sheet",
        ],
    )
    main()

    content = out.read_text(encoding="utf-8")
    ground_truth = (FIXTURES / "lead_sheet_test.ly").read_text(encoding="utf-8")
    assert content == ground_truth
