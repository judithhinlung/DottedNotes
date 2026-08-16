from __future__ import annotations

from dataclasses import dataclass, field
from typing import Union, Optional, TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .time_signature import TimeSignature
    from .key_signature import KeySignature

from .chord import Chord
from .duration import TICKS_PER_QUARTER
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


def _ending_numbers_to_braille(numbers: list[int]) -> str:
    """Render volta ending numbers per BANA Chapter 17, Par. 17.1.1, Table
    17 -- prima/seconda volta = NUMBER_SIGN + a lower-cell digit (`#1`/`#2`
    decode to the already-confirmed cells reused here; see TICKETS.md's
    S10c-3 notes on that reuse).

    Par. 17.1.1(b): combined endings (e.g. printed "1,2") each get their
    own numeric indicator, with no space and no comma cell between them
    (a comma would collide with a lower-cell numeral). A hyphenated range
    in print (e.g. "1-3") instead gets a single numeric indicator followed
    by a literary hyphen and the final number with no second indicator --
    NOT implemented here, since `ending_numbers` is a flat list with no
    record of whether the source used a range or a list, so every case is
    rendered the safe "combined" way (each number gets its own indicator),
    which Par. 17.1.1(b) also allows, just not as compact as the
    hyphen-range shorthand for a long consecutive run.
    """
    from dottednotes.bana_symbols import NUMBER_SIGN, LOWER_DIGIT_CELLS
    digit_to_cell = {v: k for k, v in LOWER_DIGIT_CELLS.items()}
    parts = []
    for n in numbers:
        parts.append(NUMBER_SIGN + ''.join(digit_to_cell[int(d)] for d in str(n)))
    return ''.join(parts)


def _item_ticks(item: MeasureItem) -> int:
    """Duration, in ticks, of a single measure item -- Note/Rest/Chord read
    `.duration` directly; a Tuplet sums its own items recursively.

    An AlternatingTremolo (S6-6) occupies only the FIRST item's written
    duration -- BANA's printed duration describes the whole alternating
    pair, which together take up one written note's worth of time, not two
    (see models/tremolo.py's _repeat_count for the same reasoning)."""
    if isinstance(item, Tuplet):
        return sum(_item_ticks(sub) for sub in item.items)
    if isinstance(item, AlternatingTremolo):
        return item.items[0].duration.duration_in_ticks()
    return item.duration.duration_in_ticks()


def _last_real_note(items: list) -> Optional[Note]:
    """Scan `items` from the end for the last item carrying an actual
    pitch (a Note, or a Chord's written note), skipping bare Rests and
    recursing into a nested Tuplet's own items -- used to find the correct
    octave-interval reference after a Tuplet/InAccord voice/
    AlternatingTremolo whose last element is a Rest, which has no pitch
    and must never itself become "the previous note" (Note.to_braille's
    octave logic accesses prev_note.octave/note_name unconditionally, so
    assigning it a Rest crashes instead of just rendering an extra octave
    mark)."""
    for sub in reversed(items):
        if hasattr(sub, 'notes') and sub.notes:
            return sub.notes[0]
        if isinstance(sub, Note):
            return sub
        if hasattr(sub, 'items') and sub.items:
            inner = _last_real_note(sub.items)
            if inner is not None:
                return inner
    return None


def _render_note_list_to_braille(
    items: list,
    prev_note: Optional[Note] = None,
    is_measure_start: bool = False,
    time_signature: Optional["TimeSignature"] = None,
    key_signature: Optional["KeySignature"] = None,
    compression_level: str = "full",
) -> str:
    n_items = len(items)

    # 1. 16th-note runs (consecutive 3+ 16th notes/chords, split at beat
    # boundaries -- BANA Par. 8.1: "a regular group consists of three or
    # more notes of the same value that occupy a full beat or a natural
    # division of a beat," and Par. 8.1.1(a) prohibits grouping notes that
    # are "not contained entirely within the same beat." A run of 16th
    # notes spanning several beats must therefore restart at each beat
    # boundary (e.g. 16 sixteenth notes in 4/4 need a full cell at
    # positions 1, 5, 9, and 13, not just position 1) -- this mirrors
    # BrailleParser._resolve_measure_durations' own beat_progress_ticks
    # state machine for the read direction, which already treats one beat
    # as one quarter note (TICKS_PER_QUARTER), the same convention used
    # here.
    is_16th_continuation = [False] * n_items

    def is_16th_note(item):
        if hasattr(item, 'notes') and item.notes:
            d = item.notes[0].duration
        elif hasattr(item, 'duration'):
            d = item.duration
        else:
            return False
        return d.value == 16 and not d.is_triplet

    def item_ticks_for_beat_tracking(item) -> int:
        # Only used for items that already failed is_16th_note (so never a
        # plain Note/Chord/Rest already handled by _item_ticks directly) --
        # covers the two shapes that can otherwise appear at this level and
        # have no `.duration` of their own: InAccord (mirrors
        # Measure.total_ticks' own longest-voice rule) and MeasureRepeat (a
        # whole-measure placeholder with no note-level content at all, so
        # there is nothing meaningful to add).
        if isinstance(item, InAccord):
            if not item.parts:
                return 0
            return max(sum(_item_ticks(n) for n in part) for part in item.parts)
        if isinstance(item, MeasureRepeat):
            return 0
        return _item_ticks(item)

    i = 0
    ticks_from_measure_start = 0
    while i < n_items:
        if is_16th_note(items[i]):
            run_end = i
            while run_end < n_items and is_16th_note(items[run_end]):
                run_end += 1
            # Split [i, run_end) into beat-aligned groups, starting from
            # wherever ticks_from_measure_start currently sits within the
            # beat -- the run doesn't necessarily begin exactly on a beat.
            pos = i
            beat_ticks = ticks_from_measure_start
            while pos < run_end:
                ticks_left_in_beat = TICKS_PER_QUARTER - (beat_ticks % TICKS_PER_QUARTER)
                group_end = pos
                group_ticks = 0
                while group_end < run_end and group_ticks + _item_ticks(items[group_end]) <= ticks_left_in_beat:
                    group_ticks += _item_ticks(items[group_end])
                    group_end += 1
                if group_end == pos:
                    # This single note's own value already exceeds the
                    # remaining beat space -- advance by one note so the
                    # loop always progresses; it isn't grouped with
                    # anything either side (matches Par. 8.1.1(a)).
                    group_end = pos + 1
                    group_ticks = _item_ticks(items[pos])
                if group_end - pos >= 3:
                    for k in range(pos + 1, group_end):
                        is_16th_continuation[k] = True
                beat_ticks += group_ticks
                pos = group_end
            ticks_from_measure_start = beat_ticks
            i = run_end
        else:
            ticks_from_measure_start += item_ticks_for_beat_tracking(items[i])
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
                curr_prev = _last_real_note(item.items) or curr_prev
            elif isinstance(item, InAccord) and item.parts and item.parts[0]:
                curr_prev = _last_real_note(item.parts[0]) or curr_prev
            elif isinstance(item, AlternatingTremolo):
                curr_prev = _last_real_note(item.items) or curr_prev

            # A leading Rest never receives (or consumes) the octave-mark
            # reset: BANA 3.2.1 requires the octave mark on the first NOTE
            # of a braille line, not literally the first item, so a rest
            # sitting before it must not clear this flag before the real
            # first note is reached.
            if not isinstance(item, (Rest, MeasureRepeat)):
                curr_measure_start = False

    return "".join(rendered)


@dataclass
class Measure:
    number: int
    notes: list[MeasureItem] = field(default_factory=list)
    time_signature: tuple[int, int] = (4, 4)
    key_signature: int = 0
    # Major/minor mode for this measure's effective key signature, used only
    # when emitting a LilyPond `\key` change (S11-2/S11-4) -- braille has no
    # mode marking (BANA Chapter 6), so key_signature (sharps/flats) alone
    # is what braille output and accidental spelling (S10d-15) care about.
    key_signature_mode: str = "major"
    clef: str = "treble"
    bar_line_type: str = 'measure_separator'
    text_markings: list[TextMarking] = field(default_factory=list)
    line: int = 0
    # A fermata over/under this measure's bar line (BANA Par. 22.2, Table
    # 22(B) -- distinct from a fermata on a note, which lives on Note
    # instead; see models/fermata.py). Which of Table 22(B)'s three
    # bar-line-fermata variants gets rendered depends on `bar_line_type`
    # (plain bar line / sectional double bar / final double bar) -- see
    # to_braille() below.
    bar_line_fermata: bool = False
    # First/second (or later) ending number(s) this measure belongs to
    # (BANA Chapter 17, Par. 17.1.1, Table 17 -- "voltas"), e.g. [1] for a
    # plain first ending, [1, 2] for a combined "1,2" ending printed over
    # one bracket, or a list built from a hyphenated range like "1-3"
    # ([1, 2, 3]). None means this measure isn't part of any ending.
    ending_numbers: list[int] | None = None

    def add_note(self, note: MeasureItem) -> None:
        self.notes.append(note)

    def total_ticks(self) -> int:
        """Sum this measure's resolved duration, in ticks (quarter = TICKS_PER_QUARTER).

        Shared by `BrailleParser._validate_measure_beat_count` (S5-8) and
        `Staff.to_lilypond()`'s `\\partial` emission for a pickup/anacrusis
        first measure, so both use one tick-accounting rule.
        """
        total = 0
        for item in self.notes:
            if isinstance(item, InAccord):
                # An in-accord's voices all cover the same span (BANA 11.1/
                # 11.1.2 require equal note value per side); use the longest
                # voice so a malformed voice mismatch doesn't silently
                # understate the count.
                if item.parts:
                    total += max(
                        sum(_item_ticks(n) for n in part) for part in item.parts
                    )
            else:
                total += _item_ticks(item)
        return total

    def to_lilypond(self, prev_midi: int = 60, key_signature_mode: str = "major") -> tuple[str, int]:
        from .key_signature import KeySignature
        key_sig = KeySignature(
            dots=frozenset(),
            category=None,
            raw_brl="",
            sharps_or_flats=self.key_signature,
            mode=key_signature_mode,
        )
        parts: list[str] = []
        for marking in self.text_markings:
            parts.append(marking.to_lilypond())
        cur_midi = prev_midi
        for item in self.notes:
            if hasattr(item, 'to_relative_lilypond'):
                s, cur_midi = item.to_relative_lilypond(cur_midi, key_signature=key_sig)
            else:
                s = item.to_lilypond(key_signature=key_sig)
            parts.append(s)

        bar_ly = _BAR_LINE_TO_LY.get(self.bar_line_type, '|')
        if self.bar_line_fermata:
            # Unlike the braille side, the LilyPond Notation Reference
            # (checked v2.26 "Bar lines" and "Expressive marks" sections)
            # does not document a way to attach \fermata to a bar line
            # itself (postfix events only attach to a rhythmic event, and
            # no example covers this case) -- warn and omit rather than
            # emit unconfirmed syntax that might not even compile.
            import warnings
            warnings.warn(
                "A fermata over a bar line has no confirmed LilyPond "
                "syntax (checked Notation Reference v2.26's \"Bar lines\" "
                "and \"Expressive marks\" sections) -- omitting it from "
                "the LilyPond output; the braille output still has it.",
                stacklevel=2,
            )
        result = ' '.join(parts) + ' ' + bar_ly
        # NOTE: `ending_numbers` (first/second endings) is deliberately not
        # consulted here. LilyPond represents them with \repeat volta N
        # { ... } \alternative { \volta numberlist {...} ... } wrapped
        # around a whole *range* of measures (Notation Reference Sec.
        # 4.1.3), not a per-measure marking, so that structure has to be
        # built by the caller that sees the whole measure range --
        # `Staff.to_lilypond()`, the only production caller of this method
        # (confirmed by grep before removing the old per-measure fallback
        # here) -- see its `_group_voltas`/volta-rendering code for the
        # real implementation, including the \relative pitch-chaining
        # verified against the real lilypond binary.
        return result, cur_midi

    def to_braille(
        self,
        prev_note: Optional[Note] = None,
        is_measure_start: bool = True,
        time_signature: Optional["TimeSignature"] = None,
        compression_level: str = "full",
        key_signature_change: Optional[int] = None,
    ) -> tuple[str, Optional[Note]]:
        # S11-3: `key_signature_change`, when not None, means this measure's
        # effective key differs from the previous measure's -- the caller
        # (BrailleRenderer/render_measure_slice) is expected to have already
        # made that comparison, since only it knows the true previous-
        # measure context across line-packing/lookahead. BANA Par. 6.5: "A
        # change of key is placed wherever it occurs ... followed by a
        # blank space (unless it is followed immediately by a meter
        # signature)" -- meter-signature adjacency isn't handled here (no
        # mid-piece meter-change support exists yet), so a trailing blank
        # is always added. No leading blank is added: the preceding
        # measure's own trailing bar-line cell is already a blank cell in
        # the ordinary case, and nothing needs separating at a line start.
        key_change_str = ""
        if key_signature_change is not None:
            from .key_signature import KeySignature as _KeySignatureChange
            change_brl = _KeySignatureChange(
                dots=frozenset(), category=None, raw_brl="",
                sharps_or_flats=key_signature_change,
            ).to_braille()
            if change_brl:
                key_change_str = change_brl + '⠀'
            else:
                # sharps_or_flats == 0: KeySignature.to_braille() has
                # nothing to show for "no sharps or flats" as a HEADER
                # signature, but BANA's braille form for cancelling a
                # previous key signature back to C major/A minor mid-piece
                # isn't confirmed anywhere in the manual excerpt this
                # project has verified against -- flagging rather than
                # guessing at a cancellation-naturals cell (CLAUDE.md's
                # standing rule).
                import warnings
                warnings.warn(
                    "A mid-piece key change back to 0 sharps/flats (C major/"
                    "A minor) has no confirmed BANA braille form in this "
                    "project yet -- omitting the change cell. Flag to the "
                    "developer before transcribing this for real.",
                    stacklevel=2,
                )
        # BANA Par. 22.3's general rule: "Any number of single words,
        # abbreviations, and other expressions that do not contain spaces
        # may be brailled without interruption, each being introduced by
        # the word sign" -- adjacent single-word/abbreviation markings get
        # no separator. Par. 22.3.8 narrows this for "longer expressions"
        # specifically: "Two or more unrelated longer expressions should be
        # enclosed in separate pairs of word signs with an intervening
        # space" -- an intervening space is needed between two adjacent
        # markings whenever at least one of the pair is a longer
        # (multi-word) expression, since its own closing word sign would
        # otherwise run straight into the next marking's opening one.
        marking_parts: list[str] = []
        for idx, m in enumerate(self.text_markings):
            if idx > 0 and (m.is_longer_expression() or self.text_markings[idx - 1].is_longer_expression()):
                marking_parts.append('⠀')  # blank braille cell (U+2800), not a literal ASCII space
            marking_parts.append(m.to_braille(inline=True))
        marking_strs = "".join(marking_parts)

        from .key_signature import KeySignature
        key_sig_obj = KeySignature(dots=frozenset(), category=None, raw_brl="", sharps_or_flats=self.key_signature)

        from .time_signature import TimeSignature
        ts_num, ts_den = self.time_signature
        ts_obj = TimeSignature(dots=frozenset(), category=None, raw_brl="", numerator=ts_num, denominator=ts_den)

        notes_str = _render_note_list_to_braille(
            self.notes,
            prev_note=prev_note,
            # BANA 3.2.1: "the octave is always marked ... for the first
            # note following any occurrence of a numeric indicator or word
            # sign" -- a mid-measure text marking is rendered as a word-sign
            # expression right before this measure's own notes (see
            # `marking_strs` above), so it forces the same reset as a real
            # line/measure start regardless of `is_measure_start`. A key
            # change (S11-3, BANA Par. 6.5) forces the same reset.
            is_measure_start=is_measure_start or bool(self.text_markings) or key_signature_change is not None,
            time_signature=ts_obj,
            key_signature=key_sig_obj,
            compression_level=compression_level,
        )

        # A key-change cell (S11-3), when present, sits right after
        # marking_strs and before notes_str -- it's what the dot-3
        # separator check below needs to look at first.
        _after_markings = key_change_str or notes_str
        if marking_strs and _after_markings and (ord(_after_markings[0]) - 0x2800) & 0x07 != 0:
            # BANA 22.3(d): the word-sign expression "must be followed by
            # dot 3 if the following sign contains dot 1, 2, or 3" -- e.g. a
            # rest cell (dots 1,2,3,6 for a quarter rest) right after the
            # marking. A following note is normally exempt (its forced
            # octave mark above uses only dots 4-6), so this only fires for
            # the rest/other cases where that protection doesn't apply.
            from dottednotes.bana_symbols import END_WORD_SIGN
            marking_strs += END_WORD_SIGN

        from dottednotes.bana_symbols import BAR_LINE_CELLS, BAR_LINE_SEQUENCES
        bar_cell = {v: k for k, v in BAR_LINE_CELLS.items()}.get(self.bar_line_type, '')
        if not bar_cell:
            bar_cell = {v: k for k, v in BAR_LINE_SEQUENCES.items()}.get(self.bar_line_type, '')

        if self.bar_line_fermata:
            from dottednotes.bana_symbols import FERMATA_OVER_BAR_LINE_CELL
            from dottednotes.models.fermata import FermataShape, Fermata
            if self.bar_line_type == 'measure_separator':
                # Table 22(B)'s "above/below a bar line" variant is its own
                # dedicated compound sign, not the (blank) plain-bar-line
                # cell with a fermata appended -- ASCII `_<l` decodes to
                # dots 4,5,6 + the plain fermata cell, unrelated to the
                # blank measure-separator cell it replaces here.
                bar_cell = FERMATA_OVER_BAR_LINE_CELL
            elif self.bar_line_type in ('section_double_bar', 'final_double_bar'):
                # These two variants ARE the existing double-bar cell with
                # the plain fermata cell appended (ASCII `<k'<l`/`<k<l`).
                bar_cell = bar_cell + Fermata(shape=FermataShape.NORMAL).to_braille()
            else:
                import warnings
                warnings.warn(
                    f"A fermata over a '{self.bar_line_type}' bar line is not "
                    "demonstrated anywhere in BANA Table 22(B) (only plain bar "
                    "lines, sectional double bars, and final double bars are) "
                    "-- rendering the bar line without the fermata sign rather "
                    "than guessing.",
                    stacklevel=2,
                )

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

        volta_str = ""
        if self.ending_numbers:
            volta_str = _ending_numbers_to_braille(self.ending_numbers)
            # Par. 17.1.1: "If the sign following the volta sign contains a
            # dot 1, 2, or 3, the volta sign must be followed by a dot 3 as
            # a separator." The first note of this measure already gets a
            # fresh octave mark from the normal is_measure_start machinery
            # (a volta always starts a measure), which independently
            # satisfies 17.1.1's "first note...requires a special octave
            # mark" -- no extra octave-forcing needed here.
            following = marking_strs or key_change_str or notes_str
            if following and (ord(following[0]) - 0x2800) & 0x07 != 0:
                volta_str += '⠄'

        return volta_str + marking_strs + key_change_str + notes_str + bar_cell, last_note

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
