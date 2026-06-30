from pathlib import Path

import pytest

from dottednotes.models import Score
from dottednotes.parser import BRLInputPipeline, BrailleParser, InputPipeline


def test_braille_parser_returns_score():
    score = BrailleParser().parse("")
    assert isinstance(score, Score)


def test_braille_parser_empty_input_empty_score():
    score = BrailleParser().parse("")
    assert score.staves == []


def test_input_pipeline_read(tmp_path: Path):
    brf = tmp_path / "sample.brf"
    brf.write_text("⠀⠼⠙⠲", encoding="utf-8")
    pipeline = InputPipeline(brf)
    assert pipeline.read() == "⠀⠼⠙⠲"


def test_input_pipeline_lines(tmp_path: Path):
    brf = tmp_path / "sample.brf"
    brf.write_text("line one\nline two", encoding="utf-8")
    pipeline = InputPipeline(brf)
    assert pipeline.lines() == ["line one", "line two"]


def test_input_pipeline_missing_file():
    pipeline = InputPipeline("/nonexistent/path.brf")
    with pytest.raises(FileNotFoundError):
        pipeline.read()


# --- BRLInputPipeline tests ---

FIXTURES = Path(__file__).parent / "fixtures"


def test_brl_detect_unicode_encoding():
    pipeline = BRLInputPipeline()
    assert pipeline._detect_encoding("⠁⠃") == "unicode"


def test_brl_detect_ascii_encoding():
    pipeline = BRLInputPipeline()
    assert pipeline._detect_encoding("ABC") == "ascii"


def test_brl_detect_unknown_encoding():
    pipeline = BRLInputPipeline()
    assert pipeline._detect_encoding("   \n  ") == "unknown"


def test_brl_ascii_to_unicode_dot1():
    # 'A' in BRF = dot 1 = U+2801
    pipeline = BRLInputPipeline()
    assert pipeline._ascii_to_unicode("A") == "⠁"


def test_brl_ascii_to_unicode_number_sign():
    # '#' in BRF = dots 3,4,5,6 = U+283C
    pipeline = BRLInputPipeline()
    assert pipeline._ascii_to_unicode("#") == "⠼"


def test_brl_ascii_to_unicode_preserves_newlines():
    pipeline = BRLInputPipeline()
    result = pipeline._ascii_to_unicode("A\nB")
    assert result == "⠁\n⠃"


def test_brl_same_content_both_encodings():
    # ASCII 'A' and Unicode U+2801 both represent dot 1 (braille C quarter note).
    pipeline = BRLInputPipeline()
    ascii_result = pipeline._ascii_to_unicode("A")
    assert ascii_result == "⠁"


def test_brl_load_unicode_file(tmp_path: Path):
    brf = tmp_path / "sample.brf"
    brf.write_text("⠁⠃", encoding="utf-8")
    pipeline = BRLInputPipeline()
    result = pipeline.load(brf)
    assert result == "⠁⠃"


def test_brl_load_ascii_file(tmp_path: Path):
    brf = tmp_path / "sample.brf"
    brf.write_text("AB", encoding="utf-8")
    pipeline = BRLInputPipeline()
    result = pipeline.load(brf)
    assert result == "⠁⠃"


def test_brl_load_missing_file():
    pipeline = BRLInputPipeline()
    with pytest.raises(FileNotFoundError):
        pipeline.load("/nonexistent/path.brf")


def test_brl_load_fengyang_fixture():
    pipeline = BRLInputPipeline()
    result = pipeline.load(FIXTURES / "fengyang_flower_drum.brf")
    assert isinstance(result, str)
    assert len(result) > 0
