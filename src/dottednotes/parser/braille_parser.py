from __future__ import annotations

import warnings

from ..bana_symbols import NOTE_CELLS, OCTAVE_MARKS, SymbolCategory
from ..models.duration import Duration
from ..models.measure import Measure
from ..models.note import Note
from ..models.score import Score
from ..models.staff import Staff
from .tokenizer import BrailleToken


class BrailleParser:
    """
    Parses a list of BrailleToken objects (from BrailleTokenizer) into a Score.

    State is reset at the start of each parse() call so the same parser
    instance can be reused, but in normal use one parser is created per file.
    """

    def __init__(self, tokens: list[BrailleToken]) -> None:
        self._tokens = tokens

    def parse(self) -> Score:
        self._reset_state()
        score = Score()

        staff = Staff(name="")
        current_measure = Measure(number=1)

        for token in self._tokens:
            if token.category == SymbolCategory.OCTAVE_MARK:
                self._handle_octave_mark(token)
            elif token.category == SymbolCategory.NOTE:
                note = self._handle_note(token)
                current_measure.add_note(note)
            elif token.category == SymbolCategory.BAR_LINE:
                pass  # TODO (S2-5): finalize current_measure, start next
            # REST, ACCIDENTAL, UNKNOWN — TODO in later tickets

        if current_measure.notes:
            staff.add_measure(current_measure)
        if staff.measures:
            score.add_staff(staff)

        return score

    # ------------------------------------------------------------------
    # Token handlers
    # ------------------------------------------------------------------

    def _handle_octave_mark(self, token: BrailleToken) -> None:
        self._current_octave = OCTAVE_MARKS[token.character]

    def _handle_note(self, token: BrailleToken) -> Note:
        note_name, base_duration = NOTE_CELLS[token.character]
        # S2-4 will resolve duration ambiguity (base_duration 1 = whole or 16th,
        # 2 = half or 32nd, 4 = quarter or 64th). For now use base_duration directly,
        # which picks the longer interpretation.
        self._current_base_duration = base_duration
        return Note(
            dots=frozenset(),
            category=SymbolCategory.NOTE,
            raw_brl=token.character,
            note_name=note_name,
            octave=self._current_octave,
            duration=Duration(value=base_duration),
        )

    # ------------------------------------------------------------------
    # Internal state
    # ------------------------------------------------------------------

    def _reset_state(self) -> None:
        self._current_octave: int = 4           # default: one-line octave (middle C)
        self._current_base_duration: int | None = None  # last resolved duration base
        self._key_signature: int = 0            # 0 = C major; positive = sharps, negative = flats
        self._time_signature: tuple[int, int] = (4, 4)  # beats per measure, beat value
        self._short_value_indicator_active: bool = False
        self._beats_used_in_measure: float = 0.0
        self._measure_number: int = 1
