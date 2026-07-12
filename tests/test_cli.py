from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from dottednotes.cli import main

FIXTURES = Path(__file__).parent / "fixtures"

# A minimal, valid Unicode-braille .brf: time signature 4/4, C4 quarter note.
_SIMPLE_BRF = '⠀⠀⠼⠙⠲\n⠐⠹\n'


def _write_simple_brf(tmp_path: Path) -> Path:
    brf = tmp_path / "simple.brf"
    brf.write_text(_SIMPLE_BRF, encoding="utf-8")
    return brf


def _run_main(monkeypatch: pytest.MonkeyPatch, args: list[str]) -> None:
    monkeypatch.setattr("sys.argv", ["dottednotes", *args])
    main()


def test_convert_writes_to_output_file(monkeypatch, tmp_path, capsys):
    brf = _write_simple_brf(tmp_path)
    out = tmp_path / "simple.ly"
    _run_main(monkeypatch, ["convert", str(brf), str(out)])

    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert r'\version' in content
    assert "c4" in content

    captured = capsys.readouterr()
    assert f"Written to {out}" in captured.err
    assert captured.out == ""


def test_convert_prints_to_stdout_when_no_output_given(monkeypatch, tmp_path, capsys):
    brf = _write_simple_brf(tmp_path)
    _run_main(monkeypatch, ["convert", str(brf)])

    captured = capsys.readouterr()
    assert r'\version' in captured.out
    assert "c4" in captured.out


def test_version_flag_prints_version_and_exits_zero(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["dottednotes", "--version"])
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "dottednotes" in captured.out


def test_missing_subcommand_exits_nonzero(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["dottednotes"])
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code != 0


def test_convert_missing_lilypond_binary_reports_plain_text_error(
    monkeypatch, tmp_path, capsys
):
    brf = _write_simple_brf(tmp_path)
    out = tmp_path / "simple.ly"
    monkeypatch.setattr("dottednotes.cli.shutil.which", lambda name: None)

    with pytest.raises(SystemExit) as exc_info:
        _run_main(monkeypatch, ["convert", str(brf), str(out), "--compile"])
    assert exc_info.value.code != 0

    captured = capsys.readouterr()
    assert "lilypond" in captured.err.lower()
    assert "Traceback" not in captured.err


# --- S7-3: error handling -- plain text, non-zero exit, no traceback ---


def test_convert_missing_input_file_reports_plain_text_error(monkeypatch, tmp_path, capsys):
    missing = tmp_path / "does_not_exist.brf"

    with pytest.raises(SystemExit) as exc_info:
        _run_main(monkeypatch, ["convert", str(missing)])
    assert exc_info.value.code != 0

    captured = capsys.readouterr()
    assert "Error:" in captured.err
    assert str(missing) in captured.err
    assert "Traceback" not in captured.err


def test_convert_malformed_input_reports_plain_text_parse_error(monkeypatch, tmp_path, capsys):
    # A whole-measure repeat sign with no previous measure to repeat is
    # malformed per BANA 18.2.3(a) -- MeasureRepeatError (a BrailleParseError).
    brf = tmp_path / "malformed.brf"
    brf.write_text('⠶', encoding="utf-8")

    with pytest.raises(SystemExit) as exc_info:
        _run_main(monkeypatch, ["convert", str(brf)])
    assert exc_info.value.code != 0

    captured = capsys.readouterr()
    assert "Error:" in captured.err
    assert "repeat sign" in captured.err
    assert "Traceback" not in captured.err
    assert captured.out == ""


# --- S7-4: --verbose trace ---


def test_convert_verbose_prints_encoding_and_tokens_to_stderr(monkeypatch, tmp_path, capsys):
    brf = _write_simple_brf(tmp_path)
    _run_main(monkeypatch, ["convert", str(brf), "--verbose"])

    captured = capsys.readouterr()
    assert "Detected encoding: unicode" in captured.err
    assert "Token: NOTE" in captured.err
    # The rendered LilyPond must still be the only thing on stdout -- a
    # composer piping `dottednotes convert piece.brf --verbose | lilypond -`
    # must not have the trace corrupt the piped source.
    assert "Token:" not in captured.out
    assert "Detected encoding" not in captured.out
    assert r'\version' in captured.out


def test_convert_verbose_prints_beat_count_warning(monkeypatch, tmp_path, capsys):
    # _SIMPLE_BRF is a 4/4 measure with a single quarter note -- 1 of 4
    # beats -- which triggers the existing beat-count validation warning.
    brf = _write_simple_brf(tmp_path)
    _run_main(monkeypatch, ["convert", str(brf), "--verbose"])

    captured = capsys.readouterr()
    assert "Warning: Measure 1: expected 4.0 beats but counted 1.0" in captured.err
    # Verbose mode replaces Python's default warning formatting with its
    # own clean line -- the default "path:line: UserWarning: ..." format
    # must not also leak through.
    assert "UserWarning" not in captured.err


def test_convert_without_verbose_omits_trace(monkeypatch, tmp_path, capsys):
    brf = _write_simple_brf(tmp_path)
    _run_main(monkeypatch, ["convert", str(brf)])

    captured = capsys.readouterr()
    assert "Detected encoding" not in captured.err
    assert "Token:" not in captured.err


# --- Regression: real fixtures, both ends of the ensemble/solo dispatch ---


def test_convert_fengyang_produces_real_multi_staff_score(monkeypatch, tmp_path, capsys):
    # S7-2's core bug fix: cli.py used to load input via a raw pass-through
    # that never normalized ASCII braille to Unicode, so this ASCII-encoded,
    # real BANA-orchestral-convention fixture silently produced an empty
    # \version-only file. Must now produce a real 6-instrument score.
    brf = FIXTURES / "fengyang_flower_drum.brf"
    out = tmp_path / "fengyang.ly"
    _run_main(monkeypatch, ["convert", str(brf), str(out)])

    content = out.read_text(encoding="utf-8")
    assert 'instrumentName = "Flute"' in content
    assert 'instrumentName = "Violin I"' in content
    assert content.count("Music = \\relative") >= 6


def test_convert_fingering_melody_not_misrouted_to_ensemble_parser(
    monkeypatch, tmp_path, capsys
):
    # Second bug found while smoke-testing the fix above: the same
    # WORD_SIGN/END_WORD_SIGN dispatch heuristic false-positived on this
    # real two-hand piano piece's hand-sign-prefixed lines, wrongly
    # routing it to EnsembleParser, which crashed with "No parallel
    # systems found in ensemble score." Must now succeed via the solo
    # parser and produce a two-staff PianoStaff, not an ensemble score.
    brf = FIXTURES / "fingering_melody.brf"
    out = tmp_path / "fingering_melody.ly"
    _run_main(monkeypatch, ["convert", str(brf), str(out)])

    content = out.read_text(encoding="utf-8")
    assert r'\new PianoStaff <<' in content
    assert content.count(r'\new Staff {') == 2
    assert "instrumentName" not in content  # not an OrchestraScore
