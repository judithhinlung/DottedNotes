"""End-to-end CLI tests: genuine subprocess invocation of the actual
`dottednotes` entry point (via `python -m dottednotes.cli`, the same
`main()` the installed `dottednotes` console script calls), as opposed to
test_cli.py's in-process `_run_main()` (monkeypatched sys.argv + a direct
`main()` call in the same process).

This distinction matters: several real bugs this project has shipped only
manifested via genuine installed/packaged execution -- a missing package-data
declaration silently dropping the web UI's static assets from a real (non-
editable) install, a case-sensitive-filesystem mismatch between a fixture's
real filename and what code referenced, and cli.py having no .ly input
handling at all (so a real `dottednotes convert some.ly out.brl` run
misread LilyPond source as braille text) -- none of which an in-process
call is guaranteed to catch the same way a real subprocess run does.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


def _run_cli(args: list[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "dottednotes.cli", *args],
        capture_output=True,
        text=True,
        timeout=30,
        **kwargs,
    )


def test_version(tmp_path):
    result = _run_cli(["--version"])
    assert result.returncode == 0
    assert "dottednotes" in result.stdout


def test_convert_brf_to_lilypond(tmp_path):
    out = tmp_path / "children.ly"
    result = _run_cli(["convert", str(FIXTURES / "children_s_piece.brf"), str(out)])

    assert result.returncode == 0, result.stderr
    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert r"\new PianoStaff" in content
    assert "r16" not in content


def test_convert_brf_to_braille_reformat(tmp_path):
    # A .brf/.brl output path switches `convert` to braille output (CLAUDE.md
    # CLI Design) -- exercises the forward-then-reformat direction, not just
    # forward-to-LilyPond.
    out = tmp_path / "children_reformatted.brf"
    result = _run_cli(["convert", str(FIXTURES / "children_s_piece.brf"), str(out)])
    assert result.returncode == 0, result.stderr
    assert out.exists()
    assert out.read_text(encoding="utf-8").strip() != ""


def test_convert_self_generated_lilypond_to_braille(tmp_path):
    # Regression: this is the exact scenario reported broken -- `dottednotes
    # convert some.ly out.brl` used to produce garbled output (a whole-file
    # measure-repeat spam of "⠶" and "⠜??⠄" placeholders), because cli.py had
    # no .ly input handling at all and silently misread the LilyPond source
    # as braille text. Uses a self-generated .ly (.brf -> .ly, then that .ly
    # -> .brl) since that's the actually-documented-supported scenario
    # (CLAUDE.md: LilypondParser "only needs to parse LilyPond that
    # DottedNotes itself generated, not arbitrary LilyPond written by
    # humans") -- see test_convert_hand_authored_lilypond_fails_cleanly for
    # the hand-authored case.
    generated_ly = tmp_path / "children.ly"
    gen_result = _run_cli(
        ["convert", str(FIXTURES / "children_s_piece.brf"), str(generated_ly)]
    )
    assert gen_result.returncode == 0, gen_result.stderr

    out = tmp_path / "children.brl"
    result = _run_cli(["convert", str(generated_ly), str(out)])

    assert result.returncode == 0, result.stderr
    assert out.exists()
    content = out.read_text(encoding="utf-8")

    # Real BANA two-hand piano notation: right/left hand signs and in-accord
    # separators, not measure-repeat spam or unresolved-name placeholders.
    assert "⠨⠜" in content  # right hand sign
    assert "⠸⠜" in content  # left hand sign
    assert "⠣⠜" in content  # in-accord separator
    assert "??" not in content
    # The original bug rendered every measure as nothing but a lone
    # measure-repeat sign -- a handful of legitimate repeats elsewhere in a
    # real piece is fine, dozens in a row is the bug's signature.
    assert content.count("⠶") < 5


def test_convert_hand_authored_lilypond_fails_cleanly(tmp_path):
    # tests/fixtures/Children_s_Piece.ly is a hand-authored ground-truth
    # fixture, not DottedNotes-generated -- outside LilypondParser's
    # documented scope, and it uses at least one construct (deep
    # chord-chain relative-octave tracking) the restricted parser can't
    # fully resolve. That's an acceptable, expected limitation; what's not
    # acceptable is a raw Python traceback. Must fail with a plain-text
    # Error: line and non-zero exit, same as any other malformed/unsupported
    # input -- not a stack trace.
    out = tmp_path / "children.brl"
    result = _run_cli(["convert", str(FIXTURES / "Children_s_Piece.ly"), str(out)])

    assert result.returncode != 0
    assert result.stderr.startswith("Error:")
    assert "Traceback" not in result.stderr
    assert not out.exists()


def test_convert_musicxml_to_braille(tmp_path):
    out = tmp_path / "dichterliebe.brf"
    result = _run_cli(
        ["convert", str(FIXTURES / "dichterliebe01.musicxml"), str(out)]
    )

    assert result.returncode == 0, result.stderr
    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert content.strip() != ""


def test_convert_missing_file_reports_plain_text_error_no_traceback(tmp_path):
    missing = tmp_path / "does_not_exist.brf"
    result = _run_cli(["convert", str(missing)])

    assert result.returncode != 0
    assert result.stderr.startswith("Error:")
    assert "Traceback" not in result.stderr
    assert result.stdout == ""


def test_convert_lilypond_missing_file_reports_plain_text_error_no_traceback(tmp_path):
    # Same guard as above, specifically for the newly-added .ly input path
    # -- Path.read_text() raises a builtin FileNotFoundError (an OSError
    # subclass), which main()'s central error handling must still catch
    # and print as a plain-text line, not let leak as a raw traceback (this
    # project's own explicit design rule -- CLAUDE.md Key Design Decision 7
    # -- and the exact failure mode the LilypondParser Dynamic-kwarg and
    # in-accord octave-drift bugs both hit before being fixed).
    missing = tmp_path / "does_not_exist.ly"
    result = _run_cli(["convert", str(missing)])

    assert result.returncode != 0
    assert result.stderr.startswith("Error:")
    assert "Traceback" not in result.stderr
    assert result.stdout == ""


def test_convert_malformed_brf_reports_plain_text_error_no_traceback(tmp_path):
    brf = tmp_path / "malformed.brf"
    brf.write_text("⠶", encoding="utf-8")  # measure repeat with nothing to repeat
    result = _run_cli(["convert", str(brf)])

    assert result.returncode != 0
    assert result.stderr.startswith("Error:")
    assert "Traceback" not in result.stderr


@pytest.mark.skipif(
    subprocess.run(
        [sys.executable, "-c", "import shutil, sys; sys.exit(0 if shutil.which('lilypond') else 1)"]
    ).returncode != 0,
    reason="lilypond not installed",
)
def test_e2e_full_pipeline_compiles_to_pdf_and_midi(tmp_path):
    out_ly = tmp_path / "children.ly"
    result = _run_cli(
        ["convert", str(FIXTURES / "children_s_piece.brf"), str(out_ly), "--compile"]
    )
    assert result.returncode == 0, result.stderr
    assert out_ly.exists()
    assert (tmp_path / "children.pdf").exists()
    assert (tmp_path / "children.midi").exists()
