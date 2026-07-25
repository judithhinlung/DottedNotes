from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .key_signature import KeySignature

from .accidental import ACCIDENTAL_TO_LILYPOND_SUFFIX, Accidental, AccidentalType
from .base import BrailleSymbol
from .breath_mark import BreathMark
from .duration import Duration
from .dynamic import Dynamic
from .fermata import Fermata
from .ornament import GraceNote, Ornament
from .fingering import Fingering
from .tremolo import RepeatedTremolo

NOTE_NAME_TO_LILYPOND = {
    'C': 'c', 'D': 'd', 'E': 'e', 'F': 'f',
    'G': 'g', 'A': 'a', 'B': 'b',
}

_LILYPOND_OCTAVE_BASE = 3  # octave 3 = c (no marks) in LilyPond; c' = C4 = middle C

# Semitone offset from C within an octave (no accidental applied)
_NOTE_SEMITONES: dict[str, int] = {
    'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11,
}

# How each accidental type shifts the MIDI pitch (keyed by AccidentalType.name)
_ACCIDENTAL_MIDI_OFFSETS: dict[str, int] = {
    'SHARP': 1, 'FLAT': -1, 'NATURAL': 0, 'DOUBLE_SHARP': 2, 'DOUBLE_FLAT': -2,
}

_OCTAVE_TO_BRL: dict[int, str] = {
    1: '⠈',
    2: '⠘',
    3: '⠸',
    4: '⠐',
    5: '⠨',
    6: '⠰',
    7: '⠠',
}


@dataclass
class Note(BrailleSymbol):
    """A single pitched note."""
    note_name: str          # 'C', 'D', 'E', 'F', 'G', 'A', 'B'
    octave: int             # absolute octave (middle C = octave 4)
    duration: Duration
    accidental: Optional[Accidental] = None
    dynamics: list[Dynamic] = field(default_factory=list)
    articulations: list = field(default_factory=list)
    ornaments: list[Ornament] = field(default_factory=list)
    grace_note: Optional[GraceNote] = None
    tie: bool = False
    slur_start: bool = False
    slur_end: bool = False
    slur_bracket_open: bool = False
    slur_bracket_close: bool = False
    fingerings: list[Fingering] = field(default_factory=list)
    tremolo: Optional[RepeatedTremolo] = None
    pedal_sustain: Optional[str] = None
    has_octave_mark: bool = False
    articulation_format: str = "single"
    parsed_tokens: list = field(default_factory=list)
    after_numeric_indicator: bool = False
    fermata: Optional[Fermata] = None
    breath_mark: Optional[BreathMark] = None

    def __post_init__(self):
        if self.note_name not in NOTE_NAME_TO_LILYPOND:
            raise ValueError(f"Invalid note name: {self.note_name}")
        if not 0 <= self.octave <= 8:
            raise ValueError(f"Octave {self.octave} out of range (0-8)")

    def _octave_marks(self) -> str:
        if self.octave < _LILYPOND_OCTAVE_BASE:
            return ',' * (_LILYPOND_OCTAVE_BASE - self.octave)
        elif self.octave > _LILYPOND_OCTAVE_BASE:
            return "'" * (self.octave - _LILYPOND_OCTAVE_BASE)
        return ''

    def _effective_accidental_type(self, key_signature: Optional[KeySignature] = None) -> Optional[AccidentalType]:
        """The AccidentalType actually sounding for this note: an explicit
        accidental wins, otherwise fall back to what the active key
        signature implies for this pitch step (S10d-15)."""
        if self.accidental:
            return self.accidental.type
        if key_signature:
            return key_signature.accidental_by_step(self.note_name)
        return None

    def _accidental_suffix(self, acc_type: Optional[AccidentalType]) -> str:
        """LilyPond accidental suffix ('is'/'es'/...) for a resolved AccidentalType."""
        return ACCIDENTAL_TO_LILYPOND_SUFFIX.get(acc_type, '') if acc_type else ''

    def to_lilypond(self, key_signature: Optional[KeySignature] = None) -> str:
        """Return LilyPond note string, e.g. 'c4', 'bes'2.', 'fis8'.

        Output order: grace_note_block note_name accidental octave duration
                      articulations ornaments tie dynamics slur
        """
        grace_str = (self.grace_note.to_lilypond(key_signature=key_signature) + ' ') if self.grace_note else ''
        ly_name = NOTE_NAME_TO_LILYPOND[self.note_name]
        accidental_str = self._accidental_suffix(self._effective_accidental_type(key_signature))

        octave_str = self._octave_marks()
        duration_str = self.duration.to_lilypond()
        tremolo_str = self.tremolo.to_lilypond() if self.tremolo else ''
        fingering_str = ''.join(f.to_lilypond() for f in self.fingerings)
        articulation_str = ''.join(a.to_lilypond() for a in self.articulations)
        ornament_str = ''.join(o.to_lilypond() for o in self.ornaments)
        fermata_str = self.fermata.to_lilypond() if self.fermata else ''
        # \breathe is a standalone music event, not a postfix articulation
        # (LilyPond Notation Reference Sec. 3.2.3, "Breath marks" -- "any
        # expressive marks pertaining to the preceding note... must be
        # placed before \breathe"), so it needs its own leading space
        # rather than gluing directly onto the duration like \fermata does.
        breath_mark_str = (' ' + self.breath_mark.to_lilypond()) if self.breath_mark else ''
        tie_str = '~' if self.tie else ''
        dynamic_str = ''.join(d.to_lilypond() for d in self.dynamics)
        slur_str = (
            ('\\(' if self.slur_bracket_open else '') +
            ('(' if self.slur_start else '') +
            (')' if self.slur_end else '') +
            ('\\)' if self.slur_bracket_close else '')
        )
        pedal_str = ''
        if self.pedal_sustain == "on":
            pedal_str = r"\sustainOn"
        elif self.pedal_sustain == "off":
            pedal_str = r"\sustainOff"
        elif self.pedal_sustain == "change":
            pedal_str = r"\sustainOff\sustainOn"
        elif self.pedal_sustain == "on_off":
            pedal_str = r"\sustainOn\sustainOff"
        return (f"{grace_str}{ly_name}{accidental_str}{octave_str}{duration_str}{tremolo_str}{fingering_str}"
                f"{articulation_str}{ornament_str}{fermata_str}{tie_str}{dynamic_str}{slur_str}{pedal_str}{breath_mark_str}")

    def to_braille(
        self,
        prev_note: Optional[Note] = None,
        is_measure_start: bool = False,
        time_signature: Optional["TimeSignature"] = None,
        is_16th_run_continuation: bool = False,
        tremolo_format: str = "single",
        intervals_str: str = "",
        articulation_format: str = "single",
        tremolo_str: str = "",
        key_signature: Optional["KeySignature"] = None,
        force_octave_mark: Optional[bool] = None,
    ) -> str:
        from dottednotes.bana_symbols import NOTE_CELLS
        from .dynamic import DynamicLevel
        from .ornament import OrnamentType

        # 1. Grace notes
        grace_str = ""
        if self.grace_note:
            grace_str = self.grace_note.to_braille(prev_note=prev_note, is_measure_start=is_measure_start, time_signature=time_signature)
            prev_note = self.grace_note.notes[-1]
            is_measure_start = False

        # 2. Octave mark
        octave_str = ""
        if force_octave_mark is True:
            if self.octave == 0:
                octave_str = '⠈⠈'
            else:
                octave_str = _OCTAVE_TO_BRL.get(self.octave, '')
        elif force_octave_mark is False:
            octave_str = ""
        else:
            if prev_note is None or is_measure_start:
                if self.octave == 0:
                    octave_str = '⠈⠈'
                else:
                    octave_str = _OCTAVE_TO_BRL.get(self.octave, '')
            else:
                PITCH_CLASS_TO_DIATONIC = {'C': 0, 'D': 1, 'E': 2, 'F': 3, 'G': 4, 'A': 5, 'B': 6}
                curr_diatonic = self.octave * 7 + PITCH_CLASS_TO_DIATONIC[self.note_name]
                prev_diatonic = prev_note.octave * 7 + PITCH_CLASS_TO_DIATONIC[prev_note.note_name]
                diff = abs(curr_diatonic - prev_diatonic)
                if diff >= 5 or (diff in (3, 4) and self.octave != prev_note.octave):
                    if self.octave == 0:
                        octave_str = '⠈⠈'
                    else:
                        octave_str = _OCTAVE_TO_BRL.get(self.octave, '')

        # 3. Accidental (only when explicit -- an accidental inferred from
        # the key signature or carried from an earlier explicit accidental
        # in this measure is not restated, per MBC 2015 Part I, Sec. 5.1)
        accidental_str = self.accidental.to_braille() if self.accidental and self.accidental.explicit else ''

        # 4. Note cell
        _NOTE_TO_BRL = {}
        for cell, info in NOTE_CELLS.items():
            if info is not None:
                name, base_dur = info
                _NOTE_TO_BRL[(name, base_dur)] = cell

        if self.duration.value == 0:
            # Breve
            whole_cell = _NOTE_TO_BRL[(self.note_name, 1)]
            if time_signature and time_signature.beats_per_measure() >= 8.0:
                note_cell = whole_cell + '⠅'
            else:
                note_cell = whole_cell + '⠘⠉' + whole_cell
        else:
            if is_16th_run_continuation:
                base_dur = 8
            else:
                if self.duration.value in (1, 16):
                    base_dur = 1
                elif self.duration.value in (2, 32):
                    base_dur = 2
                elif self.duration.value in (4, 64):
                    base_dur = 4
                elif self.duration.value in (8, 128):
                    # BANA Par. 2.1: "Each sign also represents a smaller
                    # value" -- the eighth-note cell's smaller partner is
                    # the 128th note (S10d-9), the same 16x-smaller
                    # relationship as the other three pairs above.
                    base_dur = 8
                else:
                    raise ValueError(f"Unsupported duration value: {self.duration.value}")
            note_cell = _NOTE_TO_BRL[(self.note_name, base_dur)]

        # 5. Dots
        dots_str = '⠄' * self.duration.dots

        # 6. Pedal down
        pedal_down_str = ""
        if self.pedal_sustain in ("on", "on_off"):
            pedal_down_str = '⠣⠉'
        elif self.pedal_sustain == "change":
            pedal_down_str = '⠡⠣⠉'

        # 7. Pedal up
        pedal_up_str = ""
        if self.pedal_sustain in ("off", "on_off"):
            pedal_up_str = '⠡⠉'

        # 8. Slur bracket open/close
        slur_bracket_open_str = '⠰⠃' if self.slur_bracket_open else ''
        slur_bracket_close_str = '⠘⠆' if self.slur_bracket_close else ''

        # 9. Dynamics
        start_dynamics = []
        end_dynamics = []
        for d in self.dynamics:
            if d.level in (DynamicLevel.CRESCENDO_END, DynamicLevel.DECRESCENDO_END):
                end_dynamics.append(d)
            else:
                start_dynamics.append(d)

        # 10. Articulations & Ornaments
        if articulation_format == "single" and self.articulation_format != "single":
            articulation_format = self.articulation_format
        art_str = "".join(a.to_braille() for a in self.articulations)
        if len(self.articulations) == 1:
            if articulation_format == "start_carry":
                art_str = art_str * 2
            elif articulation_format == "inside_carry":
                art_str = ""
            # stop_carry intentionally falls through unchanged: the run's last
            # note is written as a plain, single occurrence (matching tremolo
            # and triplet carry termination elsewhere in this file/tuplet.py),
            # not prefixed -- '⠘' + a staccato sign would collide with the
            # real BANA 'expressive_accent' symbol (bana_symbols.py).

        # Normal ornaments vs glissando
        norm_ornaments = [o for o in self.ornaments if o.type != OrnamentType.GLISSANDO]
        gliss_ornaments = [o for o in self.ornaments if o.type == OrnamentType.GLISSANDO]
        orn_str = "".join(o.to_braille() for o in norm_ornaments)
        gliss_str = "".join(o.to_braille() for o in gliss_ornaments)

        # Combine preceding elements:
        # dynamics + articulations + ornaments + accidental + octave_mark + note_cell
        pre_rest = art_str + orn_str + accidental_str + octave_str + note_cell

        # Determine start dynamics string and if ambiguity terminator is needed
        start_dyn_parts = []
        for d in start_dynamics:
            start_dyn_parts.append(d.to_braille())
        start_dyn_str = "".join(start_dyn_parts)
        if start_dyn_str and pre_rest:
            first_cell = pre_rest[0]
            if (ord(first_cell) - 0x2800) & 0x07 != 0:
                start_dyn_str += '⠄'

        # Suffix parts: tremolo + fingerings + tie + slur
        if not tremolo_str:
            if self.tremolo:
                from dottednotes.bana_symbols import TREMOLO_REPEATED_VALUE_CELLS
                _REP_TREM_TO_BRL = {v: k for k, v in TREMOLO_REPEATED_VALUE_CELLS.items()}
                cell_val = _REP_TREM_TO_BRL.get(self.tremolo.subdivision, '⠇')
                if tremolo_format == "single":
                    tremolo_str = '⠘' + cell_val
                elif tremolo_format == "start_carry":
                    tremolo_str = cell_val * 2
                elif tremolo_format == "stop_carry":
                    tremolo_str = '⠘' + cell_val
                elif tremolo_format == "inside_carry":
                    tremolo_str = ""

        fingering_str = "".join(f.to_braille() for f in self.fingerings)
        # Par. 22.2: the fermata (like the breath/break mark) follows the
        # note, and follows any value dot, fingering, or interval sign
        # already on that note -- placed here, after fingering_str/
        # intervals_str/dots_str, and before the tie/slur suffix.
        fermata_str = self.fermata.to_braille() if self.fermata else ''
        # Same placement rule as fermata (Par. 22.2 groups breath/break
        # marks and fermatas together as "follows the note...precedes the
        # breath/break mark or fermata" for any value dot/fingering/
        # interval) -- placed directly after fermata_str since Par. 22.2
        # doesn't give a combined ordering rule for when both signs occur
        # on the same note (a rare combination).
        breath_mark_str = self.breath_mark.to_braille() if self.breath_mark else ''
        tie_str = '⠨⠉' if getattr(self, '_is_chord_written_note', False) and self.tie else ('⠈⠉' if self.tie else '')
        slur_start_str = '⠉' if self.slur_start else ''

        end_dyn_str = "".join(d.to_braille() for d in end_dynamics)

        prefix = grace_str + pedal_down_str + slur_bracket_open_str + start_dyn_str + art_str + orn_str + accidental_str + octave_str
        suffix = dots_str + gliss_str + intervals_str + tremolo_str + fingering_str + fermata_str + breath_mark_str + tie_str + slur_start_str + slur_bracket_close_str + end_dyn_str + pedal_up_str

        return prefix + note_cell + suffix

    def musical_equals(self, other: Any) -> bool:
        if not isinstance(other, Note):
            return False
        return (
            self.note_name == other.note_name and
            self.octave == other.octave and
            self.duration == other.duration and
            (self.accidental.type if self.accidental else None) ==
            (other.accidental.type if other.accidental else None) and
            self.tie == other.tie and
            self.slur_start == other.slur_start and
            self.slur_end == other.slur_end and
            self.slur_bracket_open == other.slur_bracket_open and
            self.slur_bracket_close == other.slur_bracket_close and
            self.articulations == other.articulations and
            self.ornaments == other.ornaments and
            self.dynamics == other.dynamics and
            self.fingerings == other.fingerings and
            self.grace_note == other.grace_note and
            self.tremolo == other.tremolo and
            self.pedal_sustain == other.pedal_sustain and
            self.after_numeric_indicator == other.after_numeric_indicator and
            self.fermata == other.fermata and
            self.breath_mark == other.breath_mark
        )

    def _relative_pitch_str(self, prev_midi: int, key_signature: Optional[KeySignature] = None) -> tuple[str, int]:
        """Return (pitch_only_str, new_midi) for use inside a chord <...> block.

        Renders only the pitch (name + accidental + octave marks), no duration
        or other markings.  Each chord note is relative to the preceding chord note.
        """
        acc_type = self._effective_accidental_type(key_signature)
        semitone = _NOTE_SEMITONES[self.note_name]
        if acc_type:
            semitone += _ACCIDENTAL_MIDI_OFFSETS.get(acc_type.name, 0)

        base = (prev_midi // 12) * 12 + semitone
        # LilyPond's real nearest-neighbor rule breaks an exact tritone tie
        # (6 semitones either way) toward the LOWER pitch -- verified against
        # the real lilypond binary's \displayMusic output (S10d-16). The
        # window must therefore be asymmetric the other way: base can be as
        # low as prev_midi - 6 before shifting up, but must shift down again
        # once it exceeds prev_midi + 5 (not + 6, which would let the upper
        # tritone candidate stand).
        while base < prev_midi - 6:
            base += 12
        while base > prev_midi + 5:
            base -= 12

        target_midi = self._midi_pitch(key_signature)
        diff = target_midi - base
        octave_adj = diff // 12
        if octave_adj > 0:
            octave_str = "'" * octave_adj
        elif octave_adj < 0:
            octave_str = "," * (-octave_adj)
        else:
            octave_str = ""

        ly_name = NOTE_NAME_TO_LILYPOND[self.note_name]
        accidental_str = self._accidental_suffix(acc_type)
        fingering_str = ''.join(f.to_lilypond() for f in self.fingerings)
        return f"{ly_name}{accidental_str}{octave_str}{fingering_str}", target_midi

    def _midi_pitch(self, key_signature: Optional[KeySignature] = None) -> int:
        """MIDI pitch number for this note (C4 = 60)."""
        semitone = _NOTE_SEMITONES[self.note_name]
        acc_type = self._effective_accidental_type(key_signature)
        if acc_type:
            semitone += _ACCIDENTAL_MIDI_OFFSETS.get(acc_type.name, 0)
        return 12 * (self.octave + 1) + semitone

    def to_relative_lilypond(self, prev_midi: int, key_signature: Optional[KeySignature] = None) -> tuple[str, int]:
        """Return (lilypond_str, new_prev_midi) for use inside a \\relative block.

        Grace notes participate in the relative pitch chain: the grace note
        is rendered relative to prev_midi, and the main note is rendered
        relative to the grace note's pitch.

        Computes the octave marks needed so that the note's absolute pitch is
        preserved relative to prev_midi, following LilyPond's nearest-neighbor rule:
        choose the occurrence of the pitch class within a tritone of prev_midi,
        then add ' or , marks to reach the actual target octave.
        """
        # Handle grace notes: each renders relative to the previous, chained in order.
        grace_str = ''
        if self.grace_note:
            parts = []
            for gn in self.grace_note.notes:
                note_str, prev_midi = gn.to_relative_lilypond(prev_midi, key_signature=key_signature)
                parts.append(note_str)
            prefix = r'\appoggiatura' if self.grace_note.long_appoggiatura else r'\grace'
            grace_str = f'{prefix} {{ {" ".join(parts)} }} '

        acc_type = self._effective_accidental_type(key_signature)
        semitone = _NOTE_SEMITONES[self.note_name]
        if acc_type:
            semitone += _ACCIDENTAL_MIDI_OFFSETS.get(acc_type.name, 0)

        # Natural relative MIDI: the occurrence of this pitch class closest to
        # prev_midi. An exact tritone tie (6 semitones either way) breaks
        # toward the LOWER pitch, matching real LilyPond -- see
        # _relative_pitch_str's identical window for the S10d-16 citation.
        base = (prev_midi // 12) * 12 + semitone
        while base < prev_midi - 6:
            base += 12
        while base > prev_midi + 5:
            base -= 12

        target_midi = self._midi_pitch(key_signature)
        diff = target_midi - base
        octave_adj = diff // 12
        if octave_adj > 0:
            octave_str = "'" * octave_adj
        elif octave_adj < 0:
            octave_str = "," * (-octave_adj)
        else:
            octave_str = ""

        ly_name = NOTE_NAME_TO_LILYPOND[self.note_name]
        accidental_str = self._accidental_suffix(acc_type)
        duration_str = self.duration.to_lilypond()
        tremolo_str = self.tremolo.to_lilypond() if self.tremolo else ''
        fingering_str = ''.join(f.to_lilypond() for f in self.fingerings)
        articulation_str = ''.join(a.to_lilypond() for a in self.articulations)
        ornament_str = ''.join(o.to_lilypond() for o in self.ornaments)
        fermata_str = self.fermata.to_lilypond() if self.fermata else ''
        breath_mark_str = (' ' + self.breath_mark.to_lilypond()) if self.breath_mark else ''
        tie_str = '~' if self.tie else ''
        dynamic_str = ''.join(d.to_lilypond() for d in self.dynamics)
        slur_str = (
            ('\\(' if self.slur_bracket_open else '') +
            ('(' if self.slur_start else '') +
            (')' if self.slur_end else '') +
            ('\\)' if self.slur_bracket_close else '')
        )
        pedal_str = ''
        if self.pedal_sustain == "on":
            pedal_str = r"\sustainOn"
        elif self.pedal_sustain == "off":
            pedal_str = r"\sustainOff"
        elif self.pedal_sustain == "change":
            pedal_str = r"\sustainOff\sustainOn"
        elif self.pedal_sustain == "on_off":
            pedal_str = r"\sustainOn\sustainOff"
        result = (f"{grace_str}{ly_name}{accidental_str}{octave_str}{duration_str}{tremolo_str}{fingering_str}"
                  f"{articulation_str}{ornament_str}{fermata_str}{tie_str}{dynamic_str}{slur_str}{pedal_str}{breath_mark_str}")
        return result, target_midi


@dataclass
class Rest(BrailleSymbol):
    """A rest (silence) of a given duration."""
    duration: Duration
    is_full_measure: bool = False  # True for whole-measure rests (R1 in LilyPond)
    multi_measure_count: int = 1   # Number of measures for a multi-measure rest
    pedal_sustain: Optional[str] = None

    def to_lilypond(self, key_signature: Optional[KeySignature] = None) -> str:
        """Return LilyPond rest string e.g. 'r4', 'R1', 'r2.', 'R1*4'"""
        pedal_str = ''
        if self.pedal_sustain == "on":
            pedal_str = r"\sustainOn"
        elif self.pedal_sustain == "off":
            pedal_str = r"\sustainOff"
        elif self.pedal_sustain == "change":
            pedal_str = r"\sustainOff\sustainOn"
        elif self.pedal_sustain == "on_off":
            pedal_str = r"\sustainOn\sustainOff"

        if self.is_full_measure:
            if self.multi_measure_count > 1:
                return f"R{self.duration.to_lilypond()}*{self.multi_measure_count}{pedal_str}"
            return f"R{self.duration.to_lilypond()}{pedal_str}"
        return f"r{self.duration.to_lilypond()}{pedal_str}"

    def to_relative_lilypond(self, prev_midi: int, key_signature: Optional[KeySignature] = None) -> tuple[str, int]:
        """Rests do not change the pitch reference; pass prev_midi through unchanged."""
        return self.to_lilypond(key_signature=key_signature), prev_midi

    def to_braille(self) -> str:
        if self.is_full_measure:
            # BANA Music Braille Code 2015, Par. 5.1: "A measure of
            # silence is indicated in the print by a whole rest, whatever
            # the time signature may be, except that in 4/2 time the
            # double whole rest may sometimes be found." The rest sign
            # for a full measure never varies with that measure's actual
            # beat count/time signature (e.g. a 2/4 measure of rest is
            # NOT the half-rest sign) -- only a genuine breve (double
            # whole) rest in the source keeps its own sign.
            base_cell = '⠍⠅' if self.duration.value == 0 else '⠍'
            if self.multi_measure_count > 1:
                # Par. 5.3, "Multiple-Measure Rests": "When a silence is
                # prolonged for two or three measures, two or three
                # successive whole rests are written unspaced... When it
                # extends for four or more measures, one whole rest is
                # written, preceded by the appropriate number including
                # the numeric indicator." Par. 5.3.1 makes the numeral
                # form unconditional for a run of double whole (breve)
                # rests instead ("must be used with the appropriate
                # number"), regardless of count -- unlike the plain
                # whole-rest 2-3 case, which has no numeral at all.
                if self.duration.value == 0 or self.multi_measure_count >= 4:
                    from dottednotes.bana_symbols import LITERARY_DIGITS
                    digit_to_cell = {v: k for k, v in LITERARY_DIGITS.items()}
                    digits = ''.join(digit_to_cell[int(d)] for d in str(self.multi_measure_count))
                    cell = '⠼' + digits + base_cell
                else:
                    cell = base_cell * self.multi_measure_count
            else:
                cell = base_cell
        elif self.duration.value == 0:
            cell = '⠍⠅'
        elif self.duration.value in (1, 16):
            cell = '⠍'
        elif self.duration.value in (2, 32):
            cell = '⠥'
        elif self.duration.value in (4, 64):
            cell = '⠧'
        elif self.duration.value in (8, 128):
            # Mirrors Note.to_braille()'s same 128th/eighth pairing (S10d-9).
            cell = '⠭'
        else:
            raise ValueError(f"Unsupported rest duration: {self.duration.value}")
        # A full-measure rest's `duration` (value/dots) only exists to
        # satisfy the *value* a full measure of that time signature adds
        # up to (e.g. a 3/4 measure computes to value=2, dots=1 -- a
        # "dotted half" -- to keep LilyPond's R2. correct); per Par. 5.1
        # the braille sign is fixed regardless of that value, so no
        # augmentation dot is added either.
        dots = '' if self.is_full_measure else '⠄' * self.duration.dots

        # Sustain Pedal
        pedal_down_str = ""
        if self.pedal_sustain in ("on", "on_off"):
            pedal_down_str = '⠣⠉'
        elif self.pedal_sustain == "change":
            pedal_down_str = '⠡⠣⠉'

        pedal_up_str = ""
        if self.pedal_sustain in ("off", "on_off"):
            pedal_up_str = '⠡⠉'

        return pedal_down_str + cell + dots + pedal_up_str

    def musical_equals(self, other: Any) -> bool:
        if not isinstance(other, Rest):
            return False
        return (
            self.duration == other.duration and
            self.is_full_measure == other.is_full_measure and
            self.multi_measure_count == other.multi_measure_count and
            self.pedal_sustain == other.pedal_sustain
        )
