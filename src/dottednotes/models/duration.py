from dataclasses import dataclass


@dataclass
class Duration:
    value: int  # 1=whole, 2=half, 4=quarter, 8=eighth, 16=sixteenth, 32=thirty-second
    dots: int = 0

    def to_lilypond(self) -> str:
        return str(self.value) + "." * self.dots
