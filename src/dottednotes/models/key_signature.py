from dataclasses import dataclass

from dottednotes.bana_symbols import SymbolCategory
from dottednotes.models.base import BrailleSymbol

# Maps sharps_or_flats count → (lilypond_note, mode_string)
# Positive values = sharps, negative values = flats, 0 = C major / A minor.
# Note names use LilyPond conventions: sharps add 'is', flats add 'es'.
KEY_TO_LILYPOND: dict[int, tuple[str, str]] = {
     7: ('cis', 'major'),
     6: ('fis', 'major'),
     5: ('b',   'major'),
     4: ('e',   'major'),
     3: ('a',   'major'),
     2: ('d',   'major'),
     1: ('g',   'major'),
     0: ('c',   'major'),
    -1: ('f',   'major'),
    -2: ('bes', 'major'),
    -3: ('ees', 'major'),
    -4: ('aes', 'major'),
    -5: ('des', 'major'),
    -6: ('ges', 'major'),
    -7: ('ces', 'major'),
}


@dataclass
class KeySignature(BrailleSymbol):
    """A key signature.

    sharps_or_flats > 0 = that many sharps (G major = 1, D major = 2, …)
    sharps_or_flats < 0 = that many flats  (F major = –1, Bb major = –2, …)
    sharps_or_flats = 0 = C major / A minor (no accidentals)

    Minor keys are not yet distinguished from their relative majors;
    the same braille cell covers both.  Minor-mode support is deferred
    to a later sprint.
    """
    sharps_or_flats: int    # range –7 … +7

    def __post_init__(self) -> None:
        if not -7 <= self.sharps_or_flats <= 7:
            raise ValueError(
                f"sharps_or_flats must be in –7 … +7, got {self.sharps_or_flats}"
            )

    def to_lilypond(self) -> str:
        """Return a LilyPond key directive, e.g. '\\key g \\major'."""
        note, mode = KEY_TO_LILYPOND[self.sharps_or_flats]
        return f'\\key {note} \\{mode}'
