from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .duration import TICKS_PER_QUARTER, ticks_to_lilypond_duration
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
    verses: list[list[str]] = field(default_factory=list)
    verse_prefixes: list[str | None] = field(default_factory=list)
    # (written_pitch, concert_pitch) LilyPond absolute pitches, set by the
    # MusicXML importer (S10b-2) when the source carries structured
    # transposition data -- takes priority over the BRF path's name-string
    # lookup (`get_transposition(staff.name)`) in Score._wrap_transpose,
    # since it covers any instrument, not just the ones in transposition.py's
    # hardcoded _TRANSPOSITIONS table.
    resolved_transposition: tuple[str, str] | None = None


    def add_measure(self, measure: Measure) -> None:
        self.measures.append(measure)

    def to_braille(self) -> str:
        sig_parts = []
        if self.clef:
            sig_parts.append(self.clef.to_braille())
        if self.key_signature:
            sig_parts.append(self.key_signature.to_braille())
        if self.time_signature:
            sig_parts.append(self.time_signature.to_braille())

        sig_str = "".join(sig_parts)

        measure_strs = []
        prev_note = None
        for m in self.measures:
            m_brl, prev_note = m.to_braille(
                prev_note=prev_note,
                is_measure_start=True,
                time_signature=self.time_signature
            )
            measure_strs.append(m_brl)

        return sig_str + "".join(measure_strs)

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

    def to_lilypond(
        self,
        start_midi: int = 60,
        include_clef: bool = True,
        measure_numbers: bool = False,
    ) -> str:
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

        measure_numbers=True (S8-6) prefixes each measure's line with a
        '% N' comment using the real parsed BANA margin number
        (`Measure.number`), not a freshly-enumerated count, so it stays
        correct for non-sequential cases like a 0-numbered pickup measure.
        A consolidated run of whole-measure rests gets a '% N-M' range
        comment instead of just the first measure's number. Defaults to
        off so every existing ground-truth fixture test is unaffected.
        """
        header: list[str] = []
        if self.tempo is not None:
            header.append('    ' + self.tempo.to_lilypond())
        if self.key_signature is not None and self.key_signature.sharps_or_flats != 0:
            header.append('    ' + self.key_signature.to_lilypond())
        if self.time_signature is not None:
            header.append('    ' + self.time_signature.to_lilypond())
            partial_ly = self._resolve_partial()
            if partial_ly is not None:
                header.append('    ' + partial_ly)

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
                if measure_numbers:
                    first_num, last_num = run[0].number, run[-1].number
                    comment = f"% {first_num}" if first_num == last_num else f"% {first_num}-{last_num}"
                    measure_lines.append(f'    {comment}')
                measure_lines.append('    ' + ly_str)
                i = j
            else:
                m = self.measures[i]
                ly_str, prev_midi = m.to_lilypond(prev_midi=prev_midi)
                if measure_numbers:
                    measure_lines.append(f'    % {m.number}')
                measure_lines.append('    ' + ly_str)
                i += 1

        return '\n'.join(header + measure_lines)

    def resolve_clef(self) -> str | None:
        """Public accessor for this staff's resolved \\clef directive (S5b-8),
        for callers that render it separately from to_lilypond()'s own output
        (e.g. OrchestraScore.to_lilypond(), which places \\clef in the
        \\score block rather than inside the named music variable)."""
        return self._resolve_clef()

    def _resolve_partial(self) -> str | None:
        """Return a `\\partial <duration>` directive if the first measure is
        a pickup/anacrusis (shorter than a full measure per `time_signature`)
        -- otherwise None. Without this, LilyPond's own bar-check flags every
        downstream `|` as misplaced, since it assumes every measure is full
        length unless told otherwise (Notation Reference, "Upbeats").

        Silently omitted (no `\\partial`, keeping today's behavior) when the
        first measure's length doesn't correspond to a single plain
        (undotted/1-2-dot) note duration -- e.g. a pickup built from several
        notes/rests whose sum isn't itself one note value -- rather than
        emitting an approximate or guessed duration.
        """
        if self.time_signature is None or not self.measures:
            return None
        first_ticks = self.measures[0].total_ticks()
        full_ticks = round(self.time_signature.beats_per_measure() * TICKS_PER_QUARTER)
        if first_ticks <= 0 or first_ticks >= full_ticks:
            return None
        partial_ly = ticks_to_lilypond_duration(first_ticks)
        if partial_ly is None:
            return None
        return f'\\partial {partial_ly}'

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
