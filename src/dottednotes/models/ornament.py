from dataclasses import dataclass
from enum import Enum


class OrnamentType(Enum):
    TRILL = "trill"
    TURN = "turn"
    MORDENT = "mordent"
    INVERTED_MORDENT = "prall"
    TREMOLO = "tremolo"


@dataclass
class Ornament:
    type: OrnamentType
