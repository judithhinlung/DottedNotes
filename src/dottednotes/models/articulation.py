from dataclasses import dataclass
from enum import Enum


class ArticulationType(Enum):
    STACCATO = "staccato"
    STACCATISSIMO = "staccatissimo"
    MEZZO_STACCATO = "mezzo_staccato"
    TENUTO = "tenuto"
    ACCENT = "accent"
    EXPRESSIVE_ACCENT = "expressive_accent"
    SWELL = "swell"


_ARTICULATION_TO_LILYPOND = {
    ArticulationType.STACCATO: '-.',
    ArticulationType.STACCATISSIMO: '-!',
    ArticulationType.MEZZO_STACCATO: '-_',
    ArticulationType.TENUTO: '--',
    ArticulationType.ACCENT: '->',
    ArticulationType.EXPRESSIVE_ACCENT: '-^',
    ArticulationType.SWELL: r'\espressivo',
}


@dataclass
class Articulation:
    type: ArticulationType

    def to_lilypond(self) -> str:
        return _ARTICULATION_TO_LILYPOND[self.type]
