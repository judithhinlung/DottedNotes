"""Parses a full BANA §37.1 + §33 vocal-ensemble-with-instrumental-
ensemble score: a choral-ensemble block (§37.1) followed by a blank line
and an instrumental-ensemble block (§33) -- two separate transcriptions,
never one flat parallel mixing voices and instruments. Unlike the
keyboard-accompaniment case (§29.8), BANA defines no outline mechanism
here, so there is no outline content to strip on the parse side either.
"""

from __future__ import annotations

from ..exceptions import BrailleParseError
from ..models.orchestra_score import OrchestraScore
from .choral_ensemble_parser import parse_choral_ensemble
from .ensemble_parser import EnsembleParser


def parse_choral_with_orchestra(text: str) -> OrchestraScore:
    """Parse into an OrchestraScore whose first N staves are the vocal
    ensemble (§37.1) and whose remaining staves are the instrumental
    ensemble (§33)."""
    lines = text.split('\n')
    try:
        blank_idx = lines.index('')
    except ValueError:
        raise BrailleParseError(
            "Choral-ensemble-with-orchestra input must have a blank line "
            "separating the choral block from the instrumental-ensemble "
            "block (BANA §37.1/§33: transcribed as two separate blocks, "
            "not one parallel mixing voices and instruments)."
        )
    choral_text = '\n'.join(lines[:blank_idx])
    orchestra_text = '\n'.join(lines[blank_idx + 1:])

    choral_score = parse_choral_ensemble(choral_text)
    orchestra_score = EnsembleParser().parse(orchestra_text)

    combined = OrchestraScore()
    for staff in choral_score.staves:
        combined.add_staff(staff)
    for staff in orchestra_score.staves:
        combined.add_staff(staff)
    return combined
