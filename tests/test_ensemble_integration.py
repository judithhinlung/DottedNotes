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

def test_tchaikovsky_quartet_header_is_found_and_parsing_reaches_real_music():
    """Tchaikovsky_String_Quartet_No_1_with_header.brf originally had no
    genuine BANA Sec. 33.2 instrument-list header at all -- it went
    straight from the title into per-line abbreviation-prefixed music
    (v1'/v2'/vl'/vc'). Before the bounded instrument-list scan
    (EnsembleParser.parse()), the old unbounded loop wandered deep into
    the piece and silently produced a single fake staff with a collapsed
    whole-piece rest, dropping 3 of the 4 real parts with no error at all.

    The fixture now has a real Sec. 33.2 header added (Violin I/II, Viola,
    Violoncello, using Table 29's verified abbreviations), so parsing
    correctly finds it and proceeds into real per-instrument content --
    this test locks that in. Full parsing still doesn't succeed, but for
    an entirely separate, pre-existing reason unrelated to this fixture's
    header: the cello part's pizzicato ostinato uses a genuine BANA Sec.
    19 numeral-repeat sign (`>vc'_:99e.c7.ce_8e9c7 7`, the trailing "7"),
    a real BANA feature this codebase doesn't implement yet
    (`NumeralRepeatError`'s own docstring: "layout-specific, involve
    parsing complexity this parser does not implement" -- a documented
    scope boundary, not a bug). Asserting that specific, later error
    (rather than the old "no instrument list header found" one) proves
    the header bug is fixed without claiming full parsing works.
    """
    from dottednotes.parser.braille_parser import NumeralRepeatError

    pipeline = BRLInputPipeline()
    text = pipeline.load(FIXTURES / "Tchaikovsky_String_Quartet_No_1_with_header.brf")
    with pytest.raises(NumeralRepeatError, match="numeral repeats"):
        EnsembleParser().parse(text)


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
    text = pipeline.load(FIXTURES / "The Bear Under the Floorboard Week 3.brf")
    score = EnsembleParser().parse(text)

    for staff in score.staves:
        assert len(staff.measures) == 45, f"{staff.name} has {len(staff.measures)} measures, expected 45"
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
        for m in db.measures[37:45]
        for n in m.notes
        if isinstance(n, Note)
    ]
    assert tail_pitches == ["G", "G", "A", "G", "E", "A", "G", "F"]


# Beethoven_Ludwig_Van_String_Quartet_No_1-1.brf and
# Faure_Gabriel_Morceau_de_Concours.brf have been removed from tests/fixtures/
# entirely: per the developer, these two fixtures don't adhere to BANA
# conventions, so they aren't reliable smoke-test material. Do not
# re-introduce tests against them without the developer's go-ahead.
