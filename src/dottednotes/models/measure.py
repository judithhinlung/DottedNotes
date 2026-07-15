from __future__ import annotations

from dataclasses import dataclass, field
from typing import Union, Optional, TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .time_signature import TimeSignature
    from .key_signature import KeySignature

from .chord import Chord
from .in_accord import InAccord
from .measure_repeat import MeasureRepeat
from .note import Note, Rest
from .text_marking import TextMarking
from .tremolo import AlternatingTremolo
from .tuplet import Tuplet

NoteOrChord = Union[Note, Chord]
MeasureItem = Union[Note, Rest, Chord, InAccord, Tuplet, AlternatingTremolo, MeasureRepeat]

_BAR_LINE_TO_LY: dict[str, str] = {
    'measure_separator': '|',
    'final_double_bar': r'\bar "|."',
    'section_double_bar': r'\bar "||"',
    'forward_repeat': r'\bar ".|:"',
    'end_repeat': r'\bar ":|."',
}


def _render_note_list_to_braille(
    items: list,
    prev_note: Optional[Note] = None,
    is_measure_start: bool = False,
    time_signature: Optional["TimeSignature"] = None,
    key_signature: Optional["KeySignature"] = None,
    compression_level: str = "full",
) -> str:
    n_items = len(items)

    # 1. 16th-note runs (consecutive 3+ 16th notes/chords)
    is_16th_continuation = [False] * n_items
    i = 0
    while i < n_items:
        def is_16th_note(item):
            if hasattr(item, 'notes') and item.notes:
                d = item.notes[0].duration
            elif hasattr(item, 'duration'):
                d = item.duration
            else:
                return False
            return d.value == 16 and not d.is_triplet

        if is_16th_note(items[i]):
            j = i
            while j < n_items and is_16th_note(items[j]):
                j += 1
            if j - i >= 3:
                for k in range(i + 1, j):
                    is_16th_continuation[k] = True
            i = j
        else:
            i += 1

    # 2. Repeated tremolo runs (consecutive 3+ notes/chords with identical repeated tremolo subdivision)
    tremolo_formats = ["single"] * n_items
    i = 0
    while i < n_items:
        def get_trem_sub(item):
            note_obj = item.notes[0] if hasattr(item, 'notes') and item.notes else item
            if hasattr(note_obj, 'tremolo') and note_obj.tremolo is not None:
                from .tremolo import RepeatedTremolo
                if isinstance(note_obj.tremolo, RepeatedTremolo):
                    return note_obj.tremolo.subdivision
            return None

        sub = get_trem_sub(items[i])
        if sub is not None:
            j = i
            while j < n_items and get_trem_sub(items[j]) == sub:
                j += 1
            if j - i >= 3:
                tremolo_formats[i] = "start_carry"
                for k in range(i + 1, j - 1):
                    tremolo_formats[k] = "inside_carry"
                tremolo_formats[j - 1] = "stop_carry"
            i = j
        else:
            i += 1

    # 3. Triplet carry runs (consecutive 3+ Tuplet groups)
    triplet_formats = ["single"] * n_items
    i = 0
    while i < n_items:
        if isinstance(items[i], Tuplet):
            j = i
            while j < n_items and isinstance(items[j], Tuplet):
                j += 1
            if j - i >= 3:
                triplet_formats[i] = "start_carry"
                for k in range(i + 1, j - 1):
                    triplet_formats[k] = "inside_carry"
                triplet_formats[j - 1] = "stop_carry"
            i = j
        else:
            i += 1

    # 4. Articulation runs (consecutive 4+ notes/chords with identical articulation type)
    articulation_formats = ["single"] * n_items
    if compression_level != "none":
        i = 0
        while i < n_items:
            def get_single_art_type(item):
                note_obj = item.notes[0] if hasattr(item, 'notes') and item.notes else item
                if hasattr(note_obj, 'articulations') and len(note_obj.articulations) == 1:
                    return note_obj.articulations[0].type
                return None

            art_type = get_single_art_type(items[i])
            if art_type is not None:
                j = i
                while j < n_items and get_single_art_type(items[j]) == art_type:
                    j += 1
                if j - i >= 4:
                    articulation_formats[i] = "start_carry"
                    for k in range(i + 1, j - 1):
                        articulation_formats[k] = "inside_carry"
                    articulation_formats[j - 1] = "stop_carry"
                i = j
            else:
                i += 1

    # Render items
    rendered = []
    curr_prev = prev_note
    curr_measure_start = is_measure_start
    for idx, item in enumerate(items):
        if hasattr(item, 'to_braille'):
            kwargs = {
                'prev_note': curr_prev,
                'is_measure_start': curr_measure_start,
                'time_signature': time_signature,
            }
            if isinstance(item, Rest) or isinstance(item, MeasureRepeat):
                kwargs = {}
            elif isinstance(item, Note):
                kwargs['key_signature'] = key_signature
                kwargs['is_16th_run_continuation'] = is_16th_continuation[idx]
                kwargs['tremolo_format'] = tremolo_formats[idx]
                kwargs['articulation_format'] = item.articulation_format if item.articulation_format != "single" else articulation_formats[idx]
            elif isinstance(item, Chord):
                kwargs['key_signature'] = key_signature
                kwargs['is_16th_run_continuation'] = is_16th_continuation[idx]
                kwargs['tremolo_format'] = tremolo_formats[idx]
            elif isinstance(item, Tuplet):
                kwargs['format'] = triplet_formats[idx]
            elif isinstance(item, InAccord):
                kwargs['key_signature'] = key_signature
                kwargs['compression_level'] = compression_level
            elif isinstance(item, AlternatingTremolo):
                kwargs['key_signature'] = key_signature

            item_brl = item.to_braille(**kwargs)
            rendered.append(item_brl)

            # Update curr_prev
            if isinstance(item, Note):
                curr_prev = item
            elif isinstance(item, Chord) and item.notes:
                curr_prev = item.notes[0]
            elif isinstance(item, Tuplet) and item.items:
                last_sub = item.items[-1]
                curr_prev = last_sub.notes[0] if hasattr(last_sub, 'notes') and last_sub.notes else last_sub
            elif isinstance(item, InAccord) and item.parts and item.parts[0]:
                last_sub = item.parts[0][-1]
                curr_prev = last_sub.notes[0] if hasattr(last_sub, 'notes') and last_sub.notes else last_sub
            elif isinstance(item, AlternatingTremolo):
                curr_prev = item.items[1].notes[0] if hasattr(item.items[1], 'notes') and item.items[1].notes else item.items[1]

        curr_measure_start = False

    return "".join(rendered)


@dataclass
class Measure:
    number: int
    notes: list[MeasureItem] = field(default_factory=list)
    time_signature: tuple[int, int] = (4, 4)
    key_signature: int = 0
    clef: str = "treble"
    bar_line_type: str = 'measure_separator'
    text_markings: list[TextMarking] = field(default_factory=list)
    line: int = 0

    def add_note(self, note: MeasureItem) -> None:
        self.notes.append(note)

    def to_lilypond(self, prev_midi: int = 60) -> tuple[str, int]:
        parts: list[str] = []
        for marking in self.text_markings:
            parts.append(marking.to_lilypond())
        cur_midi = prev_midi
        for item in self.notes:
            if hasattr(item, 'to_relative_lilypond'):
                s, cur_midi = item.to_relative_lilypond(cur_midi)
            else:
                s = item.to_lilypond()
            parts.append(s)

        bar_ly = _BAR_LINE_TO_LY.get(self.bar_line_type, '|')
        return ' '.join(parts) + ' ' + bar_ly, cur_midi

    def to_braille(
        self,
        prev_note: Optional[Note] = None,
        is_measure_start: bool = True,
        time_signature: Optional["TimeSignature"] = None,
        compression_level: str = "full",
    ) -> tuple[str, Optional[Note]]:
        marking_strs = "".join(m.to_braille() for m in self.text_markings)

        from .key_signature import KeySignature
        key_sig_obj = KeySignature(dots=frozenset(), category=None, raw_brl="", sharps_or_flats=self.key_signature)

        from .time_signature import TimeSignature
        ts_num, ts_den = self.time_signature
        ts_obj = TimeSignature(dots=frozenset(), category=None, raw_brl="", numerator=ts_num, denominator=ts_den)

        notes_str = _render_note_list_to_braille(
            self.notes,
            prev_note=prev_note,
            is_measure_start=is_measure_start,
            time_signature=ts_obj,
            key_signature=key_sig_obj,
            compression_level=compression_level,
        )

        from dottednotes.bana_symbols import BAR_LINE_CELLS, BAR_LINE_SEQUENCES
        bar_cell = {v: k for k, v in BAR_LINE_CELLS.items()}.get(self.bar_line_type, '')
        if not bar_cell:
            bar_cell = {v: k for k, v in BAR_LINE_SEQUENCES.items()}.get(self.bar_line_type, '')

        # Determine last note for relative octave context propagation
        last_note = None
        for item in reversed(self.notes):
            if isinstance(item, Note):
                last_note = item
                break
            elif hasattr(item, 'notes') and item.notes:
                last_note = item.notes[0]
                break
            elif hasattr(item, 'items') and item.items:
                found = False
                for sub in reversed(item.items):
                    if isinstance(sub, Note):
                        last_note = sub
                        found = True
                        break
                    elif hasattr(sub, 'notes') and sub.notes:
                        last_note = sub.notes[0]
                        found = True
                        break
                if found:
                    break
            elif hasattr(item, 'parts') and item.parts:
                if item.parts[0]:
                    for sub in reversed(item.parts[0]):
                        if isinstance(sub, Note):
                            last_note = sub
                            break
                        elif hasattr(sub, 'notes') and sub.notes:
                            last_note = sub.notes[0]
                            break
                    break

        return marking_strs + notes_str + bar_cell, last_note

    def musical_equals(self, other: Any) -> bool:
        if not isinstance(other, Measure):
            return False
        if len(self.notes) != len(other.notes):
            return False
        for item1, item2 in zip(self.notes, other.notes):
            if hasattr(item1, 'musical_equals'):
                if not item1.musical_equals(item2):
                    return False
            else:
                if item1 != item2:
                    return False
        return True
