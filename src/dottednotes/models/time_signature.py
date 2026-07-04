from dataclasses import dataclass

from dottednotes.bana_symbols import SymbolCategory
from dottednotes.models.base import BrailleSymbol

VALID_DENOMINATORS: frozenset[int] = frozenset({1, 2, 4, 8, 16, 32})


@dataclass
class TimeSignature(BrailleSymbol):
    """A time (meter) signature.

    numerator   — beats per measure (top number, must be >= 1)
    denominator — beat unit; must be a power of 2 (1, 2, 4, 8, 16, or 32)

    beats_per_measure() returns total duration as quarter-note beat counts,
    e.g. 6/8 → 3.0 (not 6), because _resolve_measure_durations() reasons
    in quarter-beat units.
    """

    numerator: int
    denominator: int

    def __post_init__(self) -> None:
        if self.numerator < 1:
            raise ValueError(f"numerator must be >= 1, got {self.numerator}")
        if self.denominator not in VALID_DENOMINATORS:
            raise ValueError(
                f"denominator must be a power of 2 in {sorted(VALID_DENOMINATORS)}, "
                f"got {self.denominator}"
            )

    def beats_per_measure(self) -> float:
        """Total measure duration in quarter-note beats."""
        return self.numerator * (4 / self.denominator)

    def to_lilypond(self) -> str:
        return f'\\time {self.numerator}/{self.denominator}'

    def as_tuple(self) -> tuple[int, int]:
        """Return (numerator, denominator) for legacy-code compatibility."""
        return (self.numerator, self.denominator)
