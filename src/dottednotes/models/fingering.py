from dataclasses import dataclass
from typing import Optional

from dottednotes.bana_symbols import SymbolCategory
from dottednotes.models.base import BrailleSymbol


@dataclass
class Fingering(BrailleSymbol):
    """Fingering information for a note or chord."""
    finger: Optional[int] = None           # 1-5, or None if omitted
    change_to: Optional[int] = None        # 1-5 if change of fingering, else None
    alternative: Optional[int] = None      # 1-5 if alternative fingering, else None
    first_omitted: bool = False
    second_omitted: bool = False

    def to_lilypond(self) -> str:
        """Return LilyPond representation of this fingering."""
        if self.change_to is not None:
            # Change of fingering on one note (e.g. -1-2)
            f1 = str(self.finger) if self.finger is not None else ""
            f2 = str(self.change_to)
            return f"-{f1}-{f2}"
        elif self.alternative is not None or self.first_omitted or self.second_omitted:
            # Alternative fingering stacked markup.
            # In LilyPond center-column, the second listed item is on top,
            # so we list the second alternative (alternative) first, and the
            # first alternative (finger) second.
            f1 = str(self.finger) if not self.first_omitted and self.finger is not None else ""
            f2 = str(self.alternative) if not self.second_omitted and self.alternative is not None else ""
            return f'-\\markup \\center-column {{ "{f2}" "{f1}" }}'
        elif self.finger is not None:
            # Single fingering
            return f"-{self.finger}"
        return ""

    def to_braille(self) -> str:
        _FINGER_TO_BRL = {1: '⠁', 2: '⠃', 3: '⠇', 4: '⠂', 5: '⠅'}
        if self.change_to is not None:
            # Change of fingering: finger + change_cell + change_to
            t1 = _FINGER_TO_BRL.get(self.finger, '⠠')  # fallback to '⠠' for first omitted
            t3 = _FINGER_TO_BRL.get(self.change_to, '')
            return t1 + '⠉' + t3
        elif self.alternative is not None or self.first_omitted or self.second_omitted:
            # Alternative fingering
            t1 = '⠠' if self.first_omitted else _FINGER_TO_BRL.get(self.finger, '')
            t2 = '⠄' if self.second_omitted else _FINGER_TO_BRL.get(self.alternative, '')
            return t1 + t2
        elif self.finger is not None:
            # Single fingering
            return _FINGER_TO_BRL.get(self.finger, '')
        return ""
