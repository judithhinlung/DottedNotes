from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .note import Note
    from .time_signature import TimeSignature
    from .key_signature import KeySignature


@dataclass
class InAccord:
    """Two or more independent rhythmic lines written within one braille measure.

    BANA Chapter 11.  Each element of `parts` is one voice — a list of Note or
    Chord objects.  The voice order follows BANA convention: for treble/alto clef,
    highest voice first; for bass/tenor clef, lowest voice first.

    in_accord_type values:
        'full_measure'      — full-measure in-accord (BANA 11.1.1): each part fills a whole measure.
        'part_measure'      — part-measure in-accord (BANA 11.1.2): each part fills one temporal
                              section of a measure; sections are concatenated by the caller.

    S10d-13 scope decision: BANA 33.4.2's ensemble "read upward" rule also
    covers in-accord voice order, but that's cosmetic here, not a pitch
    ambiguity like `Chord.resolved_ensemble_upward` -- `to_braille()`
    below writes every voice's notes out in full (each with its own
    explicit/tracked octave marks via `_render_note_list_to_braille`),
    never as interval shorthand. Which voice comes first in `parts` never
    changes what pitch a reader reconstructs, only which voice they read
    first, so extracting a part with in-accord content needs no equivalent
    fix. A `Chord` nested inside a voice (`parts[i]`) is still covered by
    the existing check, same as one at the top level of a measure.
    """

    parts: list[list] = field(default_factory=list)
    in_accord_type: str = 'full_measure'

    def musical_equals(self, other: Any) -> bool:
        """Equivalence for measure-repeat detection (mirrors `Measure.
        musical_equals`'s hasattr-preferring pattern), ignoring notation-only
        fields (e.g. an articulation-carry-shorthand format tag) that Python's
        default dataclass `==` would otherwise compare. A `Tuplet` nested in a
        part still has no `musical_equals()` of its own and falls back to
        plain `==` here too -- a pre-existing, separate gap, not fixed by this
        method."""
        if not isinstance(other, InAccord):
            return False
        if self.in_accord_type != other.in_accord_type:
            return False
        if len(self.parts) != len(other.parts):
            return False
        for part1, part2 in zip(self.parts, other.parts):
            if len(part1) != len(part2):
                return False
            for item1, item2 in zip(part1, part2):
                if hasattr(item1, 'musical_equals'):
                    if not item1.musical_equals(item2):
                        return False
                elif item1 != item2:
                    return False
        return True

    def to_braille(
        self,
        prev_note: Optional["Note"] = None,
        is_measure_start: bool = False,
        time_signature: Optional["TimeSignature"] = None,
        key_signature: Optional["KeySignature"] = None,
        compression_level: str = "full",
    ) -> str:
        sep = {
            'full_measure': '⠣⠜',
            'part_measure': '⠐⠂',
            'measure_division': '⠨⠅',
        }.get(self.in_accord_type, '⠣⠜')

        from .measure import _render_note_list_to_braille
        part_strs = []
        for idx, part in enumerate(self.parts):
            curr_prev = prev_note if idx == 0 else None
            curr_measure_start = is_measure_start if idx == 0 else True
            part_strs.append(_render_note_list_to_braille(part, curr_prev, curr_measure_start, time_signature, key_signature, compression_level))
        return sep.join(part_strs)

    def to_relative_lilypond(self, prev_midi: int, key_signature: Optional[KeySignature] = None) -> tuple[str, int]:
        """Render as LilyPond simultaneous voices.

        LilyPond's \\relative pitch tracking treats '<<', '\\\\', and '>>' as
        complete no-ops -- it is a purely sequential/textual chain through the
        token stream, blind to the << \\\\ >> structure (verified against the
        real `lilypond` binary's `\\displayLilyMusic` output). So voice 2's
        first note continues the reference from voice 1's LAST note (not from
        `prev_midi`, the pitch before '<<'), voice 3 continues from voice 2's
        last note, and whatever follows '>>' continues from the LAST voice's
        last note, not `parts[0]`'s.

        Returns (lilypond_str, new_prev_midi).
        """
        voice_strs: list[str] = []
        cur_midi = prev_midi

        for part in self.parts:
            note_strs: list[str] = []
            for item in part:
                if hasattr(item, 'to_relative_lilypond'):
                    s, cur_midi = item.to_relative_lilypond(cur_midi, key_signature=key_signature)
                else:
                    s = item.to_lilypond(key_signature=key_signature)
                note_strs.append(s)
            voice_strs.append('{ ' + ' '.join(note_strs) + ' }')

        return '<< ' + ' \\\\ '.join(voice_strs) + ' >>', cur_midi
