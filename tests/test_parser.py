from pathlib import Path

import pytest

from dottednotes.models import Score
from dottednotes.parser import BrailleParser, InputPipeline


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
