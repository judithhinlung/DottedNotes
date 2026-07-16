import shutil
import subprocess
import warnings
from pathlib import Path

import pytest
from dottednotes.parser.ensemble_parser import EnsembleParser
from dottednotes.parser.input_pipeline import BRLInputPipeline

FIXTURES = Path(__file__).parent / "fixtures"


def _compile_and_check_no_warnings(ly_output: str, tmp_path: Path, basename: str) -> Path:
    """Write `ly_output` to `tmp_path`, compile it with the real `lilypond`
    binary (no --silent, so its full log is available), assert success and
    a non-empty PDF, and assert the compile log contains no "warning" text
    -- a clean exit code alone doesn't mean LilyPond was happy with the
    engraving. Returns the produced PDF path for optional manual review.
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


def test_strophic_fixture_parses_without_warnings():
    text = BRLInputPipeline().load(FIXTURES / "strophic_song_test.brf")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        EnsembleParser().parse(text)
    assert not caught, [str(w.message) for w in caught]


def test_strophic_fixture_verses_and_refrain_match_expected():
    text = BRLInputPipeline().load(FIXTURES / "strophic_song_test.brf")
    score = EnsembleParser().parse(text)

    soprano_staff = next(s for s in score.staves if s.name == "Soprano")
    assert soprano_staff.verse_prefixes == ["1.", "2."]
    # Verse 1's "Ho --" and verse 2's "Glo --" each carry a syllabic slur
    # across the melody's first two notes (a melisma: one syllable held
    # over two notes), and both verses share the same "A -- men" refrain,
    # replicated from the second (unprefixed) system. The verse-number
    # prefix lives only in verse_prefixes, not baked into the first
    # syllable -- rendering adds the `\set stanza` directive exactly once
    # (S8b-13).
    assert soprano_staff.verses[0] == ['Ho --', 'ly', 'A --', 'men']
    assert soprano_staff.verses[1] == ['Glo --', 'ry', 'A --', 'men']


def test_strophic_fixture_matches_ground_truth_ly():
    text = BRLInputPipeline().load(FIXTURES / "strophic_song_test.brf")
    score = EnsembleParser().parse(text)

    ly_output = score.to_lilypond()
    ground_truth = (FIXTURES / "strophic_song_test.ly").read_text(encoding="utf-8")
    assert ly_output == ground_truth
    # S8b-13 regression check: each verse's stanza directive must appear
    # exactly once -- a full-string equality check above would already
    # catch a doubled directive, but an explicit count makes the intent
    # unambiguous rather than relying on incidental ground-truth wording.
    assert ly_output.count('\\set stanza = "1. "') == 1
    assert ly_output.count('\\set stanza = "2. "') == 1


def test_strophic_fixture_compiles_cleanly(tmp_path: Path):
    if not shutil.which("lilypond"):
        pytest.skip("lilypond binary not found; skipping compile test")

    text = BRLInputPipeline().load(FIXTURES / "strophic_song_test.brf")
    score = EnsembleParser().parse(text)

    ly_output = score.to_lilypond()
    assert '\\new Voice = "vocals_soprano"' in ly_output
    assert '\\new Lyrics \\lyricsto "vocals_soprano"' in ly_output

    _compile_and_check_no_warnings(ly_output, tmp_path, "strophic_song_test")
