from dataclasses import dataclass

VALID_DURATIONS = {1, 2, 4, 8, 16, 32, 64}


@dataclass
class Duration:
    value: int  # 1=whole, 2=half, 4=quarter, 8=eighth, 16=sixteenth, 32=thirty-second, 64=sixty-fourth
    dots: int = 0  # augmentation dots (0, 1, or 2)

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
        return str(self.value) + "." * self.dots

    def duration_in_beats(self, beats_per_whole: int = 4) -> float:
        """Return duration as a float number of beats where quarter note = 1.0."""
        base = beats_per_whole / self.value
        if self.dots == 1:
            return base * 1.5
        elif self.dots == 2:
            return base * 1.75
        return base
