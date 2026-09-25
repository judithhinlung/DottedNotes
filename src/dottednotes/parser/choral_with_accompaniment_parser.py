"""Parses a full BANA §37.1 + §29.8 vocal-ensemble-with-keyboard-
accompaniment score: a choral-ensemble block (§37.1) followed by a blank
line and a keyboard-accompaniment block (§29.8) -- "the ensemble is
transcribed separately, and the accompaniment is transcribed separately,"
never as one ensemble parallel mixing voices and keyboard (see
solo_with_accompaniment_parser.py for the single-voice analogue this
mirrors).
"""

from __future__ import annotations

from ..exceptions import BrailleParseError
from ..models.orchestra_score import OrchestraScore
from .choral_ensemble_parser import parse_choral_ensemble
from .keyboard_accompaniment_parser import parse_keyboard_accompaniment


def parse_choral_with_accompaniment(text: str) -> OrchestraScore:
    """Parse into an OrchestraScore whose first N staves are the vocal
    ensemble (§37.1) and whose remaining 1-2 staves are the keyboard
    accompaniment's right hand (and, if present, left hand) (§29.8)."""
    lines = text.split('\n')
    try:
        blank_idx = lines.index('')
    except ValueError:
        raise BrailleParseError(
            "Choral-ensemble-with-accompaniment input must have a blank "
            "line separating the choral block from the keyboard-"
            "accompaniment block (BANA §37.1/§29.8: transcribed as two "
            "separate blocks, not one ensemble parallel)."
        )
    choral_text = '\n'.join(lines[:blank_idx])
    accompaniment_text = '\n'.join(lines[blank_idx + 1:])

    choral_score = parse_choral_ensemble(choral_text)
    accompaniment_score = parse_keyboard_accompaniment(accompaniment_text)

    combined = OrchestraScore()
    for staff in choral_score.staves:
        combined.add_staff(staff)
    for staff in accompaniment_score.staves:
        combined.add_staff(staff)
    return combined
