from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .duration import TICKS_PER_QUARTER, ticks_to_lilypond_duration
from .measure import Measure
from .metronome_mark import MetronomeMark
from .text_marking import TextMarking, TextMarkingType

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
    # BANA Sec. 1.8 heading metronome mark (e.g. "quarter note = 120"),
    # independent of `tempo` -- a word-sign tempo term and a metronome mark
    # can co-occur (Example 1.7-2: "Piu tosto lento e appassionato" on one
    # line, the metronome marking and signatures on the next). Combined into
    # one `\tempo` directive by to_lilypond() below when both are present.
    metronome: MetronomeMark | None = None
    # BANA Sec. 1.4's title, when the solo/single-line parser finds a
    # header word-sign expression that isn't a recognized tempo/mood term
    # (TEMPO_TERMS) -- kept separate from `tempo` (S12-2) so a piece with
    # both a title and a tempo marking (e.g. "Mystery Melody for Violin"
    # followed by "Allegro moderato") renders both, instead of the second
    # header word-sign silently overwriting the first in a single shared
    # slot. Rendered as its own \mark \markup{} ahead of \tempo -- see
    # to_lilypond().
    title_marking: TextMarking | None = None
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
    # \set Staff.midiInstrument value (S12-1, BANA Sec. 24 single-line
    # format): set only by the CLI/web API's explicit --instrument
    # selection, since a single-line-format piece's braille never states
    # its own instrument (see cli.py). None means "not user-supplied" --
    # to_lilypond() then omits both \set directives, matching every other
    # BRF-sourced score, whose staff naming has always come from BANA Sec.
    # 33.2's ensemble header or a piano hand's fixed "right hand"/"left
    # hand", never a bare "set an instrument" toggle like this one.
    midi_instrument: str | None = None


    def add_measure(self, measure: Measure) -> None:
        self.measures.append(measure)

    def title_text(self) -> str | None:
        """Best-effort title text for instrument inference (S12-3), e.g.
        deciding a single-line-format piece's default --instrument from
        "Mystery Melody for Violin". `title_marking` holds it when this
        staff also has a separate tempo marking (BrailleParser's
        title/tempo shift, S12-2). But a piece with *only* one header
        word-sign and no tempo line at all -- just a title, nothing else
        -- leaves that single marking in `tempo` untouched (preserving the
        single-marking case existing tests rely on, e.g. a lone "dolce" or
        "Allegro") -- so a non-TEMPO-typed `tempo` marking is a title too
        in that case.
        """
        if self.title_marking is not None:
            return self.title_marking.text
        if self.tempo is not None and self.tempo.type != TextMarkingType.TEMPO:
            return self.tempo.text
        return None

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
          2. Conventional clef for this staff's instrument name (S10d-12), e.g.
             Violin I/II → treble, Viola → alto, Violoncello/Double bass → bass
             (models/instrument.py's get_default_clef()) → use it. This is a
             fixed notational convention, not a function of register, so it
             takes priority over the octave heuristic below -- a second violin
             passage that dips below middle C is still written in treble clef.
          3. Heuristic: first pitched note at octave 4+ → treble; octave 3 or
             below → bass. get_default_clef() deliberately returns None for
             piano/harp hands (no fixed convention -- a left hand can cross
             into treble territory) and unpitched percussion, so this
             heuristic remains the resolution path for those staves.
          4. No notes → no \\clef directive emitted.

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
        if self.title_marking is not None:
            header.append('    ' + self.title_marking.to_lilypond())
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

        # Unconditional (not gated by include_clef): OrchestraScore's
        # \with{}-block rendering (include_clef=False) still needs tempo in
        # this staff's own music-variable content -- ensemble_parser.py
        # propagates a shared staff.tempo across staves, and that must
        # keep rendering there exactly as it did before title_marking
        # existed. Positioned after the (possibly skipped) clef so a solo
        # staff's header reads title, key, time, clef, tempo -- matching
        # BANA's own Sec. 1.7 Music Heading order (tempo/mood text last,
        # right before the music starts).
        if self.metronome is not None:
            # Combine with any separate word-sign tempo term (BANA Sec.
            # 1.7-2: a tempo term and a metronome mark can appear together)
            # into a single `\tempo "text" 4 = 120` directive.
            header.append('    ' + self.metronome.to_lilypond(
                text=self.tempo.text if self.tempo is not None else None
            ))
        elif self.tempo is not None:
            header.append('    ' + self.tempo.to_lilypond())

        if include_clef:
            # S12-1: only emitted when the CLI/web API's --instrument
            # selection set this explicitly (see midi_instrument's field
            # comment) -- nested inside include_clef so OrchestraScore's
            # \with{}-block rendering (include_clef=False) never gets this
            # a second time from its own separate instrumentName/
            # midiInstrument emission in orchestra_score.py.
            if self.midi_instrument is not None:
                header.append(f'    \\set Staff.instrumentName = "{self.name}"')
                header.append(f'    \\set Staff.midiInstrument = "{self.midi_instrument}"')

        from .note import Rest
        from .key_signature import KeySignature as _KeySignature

        prev_midi = start_midi
        measure_lines: list[str] = []

        volta_groups_by_start = {g['shared_start']: g for g in self._find_volta_groups()}

        # Tracks the last (sharps_or_flats, mode) pair actually emitted as a
        # `\key` directive, seeded from the header -- S11-2. Whenever a
        # measure's own effective key differs from this, a fresh `\key`
        # directive is emitted right before that measure's content (BANA
        # Par. 6.5: "a change of key is placed wherever it occurs").
        last_key = (
            (self.key_signature.sharps_or_flats, self.key_signature.mode)
            if self.key_signature is not None else (0, "major")
        )

        i = 0
        while i < len(self.measures):
            if i in volta_groups_by_start:
                group = volta_groups_by_start[i]
                group_lines, prev_midi, last_key = self._render_volta_group(
                    group, prev_midi, measure_numbers, last_key
                )
                measure_lines.extend(group_lines)
                i = group['group_end']
                continue

            current_key = (self.measures[i].key_signature, self.measures[i].key_signature_mode)
            if current_key != last_key:
                key_sig = _KeySignature(
                    dots=frozenset(), category=None, raw_brl="",
                    sharps_or_flats=current_key[0], mode=current_key[1],
                )
                measure_lines.append('    ' + key_sig.to_lilypond())
                last_key = current_key

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

                # A key change mid-run must not be silently absorbed into a
                # compressed multi-measure rest (S11-2) -- same shape as the
                # duration-break check above.
                if run and (m.key_signature, m.key_signature_mode) != (
                    run[0].key_signature, run[0].key_signature_mode
                ):
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
                ly_str, prev_midi = m.to_lilypond(prev_midi=prev_midi, key_signature_mode=m.key_signature_mode)
                if measure_numbers:
                    measure_lines.append(f'    % {m.number}')
                measure_lines.append('    ' + ly_str)
                i += 1

        return '\n'.join(header + measure_lines)

    def _find_volta_groups(self) -> list[dict]:
        """Scan `self.measures` for BANA/print first-second-ending repeat
        sections (Chapter 17, Par. 17.1.1) and return them as structured
        groups for `to_lilypond()`'s `\\repeat volta`/`\\alternative`
        rendering.

        Each group is a dict:
            {'shared_start': int, 'shared_end': int,
             'branches': [(start, end, ending_numbers), ...],
             'group_end': int}
        where all indices are into `self.measures`, `shared_end` is where
        the first \\volta branch begins, and `group_end` is one past the
        last measure of the last branch.

        The shared (repeated) section's start is found by looking
        backward from the first ending-numbered measure for the nearest
        `bar_line_type == 'forward_repeat'` measure -- that type means
        "the repeat starts at the NEXT measure" (this codebase's tested
        convention; see the fix alongside this feature in
        `parser/musicxml_parser.py`/`renderers/musicxml_renderer.py` for
        why it's not the measure carrying the marking itself). If none is
        found since the end of the previous volta group (or the start of
        the staff), every measure back that far is treated as shared --
        a reasonable default, but one that could pull in unrelated earlier
        material for a piece where the shared section doesn't begin with
        an explicit forward-repeat bar line.
        """
        groups: list[dict] = []
        n = len(self.measures)
        i = 0
        consumed_up_to = 0
        while i < n:
            if self.measures[i].ending_numbers:
                first_ending_idx = i
                shared_start = consumed_up_to
                for k in range(first_ending_idx - 1, consumed_up_to - 1, -1):
                    if self.measures[k].bar_line_type == 'forward_repeat':
                        shared_start = k + 1
                        break

                branches: list[tuple[int, int, list[int]]] = []
                j = first_ending_idx
                while j < n and self.measures[j].ending_numbers:
                    numbers = self.measures[j].ending_numbers
                    branch_start = j
                    while j < n and self.measures[j].ending_numbers == numbers:
                        j += 1
                    branches.append((branch_start, j, numbers))

                groups.append({
                    'shared_start': shared_start,
                    'shared_end': first_ending_idx,
                    'branches': branches,
                    'group_end': j,
                })
                consumed_up_to = j
                i = j
            else:
                i += 1
        return groups

    def _render_volta_group(
        self, group: dict, prev_midi: int, measure_numbers: bool,
        last_key: tuple[int, str] = (0, "major"),
    ) -> tuple[list[str], int, tuple[int, str]]:
        """Render one `_find_volta_groups()` entry as
        `\\repeat volta N { ... } \\alternative { \\volta k { ... } ... }`
        (LilyPond Notation Reference Sec. 4.1.3).

        `\\repeat volta`, `\\alternative`, and `\\volta k` are complete
        no-ops for `\\relative` pitch tracking -- verified against the real
        `lilypond` 2.24.4 binary's `\\displayLilyMusic` output, the same way
        this project verified `<< \\\\ >>`'s sequential (not per-voice)
        chaining (see CLAUDE.md's Known Issues and
        `InAccord.to_relative_lilypond()`). So `prev_midi` threads straight
        through the shared section into the first `\\volta` branch, from
        that branch's last note into the next branch, and so on -- the
        value returned here is the LAST branch's ending pitch, matching
        what a real `lilypond` run continues from after the `\\alternative`
        block closes.

        `\\key` behaves the same way (S11-2) -- reverified directly against
        the real `lilypond` 2.26.0 binary's `\\displayLilyMusic` output for
        this specific construct (a `\\key` inside `\\repeat volta`/
        `\\volta` is preserved literally in the linear token stream, with
        no scoping/reset at any of those block boundaries), so `last_key`
        threads through exactly like `cur_midi`: sequentially through the
        shared section, then branch by branch, returning the LAST branch's
        ending key.
        """
        from .key_signature import KeySignature as _KeySignature

        lines: list[str] = []
        cur_midi = prev_midi
        cur_key = last_key

        def _emit_key_if_changed(m: Measure, indent: str) -> None:
            nonlocal cur_key
            key_pair = (m.key_signature, m.key_signature_mode)
            if key_pair != cur_key:
                key_sig = _KeySignature(
                    dots=frozenset(), category=None, raw_brl="",
                    sharps_or_flats=key_pair[0], mode=key_pair[1],
                )
                lines.append(indent + key_sig.to_lilypond())
                cur_key = key_pair

        repeat_count = len(group['branches'])
        lines.append(f'    \\repeat volta {repeat_count} {{')
        for idx in range(group['shared_start'], group['shared_end']):
            m = self.measures[idx]
            _emit_key_if_changed(m, '        ')
            ly_str, cur_midi = m.to_lilypond(prev_midi=cur_midi, key_signature_mode=m.key_signature_mode)
            if measure_numbers:
                lines.append(f'        % {m.number}')
            lines.append('        ' + ly_str)
        lines.append('    }')

        lines.append('    \\alternative {')
        for branch_start, branch_end, numbers in group['branches']:
            numbers_str = ','.join(str(n) for n in numbers)
            lines.append(f'        \\volta {numbers_str} {{')
            for idx in range(branch_start, branch_end):
                m = self.measures[idx]
                _emit_key_if_changed(m, '            ')
                ly_str, cur_midi = m.to_lilypond(prev_midi=cur_midi, key_signature_mode=m.key_signature_mode)
                if measure_numbers:
                    lines.append(f'            % {m.number}')
                lines.append('            ' + ly_str)
            lines.append('        }')
        lines.append('    }')

        return lines, cur_midi, cur_key

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

        from .clef import CLEF_TO_LILYPOND
        from .instrument import get_default_clef
        default_clef = get_default_clef(self.name)
        if default_clef is not None:
            return f'\\clef {CLEF_TO_LILYPOND[default_clef]}'

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
