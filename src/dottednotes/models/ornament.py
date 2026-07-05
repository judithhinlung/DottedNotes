from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .note import Note


class OrnamentType(Enum):
    TRILL = auto()
    TRILL_SPAN_START = auto()        # first note of a 4+ trill series → \startTrillSpan
    TRILL_SPAN_END = auto()          # last note of a 4+ trill series → \stopTrillSpan
    MORDENT = auto()                 # lower mordent (dots 5, 2,3,5, 1,2,3) → \mordent
    UPPER_MORDENT = auto()           # upper mordent (dots 5, 2,3,5) → \prall
    EXTENDED_MORDENT = auto()        # extended lower mordent (dots 5,6, 2,3,5, 1,2,3) → \downmordent
    EXTENDED_UPPER_MORDENT = auto()  # extended upper mordent (dots 5,6, 2,3,5) → \upmordent
    TURN = auto()                    # turn (dots 2,5,6) → \turn
    INVERTED_TURN = auto()           # inverted turn (dots 2,5,6, 1,2,3) → \reverseturn
    GLISSANDO = auto()               # glissando (dot 4, dot 1 — two cells) → \glissando
    TREMOLO = auto()                 # tremolo — BANA cell not yet confirmed


ORNAMENT_TO_LILYPOND: dict[OrnamentType, str] = {
    OrnamentType.TRILL:                  r'\trill',
    OrnamentType.TRILL_SPAN_START:       r'\startTrillSpan',
    OrnamentType.TRILL_SPAN_END:         r'\stopTrillSpan',
    OrnamentType.MORDENT:                r'\mordent',
    OrnamentType.UPPER_MORDENT:          r'\prall',
    OrnamentType.EXTENDED_MORDENT:       r'\downmordent',
    OrnamentType.EXTENDED_UPPER_MORDENT: r'\upmordent',
    OrnamentType.TURN:                   r'\turn',
    OrnamentType.INVERTED_TURN:          r'\reverseturn',
    OrnamentType.GLISSANDO:              r'\glissando',
    OrnamentType.TREMOLO:                ':32',
}


@dataclass
class Ornament:
    type: OrnamentType

    def to_lilypond(self) -> str:
        return ORNAMENT_TO_LILYPOND[self.type]


@dataclass
class GraceNote:
    """One or more grace notes that precede a main note, rendered as a single block.

    BANA encoding (verified by developer):
    - Short grace note (dots 2,6 = ⠢): long_appoggiatura=False → \\grace { notes... }
      Has a slash through the stem in printed notation.
    - Long grace note (dots 5, 2,6 = ⠐⠢): long_appoggiatura=True → \\appoggiatura { notes... }
      No slash through the stem in printed notation.

    1–3 grace notes: each is preceded by its own indicator sign in braille.
    4+ grace notes: doubled indicator before the first, single indicator before
    the last — the same doubling convention used for articulations (carry mode).
    All notes in the group are enclosed in a single \\grace { } block.
    """
    notes: list[Note]
    long_appoggiatura: bool = False  # False → \grace { }; True → \appoggiatura { }

    def to_lilypond(self) -> str:
        prefix = r'\appoggiatura' if self.long_appoggiatura else r'\grace'
        notes_str = ' '.join(n.to_lilypond() for n in self.notes)
        return f'{prefix} {{ {notes_str} }}'
