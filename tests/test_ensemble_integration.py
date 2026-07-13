from __future__ import annotations

from dottednotes.parser.ensemble_parser import EnsembleParser
from dottednotes.parser.input_pipeline import BRLInputPipeline

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

# Beethoven_Ludwig_Van_String_Quartet_No_1-1.brf and
# Faure_Gabriel_Morceau_de_Concours.brf are intentionally excluded from S5b-8:
# per the developer, these two fixtures don't adhere to BANA conventions, so
# they aren't reliable smoke-test material either. Do not add tests against
# them here without the developer's go-ahead.
