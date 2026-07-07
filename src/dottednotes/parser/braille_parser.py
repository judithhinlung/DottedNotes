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
    IN_ACCORD_CELLS,
    INTERVAL_CELLS,
    KEY_SIGNATURE_CELLS,
    NOTE_CELLS,
    OCTAVE_MARKS,
    ORNAMENT_CELLS,
    REST_CELLS,
    SLUR_CELLS,
    TIME_SIGNATURE_CELLS,
    SymbolCategory,
)
from ..models.accidental import Accidental, AccidentalType
from ..models.chord import Chord
from ..models.in_accord import InAccord
from ..models.articulation import Articulation, ArticulationType
from ..models.clef import Clef, ClefType
from ..models.duration import Duration
from ..models.dynamic import Dynamic, DynamicLevel
from ..models.key_signature import KeySignature
from ..models.measure import Measure
from ..models.note import Note, Rest
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


_DIATONIC_NOTES = ['C', 'D', 'E', 'F', 'G', 'A', 'B']

# Sharps order: F C G D A E B
_SHARP_ORDER = ['F', 'C', 'G', 'D', 'A', 'E', 'B']
# Flats order: B E A D G C F
_FLAT_ORDER = ['B', 'E', 'A', 'D', 'G', 'C', 'F']


def _key_sig_accidental(note_name: str, sharps_or_flats: int) -> AccidentalType | None:
    """Return the AccidentalType implied by the key signature for this note, or None."""
    if sharps_or_flats > 0:
        if note_name in _SHARP_ORDER[:sharps_or_flats]:
            return AccidentalType.SHARP
    elif sharps_or_flats < 0:
        num_flats = -sharps_or_flats
        if note_name in _FLAT_ORDER[:num_flats]:
            return AccidentalType.FLAT
    return None


def _interval_pitch(
    written_name: str,
    written_octave: int,
    interval_number: int,
    descending: bool,
) -> tuple[str, int]:
    """Return (note_name, octave) for an interval from the written note.

    descending=True for treble/alto clef (intervals go downward from written note).
    descending=False for bass/tenor clef (intervals go upward from written note).
    """
    written_index = _DIATONIC_NOTES.index(written_name)
    steps = interval_number - 1
    raw = written_index - steps if descending else written_index + steps
    note_index = raw % 7
    octave_offset = raw // 7  # Python floor division handles negatives correctly
    return _DIATONIC_NOTES[note_index], written_octave + octave_offset


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
    # Each tuple: (note_name, octave, accidental_or_None)
    interval_notes: list[tuple[str, int, Accidental | None]] = field(default_factory=list)
    dots: int = 0


@dataclass
class _PendingRest:
    """A rest buffered during measure accumulation, before duration resolution."""
    base_duration: int   # 1, 2, or 4 from REST_CELLS
    raw_brl: str
    dots: int = 0


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
        right_staff = Staff(name="right hand")
        left_staff = Staff(name="left hand")
        pending: list[_PendingNote] = []

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
            elif token.category == SymbolCategory.HAND_SIGN:
                self._current_hand = token.character
            elif token.category == SymbolCategory.BAR_LINE:
                if pending:
                    bar_type = (
                        BAR_LINE_SEQUENCES.get(token.character)
                        or BAR_LINE_CELLS.get(token.character, 'measure_separator')
                    )
                    active = left_staff if self._current_hand == 'left' else right_staff
                    active.add_measure(
                        self._finalize_measure(
                            pending,
                            self._next_measure_number_for(active, right_staff, left_staff),
                            bar_type,
                        )
                    )
                    pending = []
                    # Terminate all active interval doublings at double/section bars.
                    if bar_type in ('final_double_bar', 'section_double_bar'):
                        self._active_intervals.clear()
                        self._last_interval_seen = None
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
            elif token.category == SymbolCategory.INTERVAL:
                self._handle_interval(token, pending)
            elif token.category == SymbolCategory.IN_ACCORD:
                self._handle_in_accord(token, pending)
                pending = []
            elif token.category == SymbolCategory.REST:
                pending.append(self._buffer_rest(token))
            elif token.category == SymbolCategory.MEASURE_NUMBER:
                self._handle_measure_number(token)
            elif token.category == SymbolCategory.WORD_SIGN:
                piece_started = bool(right_staff.measures or left_staff.measures)
                self._handle_word_sign(token, pending, piece_started)
            elif token.category == SymbolCategory.AUGMENTATION_DOT:
                if pending:
                    pending[-1].dots = min(pending[-1].dots + 1, 2)
                else:
                    warnings.warn(
                        "Augmentation dot with no preceding note or rest; ignoring.",
                        stacklevel=2,
                    )
            # UNKNOWN — handled in later tickets

        # Finalize the last measure (no trailing blank cell required)
        if pending:
            active = left_staff if self._current_hand == 'left' else right_staff
            active.add_measure(
                self._finalize_measure(
                    pending, self._next_measure_number_for(active, right_staff, left_staff)
                )
            )

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

        # Attach parsed header state. Key/time signature apply to the whole
        # piece, so both hands get them. Clef and tempo are attached to the
        # right hand only (top staff) — this fixture never restates them
        # per hand; see the S5-4 Senior note for the rationale.
        for hand_staff in (right_staff, left_staff):
            if not hand_staff.measures:
                continue
            if self._key_signature_parsed:
                hand_staff.key_signature = self._key_signature
            if self._time_signature_parsed:
                hand_staff.time_signature = self._time_signature
        if self._clef_parsed:
            right_staff.clef = self._clef
        if self._pending_tempo is not None:
            right_staff.tempo = self._pending_tempo

        for hand_staff in (right_staff, left_staff):
            if hand_staff.measures:
                score.add_staff(hand_staff)

        return score

    # ------------------------------------------------------------------
    # Token handlers
    # ------------------------------------------------------------------

    def _handle_octave_mark(self, token: BrailleToken) -> None:
        self._current_octave = OCTAVE_MARKS[token.character]
        self._octave_mark_pending = True

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

    def _handle_interval(self, token: BrailleToken, pending: list[_PendingNote]) -> None:
        """Handle an interval cell, attaching a chord note to the most recent pending note.

        Interval doubling (carry mode):
          - Intervals always come AFTER the note they modify.
          - On the first note: write the interval sign immediately after the note.
            Write the same sign again (no note between) to activate carry.
          - Every subsequent note receives the interval automatically via carry.
          - A single instance of the sign after the LAST carried note is the
            terminator: it does NOT add another interval, it just clears carry.
          - All active doublings terminate simultaneously when any one must be
            terminated (BANA 9.3.3).
          - All active doublings terminate at a double bar or section end.
        """
        interval_number = INTERVAL_CELLS[token.character]

        # If an octave mark was set since the last note, it belongs to this interval.
        if self._octave_mark_pending:
            self._interval_octave_override = self._current_octave
            self._octave_mark_pending = False

        # Case 1: carry is active — this sign after a note is the series terminator.
        if interval_number in self._active_intervals and pending:
            # The preceding note already received this interval via carry in _buffer_note.
            # Terminator: clear all active doublings simultaneously (BANA 9.3.3).
            self._active_intervals.clear()
            self._last_interval_seen = None
            return

        # Case 2: doubled sign detected (same sign seen twice, no note between).
        if interval_number == self._last_interval_seen:
            # Activate carry; first-note application will happen in _buffer_note.
            self._active_intervals[interval_number] = None
            self._last_interval_seen = None
            return

        # Case 3: first occurrence of this sign — could be single or first of doubled.
        self._last_interval_seen = interval_number
        if pending:
            # There is a preceding note: apply immediately as a single-note interval.
            self._apply_interval(interval_number, pending[-1])
        # If no preceding note: just record _last_interval_seen and wait for the
        # next token to determine if this is a doubled sign (carry start) or an error.

    def _apply_interval(
        self,
        interval_number: int,
        pnote: '_PendingNote',
    ) -> None:
        """Compute the interval note's pitch and append it to pnote.interval_notes."""
        clef_str = self._clef.clef_type.name  # 'TREBLE', 'BASS', 'ALTO', 'TENOR'
        descending = clef_str in ('TREBLE', 'ALTO')
        iname, ioctave = _interval_pitch(
            pnote.note_name, pnote.octave, interval_number, descending
        )

        # An explicit octave mark before this interval overrides the calculated octave.
        if self._interval_octave_override is not None:
            ioctave = self._interval_octave_override
            self._interval_octave_override = None

        # An explicit accidental before the interval sign takes priority over the key sig.
        if self._pending_accidental is not None:
            iacc_type = self._pending_accidental.type
            self._pending_accidental = None
        else:
            iacc_type = _key_sig_accidental(iname, self._key_signature.sharps_or_flats)

        iacc: Accidental | None = None
        if iacc_type is not None:
            iacc = Accidental(
                dots=frozenset(),
                category=SymbolCategory.ACCIDENTAL,
                raw_brl='',
                type=iacc_type,
            )

        pnote.interval_notes.append((iname, ioctave, iacc))

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
        self._octave_mark_pending = False  # octave mark was consumed by this note

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

        pnote = _PendingNote(
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

        # Apply any active (carried) intervals to this new note.
        for interval_number in sorted(self._active_intervals):
            self._apply_interval(interval_number, pnote)

        # A note resets doubled-sign detection for intervals.
        self._last_interval_seen = None

        return pnote

    def _buffer_rest(self, token: BrailleToken) -> _PendingRest:
        # An octave mark before a rest is meaningless (rests have no pitch); clear it.
        self._octave_mark_pending = False
        return _PendingRest(
            base_duration=REST_CELLS[token.character],
            raw_brl=token.character,
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
        piece_started: bool,
    ) -> None:
        text = token.character  # already decoded to a plain string by the tokenizer
        marking_type = (
            TextMarkingType.TEMPO
            if text.lower() in TEMPO_TERMS
            else TextMarkingType.EXPRESSION
        )
        marking = TextMarking(text=text, type=marking_type)
        if not pending and not piece_started:
            # Before the first note and first measure of either staff: this is
            # a header tempo/direction.
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

    def _handle_measure_number(self, token: BrailleToken) -> None:
        """Update the current measure number from an explicit margin token.

        Warns (plain text) if the number is not sequential from the running
        internal counter — score may have missing or repeated measures.
        Best-effort parsing continues regardless.
        """
        explicit_number = int(token.character)
        if self._last_margin_measure_number != 0 and explicit_number != self._next_measure_number:
            warnings.warn(
                f"Line {token.line}: measure number {explicit_number} found, "
                f"expected {self._next_measure_number}. "
                "Score may have missing or repeated measures.",
                stacklevel=2,
            )
        self._next_measure_number = explicit_number
        self._last_margin_measure_number = explicit_number

    def _next_measure_number_for(
        self, active: Staff, right_staff: Staff, left_staff: Staff
    ) -> int:
        """Return the measure number to assign to the measure being finalized on `active`.

        BANA margin numbers are only ever restated on right-hand lines, so
        the shared `_next_measure_number` counter must advance only for the
        right hand. Left-hand measures mirror the right hand's measure at
        the same position, since a system's right-hand line (and all of its
        bar lines) always fully precedes its paired left-hand line in the
        token stream.
        """
        if active is left_staff:
            idx = len(left_staff.measures)
            if idx < len(right_staff.measures):
                return right_staff.measures[idx].number
            return self._next_measure_number
        number = self._next_measure_number
        self._next_measure_number += 1
        return number

    def _handle_in_accord(
        self, token: BrailleToken, pending: list[_PendingNote]
    ) -> None:
        """Handle an in-accord separator token (BANA 11.1).

        ⠣⠜ (full_measure, 11.1.1): snapshots `pending` as one voice part and
        appends it to `_in_accord_parts` — both voices span the whole measure.
        ⠐⠂ (part_measure, 11.1.2): snapshots `pending` as one voice part within
        the current temporal section.
        ⠨⠅ (measure_division, 11.1.2): closes the current section (appending
        its final voice part) and starts a new section.
        In all three cases, resets accidental state per BANA 11.2.
        """
        in_accord_type = IN_ACCORD_CELLS[token.character]

        if in_accord_type == 'full_measure':
            self._in_accord_parts.append(self._finalize_voice_part(pending))
        elif in_accord_type == 'part_measure':
            self._current_section_parts.append(self._finalize_voice_part(pending))
        elif in_accord_type == 'measure_division':
            self._current_section_parts.append(self._finalize_voice_part(pending))
            self._in_accord_sections.append(list(self._current_section_parts))
            self._current_section_parts = []

        # BANA 11.2: accidentals written before an in-accord sign do not carry
        # over to notes written after the sign.
        self._pending_accidental = None
        self._in_accord_type = in_accord_type

    # ------------------------------------------------------------------
    # Measure finalization and duration resolution
    # ------------------------------------------------------------------

    def _finalize_voice_part(self, pending: list[_PendingNote]) -> list:
        """Build a list of Note/Chord objects from pending notes with resolved durations.

        Extracted from _finalize_measure so that in-accord voices can each be
        processed independently.
        """
        resolved = self._resolve_measure_durations(pending)
        items: list = []
        for pnote, dur_value in zip(pending, resolved):
            dur = Duration(value=dur_value, dots=pnote.dots)
            if isinstance(pnote, _PendingRest):
                is_full = (
                    len(pending) == 1
                    and dur.duration_in_beats() == self._time_signature.beats_per_measure()
                )
                items.append(Rest(
                    dots=frozenset(),
                    category=SymbolCategory.REST,
                    raw_brl=pnote.raw_brl,
                    duration=dur,
                    is_full_measure=is_full,
                ))
                continue
            written = Note(
                dots=frozenset(),
                category=SymbolCategory.NOTE,
                raw_brl=pnote.raw_brl,
                note_name=pnote.note_name,
                octave=pnote.octave,
                duration=dur,
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
            )
            if pnote.interval_notes:
                chord_notes = [written]
                for iname, ioctave, iacc in pnote.interval_notes:
                    chord_notes.append(Note(
                        dots=frozenset(),
                        category=SymbolCategory.NOTE,
                        raw_brl='',
                        note_name=iname,
                        octave=ioctave,
                        duration=dur,
                        accidental=iacc,
                    ))
                items.append(Chord(notes=chord_notes))
            else:
                items.append(written)
        return items

    def _finalize_measure(
        self,
        pending: list[_PendingNote],
        number: int,
        bar_line_type: str = 'measure_separator',
    ) -> Measure:
        text_markings = list(self._pending_text_markings)
        self._pending_text_markings = []
        measure = Measure(number=number, bar_line_type=bar_line_type, text_markings=text_markings)

        if self._in_accord_sections or self._current_section_parts:
            # Part-measure in-accord (BANA 11.1.2): close the final section
            # with whatever is still in pending after the last in-accord sign.
            self._current_section_parts.append(self._finalize_voice_part(pending))
            self._in_accord_sections.append(list(self._current_section_parts))
            self._current_section_parts = []

            for section_parts in self._in_accord_sections:
                if len(section_parts) == 1:
                    # Single-voice section: add its notes directly to the measure.
                    for item in section_parts[0]:
                        measure.add_note(item)
                else:
                    measure.add_note(
                        InAccord(parts=section_parts, in_accord_type='part_measure')
                    )

            self._in_accord_sections = []
        elif self._in_accord_parts:
            # Final voice: whatever is still in pending after the last in-accord sign.
            all_parts = list(self._in_accord_parts)
            all_parts.append(self._finalize_voice_part(pending))
            measure.add_note(InAccord(parts=all_parts, in_accord_type=self._in_accord_type))
            self._in_accord_parts = []
            self._in_accord_type = 'full'
        else:
            for item in self._finalize_voice_part(pending):
                measure.add_note(item)

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

        After the state machine runs, any base_1 cell resolved to whole via
        the "otherwise" branch (no run/individual adjacency) is re-checked
        against the measure's beat budget (S5-6 Bug B): a whole note must
        fill the entire measure, so if the total (including augmentation
        dots) overflows, that cell is re-resolved as a 16th instead. This
        only affects standalone ambiguous cells — the run/individual
        adjacency detection above is unchanged.
        """
        beats = self._time_signature.beats_per_measure()
        count_2 = sum(1 for n in pending if n.base_duration == 2)
        resolve_2 = 32 if count_2 * 2.0 > beats else 2

        resolved = [0] * len(pending)
        state = "normal"  # "normal" | "run" | "individual"
        # Indices tentatively resolved to a whole note by the "otherwise"
        # branch below — a whole note must fill the entire measure by BANA
        # convention, so these are re-checked against the measure's beat
        # budget afterward (Bug B).
        whole_candidates: list[int] = []

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
                    resolved[i] = 1  # tentatively whole note
                    whole_candidates.append(i)
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

        if whole_candidates:
            total = sum(
                Duration(value=resolved[i], dots=pending[i].dots).duration_in_beats()
                for i in range(len(pending))
            )
            for idx in whole_candidates:
                if total <= beats:
                    break
                # A whole note here would overflow the measure — it must
                # actually be a 16th note (context-based disambiguation).
                old = Duration(value=1, dots=pending[idx].dots).duration_in_beats()
                new = Duration(value=16, dots=pending[idx].dots).duration_in_beats()
                resolved[idx] = 16
                total += new - old

        return resolved

    def _validate_measure_beat_count(self, measure: Measure) -> None:
        """Warn (plain text) if resolved beat count doesn't match the time signature."""
        beats_expected = self._time_signature.beats_per_measure()
        beats_actual = 0.0
        for item in measure.notes:
            if isinstance(item, InAccord):
                # An in-accord's voices all cover the same span (BANA 11.1/11.1.2
                # require equal note value per side); use the longest voice so a
                # malformed voice mismatch doesn't silently understate the count.
                if item.parts:
                    beats_actual += max(
                        sum(n.duration.duration_in_beats() for n in part)
                        for part in item.parts
                    )
            else:
                beats_actual += item.duration.duration_in_beats()
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
        # Interval / chord state
        self._active_intervals: dict[int, AccidentalType | None] = {}
        self._last_interval_seen: int | None = None
        self._interval_octave_override: int | None = None
        self._octave_mark_pending: bool = False
        # In-accord state
        self._in_accord_parts: list[list] = []
        self._in_accord_type: str = 'full'
        # Part-measure in-accord state (BANA 11.1.2): sections are temporal
        # sub-groups of the measure separated by the measure-division sign;
        # within a section, voice parts are separated by the part-measure sign.
        self._in_accord_sections: list[list[list]] = []
        self._current_section_parts: list[list] = []
        # Measure numbering state
        # _next_measure_number: the number to assign to the next measure finalized.
        # It starts at 1 and is overridden by explicit MEASURE_NUMBER tokens from
        # the margin, then incremented after each bar line.
        # _last_margin_measure_number: tracks the last number seen in the margin
        # so we can warn about non-sequential jumps (0 = none seen yet).
        self._next_measure_number: int = 1
        self._last_margin_measure_number: int = 0
        # Hand-sign state: which staff subsequent measures belong to.
        # None (no hand sign seen yet) routes to the right-hand staff, so
        # single-staff files with no hand signs behave exactly as before.
        self._current_hand: str | None = None
