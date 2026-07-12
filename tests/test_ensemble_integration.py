from __future__ import annotations

import pytest

from dottednotes.parser.ensemble_parser import EnsembleParser
from dottednotes.parser.input_pipeline import BRLInputPipeline

from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.mark.xfail(
    reason=(
        "Bartok_Bella_Romanian_Folk_Dances_for_Orchestra.brl was auto-"
        "transcribed by Sao Mai Braille software using a measure-numbering "
        "convention that only partially overlaps with the BANA Sec. 33.4.6 "
        "standalone-line convention EnsembleParser now supports (added for "
        "Fengyang): Sao Mai's header lines list several measure numbers "
        "together (e.g. multiple number-sign-prefixed digits across one "
        "line), rather than exactly one number alone per line. Partial "
        "overlap means the parser now gets much further into the piece "
        "before failing than it originally did (previously an immediate "
        "'No parallel systems found' ValueError; now an AttributeError deep "
        "into parsing, since misaligned measure boundaries eventually feed "
        "a dynamic marking to an unresolved pending rest) -- either way, "
        "correctly supporting Sao Mai's actual convention is new parsing "
        "logic, out of scope for S5b-8 (per its own Senior note) -- tracked "
        "as a follow-up ticket."
    ),
    strict=True,
)
def test_bartok_smoke_documents_current_crash():
    pipeline = BRLInputPipeline()
    text = pipeline.load(FIXTURES / "Bartok_Bella_Romanian_Folk_Dances_for_Orchestra.brl")
    EnsembleParser().parse(text)

# Beethoven_Ludwig_Van_String_Quartet_No_1-1.brf and
# Faure_Gabriel_Morceau_de_Concours.brf are intentionally excluded from S5b-8:
# per the developer, these two fixtures don't adhere to BANA conventions, so
# they aren't reliable smoke-test material either. Do not add tests against
# them here without the developer's go-ahead.
