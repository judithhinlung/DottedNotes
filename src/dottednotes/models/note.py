from dataclasses import dataclass, field
from typing import Optional

from .articulation import Articulation
from .duration import Duration
from .dynamic import Dynamic
from .ornament import Ornament


@dataclass
class Note:
    pitch: str  # "c" through "b", or "r" for rest
    octave: int
    duration: Duration
    articulations: list[Articulation] = field(default_factory=list)
    dynamic: Optional[Dynamic] = None
    ornaments: list[Ornament] = field(default_factory=list)
    is_rest: bool = False
    is_chord: bool = False
    tie: bool = False
