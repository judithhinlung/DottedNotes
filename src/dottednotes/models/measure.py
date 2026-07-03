from dataclasses import dataclass, field

from .note import Note

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
    notes: list[Note] = field(default_factory=list)
    time_signature: tuple[int, int] = (4, 4)
    # positive = sharps, negative = flats
    key_signature: int = 0
    clef: str = "treble"
    bar_line_type: str = 'measure_separator'

    def add_note(self, note: Note) -> None:
        self.notes.append(note)

    def to_lilypond(self, prev_midi: int = 60) -> tuple[str, int]:
        """Return (lilypond_str, last_midi) for this measure in relative mode.

        Each note is rendered relative to the previous note's absolute MIDI pitch.
        Rests pass the MIDI pitch through unchanged.
        """
        parts: list[str] = []
        cur_midi = prev_midi
        for item in self.notes:
            if hasattr(item, 'to_relative_lilypond'):
                s, cur_midi = item.to_relative_lilypond(cur_midi)
            else:
                s = item.to_lilypond()
            parts.append(s)

        bar_ly = _BAR_LINE_TO_LY.get(self.bar_line_type, '|')
        return ' '.join(parts) + ' ' + bar_ly, cur_midi
