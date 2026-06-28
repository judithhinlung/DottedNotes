from dataclasses import dataclass
from enum import Enum


class ArticulationType(Enum):
    STACCATO = "staccato"
    TENUTO = "tenuto"
    ACCENT = "accent"
    MARCATO = "marcato"
    STACCATISSIMO = "staccatissimo"
    PORTATO = "portato"


@dataclass
class Articulation:
    type: ArticulationType
