from dataclasses import dataclass, field

from .note import Note


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
