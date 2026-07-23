from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

VALID_DURATIONS = {0, 1, 2, 4, 8, 16, 32, 64}

# MusicXML-style integer tick resolution (quarter note = 24 ticks). Chosen
# over float beats (S5-8) so triplet math (thirds) is always exact: a
# triplet eighth is 12 * 2 // 3 == 8 ticks, never a rounded float.
TICKS_PER_QUARTER = 24


@dataclass
class Duration:
    value: int  # 0=breve, 1=whole, 2=half, 4=quarter, 8=eighth, 16=sixteenth, 32=thirty-second, 64=sixty-fourth
    dots: int = 0  # augmentation dots (0, 1, or 2)
    is_triplet: bool = False  # BANA 8.4's single-cell sign applies (exactly 3 notes, any value)
    # Exact (actual, normal) tuplet ratio, e.g. (5, 4) for a quintuplet
    # (S10d-4, BANA 8.5) -- None for a plain (non-tuplet) duration. A
    # classic triplet (is_triplet=True) may leave this None and rely on
    # the hardcoded 2/3 scale below instead, for backward compatibility
    # with callers (braille_parser.py's BRF -> Score direction) that only
    # ever set is_triplet.
    tuplet_ratio: Optional[tuple[int, int]] = None

    def __post_init__(self) -> None:
        if self.value not in VALID_DURATIONS:
            raise ValueError(
                f"Invalid duration value: {self.value}. "
                f"Must be one of {sorted(VALID_DURATIONS)}"
            )
        if self.dots not in (0, 1, 2):
            raise ValueError(
                f"Invalid dot count: {self.dots}. Must be 0, 1, or 2."
            )

    def to_lilypond(self) -> str:
        if self.value == 0:
            return r"\breve" + "." * self.dots
        return str(self.value) + "." * self.dots

    def duration_in_ticks(self) -> int:
        """Return duration as an integer number of ticks (quarter note = TICKS_PER_QUARTER).

        Tuplet notes are written in LilyPond at their face value inside a
        \\tuplet wrapper (see models/tuplet.py) — the wrapper handles the
        ratio's scaling for notation, so this method also applies it here
        for our own internal beat-accounting (S5-6/S5-7's duration
        resolution and _validate_measure_beat_count), independent of
        LilyPond output. `tuplet_ratio`, when set, gives the exact scale
        for any ratio (S10d-4); otherwise `is_triplet` falls back to the
        classic 2/3 scale.
        """
        if self.value == 0:
            base = TICKS_PER_QUARTER * 8
        else:
            base = TICKS_PER_QUARTER * 4 // self.value
        if self.dots == 1:
            ticks = base * 3 // 2
        elif self.dots == 2:
            ticks = base * 7 // 4
        else:
            ticks = base
        if self.tuplet_ratio is not None:
            actual, normal = self.tuplet_ratio
            ticks = ticks * normal // actual
        elif self.is_triplet:
            ticks = ticks * 2 // 3
        return ticks


def ticks_to_lilypond_duration(ticks: int) -> str | None:
    """Inverse of `Duration.duration_in_ticks()`: the plain (non-triplet)
    LilyPond duration string for an exact tick count, e.g. `\\partial`'s
    argument for a pickup measure (`Staff.to_lilypond()`). Returns None if
    no single plain duration (0-2 dots) matches exactly, rather than
    guessing a tied/compound approximation.
    """
    for value in (1, 2, 4, 8, 16, 32, 64):
        for dots in (0, 1, 2):
            if Duration(value=value, dots=dots).duration_in_ticks() == ticks:
                return Duration(value=value, dots=dots).to_lilypond()
    return None
