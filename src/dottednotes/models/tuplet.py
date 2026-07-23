from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING

from dottednotes.bana_symbols import LOWER_DIGIT_CELLS
from .note import Rest

if TYPE_CHECKING:
    from .note import Note
    from .time_signature import TimeSignature

_DIGIT_TO_LOWER_CELL = {v: k for k, v in LOWER_DIGIT_CELLS.items()}


@dataclass
class Tuplet:
    """A tuplet grouping (BANA 8.4/8.5, S5-8/S5-9/S10d-4): notes/rests
    totaling the time of `ratio[1]` of the group's smallest written value
    -- 3 notes of the same value (S5-8), or a variable-length mix of
    values (S5-9, e.g. a quarter + an eighth in an eighth-note triplet)
    that reach the same total duration. `ratio` is the exact
    (actual, normal) tuplet ratio, e.g. (3, 2) for a classic triplet or
    (5, 4) for a quintuplet (S10d-4).

    Braille sign (BANA Table 8): exactly 3 notes (`ratio[0] == 3`,
    regardless of `ratio[1]` -- Par. 8.4's wording ties the sign to the
    note count, not the ratio's denominator) uses the single-cell triplet
    sign, doubled for four or more successive triplets of the same value
    (`format="start_carry"/"stop_carry"`, mirroring the existing carry-run
    convention elsewhere in this codebase). Any other count uses Par.
    8.5's three-cell (or four-cell if the count is greater than nine) sign
    instead: dots 4,5,6, the count spelled with the LOWER_DIGIT_CELLS
    numeral alphabet (bana_symbols.py, inverted -- a different digit
    alphabet than the LITERARY_DIGITS one BANA measure numbers use), then
    a dot-3 terminator. Par. 8.5 also allows doubling this sign for four
    or more successive like groups ("dots 456 and numeral twice followed
    by one dot 3") -- deliberately not implemented, since doubling is
    explicitly optional ("may be doubled") and always rendering the plain
    single-group form remains fully BANA-compliant either way; the
    `format` argument is therefore ignored for this branch, always
    producing the single (undoubled) form regardless of what carry-run
    state a caller computed for it.

    LilyPond renders the group's notes at their plain face value inside a
    \\tuplet wrapper, which performs the ratio's timing scale for notation
    -- the individual Note/Rest durations are unadjusted for output (only
    Duration.tuplet_ratio / Duration.is_triplet + duration_in_ticks()
    adjusts internally, for our own beat-accounting). LilyPond's \\tuplet
    wraps an arbitrary music expression and any ratio (verified against
    the Notation Reference, S5-9/S10d-4) so no fixed item count or ratio
    restriction is needed here.
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
        if self.ratio[0] == 3:
            indicator = ""
            if format == "single":
                indicator = '⠆'
            elif format == "start_carry":
                indicator = '⠆⠆'
            elif format == "stop_carry":
                indicator = '⠆'
        else:
            digits = "".join(_DIGIT_TO_LOWER_CELL[int(d)] for d in str(self.ratio[0]))
            indicator = '⠸' + digits + '⠄'

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
                # Nor may it consume the line/measure-start octave-mark
                # reset (BANA 3.2.1) before a real note reaches it.
                curr_measure_start = False

        if rendered_items:
            rendered_items[0] = indicator + rendered_items[0]
        return "".join(rendered_items)
