from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .accidental import Accidental
from .base import BrailleSymbol
from .duration import Duration
from .dynamic import Dynamic
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

    def to_lilypond(self) -> str:
        """Return LilyPond note string, e.g. 'c4', 'bes'2.', 'fis8'.

        Output order: grace_note_block note_name accidental octave duration
                      articulations ornaments tie dynamics slur
        """
        grace_str = (self.grace_note.to_lilypond() + ' ') if self.grace_note else ''
        ly_name = NOTE_NAME_TO_LILYPOND[self.note_name]
        accidental_str = self.accidental.to_lilypond() if self.accidental else ''
        octave_str = self._octave_marks()
        duration_str = self.duration.to_lilypond()
        tremolo_str = self.tremolo.to_lilypond() if self.tremolo else ''
        fingering_str = ''.join(f.to_lilypond() for f in self.fingerings)
        articulation_str = ''.join(a.to_lilypond() for a in self.articulations)
        ornament_str = ''.join(o.to_lilypond() for o in self.ornaments)
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
                f"{articulation_str}{ornament_str}{tie_str}{dynamic_str}{slur_str}{pedal_str}")

    def _relative_pitch_str(self, prev_midi: int) -> tuple[str, int]:
        """Return (pitch_only_str, new_midi) for use inside a chord <...> block.

        Renders only the pitch (name + accidental + octave marks), no duration
        or other markings.  Each chord note is relative to the preceding chord note.
        """
        semitone = _NOTE_SEMITONES[self.note_name]
        if self.accidental:
            semitone += _ACCIDENTAL_MIDI_OFFSETS.get(self.accidental.type.name, 0)

        base = (prev_midi // 12) * 12 + semitone
        while base < prev_midi - 5:
            base += 12
        while base > prev_midi + 6:
            base -= 12

        target_midi = self._midi_pitch()
        diff = target_midi - base
        octave_adj = diff // 12
        if octave_adj > 0:
            octave_str = "'" * octave_adj
        elif octave_adj < 0:
            octave_str = "," * (-octave_adj)
        else:
            octave_str = ""

        ly_name = NOTE_NAME_TO_LILYPOND[self.note_name]
        accidental_str = self.accidental.to_lilypond() if self.accidental else ''
        fingering_str = ''.join(f.to_lilypond() for f in self.fingerings)
        return f"{ly_name}{accidental_str}{octave_str}{fingering_str}", target_midi

    def _midi_pitch(self) -> int:
        """MIDI pitch number for this note (C4 = 60)."""
        semitone = _NOTE_SEMITONES[self.note_name]
        if self.accidental:
            semitone += _ACCIDENTAL_MIDI_OFFSETS.get(self.accidental.type.name, 0)
        return 12 * (self.octave + 1) + semitone

    def to_relative_lilypond(self, prev_midi: int) -> tuple[str, int]:
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
                note_str, prev_midi = gn.to_relative_lilypond(prev_midi)
                parts.append(note_str)
            prefix = r'\appoggiatura' if self.grace_note.long_appoggiatura else r'\grace'
            grace_str = f'{prefix} {{ {" ".join(parts)} }} '

        semitone = _NOTE_SEMITONES[self.note_name]
        if self.accidental:
            semitone += _ACCIDENTAL_MIDI_OFFSETS.get(self.accidental.type.name, 0)

        # Natural relative MIDI: the occurrence of this pitch class closest to prev_midi
        base = (prev_midi // 12) * 12 + semitone
        while base < prev_midi - 5:
            base += 12
        while base > prev_midi + 6:
            base -= 12

        target_midi = self._midi_pitch()
        diff = target_midi - base
        octave_adj = diff // 12
        if octave_adj > 0:
            octave_str = "'" * octave_adj
        elif octave_adj < 0:
            octave_str = "," * (-octave_adj)
        else:
            octave_str = ""

        ly_name = NOTE_NAME_TO_LILYPOND[self.note_name]
        accidental_str = self.accidental.to_lilypond() if self.accidental else ''
        duration_str = self.duration.to_lilypond()
        tremolo_str = self.tremolo.to_lilypond() if self.tremolo else ''
        fingering_str = ''.join(f.to_lilypond() for f in self.fingerings)
        articulation_str = ''.join(a.to_lilypond() for a in self.articulations)
        ornament_str = ''.join(o.to_lilypond() for o in self.ornaments)
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
                  f"{articulation_str}{ornament_str}{tie_str}{dynamic_str}{slur_str}{pedal_str}")
        return result, target_midi


@dataclass
class Rest(BrailleSymbol):
    """A rest (silence) of a given duration."""
    duration: Duration
    is_full_measure: bool = False  # True for whole-measure rests (R1 in LilyPond)
    multi_measure_count: int = 1   # Number of measures for a multi-measure rest
    pedal_sustain: Optional[str] = None

    def to_lilypond(self) -> str:
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

    def to_relative_lilypond(self, prev_midi: int) -> tuple[str, int]:
        """Rests do not change the pitch reference; pass prev_midi through unchanged."""
        return self.to_lilypond(), prev_midi
