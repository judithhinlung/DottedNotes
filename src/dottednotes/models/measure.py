from __future__ import annotations

from dataclasses import dataclass, field
from typing import Union

from .chord import Chord
from .in_accord import InAccord
from .note import Note, Rest
from .text_marking import TextMarking
from .tremolo import AlternatingTremolo
from .tuplet import Tuplet

NoteOrChord = Union[Note, Chord]
MeasureItem = Union[Note, Rest, Chord, InAccord, Tuplet, AlternatingTremolo]

_BAR_LINE_TO_LY: dict[str, str] = {
    'measure_separator': '|',
    'final_double_bar': r'\bar "|."',
    'section_double_bar': r'\bar "||"',
    'forward_repeat': r'\bar ".|:"',
    'end_repeat': r'\bar ":|."',
}


def _item_ticks(item: MeasureItem) -> int:
    """Duration, in ticks, of a single measure item -- Note/Rest/Chord read
    `.duration` directly; a Tuplet sums its own items recursively.

    An AlternatingTremolo (S6-6) occupies only the FIRST item's written
    duration -- BANA's printed duration describes the whole alternating
    pair, which together take up one written note's worth of time, not two
    (see models/tremolo.py's _repeat_count for the same reasoning)."""
    if isinstance(item, Tuplet):
        return sum(_item_ticks(sub) for sub in item.items)
    if isinstance(item, AlternatingTremolo):
        return item.items[0].duration.duration_in_ticks()
    return item.duration.duration_in_ticks()


@dataclass
class Measure:
    number: int
    notes: list[MeasureItem] = field(default_factory=list)
    time_signature: tuple[int, int] = (4, 4)
    # positive = sharps, negative = flats
    key_signature: int = 0
    clef: str = "treble"
    bar_line_type: str = 'measure_separator'
    text_markings: list[TextMarking] = field(default_factory=list)
    # Braille line this measure's closing bar line was read from. Used only
    # to validate BANA 33.4.3's same-braille-line requirement when a
    # following measure is a whole-measure repeat (S5b-2). 0 = not tracked
    # (e.g. measures built directly in tests, not through BrailleParser).
    line: int = 0

    def add_note(self, note: MeasureItem) -> None:
        self.notes.append(note)

    def total_ticks(self) -> int:
        """Sum this measure's resolved duration, in ticks (quarter = TICKS_PER_QUARTER).

        Shared by `BrailleParser._validate_measure_beat_count` (S5-8) and
        `Staff.to_lilypond()`'s `\\partial` emission for a pickup/anacrusis
        first measure, so both use one tick-accounting rule.
        """
        total = 0
        for item in self.notes:
            if isinstance(item, InAccord):
                # An in-accord's voices all cover the same span (BANA 11.1/
                # 11.1.2 require equal note value per side); use the longest
                # voice so a malformed voice mismatch doesn't silently
                # understate the count.
                if item.parts:
                    total += max(
                        sum(_item_ticks(n) for n in part) for part in item.parts
                    )
            else:
                total += _item_ticks(item)
        return total

    def to_lilypond(self, prev_midi: int = 60) -> tuple[str, int]:
        """Return (lilypond_str, last_midi) for this measure in relative mode.

        Each note is rendered relative to the previous note's absolute MIDI pitch.
        Rests pass the MIDI pitch through unchanged.
        Text markings (expression directions) are prepended before the notes.
        """
        parts: list[str] = []
        for marking in self.text_markings:
            parts.append(marking.to_lilypond())
        cur_midi = prev_midi
        for item in self.notes:
            if hasattr(item, 'to_relative_lilypond'):
                s, cur_midi = item.to_relative_lilypond(cur_midi)
            else:
                s = item.to_lilypond()
            parts.append(s)

        bar_ly = _BAR_LINE_TO_LY.get(self.bar_line_type, '|')
        return ' '.join(parts) + ' ' + bar_ly, cur_midi
