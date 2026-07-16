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


# --- S7b-10: category and formatting overrides ---


def test_cli_convert_valid_category_applies(monkeypatch, tmp_path):
    brf = _write_simple_brf(tmp_path)
    out = tmp_path / "category_solo.ly"
    # By default, a 1-staff score is Solo Piano, which has staff size 20.0
    # Let's override category to Chamber, which has staff size 16.0
    _run_main(monkeypatch, ["convert", str(brf), str(out), "--category", "Chamber"])

    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert "set-global-staff-size 16.0" in content


def test_cli_convert_invalid_category_exits_nonzero(monkeypatch, tmp_path, capsys):
    brf = _write_simple_brf(tmp_path)

    with pytest.raises(SystemExit) as exc_info:
        _run_main(monkeypatch, ["convert", str(brf), "--category", "InvalidCategory"])
    assert exc_info.value.code == 1

    captured = capsys.readouterr()
    assert "Error: Invalid category: 'InvalidCategory'" in captured.err
    assert "Traceback" not in captured.err


def test_cli_convert_valid_format_overrides(monkeypatch, tmp_path):
    brf = _write_simple_brf(tmp_path)
    out = tmp_path / "format_overridden.ly"
    _run_main(
        monkeypatch,
        [
            "convert",
            str(brf),
            str(out),
            "--format",
            "paper_size=a4,margin_mm=10,staff_size=15.5,basic_distance=11.2,padding=1.5",
        ],
    )

    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert 'set-paper-size "a4"' in content
    assert "top-margin = 10.0\\mm" in content
    assert "set-global-staff-size 15.5" in content
    assert "basic-distance . 11.2" in content
    assert "padding . 1.5" in content


def test_cli_convert_invalid_format_keys_exits_nonzero(monkeypatch, tmp_path, capsys):
    brf = _write_simple_brf(tmp_path)

    # 1. Unknown key
    with pytest.raises(SystemExit) as exc_info:
        _run_main(monkeypatch, ["convert", str(brf), "--format", "unknown_key=10"])
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Unknown/invalid format key: 'unknown_key'" in captured.err

    # 2. Invalid float value
    with pytest.raises(SystemExit) as exc_info:
        _run_main(monkeypatch, ["convert", str(brf), "--format", "margin_mm=not_float"])
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Invalid float value for margin_mm: 'not_float'" in captured.err

    # 3. Malformed format option (missing `=`)
    with pytest.raises(SystemExit) as exc_info:
        _run_main(monkeypatch, ["convert", str(brf), "--format", "margin_mm"])
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Must be in key=value format" in captured.err


def test_cli_convert_lead_sheet_category_routes_to_lead_sheet_parser(monkeypatch, tmp_path):
    # S8b-5 follow-up: --category "Lead Sheet" routes _parse_score() through
    # parse_lead_sheet() (BANA Sec. 27's two-line melody/chord-symbol
    # parallel) instead of the normal solo/ensemble dispatch. Whole notes
    # C/D/E/F paired with C/Dm/Em/F chord symbols -- same fixture verified
    # against a real `lilypond` compile in test_chord_symbols.py.
    music = '⠽⠀⠵⠀⠯⠀⠿⠣⠅'   # whole notes C D E F (blank-cell bar lines between), final double bar
    chords = '⠠⠉⠠⠙⠍⠠⠑⠍⠠⠋'  # ,C ,DM ,EM ,F
    brf = tmp_path / "lead_sheet.brf"
    brf.write_text(music + '\n' + chords + '\n', encoding="utf-8")
    out = tmp_path / "lead_sheet.ly"

    _run_main(monkeypatch, ["convert", str(brf), str(out), "--category", "Lead Sheet"])

    content = out.read_text(encoding="utf-8")
    assert "\\new ChordNames" in content
    assert "\\chordmode { c1 d1:m e1:m f1 }" in content


def test_cli_convert_lead_sheet_category_on_non_lead_sheet_input_errors(monkeypatch, tmp_path, capsys):
    # A single physical line isn't a valid two-line melody/chord parallel --
    # parse_lead_sheet()'s own validation should surface as a plain-text
    # CLI error, not a traceback.
    brf = tmp_path / "single_line.brf"
    brf.write_text('⠐⠹\n', encoding="utf-8")

    with pytest.raises(SystemExit) as exc_info:
        _run_main(monkeypatch, ["convert", str(brf), "--category", "Lead Sheet"])
    assert exc_info.value.code == 1

    captured = capsys.readouterr()
    assert captured.err.startswith("Error:")
    assert "Traceback" not in captured.err


def test_cli_convert_category_override_affects_lyrics_parsing(monkeypatch, tmp_path):
    # A simple vocal + piano accompaniment BRF score, same as in test_vocal.py
    brf_text = (
        "⠠⠎⠕⠏⠗⠁⠝⠕⠀⠀⠀⠜⠎⠄\n"
        "⠠⠏⠊⠁⠝⠕⠀⠀⠀⠜⠏⠄\n"
        "\n"
        "⠼⠁\n"
        "⠠⠓⠕⠤⠇⠽⠀⠔\n"
        "⠜⠎⠄⠀⠐⠽⠉⠐⠵⠐⠯\n"
        "⠜⠏⠄⠀⠐⠽⠐⠵⠐⠯\n"
    )
    brf = tmp_path / "vocal.brf"
    brf.write_text(brf_text, encoding="utf-8")

    # 1. Normal conversion: Soprano is VOCAL, so lyrics are parsed and mapped
    out_default = tmp_path / "vocal_default.ly"
    _run_main(monkeypatch, ["convert", str(brf), str(out_default)])
    content_default = out_default.read_text(encoding="utf-8")
    assert "\\new Lyrics \\lyricsto" in content_default

    # 2. Overridden conversion to "Chamber" (non-vocal category override)
    # This should skip/suppress lyrics parsing and mapping, and not emit lyrics in output
    out_override = tmp_path / "vocal_chamber.ly"
    _run_main(monkeypatch, ["convert", str(brf), str(out_override), "--category", "Chamber"])
    content_override = out_override.read_text(encoding="utf-8")
    assert "\\new Lyrics" not in content_override


# --- S7-5: End-to-end test ---


@pytest.mark.skipif(shutil.which("lilypond") is None, reason="lilypond not installed")
def test_e2e_conversion(monkeypatch, tmp_path):
    input_brf = FIXTURES / "fengyang_flower_drum.brf"
    output_ly = tmp_path / "fengyang_flower_drum.ly"

    # 1. Run conversion with --compile flag
    _run_main(monkeypatch, ["convert", str(input_brf), str(output_ly), "--compile"])

    # 2. Assert output files exist and are non-empty
    assert output_ly.exists()
    assert output_ly.stat().st_size > 0

    output_pdf = tmp_path / "fengyang_flower_drum.pdf"
    output_midi = tmp_path / "fengyang_flower_drum.midi"

    assert output_pdf.exists()
    assert output_pdf.stat().st_size > 0
    assert output_midi.exists()
    assert output_midi.stat().st_size > 0


def test_cli_report_option(monkeypatch, tmp_path, capsys):
    brf_file = tmp_path / "test_report.brf"
    brf_file.write_text("⠐⠹⠞", encoding="utf-8")
    _run_main(monkeypatch, ["convert", str(brf_file), "--report"])
    captured = capsys.readouterr()
    assert "Line 1: Measure 1: Missing octave mark" in captured.err


def test_cli_report_line_length_correction_has_no_measure_number(monkeypatch, tmp_path, capsys):
    # Line-length corrections (S9b-4) aren't tied to a specific measure, so the
    # report must not print a meaningless "Measure 0:" segment for them.
    brf_file = tmp_path / "test_report_long_line.brf"
    brf_file.write_text("⠐⠹" * 25, encoding="utf-8")  # 50 cells, over the 40-cell limit
    _run_main(monkeypatch, ["convert", str(brf_file), "--report"])
    captured = capsys.readouterr()
    assert "exceeds BANA column limit" in captured.err
    assert "Measure 0" not in captured.err


def test_cli_compression_option_writes_braille_output(monkeypatch, tmp_path, capsys):
    # A .brf/.brl output path switches `convert` to braille output; --compression
    # controls that render (it has no effect on the default .ly output).
    brf_file = tmp_path / "test_comp.brf"
    brf_file.write_text("⠐⠹", encoding="utf-8")
    out = tmp_path / "test_comp_out.brf"
    _run_main(monkeypatch, ["convert", str(brf_file), str(out), "--compression", "none"])
    captured = capsys.readouterr()
    assert "Error:" not in captured.err

    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert "⠹" in content
    assert r"\version" not in content
    assert r"\relative" not in content


def test_cli_compile_with_braille_output_errors(monkeypatch, tmp_path, capsys):
    brf_file = tmp_path / "test_comp.brf"
    brf_file.write_text("⠐⠹", encoding="utf-8")
    out = tmp_path / "test_comp_out.brf"

    with pytest.raises(SystemExit) as exc_info:
        _run_main(monkeypatch, ["convert", str(brf_file), str(out), "--compile"])
    assert exc_info.value.code != 0

    captured = capsys.readouterr()
    assert "Error: --compile requires LilyPond (.ly) output" in captured.err
    assert "Traceback" not in captured.err


def test_cli_profile_option(monkeypatch, tmp_path, capsys):
    brf_file = tmp_path / "test_cli_profile.brf"
    brf_file.write_text("⠐⠹⠀⠐⠹", encoding="utf-8")

    _run_main(monkeypatch, ["convert", str(brf_file), "--report", "--profile", "standard"])
    captured_std = capsys.readouterr()
    assert "identical to measure" not in captured_std.err

    _run_main(monkeypatch, ["convert", str(brf_file), "--report", "--profile", "strict"])
    captured_strict = capsys.readouterr()
    assert "identical to measure" in captured_strict.err


