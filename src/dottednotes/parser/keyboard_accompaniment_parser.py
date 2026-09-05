"""Parses the BANA §29.8 keyboard-accompaniment block of a solo-with-
accompaniment score: right-hand (⠨⠜) and optional left-hand (⠸⠜) lines,
each measure group preceded by a solo-outline line (bare ⠜, "treated as a
hand sign") that this module discards -- the solo block, parsed
separately (see `vocal_solo_parser.py`), already carries the authoritative
pitch data the outline echoes in stripped-down form (no dynamics, slurs,
word-sign expressions, or lyrics -- see `braille_renderer.build_solo_
outline_measures()`), so nothing is lost by not re-parsing it here.

Once the outline lines are removed, what remains is exactly BANA's plain
two-hand keyboard-solo shape (§29.2/29.3), which `BrailleParser` already
parses -- this module's only job is that filtering step, plus stripping
the measure number left in front of the outline line (BANA §29.8: "The
marginal measure number is placed in this line instead of in the
right-hand line" -- so the RH/LH lines here carry only blank padding
where a number would otherwise sit, never a real digit prefix).
"""

from __future__ import annotations

from ..bana_symbols import LITERARY_DIGITS
from ..exceptions import BrailleParseError
from ..models.score import Score
from .braille_parser import BrailleParser
from .lead_sheet_parser import _is_header_line
from .tokenizer import BrailleTokenizer

_RIGHT_HAND_SIGN = '⠨⠜'
_LEFT_HAND_SIGN = '⠸⠜'
_OUTLINE_SIGN = '⠜'


def _strip_margin_prefix(line: str) -> str:
    """Strip a line's leading blank cells and/or literary-digit measure
    number (with its trailing blank cell), matching the fixed-width
    prefixes `braille_renderer.py`'s accompaniment-with-outline layout
    functions produce, so the hand-sign/outline marker that follows can be
    checked without the margin column in the way."""
    i, n = 0, len(line)
    while i < n and line[i] == '⠀':
        i += 1
    while i < n and line[i] in LITERARY_DIGITS:
        i += 1
    if i < n and line[i] == '⠀':
        i += 1
    return line[i:]


def parse_keyboard_accompaniment(text: str) -> Score:
    """Parse a §29.8 keyboard-accompaniment block into a `Score` with 1
    staff (right hand only) or 2 (right hand, then left hand)."""
    lines = text.split('\n')
    while lines and lines[-1] == '':
        lines.pop()

    header_lines: list[str] = []
    while lines and _is_header_line(lines[0]):
        header_lines.append(lines.pop(0))

    kept_lines: list[str] = []
    for line in lines:
        if not line.strip('⠀'):
            continue
        content = _strip_margin_prefix(line)
        if content.startswith(_RIGHT_HAND_SIGN) or content.startswith(_LEFT_HAND_SIGN):
            kept_lines.append(line)
        elif content.startswith(_OUTLINE_SIGN):
            continue  # solo-outline line -- discarded, see module docstring
        else:
            raise BrailleParseError(
                "Keyboard accompaniment line does not start with a "
                "right-hand (⠨⠜), left-hand (⠸⠜), or solo-outline (⠜) sign "
                "after its margin: " + repr(line)
            )

    if not kept_lines:
        raise BrailleParseError(
            "Keyboard accompaniment input has no right-/left-hand content "
            "(⠨⠜/⠸⠜) -- only solo-outline lines or blanks."
        )

    music_text = '\n'.join(header_lines + kept_lines)
    tokens = BrailleTokenizer().tokenize(music_text)
    score = BrailleParser(tokens=tokens).parse()

    if len(score.staves) not in (1, 2):
        raise BrailleParseError(
            f"Keyboard accompaniment parsing expected 1 or 2 staves, got {len(score.staves)}."
        )
    return score
