from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING, Optional

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
}


_ORNAMENT_TO_BRL = {
    OrnamentType.TRILL: '⠖',
    OrnamentType.TRILL_SPAN_START: '⠖⠖',
    OrnamentType.TRILL_SPAN_END: '⠖',
    OrnamentType.MORDENT: '⠐⠖⠇',
    OrnamentType.UPPER_MORDENT: '⠐⠖',
    OrnamentType.EXTENDED_MORDENT: '⠰⠖⠇',
    OrnamentType.EXTENDED_UPPER_MORDENT: '⠰⠖',
    OrnamentType.TURN: '⠲',
    OrnamentType.INVERTED_TURN: '⠲⠇',
    OrnamentType.GLISSANDO: '⠈⠁',
}


@dataclass
class Ornament:
    type: OrnamentType

    def to_lilypond(self) -> str:
        return ORNAMENT_TO_LILYPOND[self.type]

    def to_braille(self) -> str:
        return _ORNAMENT_TO_BRL[self.type]


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

    def to_braille(
        self,
        prev_note: Optional[Note] = None,
        is_measure_start: bool = False,
        time_signature: Optional[TimeSignature] = None,
    ) -> str:
        if not self.notes:
            return ""

        indicator = '⠐⠢' if self.long_appoggiatura else '⠢'
        rendered_notes = []
        curr_prev = prev_note
        # BANA 3.2.1's line/measure-start octave-mark force applies to
        # whichever note is genuinely first on the line -- when this note
        # has a grace-note group attached, that is the group's own first
        # note, not the main note that follows it (previously this whole
        # method hardcoded is_measure_start=False for every grace note,
        # silently dropping the required mark whenever a line happened to
        # start on a grace note). Only the first note keeps the caller's
        # real is_measure_start; every later note in the group is never
        # itself "first," so it always gets False, matching every other
        # multi-item sequence in this codebase (e.g. Measure's own item
        # loop).
        first = True

        if len(self.notes) <= 3:
            for n in self.notes:
                rendered_notes.append(indicator + n.to_braille(prev_note=curr_prev, is_measure_start=(is_measure_start and first), time_signature=time_signature))
                curr_prev = n
                first = False
        else:
            # 4+ notes: doubled indicator before first, none for middle, single before last
            rendered_notes.append(indicator + indicator + self.notes[0].to_braille(prev_note=curr_prev, is_measure_start=is_measure_start, time_signature=time_signature))
            curr_prev = self.notes[0]
            for n in self.notes[1:-1]:
                rendered_notes.append(n.to_braille(prev_note=curr_prev, is_measure_start=False, time_signature=time_signature))
                curr_prev = n
            rendered_notes.append(indicator + self.notes[-1].to_braille(prev_note=curr_prev, is_measure_start=False, time_signature=time_signature))

        return "".join(rendered_notes)
