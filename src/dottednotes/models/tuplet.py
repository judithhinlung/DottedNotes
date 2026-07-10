from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Tuplet:
    """A single-cell triplet grouping (BANA 8.4, S5-8): exactly 3 notes/rests
    in the time of 2 of their written value.

    LilyPond renders the group's notes at their plain face value inside a
    \\tuplet wrapper, which performs the 2/3 timing scale for notation —
    the individual Note/Rest durations are unadjusted for output (only
    Duration.is_triplet / duration_in_ticks() adjusts internally, for our
    own beat-accounting). Only the 3-in-the-time-of-2 ratio is supported
    (BANA 8.5's three-/four-cell irregular-group sign is out of scope).
    """

    items: list = field(default_factory=list)
    ratio: tuple[int, int] = (3, 2)

    def to_relative_lilypond(self, prev_midi: int) -> tuple[str, int]:
        parts: list[str] = []
        cur_midi = prev_midi
        for item in self.items:
            if hasattr(item, 'to_relative_lilypond'):
                s, cur_midi = item.to_relative_lilypond(cur_midi)
            else:
                s = item.to_lilypond()
            parts.append(s)
        inner = ' '.join(parts)
        num, den = self.ratio
        return f'\\tuplet {num}/{den} {{ {inner} }}', cur_midi
