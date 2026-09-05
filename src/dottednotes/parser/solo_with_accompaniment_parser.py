"""Parses a full BANA §29.8 solo-with-keyboard-accompaniment score: a solo
block (vocal, per §35.1, or plain instrumental) followed by a blank line
and a keyboard-accompaniment block (§29.8) -- "the solo or instrumental
parts are transcribed individually, and the accompaniment is transcribed
separately," never as one ensemble parallel.
"""

from __future__ import annotations

from ..exceptions import BrailleParseError
from ..models.score import Score
from .braille_parser import BrailleParser
from .keyboard_accompaniment_parser import parse_keyboard_accompaniment
from .tokenizer import BrailleTokenizer
from .vocal_solo_parser import parse_vocal_solo


def parse_solo_with_accompaniment(text: str) -> Score:
    """Parse a §29.8 solo-with-accompaniment score into a `Score` whose
    first staff is the solo part and whose remaining 1-2 staves are the
    keyboard accompaniment's right hand (and, if present, left hand)."""
    lines = text.split('\n')
    try:
        blank_idx = lines.index('')
    except ValueError:
        raise BrailleParseError(
            "Solo-with-accompaniment input must have a blank line "
            "separating the solo block from the keyboard-accompaniment "
            "block (BANA §29.8: transcribed as two separate blocks, not "
            "one ensemble parallel)."
        )
    solo_text = '\n'.join(lines[:blank_idx])
    accompaniment_text = '\n'.join(lines[blank_idx + 1:])

    try:
        solo_score = parse_vocal_solo(solo_text)
    except BrailleParseError:
        # Not in the §35.1 lyric/music alternation -- a plain instrumental
        # solo (§24) block, which BrailleParser already handles directly.
        tokens = BrailleTokenizer().tokenize(solo_text)
        solo_score = BrailleParser(tokens=tokens).parse()

    if len(solo_score.staves) != 1:
        raise BrailleParseError(
            f"Solo-with-accompaniment parsing expected a single solo staff, "
            f"got {len(solo_score.staves)}."
        )

    accompaniment_score = parse_keyboard_accompaniment(accompaniment_text)

    combined = Score(title=solo_score.title)
    combined.add_staff(solo_score.staves[0])
    for staff in accompaniment_score.staves:
        combined.add_staff(staff)
    return combined
