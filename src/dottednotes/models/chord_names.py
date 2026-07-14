from __future__ import annotations

from dataclasses import dataclass, field

from .chord_symbol import ChordSymbol
from .duration import Duration


@dataclass
class ChordNamesTrack:
    """An ordered list of (duration, chord) entries for a BANA Sec. 27
    lead-sheet chord-symbol line, one entry per melody note/rest, in the
    same rhythmic order as the melody, so the rendered LilyPond ChordNames
    context stays vertically aligned with the staff above it (BANA 27.1:
    "the initial capital sign of each chord symbol is placed below the
    first sign of the note...with which it coincides").

    `chord` is None for a melody note/rest that falls under a still-active
    chord rather than a newly-written symbol (BANA 27.1.2: a chord "is
    assumed to be in effect until it is cancelled by a new symbol") --
    to_lilypond() carries the last seen chord forward for those, and sets
    `\\set chordChanges = ##t` so LilyPond only prints the chord name where
    it actually changes.
    """
    entries: list[tuple[Duration, ChordSymbol | None]] = field(default_factory=list)

    def to_lilypond(self) -> str:
        chords: list[str] = []
        last_chord: ChordSymbol | None = None
        for duration, chord in self.entries:
            current = chord if chord is not None else last_chord
            if current is None:
                raise ValueError(
                    "ChordNamesTrack entry has no chord and no prior chord to hold over."
                )
            last_chord = current
            chords.append(current.to_lilypond(duration=duration.to_lilypond()))
        body = ' '.join(chords)
        return (
            "\\new ChordNames {\n"
            "  \\set chordChanges = ##t\n"
            f"  \\chordmode {{ {body} }}\n"
            "}"
        )
