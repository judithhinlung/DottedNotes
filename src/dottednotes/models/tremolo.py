from __future__ import annotations

import dataclasses
from dataclasses import dataclass

from .duration import Duration, TICKS_PER_QUARTER


@dataclass
class RepeatedTremolo:
    """Repeated-note tremolo / fractioning (BANA 14.2).

    Attached to a single Note or Chord (via its written note's `tremolo`
    field); renders as LilyPond colon syntax appended directly after the
    duration, e.g. 'c4:16' -- verified against LilyPond Notation Reference
    v2.24 SS1.4.2 "Tremolo repeats" (colon immediately follows the duration,
    no space).
    """
    subdivision: int  # 8, 16, 32, 64, or 128

    def to_lilypond(self) -> str:
        return f':{self.subdivision}'


from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .note import Note
    from .time_signature import TimeSignature
    from .key_signature import KeySignature


@dataclass
class AlternatingTremolo:
    """Alternating-note tremolo (BANA 14.3): alternation between two notes
    or chords, each written at its own full print duration in the source.

    LilyPond instead renders both at the tremolo subdivision value inside a
    \\repeat tremolo block (verified against LilyPond Notation Reference
    v2.24 SS1.4.2, e.g. '\\repeat tremolo 8 { c16 d }'). The repeat count is
    derived from the first item's written duration: BANA's printed duration
    describes the whole alternating pair, so one full cycle through both
    notes takes 2 * (1 tremolo-subdivision note), and the pair repeats
    enough times to fill the written duration.
    """
    items: list  # exactly two Note or Chord objects, at full written duration
    subdivision: int

    def _repeat_count(self) -> int:
        written_ticks = self.items[0].duration.duration_in_ticks()
        subdivision_ticks = TICKS_PER_QUARTER * 4 // self.subdivision
        return written_ticks // (2 * subdivision_ticks)

    @staticmethod
    def _at_subdivision(item, subdivision: int):
        new_duration = Duration(value=subdivision)
        if hasattr(item, 'notes'):  # Chord
            return dataclasses.replace(
                item,
                notes=[dataclasses.replace(n, duration=new_duration) for n in item.notes],
            )
        return dataclasses.replace(item, duration=new_duration)

    def to_relative_lilypond(self, prev_midi: int) -> tuple[str, int]:
        count = self._repeat_count()
        parts: list[str] = []
        cur_midi = prev_midi
        for item in self.items:
            scaled = self._at_subdivision(item, self.subdivision)
            s, cur_midi = scaled.to_relative_lilypond(cur_midi)
            parts.append(s)
        inner = ' '.join(parts)
        return f'\\repeat tremolo {count} {{ {inner} }}', cur_midi

    def to_braille(
        self,
        prev_note: Optional["Note"] = None,
        is_measure_start: bool = False,
        time_signature: Optional["TimeSignature"] = None,
        key_signature: Optional["KeySignature"] = None,
    ) -> str:
        from dottednotes.bana_symbols import TREMOLO_ALTERNATING_VALUE_CELLS
        _ALT_TREM_TO_BRL = {v: k for k, v in TREMOLO_ALTERNATING_VALUE_CELLS.items()}

        alt_sign = '⠨' + _ALT_TREM_TO_BRL[self.subdivision]

        first_kwargs = {
            'prev_note': prev_note,
            'is_measure_start': is_measure_start,
            'time_signature': time_signature,
            'key_signature': key_signature,
            'tremolo_str': alt_sign,
        }
        first_brl = self.items[0].to_braille(**first_kwargs)

        ref_note = self.items[0].notes[0] if hasattr(self.items[0], 'notes') and self.items[0].notes else self.items[0]

        second_kwargs = {
            'prev_note': ref_note,
            'is_measure_start': False,
            'time_signature': time_signature,
            'key_signature': key_signature,
        }
        second_brl = self.items[1].to_braille(**second_kwargs)

        return first_brl + second_brl
