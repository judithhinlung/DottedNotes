from __future__ import annotations

from typing import TYPE_CHECKING

from ..models.score import Score

if TYPE_CHECKING:
    from .tokenizer import BrailleToken


class BrailleParser:
    """
    Parses a list of BrailleToken objects (from BrailleTokenizer) into a Score.

    State is reset on each call to parse() so the same parser instance can be
    reused, but in normal use one parser is created per file.
    """

    def __init__(self, tokens: list[BrailleToken]) -> None:
        self._tokens = tokens

    def parse(self) -> Score:
        self._reset_state()
        score = Score()
        # TODO (S2-3): consume OCTAVE_MARK tokens and update _current_octave
        # TODO (S2-4): consume NOTE tokens and resolve duration ambiguity
        # TODO (S2-5): consume BAR_LINE tokens to finalize measures
        return score

    # ------------------------------------------------------------------
    # Internal state
    # ------------------------------------------------------------------

    def _reset_state(self) -> None:
        self._current_octave: int = 4          # default: one-line octave (middle C)
        self._current_base_duration: int | None = None  # last resolved duration base
        self._key_signature: int = 0           # 0 = C major; positive = sharps, negative = flats
        self._time_signature: tuple[int, int] = (4, 4)  # beats per measure, beat value
        self._short_value_indicator_active: bool = False
        self._beats_used_in_measure: float = 0.0
