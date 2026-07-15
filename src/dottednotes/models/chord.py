from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .time_signature import TimeSignature
    from .key_signature import KeySignature

from .duration import Duration
from .note import Note


@dataclass
class Chord:
    """A simultaneity: a written note plus one or more interval notes.

    For treble/alto clef: notes[0] is the written (highest) note;
    notes[1:] are interval notes in descending pitch order.

    For bass/tenor clef: notes[0] is the written (lowest) note;
    notes[1:] are interval notes in ascending pitch order.

    All notes share the same duration (intervals never add dots even when the
    written note is dotted, per BANA rules).
    """

    notes: list[Note] = field(default_factory=list)

    @property
    def duration(self) -> Duration:
        return self.notes[0].duration

    def to_braille(
        self,
        prev_note: Optional[Note] = None,
        is_measure_start: bool = False,
        time_signature: Optional["TimeSignature"] = None,
        key_signature: Optional["KeySignature"] = None,
        is_16th_run_continuation: bool = False,
        tremolo_format: str = "single",
        tremolo_str: str = "",
    ) -> str:
        written = self.notes[0]
        written._is_chord_written_note = True

        # Calculate intervals
        descending = False
        if len(self.notes) > 1:
            descending = self.notes[1]._midi_pitch() < self.notes[0]._midi_pitch()

        PITCH_CLASS_TO_DIATONIC = {'C': 0, 'D': 1, 'E': 2, 'F': 3, 'G': 4, 'A': 5, 'B': 6}
        _DIATONIC_NOTES = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
        _INTERVAL_TO_BRL = {2: '⠴', 3: '⠵', 4: '⠦', 5: '⠔', 6: '⠢', 7: '⠖', 8: '⠶'}
        _OCTAVE_TO_BRL = {1: '⠈', 2: '⠘', 3: '⠸', 4: '⠐', 5: '⠨', 6: '⠰', 7: '⠠'}

        written_diatonic = written.octave * 7 + PITCH_CLASS_TO_DIATONIC[written.note_name]

        interval_strs = []
        for n in self.notes[1:]:
            curr_diatonic = n.octave * 7 + PITCH_CLASS_TO_DIATONIC[n.note_name]
            steps = abs(curr_diatonic - written_diatonic)

            # Accidental
            acc_brl = ""
            sharps_or_flats = key_signature.sharps_or_flats if key_signature else 0
            from dottednotes.parser.braille_parser import _key_sig_accidental
            default_acc_type = _key_sig_accidental(n.note_name, sharps_or_flats)

            actual_acc_type = n.accidental.type if n.accidental else None
            if actual_acc_type != default_acc_type:
                acc_brl = n.accidental.to_braille() if n.accidental else '⠡'

            # Octave mark override
            written_index = _DIATONIC_NOTES.index(written.note_name)
            raw = written_index - steps if descending else written_index + steps
            calc_octave = written.octave + (raw // 7)

            oct_brl = ""
            if n.octave != calc_octave:
                oct_brl = _OCTAVE_TO_BRL.get(n.octave, '')

            # Interval cell
            int_cell = _INTERVAL_TO_BRL[((steps - 1) % 7) + 2]

            # Fingering
            f_brl = "".join(f.to_braille() for f in n.fingerings)

            interval_strs.append(acc_brl + oct_brl + int_cell + f_brl)

        # Render written note, passing the interval string
        written_brl = written.to_braille(
            prev_note=prev_note,
            is_measure_start=is_measure_start,
            time_signature=time_signature,
            is_16th_run_continuation=is_16th_run_continuation,
            tremolo_format=tremolo_format,
            intervals_str="".join(interval_strs),
            tremolo_str=tremolo_str,
        )
        return written_brl

    def to_lilypond(self) -> str:
        """Return LilyPond chord string in absolute mode, e.g. '<c ees>4'."""
        parts = [
            NOTE_PITCH_ONLY(n)
            for n in self.notes
        ]
        dur = self.duration.to_lilypond()
        tremolo_str = self.notes[0].tremolo.to_lilypond() if self.notes[0].tremolo else ''
        extra = _chord_extras(self.notes[0])
        return f"<{' '.join(parts)}>{dur}{tremolo_str}{extra}"

    def to_relative_lilypond(self, prev_midi: int) -> tuple[str, int]:
        """Return (lilypond_str, new_prev_midi) for use inside a \\relative block.

        The first note is relative to prev_midi.  Each subsequent note within
        the chord is relative to the preceding chord note.  After the chord,
        prev_midi advances to the first note's MIDI pitch (LilyPond rule).
        """
        parts: list[str] = []
        cur_midi = prev_midi
        for note in self.notes:
            pitch_str, cur_midi = note._relative_pitch_str(cur_midi)
            parts.append(pitch_str)

        dur = self.duration.to_lilypond()
        tremolo_str = self.notes[0].tremolo.to_lilypond() if self.notes[0].tremolo else ''
        extra = _chord_extras(self.notes[0])

        # After the chord, reference advances to the first note (LilyPond rule).
        ref_midi = self.notes[0]._midi_pitch()
        return f"<{' '.join(parts)}>{dur}{tremolo_str}{extra}", ref_midi


def NOTE_PITCH_ONLY(note: Note) -> str:
    """Return just the pitch portion of a note (name + accidental + fingering), no octave or duration."""
    from .note import NOTE_NAME_TO_LILYPOND
    ly_name = NOTE_NAME_TO_LILYPOND[note.note_name]
    accidental_str = note.accidental.to_lilypond() if note.accidental else ''
    fingering_str = ''.join(f.to_lilypond() for f in note.fingerings)
    return f"{ly_name}{accidental_str}{fingering_str}"


def _chord_extras(written: Note) -> str:
    """Return articulation, ornament, tie, dynamic, and slur strings from the written note."""
    art_str = ''.join(a.to_lilypond() for a in written.articulations)
    orn_str = ''.join(o.to_lilypond() for o in written.ornaments)
    tie_str = '~' if written.tie else ''
    dyn_str = ''.join(d.to_lilypond() for d in written.dynamics)
    slur_str = (
        ('\\(' if written.slur_bracket_open else '') +
        ('(' if written.slur_start else '') +
        (')' if written.slur_end else '') +
        ('\\)' if written.slur_bracket_close else '')
    )
    pedal_str = ''
    if written.pedal_sustain == "on":
        pedal_str = r"\sustainOn"
    elif written.pedal_sustain == "off":
        pedal_str = r"\sustainOff"
    elif written.pedal_sustain == "change":
        pedal_str = r"\sustainOff\sustainOn"
    elif written.pedal_sustain == "on_off":
        pedal_str = r"\sustainOn\sustainOff"
    return f"{art_str}{orn_str}{tie_str}{dyn_str}{slur_str}{pedal_str}"
