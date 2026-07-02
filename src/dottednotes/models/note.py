from dataclasses import dataclass, field
from typing import Optional

from .accidental import Accidental
from .base import BrailleSymbol
from .duration import Duration

NOTE_NAME_TO_LILYPOND = {
    'C': 'c', 'D': 'd', 'E': 'e', 'F': 'f',
    'G': 'g', 'A': 'a', 'B': 'b',
}

_LILYPOND_OCTAVE_BASE = 3  # octave 3 = c (no marks) in LilyPond; c' = C4 = middle C


@dataclass
class Note(BrailleSymbol):
    """A single pitched note."""
    note_name: str          # 'C', 'D', 'E', 'F', 'G', 'A', 'B'
    octave: int             # absolute octave (middle C = octave 4)
    duration: Duration
    accidental: Optional[Accidental] = None
    articulations: list = field(default_factory=list)
    ornaments: list = field(default_factory=list)

    def __post_init__(self):
        if self.note_name not in NOTE_NAME_TO_LILYPOND:
            raise ValueError(f"Invalid note name: {self.note_name}")
        if not 0 <= self.octave <= 8:
            raise ValueError(f"Octave {self.octave} out of range (0-8)")

    def _octave_marks(self) -> str:
        if self.octave < _LILYPOND_OCTAVE_BASE:
            return ',' * (_LILYPOND_OCTAVE_BASE - self.octave)
        elif self.octave > _LILYPOND_OCTAVE_BASE:
            return "'" * (self.octave - _LILYPOND_OCTAVE_BASE)
        return ''

    def to_lilypond(self) -> str:
        """Return LilyPond note string e.g. 'c4', 'bes'2.', 'fis8'"""
        ly_name = NOTE_NAME_TO_LILYPOND[self.note_name]
        accidental_str = self.accidental.to_lilypond() if self.accidental else ''
        octave_str = self._octave_marks()
        duration_str = self.duration.to_lilypond()
        articulation_str = ''.join(a.to_lilypond() for a in self.articulations)
        return f"{ly_name}{accidental_str}{octave_str}{duration_str}{articulation_str}"
