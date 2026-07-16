import shutil
import subprocess
import warnings
from pathlib import Path

import pytest
from dottednotes.parser.input_pipeline import BRLInputPipeline
from dottednotes.parser.strophic_song_parser import parse_strophic_song

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
        parse_strophic_song(text)
    assert not caught, [str(w.message) for w in caught]


def test_strophic_fixture_verses_and_refrain_match_expected():
    text = BRLInputPipeline().load(FIXTURES / "strophic_song_test.brf")
    score = parse_strophic_song(text)

    staff = score.staves[0]
    # Verse 1 has no prefix (BANA 35.7: "The numeral 1 is not shown in the
    # braille even if it has been included in the print"); verse 2 (the
    # "<#b">" overflow block) is prefixed "2.".
    assert staff.verse_prefixes == [None, "2."]
    # Verse 1's own text ("Fly away oh my friend, Please go quickly.") is
    # followed by the refrain ("Go far away, please go far away."),
    # replicated onto verse 2's own text ("Everyone has gone to sleep,
    # Tarry no more.") via the bare trailing "REFRAIN" marker (BANA 35.7.2)
    # -- reusing the already-parsed refrain syllables, not re-parsing them.
    assert staff.verses[0] == [
        "Fly", "away", "oh", "my", "friend,",
        "Ple --", "ase", "go", "quickly.",
        "Go", "far", "away,", "please", "go", "far", "away.",
    ]
    assert staff.verses[1] == [
        "Everyone", "has", "gone", "to", "sleep,",
        "Tar --", "ry", "no", "more.",
        "Go", "far", "away,", "please", "go", "far", "away.",
    ]


def test_strophic_fixture_chords_match_expected():
    # Verse 1's two chord lines (Bb over "Fly away oh my friend," and
    # Bb/F7/Bb over "Please go quickly.") and the refrain's chord line
    # (Eb/Bb/Bb over "Go far away, please go far away.") -- BANA 36.1
    # aligns each chord's column to the syllable it's placed under, and
    # that syllable's position pairs 1:1 (BANA 35.1) with a melody note.
    text = BRLInputPipeline().load(FIXTURES / "strophic_song_test.brf")
    score = parse_strophic_song(text)

    chords = [
        (c.root, c.accidental, c.extensions) if c is not None else None
        for _, c in score.chord_names.entries
    ]
    assert chords == [
        ("B", "flat", []), ("B", "flat", []), None, None, None, None,
        ("F", None, [(7, None)]), None, None,
        ("B", "flat", []), None,
        ("E", "flat", []), ("B", "flat", []), ("B", "flat", []),
        None, None, None, None, None, None,
    ]


def test_strophic_fixture_matches_ground_truth_ly():
    text = BRLInputPipeline().load(FIXTURES / "strophic_song_test.brf")
    score = parse_strophic_song(text)

    ly_output = score.to_lilypond(category_override="Strophic Song")
    ground_truth = (FIXTURES / "strophic_song_test.ly").read_text(encoding="utf-8")
    assert ly_output == ground_truth


def test_strophic_fixture_compiles_cleanly(tmp_path: Path):
    if not shutil.which("lilypond"):
        pytest.skip("lilypond binary not found; skipping compile test")

    text = BRLInputPipeline().load(FIXTURES / "strophic_song_test.brf")
    score = parse_strophic_song(text)

    ly_output = score.to_lilypond(category_override="Strophic Song")
    assert '\\new ChordNames' in ly_output
    assert '\\new Lyrics \\lyricsto' in ly_output

    _compile_and_check_no_warnings(ly_output, tmp_path, "strophic_song_test")
