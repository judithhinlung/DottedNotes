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
    DOWN_BOW = "down_bow"   # S8b-2, BANA Sec. 25.3 (Table 24B) -> \downbow
    UP_BOW = "up_bow"       # S8b-2, BANA Sec. 25.3 (Table 24B) -> \upbow


_ARTICULATION_TO_LILYPOND = {
    ArticulationType.STACCATO: '-.',
    ArticulationType.STACCATISSIMO: '-!',
    ArticulationType.MEZZO_STACCATO: '-_',
    ArticulationType.TENUTO: '--',
    ArticulationType.ACCENT: '->',
    ArticulationType.EXPRESSIVE_ACCENT: '-^',
    ArticulationType.SWELL: r'\espressivo',
    # No shorthand punctuation exists for bowing marks (LilyPond Notation
    # Reference Sec. 11.1.2, "Bowing indications" -- created as articulations,
    # verified against a real `lilypond` compile: bare `\downbow`/`\upbow`
    # attach correctly with no leading hyphen, same as \espressivo above).
    ArticulationType.DOWN_BOW: r'\downbow',
    ArticulationType.UP_BOW: r'\upbow',
}


@dataclass
class Articulation:
    type: ArticulationType

    def to_lilypond(self) -> str:
        return _ARTICULATION_TO_LILYPOND[self.type]
