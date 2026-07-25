from dataclasses import dataclass, field
from enum import Enum, auto

from dottednotes.bana_symbols import SymbolCategory
from dottednotes.models.base import BrailleSymbol


class AccidentalType(Enum):
    SHARP = auto()
    FLAT = auto()
    NATURAL = auto()
    DOUBLE_SHARP = auto()
    DOUBLE_FLAT = auto()


ACCIDENTAL_TO_LILYPOND_SUFFIX = {
    AccidentalType.SHARP: 'is',
    AccidentalType.FLAT: 'es',
    AccidentalType.NATURAL: '',
    AccidentalType.DOUBLE_SHARP: 'isis',
    AccidentalType.DOUBLE_FLAT: 'eses',
}


@dataclass
class Accidental(BrailleSymbol):
    """An accidental (sharp, flat, natural, etc.)"""
    type: AccidentalType
    # Whether the source BRF wrote this accidental explicitly vs. it being
    # inferred from the key signature or carried from an earlier explicit
    # accidental on the same pitch+octave within the current measure (MBC
    # 2015 Part I, Sec. 5.1). compare=False keeps it out of Accidental's
    # (and therefore Note.musical_equals()'s) equality check -- notation
    # provenance, not a musical attribute. Mirrors Articulation.explicit.
    explicit: bool = field(default=True, compare=False)

    def to_lilypond(self) -> str:
        """Return LilyPond accidental suffix e.g. 'is', 'es', 'isis'"""
        return ACCIDENTAL_TO_LILYPOND_SUFFIX[self.type]

    def to_braille(self) -> str:
        if self.type == AccidentalType.SHARP:
            return '⠩'
        elif self.type == AccidentalType.FLAT:
            return '⠣'
        elif self.type == AccidentalType.NATURAL:
            return '⠡'
        elif self.type == AccidentalType.DOUBLE_SHARP:
            return '⠩⠩'
        elif self.type == AccidentalType.DOUBLE_FLAT:
            return '⠣⠣'
        return ''
