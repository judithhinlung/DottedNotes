from dataclasses import dataclass
from enum import Enum


class ArticulationType(Enum):
    STACCATO = "staccato"
    TENUTO = "tenuto"
    ACCENT = "accent"
    MARCATO = "marcato"
    STACCATISSIMO = "staccatissimo"
    PORTATO = "portato"


_ARTICULATION_TO_LILYPOND = {
    ArticulationType.STACCATO: '-.',
    ArticulationType.ACCENT: '->',
    ArticulationType.TENUTO: '--',
    ArticulationType.MARCATO: '-^',
    ArticulationType.PORTATO: '-_',
    ArticulationType.STACCATISSIMO: '-!',
}


@dataclass
class Articulation:
    type: ArticulationType

    def to_lilypond(self) -> str:
        return _ARTICULATION_TO_LILYPOND[self.type]
