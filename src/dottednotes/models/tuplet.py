from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING

from .note import Rest

if TYPE_CHECKING:
    from .note import Note
    from .time_signature import TimeSignature


@dataclass
class Tuplet:
    """A single-cell triplet grouping (BANA 8.4, S5-8/S5-9): notes/rests
    totaling the time of 2 of the group's smallest written value — 3 notes
    of the same value (S5-8), or a variable-length mix of values (S5-9,
    e.g. a quarter + an eighth in an eighth-note triplet) that reach the
    same total duration.

    LilyPond renders the group's notes at their plain face value inside a
    \\tuplet wrapper, which performs the 2/3 timing scale for notation —
    the individual Note/Rest durations are unadjusted for output (only
    Duration.is_triplet / duration_in_ticks() adjusts internally, for our
    own beat-accounting). LilyPond's \\tuplet wraps an arbitrary music
    expression (verified against the Notation Reference, S5-9) so no fixed
    item count is required here. Only the 3-in-the-time-of-2 ratio is
    supported (BANA 8.5's three-/four-cell irregular-group sign is out of
    scope).
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

    def to_braille(
        self,
        prev_note: Optional["Note"] = None,
        is_measure_start: bool = False,
        time_signature: Optional["TimeSignature"] = None,
        format: str = "single",
    ) -> str:
        indicator = ""
        if format == "single":
            indicator = '⠆'
        elif format == "start_carry":
            indicator = '⠆⠆'
        elif format == "stop_carry":
            indicator = '⠆'

        rendered_items = []
        curr_prev = prev_note
        curr_measure_start = is_measure_start
        for item in self.items:
            # Pass all appropriate context args
            # Some items (like Note/Chord) accept is_16th_run_continuation etc. which will be default
            if isinstance(item, Rest):
                kwargs = {}
            else:
                kwargs = {
                    'prev_note': curr_prev,
                    'is_measure_start': curr_measure_start,
                    'time_signature': time_signature,
                }
            rendered_items.append(item.to_braille(**kwargs))
            if not isinstance(item, Rest):
                # A rest carries no pitch, so it must not become the octave-mark
                # reference for the next note (matching Measure's own item loop,
                # which likewise leaves curr_prev unchanged across a Rest).
                curr_prev = item.notes[0] if hasattr(item, 'notes') else item
            curr_measure_start = False

        if rendered_items:
            rendered_items[0] = indicator + rendered_items[0]
        return "".join(rendered_items)
