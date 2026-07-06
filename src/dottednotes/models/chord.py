from __future__ import annotations

from dataclasses import dataclass, field

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

    def to_lilypond(self) -> str:
        """Return LilyPond chord string in absolute mode, e.g. '<c ees>4'."""
        parts = [
            NOTE_PITCH_ONLY(n)
            for n in self.notes
        ]
        dur = self.duration.to_lilypond()
        extra = _chord_extras(self.notes[0])
        return f"<{' '.join(parts)}>{dur}{extra}"

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
        extra = _chord_extras(self.notes[0])

        # After the chord, reference advances to the first note (LilyPond rule).
        ref_midi = self.notes[0]._midi_pitch()
        return f"<{' '.join(parts)}>{dur}{extra}", ref_midi


def NOTE_PITCH_ONLY(note: Note) -> str:
    """Return just the pitch portion of a note (name + accidental), no octave or duration."""
    from .note import NOTE_NAME_TO_LILYPOND
    ly_name = NOTE_NAME_TO_LILYPOND[note.note_name]
    accidental_str = note.accidental.to_lilypond() if note.accidental else ''
    return f"{ly_name}{accidental_str}"


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
    return f"{art_str}{orn_str}{tie_str}{dyn_str}{slur_str}"
