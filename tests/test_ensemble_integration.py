from __future__ import annotations

import pytest

from dottednotes.parser.ensemble_parser import EnsembleParser
from dottednotes.parser.input_pipeline import BRLInputPipeline
from dottednotes.models.note import Note

from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"


def test_bartok_smoke_parses_without_crashing():
    """Smoke test only (S5b-9) -- this fixture is not developer-verified
    ground truth (per S5b-8's own Senior note), so this checks structural
    parsing (staff count, measure count, non-empty content), not exact
    pitches/rhythms against a reference score.

    Bartok_Bella_Romanian_Folk_Dances_for_Orchestra.brl was auto-
    transcribed by Sao Mai Braille software using a measure-numbering
    convention that only partially overlaps with the BANA Sec. 33.4.6
    standalone-line convention EnsembleParser already supported (added for
    Fengyang): Sao Mai's header lines can list several measure numbers
    together on one physical line (e.g. multiple NUMBER_SIGN-prefixed
    digit groups spaced across the line), rather than exactly one number
    alone per line. EnsembleParser now recognizes that convention too
    (`extract_all_measure_numbers`), column-slicing every content line
    that follows such a header at the same marker positions.
    """
    pipeline = BRLInputPipeline()
    text = pipeline.load(FIXTURES / "Bartok_Bella_Romanian_Folk_Dances_for_Orchestra.brl")
    score = EnsembleParser().parse(text)

    # Leading word only -- some of these instrument names contain
    # punctuation ("I&II") that a separate, pre-existing gap in
    # decode_literary_braille doesn't decode (renders as "?"); that gap is
    # unrelated to S5b-9's measure-numbering scope, so this only checks
    # enough of each name to confirm instrument identity/order survived.
    expected_first_words = [
        "Piccolo?",
        "Clarinets",
        "Bassoons",
        "Horns",
        "Violins",
        "Violins",
        "Violas",
        "Violoncellos",
        "Double",
    ]
    assert len(score.staves) == len(expected_first_words)
    for staff, expected_first_word in zip(score.staves, expected_first_words):
        assert staff.name.split()[0] == expected_first_word
        assert len(staff.measures) == 247

# Tchaikovsky_String_Quartet_No_1_with_header.brf and its test
# (test_tchaikovsky_quartet_header_is_found_and_parsing_reaches_real_music)
# have been removed from tests/fixtures/ entirely, for the same reason as
# the Beethoven/Faure removal noted below: the new Sec. 33.4.6/22.3
# end-word-sign validation (EnsembleParser._line_missing_end_word_sign)
# found 5 separate lines (indented continuation lines opening with an
# unterminated ">c"/">d" word-sign, very plausibly truncated "cresc."/
# "dim." markings) with no closing end-word-sign anywhere in the line --
# a systematic transcription gap in this externally-sourced fixture, not
# an isolated typo. Per the developer, don't guess at what the missing
# text/boundary should have been; drop the fixture instead. Do not
# re-introduce tests against it without the developer's go-ahead.


def test_bear_under_the_floorboard_no_empty_measures_or_spurious_key_changes():
    """Regression for a user-reported bug: several instrument lines in
    this fixture drift by more than the usual one-cell marker/content
    offset in the measures-38-45 region (e.g. Double Bass's measure 44
    content sits 4 cells before its own marker). Naive column slicing
    merged a note into the wrong measure as unrecoverable "overflow",
    starving a BANA tied-continuation measure (just an augmentation dot
    + tie, no restated pitch) of its only content. That measure's
    braille_parser.py `pending` list ended up empty, so no Measure object
    was created at all and the measure-number counter never advanced --
    desyncing every later measure number for that instrument until
    EnsembleParser's own measure-reconciliation fell back to an empty,
    key-signature-0 placeholder. That showed up as a spurious mid-piece
    `\\key c \\major` and empty measures 41-45 in the converted LilyPond,
    at a point that differed per instrument.
    """
    pipeline = BRLInputPipeline()
    text = pipeline.load(FIXTURES / "The_Bear_Under_the_Floorboard_Week_3.brf")
    score = EnsembleParser().parse(text)

    for staff in score.staves:
        assert len(staff.measures) == 43, f"{staff.name} has {len(staff.measures)} measures, expected 43"
        assert all(m.notes for m in staff.measures), (
            f"{staff.name} has empty measure(s): "
            f"{[m.number for m in staff.measures if not m.notes]}"
        )
        assert len({m.key_signature for m in staff.measures}) == 1, (
            f"{staff.name} has inconsistent key signatures: "
            f"{sorted({(m.number, m.key_signature) for m in staff.measures})}"
        )

    db = next(s for s in score.staves if s.name == "Double bass")
    tail_pitches = [
        n.note_name
        for m in db.measures[-8:]
        for n in m.notes
        if isinstance(n, Note)
    ]
    assert tail_pitches == ["G", "G", "A", "G", "E", "A", "G", "F"]


# Beethoven_Ludwig_Van_String_Quartet_No_1-1.brf and
# Faure_Gabriel_Morceau_de_Concours.brf have been removed from tests/fixtures/
# entirely: per the developer, these two fixtures don't adhere to BANA
# conventions, so they aren't reliable smoke-test material. Do not
# re-introduce tests against them without the developer's go-ahead.


def test_percussion_ensemble_parses_and_renders_drummode():
    """End-to-end unpitched-percussion pipeline test (BANA Ch. 34): a
    Sec. 33.2 instrument-list header naming "Snare drum"/"Bass drum"
    (Table 29 abbreviations sdr/bdr), followed by per-line content in the
    same ensemble format every other instrument already uses. No parser
    changes were needed for this to work -- BANA writes percussion notes
    with ordinary letter+octave+duration cells (Sec. 34.2.1/34.2.2), so
    EnsembleParser/BrailleParser already produced valid Note/Rest objects
    for these lines; the only new code is at the classification/rendering
    layer (instrument.is_unpitched_percussion/get_drum_note_name,
    Staff.to_lilypond_drummode(), OrchestraScore's DrumStaff branch).

    See tests/fixtures/README.md for how this fixture was generated
    (BrailleRenderer -> unicode_to_ascii_braille, round-trip verified, not
    hand-transcribed).
    """
    pipeline = BRLInputPipeline()
    text = pipeline.load(FIXTURES / "percussion_ensemble_snare_bass_drum.brf")
    score = EnsembleParser().parse(text)

    assert [s.name for s in score.staves] == ["Snare drum", "Bass drum"]
    assert len(score.staves[0].measures) == 2
    assert len(score.staves[1].measures) == 2

    ly = score.to_lilypond()
    assert "\\new DrumStaff" in ly
    assert "\\new Staff \\with" not in ly
    assert "sn4 sn4 sn4 sn4 |" in ly
    assert "bd2 r2 |" in ly
    assert "\\relative" not in ly
    assert "\\clef" not in ly


def test_percussion_ensemble_lilypond_output_compiles_cleanly(tmp_path):
    import shutil
    import subprocess

    if not shutil.which("lilypond"):
        pytest.skip("lilypond binary not installed")

    pipeline = BRLInputPipeline()
    text = pipeline.load(FIXTURES / "percussion_ensemble_snare_bass_drum.brf")
    score = EnsembleParser().parse(text)
    ly_output = score.to_lilypond()

    ly_file = tmp_path / "percussion_ensemble.ly"
    ly_file.write_text(ly_output, encoding="utf-8")
    result = subprocess.run(
        ["lilypond", "-o", str(tmp_path / "percussion_ensemble"), str(ly_file)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"lilypond compile failed:\n{result.stdout}\n{result.stderr}"
    assert "warning" not in (result.stdout + result.stderr).lower()
    pdf_path = tmp_path / "percussion_ensemble.pdf"
    assert pdf_path.exists() and pdf_path.stat().st_size > 0
