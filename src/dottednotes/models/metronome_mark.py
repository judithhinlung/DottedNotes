from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MetronomeMark:
    """BANA Music Braille Code 2015, Par. 1.8: a heading metronome
    indication (e.g. "quarter note = 120"). `note_value` is 1/2/4/8
    (whole/half/quarter/eighth), matching both `Duration.value`'s and
    LilyPond's own numbering. `bpm_range_end` is set only for a print
    range like "104-112" (Example 1.8-3).

    A "circa"/"ca."/"about"-equivalent qualifier (Examples 1.8-4/5/6) needs
    no field of its own here: in the source, it's just a header word-sign
    immediately before the mark, so it's already captured as `Staff.tempo`
    by the normal word-sign parsing path and combined back in by
    `to_lilypond`'s `text` parameter -- see `Staff.to_lilypond`.
    """
    note_value: int
    dots: int = 0
    bpm: int = 0
    bpm_range_end: int | None = None

    def to_lilypond(self, text: str | None = None) -> str:
        """Return a complete `\\tempo` directive. `text` is typically the
        staff's separate word-sign tempo term (e.g. "Allegro", or a
        "circa"-equivalent qualifier) -- LilyPond Notation Reference,
        "Metronome marks": `\\tempo "Allegro" 4 = 120` auto-parenthesizes
        the metronome mark when combined with text.
        """
        duration = str(self.note_value) + '.' * self.dots
        bpm_str = (
            f"{self.bpm} - {self.bpm_range_end}"
            if self.bpm_range_end is not None
            else str(self.bpm)
        )
        if text:
            return f'\\tempo "{text}" {duration} = {bpm_str}'
        return f'\\tempo {duration} = {bpm_str}'
