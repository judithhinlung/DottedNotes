from dataclasses import dataclass
from enum import Enum, auto

from dottednotes.bana_symbols import SymbolCategory
from dottednotes.models.base import BrailleSymbol


class ClefType(Enum):
    TREBLE = auto()
    BASS = auto()
    ALTO = auto()    # viola clef
    TENOR = auto()   # upper strings in high passages


CLEF_TO_LILYPOND: dict[ClefType, str] = {
    ClefType.TREBLE: 'treble',
    ClefType.BASS:   'bass',
    ClefType.ALTO:   'alto',
    ClefType.TENOR:  'tenor',
}


_CLEF_TO_BRL = {
    ClefType.TREBLE: '⠜⠌⠇',
    ClefType.BASS:   '⠜⠼⠇',
    ClefType.ALTO:   '⠜⠬⠇',
    ClefType.TENOR:  '⠜⠬⠐⠇',
}


@dataclass
class Clef(BrailleSymbol):
    """A clef sign."""
    clef_type: ClefType

    def to_lilypond(self) -> str:
        return f'\\clef {CLEF_TO_LILYPOND[self.clef_type]}'

    def to_braille(self) -> str:
        return _CLEF_TO_BRL[self.clef_type]
