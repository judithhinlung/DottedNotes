from __future__ import annotations

import warnings
from dataclasses import dataclass, field

from ..bana_symbols import (
    ACCIDENTAL_CELLS,
    ARTICULATION_CELLS,
    BAR_LINE_CELLS,
    BAR_LINE_SEQUENCES,
    CLEF_CELLS,
    KEY_SIGNATURE_CELLS,
    NOTE_CELLS,
    OCTAVE_MARKS,
    TIME_SIGNATURE_CELLS,
    SymbolCategory,
)
from ..models.accidental import Accidental, AccidentalType
from ..models.articulation import Articulation, ArticulationType
from ..models.clef import Clef, ClefType
from ..models.duration import Duration
from ..models.key_signature import KeySignature
from ..models.measure import Measure
from ..models.note import Note
from ..models.score import Score
from ..models.staff import Staff
from ..models.time_signature import TimeSignature
from .tokenizer import BrailleToken


_STR_TO_ACCIDENTAL_TYPE: dict[str, AccidentalType] = {
    'sharp':   AccidentalType.SHARP,
    'flat':    AccidentalType.FLAT,
    'natural': AccidentalType.NATURAL,
}

_STR_TO_ARTICULATION_TYPE: dict[str, ArticulationType] = {
    'staccato':          ArticulationType.STACCATO,
    'staccatissimo':     ArticulationType.STACCATISSIMO,
    'mezzo_staccato':    ArticulationType.MEZZO_STACCATO,
    'tenuto':            ArticulationType.TENUTO,
    'accent':            ArticulationType.ACCENT,
    'expressive_accent': ArticulationType.EXPRESSIVE_ACCENT,
    'swell':             ArticulationType.SWELL,
}


@dataclass
class _PendingNote:
    """A note buffered during measure accumulation, before duration resolution."""
    note_name: str
    octave: int
    base_duration: int   # 1, 2, 4, or 8 from NOTE_CELLS
    raw_brl: str
    accidental: Accidental | None = None
    articulations: list[Articulation] = field(default_factory=list)


class BrailleParser:
    """
    Parses a list of BrailleToken objects (from BrailleTokenizer) into a Score.

    Duration ambiguity is resolved at the measure level.  The parser buffers
    all notes in a measure, then at the measure boundary decides whether each
    ambiguous group should use the long or short interpretation:

      base_duration 1 (whole/16th): if treating all as whole notes overflows
          the time signature → all become 16th notes; otherwise all whole.
      base_duration 2 (half/32nd):  if treating all as half notes overflows
          the time signature → all become 32nd notes; otherwise all half.
      base_duration 4:              always quarter for now.

    Key / time / clef tokens update internal state and are attached to the
    Staff so that Staff.to_lilypond() can emit the appropriate directives.

    State is reset at the start of each parse() call.
    """

    def __init__(self, tokens: list[BrailleToken]) -> None:
        self._tokens = tokens

    def parse(self) -> Score:
        self._reset_state()
        score = Score()
        staff = Staff(name="")
        pending: list[_PendingNote] = []
        measure_number = 1

        for token in self._tokens:
            if token.category == SymbolCategory.OCTAVE_MARK:
                self._handle_octave_mark(token)
            elif token.category == SymbolCategory.NOTE:
                pending.append(self._buffer_note(token))
            elif token.category == SymbolCategory.BAR_LINE:
                if pending:
                    bar_type = (
                        BAR_LINE_SEQUENCES.get(token.character)
                        or BAR_LINE_CELLS.get(token.character, 'measure_separator')
                    )
                    staff.add_measure(
                        self._finalize_measure(pending, measure_number, bar_type)
                    )
                    pending = []
                    measure_number += 1
            elif token.category == SymbolCategory.KEY_SIGNATURE:
                self._handle_key_signature(token)
            elif token.category == SymbolCategory.TIME_SIGNATURE:
                self._handle_time_signature(token)
            elif token.category == SymbolCategory.CLEF:
                self._handle_clef(token)
            elif token.category == SymbolCategory.ACCIDENTAL:
                self._handle_accidental(token)
            elif token.category == SymbolCategory.ARTICULATION:
                self._handle_articulation(token)
            # REST, UNKNOWN — handled in later tickets

        # Finalize the last measure (no trailing blank cell required)
        if pending:
            staff.add_measure(self._finalize_measure(pending, measure_number))

        # Attach parsed header state to the staff
        if self._key_signature_parsed:
            staff.key_signature = self._key_signature
        if self._time_signature_parsed:
            staff.time_signature = self._time_signature
        if self._clef_parsed:
            staff.clef = self._clef

        if staff.measures:
            score.add_staff(staff)

        return score

    # ------------------------------------------------------------------
    # Token handlers
    # ------------------------------------------------------------------

    def _handle_octave_mark(self, token: BrailleToken) -> None:
        self._current_octave = OCTAVE_MARKS[token.character]

    def _handle_accidental(self, token: BrailleToken) -> None:
        self._pending_accidental = Accidental(
            dots=frozenset(),
            category=SymbolCategory.ACCIDENTAL,
            raw_brl=token.character,
            type=_STR_TO_ACCIDENTAL_TYPE[ACCIDENTAL_CELLS[token.character]],
        )

    def _handle_articulation(self, token: BrailleToken) -> None:
        art_type = _STR_TO_ARTICULATION_TYPE[ARTICULATION_CELLS[token.character]]

        if art_type in self._active_articulations:
            # Terminator: next note gets this articulation, then carry mode ends.
            self._pending_articulations.append(Articulation(type=art_type))
            self._terminating_articulations.add(art_type)
            self._last_articulation_seen = None
        elif art_type == self._last_articulation_seen:
            # Same sign twice with no note between → doubled sign → activate carry.
            # The first occurrence already added to _pending_articulations so the
            # first note of the run will still carry the articulation.
            self._active_articulations.add(art_type)
            self._last_articulation_seen = None
        else:
            # Normal single sign: applies to the next note only.
            self._pending_articulations.append(Articulation(type=art_type))
            self._last_articulation_seen = art_type

    def _buffer_note(self, token: BrailleToken) -> _PendingNote:
        note_name, base_duration = NOTE_CELLS[token.character]
        accidental = self._pending_accidental
        self._pending_accidental = None

        # Combine single-note pending articulations with carried articulations.
        # Pending types take priority; carried types fill in what isn't already present.
        pending_types = {a.type for a in self._pending_articulations}
        articulations = list(self._pending_articulations)
        for art_type in self._active_articulations:
            if art_type not in pending_types:
                articulations.append(Articulation(type=art_type))

        self._pending_articulations = []
        # End carry for any articulations that were just terminated.
        for art_type in self._terminating_articulations:
            self._active_articulations.discard(art_type)
        self._terminating_articulations = set()
        self._last_articulation_seen = None  # note breaks doubled-sign detection

        return _PendingNote(
            note_name=note_name,
            octave=self._current_octave,
            base_duration=base_duration,
            raw_brl=token.character,
            accidental=accidental,
            articulations=articulations,
        )

    def _handle_key_signature(self, token: BrailleToken) -> None:
        self._key_signature = KeySignature(
            dots=frozenset(),
            category=SymbolCategory.KEY_SIGNATURE,
            raw_brl=token.character,
            sharps_or_flats=KEY_SIGNATURE_CELLS[token.character],
        )
        self._key_signature_parsed = True

    def _handle_time_signature(self, token: BrailleToken) -> None:
        numerator, denominator = TIME_SIGNATURE_CELLS[token.character]
        self._time_signature = TimeSignature(
            dots=frozenset(),
            category=SymbolCategory.TIME_SIGNATURE,
            raw_brl=token.character,
            numerator=numerator,
            denominator=denominator,
        )
        self._time_signature_parsed = True

    def _handle_clef(self, token: BrailleToken) -> None:
        _str_to_clef_type: dict[str, ClefType] = {
            'treble': ClefType.TREBLE,
            'bass':   ClefType.BASS,
            'alto':   ClefType.ALTO,
            'tenor':  ClefType.TENOR,
        }
        self._clef = Clef(
            dots=frozenset(),
            category=SymbolCategory.CLEF,
            raw_brl=token.character,
            clef_type=_str_to_clef_type[CLEF_CELLS[token.character]],
        )
        self._clef_parsed = True

    # ------------------------------------------------------------------
    # Measure finalization and duration resolution
    # ------------------------------------------------------------------

    def _finalize_measure(
        self,
        pending: list[_PendingNote],
        number: int,
        bar_line_type: str = 'measure_separator',
    ) -> Measure:
        resolved = self._resolve_measure_durations(pending)
        measure = Measure(number=number, bar_line_type=bar_line_type)
        for pnote, dur_value in zip(pending, resolved):
            measure.add_note(Note(
                dots=frozenset(),
                category=SymbolCategory.NOTE,
                raw_brl=pnote.raw_brl,
                note_name=pnote.note_name,
                octave=pnote.octave,
                duration=Duration(value=dur_value),
                accidental=pnote.accidental,
                articulations=pnote.articulations,
            ))
        self._validate_measure_beat_count(measure)
        return measure

    def _resolve_measure_durations(
        self, pending: list[_PendingNote]
    ) -> list[int]:
        """
        Resolve ambiguous note durations for a complete measure.

        A three-state machine processes notes left to right:

        NORMAL (initial state):
          base_1, next is base_8  → 16th, enter RUN
          base_1, next is base_1  → 16th, enter INDIVIDUAL
          base_1, otherwise       → whole note, stay NORMAL
          base_8                  → genuine 8th, stay NORMAL
          base_2 / base_4         → half/32nd or quarter, stay NORMAL

        RUN (a single base_1 cell started a run; base_8 cells are 16th):
          base_8                  → 16th (run continuation), stay RUN
          base_1, next is base_8  → 16th (new run leader), stay RUN
          base_1, next is base_1  → 16th, enter INDIVIDUAL
          base_1, otherwise       → whole note, enter NORMAL
          base_2 / base_4         → half/32nd or quarter, enter NORMAL

        INDIVIDUAL (consecutive base_1 cells; each is an individual 16th note):
          base_1                  → 16th, stay INDIVIDUAL
          base_8                  → genuine 8th (NOT a run), enter NORMAL
          base_2 / base_4         → half/32nd or quarter, enter NORMAL

        Key rule: only a single base_1 cell can start a run.  Two or more
        consecutive base_1 cells are individual 16th notes; a base_8 cell
        that follows them is a genuine 8th note, never a run continuation.

        Half/32nd (base_duration 2): count_2 * 2 > beats → all 32nd.
        Quarter (base_duration 4): always quarter.
        """
        beats = self._time_signature.beats_per_measure()
        count_2 = sum(1 for n in pending if n.base_duration == 2)
        resolve_2 = 32 if count_2 * 2.0 > beats else 2

        resolved = [0] * len(pending)
        state = "normal"  # "normal" | "run" | "individual"

        for i, n in enumerate(pending):
            next_bd = pending[i + 1].base_duration if i + 1 < len(pending) else None

            if n.base_duration == 1:
                if state == "individual":
                    resolved[i] = 16
                elif next_bd == 8:
                    resolved[i] = 16
                    state = "run"
                elif next_bd == 1:
                    resolved[i] = 16
                    state = "individual"
                else:
                    resolved[i] = 1  # whole note
                    state = "normal"

            elif n.base_duration == 8:
                if state == "run":
                    resolved[i] = 16
                else:
                    resolved[i] = 8
                    state = "normal"

            elif n.base_duration == 2:
                resolved[i] = resolve_2
                state = "normal"

            else:  # base_duration == 4
                resolved[i] = 4
                state = "normal"

        return resolved

    def _validate_measure_beat_count(self, measure: Measure) -> None:
        """Warn (plain text) if resolved beat count doesn't match the time signature."""
        beats_expected = self._time_signature.beats_per_measure()
        beats_actual = sum(n.duration.duration_in_beats() for n in measure.notes)
        if beats_actual != beats_expected:
            warnings.warn(
                f"Measure {measure.number}: expected {beats_expected} beats "
                f"but counted {beats_actual}. "
                f"Check for notation ambiguity or missing/extra notes.",
                stacklevel=2,
            )

    # ------------------------------------------------------------------
    # Internal state
    # ------------------------------------------------------------------

    def _reset_state(self) -> None:
        self._current_octave: int = 4
        self._key_signature: KeySignature = KeySignature(
            dots=frozenset(),
            category=SymbolCategory.KEY_SIGNATURE,
            raw_brl='',
            sharps_or_flats=0,
        )
        self._time_signature: TimeSignature = TimeSignature(
            dots=frozenset(),
            category=SymbolCategory.TIME_SIGNATURE,
            raw_brl='',
            numerator=4,
            denominator=4,
        )
        self._clef: Clef = Clef(
            dots=frozenset(),
            category=SymbolCategory.CLEF,
            raw_brl='',
            clef_type=ClefType.TREBLE,
        )
        self._key_signature_parsed: bool = False
        self._time_signature_parsed: bool = False
        self._clef_parsed: bool = False
        self._pending_accidental: Accidental | None = None
        self._pending_articulations: list[Articulation] = []
        self._active_articulations: set[ArticulationType] = set()
        self._terminating_articulations: set[ArticulationType] = set()
        self._last_articulation_seen: ArticulationType | None = None
