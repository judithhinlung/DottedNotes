from __future__ import annotations

import warnings
from dataclasses import dataclass

from ..bana_symbols import (
    BAR_LINE_CELLS,
    BAR_LINE_SEQUENCES,
    NOTE_CELLS,
    OCTAVE_MARKS,
    SymbolCategory,
)
from ..models.duration import Duration
from ..models.measure import Measure
from ..models.note import Note
from ..models.score import Score
from ..models.staff import Staff
from .tokenizer import BrailleToken


@dataclass
class _PendingNote:
    """A note buffered during measure accumulation, before duration resolution."""
    note_name: str
    octave: int
    base_duration: int   # 1, 2, or 4 from NOTE_CELLS
    raw_brl: str


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
            # REST, ACCIDENTAL, UNKNOWN — TODO in later tickets

        # Finalize the last measure (no trailing blank cell required)
        if pending:
            staff.add_measure(self._finalize_measure(pending, measure_number))

        if staff.measures:
            score.add_staff(staff)

        return score

    # ------------------------------------------------------------------
    # Token handlers
    # ------------------------------------------------------------------

    def _handle_octave_mark(self, token: BrailleToken) -> None:
        self._current_octave = OCTAVE_MARKS[token.character]

    def _buffer_note(self, token: BrailleToken) -> _PendingNote:
        note_name, base_duration = NOTE_CELLS[token.character]
        return _PendingNote(
            note_name=note_name,
            octave=self._current_octave,
            base_duration=base_duration,
            raw_brl=token.character,
        )

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
        measure = Measure(
            number=number,
            time_signature=self._time_signature,
            bar_line_type=bar_line_type,
        )
        for pnote, dur_value in zip(pending, resolved):
            measure.add_note(Note(
                dots=frozenset(),
                category=SymbolCategory.NOTE,
                raw_brl=pnote.raw_brl,
                note_name=pnote.note_name,
                octave=pnote.octave,
                duration=Duration(value=dur_value),
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
        beats = float(self._time_signature[0])
        count_2 = sum(1 for n in pending if n.base_duration == 2)
        resolve_2 = 32 if count_2 * 2.0 > beats else 2

        resolved = [0] * len(pending)
        state = "normal"  # "normal" | "run" | "individual"

        for i, n in enumerate(pending):
            next_bd = pending[i + 1].base_duration if i + 1 < len(pending) else None

            if n.base_duration == 1:
                if state == "individual":
                    resolved[i] = 16
                    # state stays "individual"
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
                    # state stays "run"
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
        beats_expected = float(self._time_signature[0])
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
        self._key_signature: int = 0
        self._time_signature: tuple[int, int] = (4, 4)
        self._measure_number: int = 1
