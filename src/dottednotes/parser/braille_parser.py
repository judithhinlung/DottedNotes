from __future__ import annotations

import warnings
from dataclasses import dataclass, field

from ..bana_symbols import (
    ACCIDENTAL_CELLS,
    ACCIACCATURA_INDICATOR,
    ARTICULATION_CELLS,
    BAR_LINE_CELLS,
    BAR_LINE_SEQUENCES,
    CLEF_CELLS,
    DYNAMIC_CELLS,
    GRACE_NOTE_INDICATOR,
    KEY_SIGNATURE_CELLS,
    NOTE_CELLS,
    OCTAVE_MARKS,
    ORNAMENT_CELLS,
    SLUR_CELLS,
    TIME_SIGNATURE_CELLS,
    SymbolCategory,
)
from ..models.accidental import Accidental, AccidentalType
from ..models.articulation import Articulation, ArticulationType
from ..models.clef import Clef, ClefType
from ..models.duration import Duration
from ..models.dynamic import Dynamic, DynamicLevel
from ..models.key_signature import KeySignature
from ..models.measure import Measure
from ..models.note import Note
from ..models.ornament import GraceNote, Ornament, OrnamentType
from ..models.score import Score
from ..models.staff import Staff
from ..models.text_marking import TEMPO_TERMS, TextMarking, TextMarkingType
from ..models.time_signature import TimeSignature
from .tokenizer import BrailleToken


_STR_TO_ACCIDENTAL_TYPE: dict[str, AccidentalType] = {
    'sharp':   AccidentalType.SHARP,
    'flat':    AccidentalType.FLAT,
    'natural': AccidentalType.NATURAL,
}

_STR_TO_DYNAMIC_LEVEL: dict[str, DynamicLevel] = {
    'ppp':               DynamicLevel.PPP,
    'pp':                DynamicLevel.PP,
    'p':                 DynamicLevel.P,
    'mp':                DynamicLevel.MP,
    'mf':                DynamicLevel.MF,
    'f':                 DynamicLevel.F,
    'ff':                DynamicLevel.FF,
    'fff':               DynamicLevel.FFF,
    'sf':                DynamicLevel.SF,
    'sfz':               DynamicLevel.SFZ,
    'fp':                DynamicLevel.FP,
    'crescendo_start':   DynamicLevel.CRESCENDO_START,
    'decrescendo_start': DynamicLevel.DECRESCENDO_START,
    'crescendo_end':     DynamicLevel.CRESCENDO_END,
    'decrescendo_end':   DynamicLevel.DECRESCENDO_END,
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

_STR_TO_ORNAMENT_TYPE: dict[str, OrnamentType] = {
    'trill':                   OrnamentType.TRILL,
    'turn':                    OrnamentType.TURN,
    'inverted_turn':           OrnamentType.INVERTED_TURN,
    'upper_mordent':           OrnamentType.UPPER_MORDENT,
    'extended_upper_mordent':  OrnamentType.EXTENDED_UPPER_MORDENT,
    'lower_mordent':           OrnamentType.MORDENT,
    'extended_lower_mordent':  OrnamentType.EXTENDED_MORDENT,
    'glissando':               OrnamentType.GLISSANDO,
}


@dataclass
class _PendingNote:
    """A note buffered during measure accumulation, before duration resolution."""
    note_name: str
    octave: int
    base_duration: int   # 1, 2, 4, or 8 from NOTE_CELLS
    raw_brl: str
    accidental: Accidental | None = None
    dynamics: list[Dynamic] = field(default_factory=list)
    articulations: list[Articulation] = field(default_factory=list)
    ornaments: list[Ornament] = field(default_factory=list)
    grace_note: GraceNote | None = None
    tie: bool = False
    slur_start: bool = False
    slur_end: bool = False
    slur_bracket_open: bool = False
    slur_bracket_close: bool = False


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
            elif token.category == SymbolCategory.ORNAMENT:
                self._handle_ornament(token, pending)
            elif token.category == SymbolCategory.NOTE:
                if self._pending_grace_note_indicator:
                    # This note cell is a grace note (single indicator or carry start/end).
                    self._pending_grace_notes.append(self._build_grace_note_cell(token))
                    self._pending_grace_note_indicator = False
                    if self._grace_carry_ending:
                        self._grace_carry_active = False
                        self._grace_carry_ending = False
                elif self._grace_carry_active:
                    # Middle grace note in carry mode — no indicator needed.
                    self._pending_grace_notes.append(self._build_grace_note_cell(token))
                else:
                    # Simple slur: single ⠉ between previous note and this one
                    if self._last_token_was_slur and not self._slur_carry_active:
                        if pending:
                            pending[-1].slur_start = True
                        self._pending_slur_end = True
                        self._last_token_was_slur = False
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
            elif token.category == SymbolCategory.DYNAMIC:
                dyn_level = _STR_TO_DYNAMIC_LEVEL[DYNAMIC_CELLS[token.character]]
                dynamic = Dynamic(level=dyn_level)
                if dyn_level in (DynamicLevel.CRESCENDO_END, DynamicLevel.DECRESCENDO_END):
                    # End marks follow the last note of the passage; attach there.
                    if pending:
                        pending[-1].dynamics.append(dynamic)
                else:
                    self._pending_dynamics.append(dynamic)
            elif token.category == SymbolCategory.SLUR:
                self._handle_slur(token, pending)
            elif token.category == SymbolCategory.WORD_SIGN:
                self._handle_word_sign(token, pending, staff)
            # REST, UNKNOWN — handled in later tickets

        # Finalize the last measure (no trailing blank cell required)
        if pending:
            staff.add_measure(self._finalize_measure(pending, measure_number))

        # Warn about orphaned grace note state at end of input
        if self._pending_grace_note_indicator:
            warnings.warn(
                "Grace note indicator at end of input with no following note cell.",
                stacklevel=2,
            )
        if self._pending_grace_notes:
            warnings.warn(
                f"{len(self._pending_grace_notes)} grace note(s) at end of input "
                "with no following main note.",
                stacklevel=2,
            )

        # Attach parsed header state to the staff
        if self._key_signature_parsed:
            staff.key_signature = self._key_signature
        if self._time_signature_parsed:
            staff.time_signature = self._time_signature
        if self._clef_parsed:
            staff.clef = self._clef
        if self._pending_tempo is not None:
            staff.tempo = self._pending_tempo

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

    def _handle_slur(self, token: BrailleToken, pending: list[_PendingNote]) -> None:
        slur_type = SLUR_CELLS[token.character]

        if slur_type == 'tie':
            if pending:
                pending[-1].tie = True

        elif slur_type == 'slur':
            if self._slur_carry_active:
                # Terminator: the next note ends the slurred passage.
                self._pending_slur_end = True
                self._slur_carry_active = False
                self._last_token_was_slur = False
            elif self._last_token_was_slur:
                # Doubled sign detected: activate carry, mark the preceding note.
                if pending:
                    pending[-1].slur_start = True
                self._slur_carry_active = True
                self._last_token_was_slur = False
            else:
                # First single slur sign — wait to see if it's doubled or simple.
                self._last_token_was_slur = True

        elif slur_type == 'slur_bracket_open':
            self._pending_slur_bracket_open = True

        elif slur_type == 'slur_bracket_close':
            if pending:
                pending[-1].slur_bracket_close = True

    def _handle_ornament(self, token: BrailleToken, pending: list[_PendingNote]) -> None:
        char = token.character
        if char == GRACE_NOTE_INDICATOR:
            if self._grace_carry_active:
                # Terminating single sign: next note is the last grace note.
                self._grace_carry_ending = True
                self._pending_grace_note_indicator = True
            elif self._pending_grace_note_indicator:
                # Doubled sign (two indicators in a row, no note between): enter carry mode.
                self._grace_carry_active = True
                # _pending_grace_note_indicator stays True; next note is first grace note.
            else:
                self._pending_grace_note_indicator = True
                self._pending_grace_note_is_long = False
        elif char == ACCIACCATURA_INDICATOR:
            if self._grace_carry_active:
                self._grace_carry_ending = True
                self._pending_grace_note_indicator = True
            elif self._pending_grace_note_indicator:
                self._grace_carry_active = True
            else:
                self._pending_grace_note_indicator = True
                self._pending_grace_note_is_long = True
        elif char in ORNAMENT_CELLS:
            orn_name = ORNAMENT_CELLS[char]
            if orn_name == 'trill':
                self._handle_trill()
            elif orn_name == 'glissando':
                # Glissando follows the note it modifies (not precedes it).
                if pending:
                    pending[-1].ornaments.append(Ornament(type=OrnamentType.GLISSANDO))
                else:
                    warnings.warn(
                        f"Glissando sign at position {token.position} "
                        "has no preceding note to attach to."
                    )
            else:
                self._pending_ornaments.append(
                    Ornament(type=_STR_TO_ORNAMENT_TYPE[orn_name])
                )
                self._last_ornament_was_trill = False

    def _handle_trill(self) -> None:
        if self._trill_carry_active:
            # Terminating sign: this note is the last of the trill series.
            self._pending_ornaments.append(Ornament(type=OrnamentType.TRILL_SPAN_END))
            self._trill_carry_active = False
            self._last_ornament_was_trill = False
        elif self._last_ornament_was_trill:
            # Doubled sign (same sign twice with no note between):
            # upgrade the already-pending TRILL to TRILL_SPAN_START, activate carry.
            for idx, o in enumerate(self._pending_ornaments):
                if o.type == OrnamentType.TRILL:
                    self._pending_ornaments[idx] = Ornament(type=OrnamentType.TRILL_SPAN_START)
            self._trill_carry_active = True
            self._last_ornament_was_trill = False
        else:
            # Simple single trill sign.
            self._pending_ornaments.append(Ornament(type=OrnamentType.TRILL))
            self._last_ornament_was_trill = True

    def _build_grace_note_cell(self, token: BrailleToken) -> Note:
        """Consume a note token as a single grace note pitch (always duration 8)."""
        note_name, _ = NOTE_CELLS[token.character]
        accidental = self._pending_accidental
        self._pending_accidental = None
        return Note(
            dots=frozenset(),
            category=SymbolCategory.NOTE,
            raw_brl=token.character,
            note_name=note_name,
            octave=self._current_octave,
            duration=Duration(value=8),
            accidental=accidental,
        )

    def _buffer_note(self, token: BrailleToken) -> _PendingNote:
        note_name, base_duration = NOTE_CELLS[token.character]
        accidental = self._pending_accidental
        self._pending_accidental = None

        # Capture and clear pre-note dynamics.
        dynamics = list(self._pending_dynamics)
        self._pending_dynamics = []

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

        # Capture and clear pending ornaments.
        ornaments = list(self._pending_ornaments)
        self._pending_ornaments = []
        # A note resets doubled-sign detection for trills, but preserves trill carry state.
        self._last_ornament_was_trill = False

        # Build GraceNote from any accumulated grace note cells.
        grace_note: GraceNote | None = None
        if self._pending_grace_notes:
            grace_note = GraceNote(
                notes=list(self._pending_grace_notes),
                long_appoggiatura=self._pending_grace_note_is_long,
            )
            self._pending_grace_notes = []
            self._pending_grace_note_is_long = False

        # Capture slur/tie state for this note, then clear the pending flags.
        slur_end = self._pending_slur_end
        slur_bracket_open = self._pending_slur_bracket_open
        self._pending_slur_end = False
        self._pending_slur_bracket_open = False

        return _PendingNote(
            note_name=note_name,
            octave=self._current_octave,
            base_duration=base_duration,
            raw_brl=token.character,
            accidental=accidental,
            dynamics=dynamics,
            articulations=articulations,
            ornaments=ornaments,
            grace_note=grace_note,
            slur_end=slur_end,
            slur_bracket_open=slur_bracket_open,
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

    def _handle_word_sign(
        self,
        token: BrailleToken,
        pending: list[_PendingNote],
        staff: Staff,
    ) -> None:
        text = token.character  # already decoded to a plain string by the tokenizer
        marking_type = (
            TextMarkingType.TEMPO
            if text.lower() in TEMPO_TERMS
            else TextMarkingType.EXPRESSION
        )
        marking = TextMarking(text=text, type=marking_type)
        if not pending and not staff.measures:
            # Before the first note and first measure: this is a header tempo/direction.
            self._pending_tempo = marking
        else:
            # Mid-piece: attach to the current (not-yet-finalized) measure.
            self._pending_text_markings.append(marking)

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
        text_markings = list(self._pending_text_markings)
        self._pending_text_markings = []
        measure = Measure(number=number, bar_line_type=bar_line_type, text_markings=text_markings)
        for pnote, dur_value in zip(pending, resolved):
            measure.add_note(Note(
                dots=frozenset(),
                category=SymbolCategory.NOTE,
                raw_brl=pnote.raw_brl,
                note_name=pnote.note_name,
                octave=pnote.octave,
                duration=Duration(value=dur_value),
                accidental=pnote.accidental,
                dynamics=pnote.dynamics,
                articulations=pnote.articulations,
                ornaments=pnote.ornaments,
                grace_note=pnote.grace_note,
                tie=pnote.tie,
                slur_start=pnote.slur_start,
                slur_end=pnote.slur_end,
                slur_bracket_open=pnote.slur_bracket_open,
                slur_bracket_close=pnote.slur_bracket_close,
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
        self._pending_dynamics: list[Dynamic] = []
        self._pending_articulations: list[Articulation] = []
        self._active_articulations: set[ArticulationType] = set()
        self._terminating_articulations: set[ArticulationType] = set()
        self._last_articulation_seen: ArticulationType | None = None
        self._pending_ornaments: list[Ornament] = []
        self._trill_carry_active: bool = False
        self._last_ornament_was_trill: bool = False
        self._pending_grace_note_indicator: bool = False
        self._pending_grace_note_is_long: bool = False
        self._pending_grace_notes: list[Note] = []
        self._grace_carry_active: bool = False
        self._grace_carry_ending: bool = False
        self._last_token_was_slur: bool = False
        self._slur_carry_active: bool = False
        self._pending_slur_end: bool = False
        self._pending_slur_bracket_open: bool = False
        self._pending_tempo: TextMarking | None = None
        self._pending_text_markings: list[TextMarking] = []
