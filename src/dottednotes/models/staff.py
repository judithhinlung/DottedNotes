from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .measure import Measure
from .text_marking import TextMarking

if TYPE_CHECKING:
    from .clef import Clef, ClefType
    from .key_signature import KeySignature
    from .time_signature import TimeSignature


@dataclass
class Staff:
    name: str
    measures: list[Measure] = field(default_factory=list)
    # Set by the parser only when these cells are explicitly present in the BRF file.
    # None means "not parsed from file" — to_lilypond() will omit the directive.
    key_signature: KeySignature | None = None
    time_signature: TimeSignature | None = None
    clef: Clef | None = None
    tempo: TextMarking | None = None
    lyrics: list[str] = field(default_factory=list)


    def add_measure(self, measure: Measure) -> None:
        self.measures.append(measure)

    def relative_anchor(self) -> tuple[str, int]:
        """Return (anchor_pitch, start_midi) for this staff's \\relative block.

        Chosen from the staff's first pitched note so that note needs no
        octave marks at all -- the LilyPond idiom hand-engravers use (e.g. a
        bass-register staff opens with `\\relative c`, not `\\relative c'`;
        see tests/fixtures/Children_s_Piece.ly and fingering_melody.ly, whose
        lower/left-hand staves both open on plain `c`). Falls back to middle
        C (`c'`, MIDI 60) when the staff has no pitched notes.
        """
        octave = self._first_note_octave()
        if octave is None:
            octave = 4
        base = 3  # octave 3 = plain "c" (matches Note._octave_marks's convention)
        if octave < base:
            marks = ',' * (base - octave)
        elif octave > base:
            marks = "'" * (octave - base)
        else:
            marks = ''
        start_midi = 12 * (octave + 1)  # MIDI pitch of C in that octave (C4 = 60)
        return f'c{marks}', start_midi

    def to_lilypond(self, start_midi: int = 60, include_clef: bool = True) -> str:
        """Return indented LilyPond lines for all measures in relative mode,
        preceded by \\key / \\time / \\clef directives.

        Clef selection (LilyPond requires an explicit clef for almost every piece,
        even though BANA braille music rarely contains clef cells):
          1. Explicit clef cell parsed from the BRF file → use it.
          2. Heuristic: first pitched note at octave 4+ → treble; octave 3 or
             below → bass.  This handles the common piano/orchestra case until
             the parser can read literary-braille part labels (a later sprint).
          3. No notes → no \\clef directive emitted.

        include_clef=False omits the \\clef directive from this output (S5b-8's
        OrchestraScore.to_lilypond() places \\clef in the \\score block's
        per-staff body instead of inside the named music variable -- see
        resolve_clef() for getting the same directive separately).
        """
        header: list[str] = []
        if self.tempo is not None:
            header.append('    ' + self.tempo.to_lilypond())
        if self.key_signature is not None and self.key_signature.sharps_or_flats != 0:
            header.append('    ' + self.key_signature.to_lilypond())
        if self.time_signature is not None:
            header.append('    ' + self.time_signature.to_lilypond())

        if include_clef:
            clef_ly = self._resolve_clef()
            if clef_ly is not None:
                header.append('    ' + clef_ly)

        from .note import Rest

        prev_midi = start_midi
        measure_lines: list[str] = []

        i = 0
        while i < len(self.measures):
            # Look ahead to see if we can start/continue a run of rests
            run = []
            j = i
            while j < len(self.measures):
                m = self.measures[j]
                is_simple_rest = (
                    len(m.notes) == 1 and
                    isinstance(m.notes[0], Rest) and
                    m.notes[0].is_full_measure and
                    not m.text_markings
                )
                if not is_simple_rest:
                    break

                if run and m.notes[0].duration != run[0].notes[0].duration:
                    break

                run.append(m)
                if m.bar_line_type != 'measure_separator':
                    j += 1
                    break
                j += 1

            if len(run) >= 2:
                first_rest = run[0].notes[0]
                count = len(run)
                compressed_rest = Rest(
                    dots=first_rest.dots,
                    category=first_rest.category,
                    raw_brl=first_rest.raw_brl,
                    duration=first_rest.duration,
                    is_full_measure=True,
                    multi_measure_count=count,
                )
                ly_str = compressed_rest.to_lilypond()
                last_m = run[-1]
                if last_m.bar_line_type != 'measure_separator':
                    from .measure import _BAR_LINE_TO_LY
                    bar_ly = _BAR_LINE_TO_LY.get(last_m.bar_line_type, '|')
                    ly_str += f" {bar_ly}"
                else:
                    ly_str += " |"
                measure_lines.append('    ' + ly_str)
                i = j
            else:
                m = self.measures[i]
                ly_str, prev_midi = m.to_lilypond(prev_midi=prev_midi)
                measure_lines.append('    ' + ly_str)
                i += 1

        return '\n'.join(header + measure_lines)

    def resolve_clef(self) -> str | None:
        """Public accessor for this staff's resolved \\clef directive (S5b-8),
        for callers that render it separately from to_lilypond()'s own output
        (e.g. OrchestraScore.to_lilypond(), which places \\clef in the
        \\score block rather than inside the named music variable)."""
        return self._resolve_clef()

    def _resolve_clef(self) -> str | None:
        """Return the LilyPond clef directive string, or None if there are no notes."""
        if self.clef is not None:
            return self.clef.to_lilypond()
        octave = self._first_note_octave()
        if octave is None:
            return None
        return r'\clef treble' if octave >= 4 else r'\clef bass'

    def _first_note_octave(self) -> int | None:
        """Return the octave of the first pitched note, or None if none exists."""
        for measure in self.measures:
            for item in measure.notes:
                if hasattr(item, 'octave'):
                    return item.octave  # type: ignore[attr-defined]
        return None
