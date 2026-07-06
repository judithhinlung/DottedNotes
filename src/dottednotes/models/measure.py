from __future__ import annotations

from dataclasses import dataclass, field
from typing import Union

from .chord import Chord
from .note import Note
from .text_marking import TextMarking

NoteOrChord = Union[Note, Chord]

_BAR_LINE_TO_LY: dict[str, str] = {
    'measure_separator': '|',
    'final_double_bar': r'\bar "|."',
    'section_double_bar': r'\bar "||"',
    'forward_repeat': r'\bar ".|:"',
    'end_repeat': r'\bar ":|."',
}


@dataclass
class Measure:
    number: int
    notes: list[NoteOrChord] = field(default_factory=list)
    time_signature: tuple[int, int] = (4, 4)
    # positive = sharps, negative = flats
    key_signature: int = 0
    clef: str = "treble"
    bar_line_type: str = 'measure_separator'
    text_markings: list[TextMarking] = field(default_factory=list)

    def add_note(self, note: NoteOrChord) -> None:
        self.notes.append(note)

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
