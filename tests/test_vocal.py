import shutil
import subprocess
from pathlib import Path

import pytest
from dottednotes.models import Score, Staff, Note, Duration
from dottednotes.parser.ensemble_parser import EnsembleParser, parse_lyrics
from dottednotes.parser.input_pipeline import BRLInputPipeline
from dottednotes.models.instrument import InstrumentFamily, get_instrument_family

FIXTURES = Path(__file__).parent / "fixtures"


def test_vocal_instrument_family():
    assert get_instrument_family("Soprano") == InstrumentFamily.VOCAL
    assert get_instrument_family("Alto") == InstrumentFamily.VOCAL
    assert get_instrument_family("Tenor") == InstrumentFamily.VOCAL
    assert get_instrument_family("Bass") == InstrumentFamily.VOCAL
    assert get_instrument_family("Voice") == InstrumentFamily.VOCAL
    assert get_instrument_family("Vocal") == InstrumentFamily.VOCAL


def test_parse_lyrics_simple():
    # "ho-ly" in braille is ⠓⠕⠤⠇⠽ (h-o-hyphen-l-y)
    # capital indicator is ⠠ (dot 6)
    # "9" is ⠔ (dots 3-5)
    # let's test: "⠠⠓⠕⠤⠇⠽⠀⠔" -> "Ho-ly", "Ho-ly"
    cells = "⠠⠓⠕⠤⠇⠽⠀⠔"
    syllables = parse_lyrics(cells)
    
    assert syllables == [
        ("Ho", True),
        ("ly", False),
        ("Ho", True),
        ("ly", False),
    ]


def test_parse_lyrics_capitals_and_spaces():
    # UEB capitals: ,sing -> Sing; ,,song -> SONG
    # ⠠⠎⠊⠝⠛⠀⠠⠠⠎⠕⠝⠛ -> ,sing ,,song
    cells = "⠠⠎⠊⠝⠛⠀⠠⠠⠎⠕⠝⠛"
    syllables = parse_lyrics(cells)
    assert syllables == [
        ("Sing", False),
        ("SONG", False),
    ]


def test_vocal_lyrics_mapping_integration():
    # A simple vocal + piano accompaniment BRF score. Per BANA Sec. 35.1/37.2,
    # a single voice's word line has *no* instrument abbreviation at all --
    # it's plain literary text at the margin, immediately followed by the
    # voice's ordinary WORD_SIGN-abbreviated music line (same §33.2 shape as
    # any other instrument's abbreviation).
    brf_text = (
        "⠠⠎⠕⠏⠗⠁⠝⠕⠀⠀⠀⠜⠎⠄\n"
        "⠠⠏⠊⠁⠝⠕⠀⠀⠀⠜⠏⠄\n"
        "\n"
        "⠼⠁\n"
        "⠠⠓⠕⠤⠇⠽⠀⠔\n"
        "⠜⠎⠄⠀⠐⠽⠉⠐⠵⠐⠯\n"
        "⠜⠏⠄⠀⠐⠽⠐⠵⠐⠯\n"
    )
    score = EnsembleParser().parse(brf_text)
    
    assert len(score.staves) == 2
    soprano_staff = score.staves[0]
    piano_staff = score.staves[1]
    
    assert soprano_staff.name == "Soprano"
    assert piano_staff.name == "Piano"
    
    # Soprano staff should have lyrics parsed and mapped
    # C4(slur) D4, E4 -> Group 1: [C4, D4], Group 2: [E4]
    # Syllables: Ho-ly, Ho-ly
    # Groups match to: "Ho --", "ly"
    assert soprano_staff.lyrics == ["Ho --", "ly"]
    
    # LilyPond output check
    ly_output = score.to_lilypond()
    
    # Check that Soprano staff uses \new Staff \with { ... } << \new Voice ... \new Lyrics \lyricsto ... >>
    assert '} <<' in ly_output
    assert '\\new Voice = "vocals_soprano"' in ly_output
    assert '\\new Lyrics \\lyricsto "vocals_soprano" { Ho -- ly }' in ly_output
    # Check that Piano staff uses standard \new Staff \with { ... } { ... }
    assert '} {' in ly_output


# ---------------------------------------------------------------------------
# S7b-9: real-fixture integration test -- vocal_test.brf (Soprano + Piano
# Right Hand + Piano Left-Hand, an art-song-shaped score with lyrics, a
# crescendo/decrescendo pair, and a whole-measure repeat sign that carries
# its own new dynamic marking) parses end to end, groups its staves into
# the right InstrumentFamily, associates lyrics with the soprano line, and
# -- per CLAUDE.md's "check the compile log for warnings, not just the exit
# code" testing philosophy -- transcribes to LilyPond that compiles with the
# real lilypond binary with zero warnings. Mirrors the tmp_path/skip-if
# pattern already established in test_lilypond_formatter.py's
# _compile_and_check_no_warnings for the other three formatting categories.
# ---------------------------------------------------------------------------


def test_vocal_test_fixture_groups_staves_and_maps_lyrics():
    text = BRLInputPipeline().load(FIXTURES / "vocal_test.brf")
    score = EnsembleParser().parse(text)

    assert [s.name for s in score.staves] == [
        "Soprano",
        "Piano Right Hand",
        "Piano Left-Hand",
    ]
    assert get_instrument_family("Soprano") == InstrumentFamily.VOCAL
    assert get_instrument_family("Piano Right Hand") == InstrumentFamily.KEYBOARD_HARP
    assert get_instrument_family("Piano Left-Hand") == InstrumentFamily.KEYBOARD_HARP

    soprano_staff, piano_right_staff, piano_left_staff = score.staves
    assert soprano_staff.lyrics[:2] == ["Let", "me"]
    assert soprano_staff.lyrics[-1] == "hope."
    # "flo-wers" carries a BANA syllabic slur -- rendered as a lyric
    # continuation ("flo --") so LilyPond draws the syllable-joining line.
    assert "flo --" in soprano_staff.lyrics
    assert piano_right_staff.lyrics == []
    assert piano_left_staff.lyrics == []


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


def test_vocal_test_fixture_matches_ground_truth():
    text = BRLInputPipeline().load(FIXTURES / "vocal_test.brf")
    score = EnsembleParser().parse(text)

    ly_output = score.to_lilypond()
    ground_truth = (FIXTURES / "vocal_test.ly").read_text(encoding="utf-8")
    assert ly_output == ground_truth


def test_vocal_test_fixture_compiles_cleanly(tmp_path: Path):
    if not shutil.which("lilypond"):
        pytest.skip("lilypond binary not found; skipping compile test")

    text = BRLInputPipeline().load(FIXTURES / "vocal_test.brf")
    score = EnsembleParser().parse(text)

    ly_output = score.to_lilypond()
    assert '\\new Voice = "vocals_soprano"' in ly_output
    assert '\\new Lyrics \\lyricsto "vocals_soprano"' in ly_output

    _compile_and_check_no_warnings(ly_output, tmp_path, "vocal_test")


def test_parse_strophic_multiverse_lyrics_and_refrain():
    # Soprano instrument abbreviation is ⠜⠎⠄ (\x1cs.)
    # We will provide:
    # Verse 1 text: ⠶⠼⠁⠶⠀⠠⠓⠕⠤⠇⠽ (brackets around number 1, then "Ho-ly")
    # Verse 2 text: ⠶⠼⠃⠶⠀⠠⠛⠇⠕⠤⠗⠽ (brackets around number 2, then "Glo-ry")
    # Soprano music line
    # Then a second system representing a refrain:
    # Refrain text: ⠠⠗⠑⠋⠗⠁⠊⠝⠀⠠⠁⠤⠍⠑⠝ ("Refrain A-men")
    # Soprano music line
    brf_text = (
        "⠠⠎⠕⠏⠗⠁⠝⠕⠀⠀⠀⠜⠎⠄\n"
        "\n"
        "⠼⠁\n"
        "⠶⠼⠁⠶⠀⠠⠓⠕⠤⠇⠽\n"
        "⠶⠼⠃⠶⠀⠠⠛⠇⠕⠤⠗⠽\n"
        "⠜⠎⠄⠀⠐⠽⠉⠐⠵⠐⠯\n"
        "\n"
        "⠼⠃\n"
        "⠠⠗⠑⠋⠗⠁⠊⠝⠀⠠⠁⠤⠍⠑⠝\n"
        "⠜⠎⠄⠀⠐⠽⠉⠐⠵⠐⠯\n"
    )
    
    score = EnsembleParser().parse(brf_text)
    assert len(score.staves) == 1
    staff = score.staves[0]
    
    assert staff.name == "Soprano"
    assert len(staff.verses) == 2
    
    # Verse 1: "Ho --", "ly", "A --", "men"
    # Verse 2: "Glo --", "ry", "A --", "men"
    # (Since system 2 is a single refrain line, it is replicated across all verses)
    assert staff.verses[0] == ['\\set stanza = "1. " Ho --', 'ly', '\\set stanza = "Refrain. " A --', 'men']
    assert staff.verses[1] == ['\\set stanza = "2. " Glo --', 'ry', '\\set stanza = "Refrain. " A --', 'men']
    
    assert staff.verse_prefixes == ["1.", "2."]
    
    ly_output = score.to_lilypond()
    
    # Verify that the stanzas and stacked lyrics are output correctly
    assert '\\set stanza = "1. " Ho -- ly \\set stanza = "Refrain. " A -- men' in ly_output
    assert '\\set stanza = "2. " Glo -- ry \\set stanza = "Refrain. " A -- men' in ly_output
    assert '\\new Lyrics \\lyricsto "vocals_soprano"' in ly_output
    assert ly_output.count('\\new Lyrics \\lyricsto') == 2


def test_parse_strophic_with_word_number_verse_prefixes():
    # Let's test a plain number sign like ⠼⠁ (without brackets) at the start of a verse line.
    # ⠼⠁⠀⠠⠓⠕⠤⠇⠽ -> 1. Ho-ly
    # ⠼⠃⠀⠠⠛⠇⠕⠤⠗⠽ -> 2. Glo-ry
    brf_text = (
        "⠠⠎⠕⠏⠗⠁⠝⠕⠀⠀⠀⠜⠎⠄\n"
        "\n"
        "⠼⠁\n"
        "⠼⠁⠀⠠⠓⠕⠤⠇⠽\n"
        "⠼⠃⠀⠠⠛⠇⠕⠤⠗⠽\n"
        "⠜⠎⠄⠀⠐⠽⠉⠐⠵⠐⠯\n"
    )
    score = EnsembleParser().parse(brf_text)
    staff = score.staves[0]
    
    assert staff.verse_prefixes == ["1.", "2."]
    assert staff.verses[0] == ['\\set stanza = "1. " Ho --', 'ly']
    assert staff.verses[1] == ['\\set stanza = "2. " Glo --', 'ry']
    
    ly_output = score.to_lilypond()
    assert '\\set stanza = "1. " Ho -- ly' in ly_output
    assert '\\set stanza = "2. " Glo -- ry' in ly_output
