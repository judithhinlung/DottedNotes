import re
from dataclasses import dataclass
from typing import Optional, Union, Any
from dottednotes.models.score import Score
from dottednotes.models.orchestra_score import OrchestraScore
from dottednotes.models.staff import Staff
from dottednotes.models.measure import Measure
from dottednotes.models.note import Note, Rest
from dottednotes.models.chord import Chord
from dottednotes.models.tuplet import Tuplet
from dottednotes.models.in_accord import InAccord
from dottednotes.models.dynamic import Dynamic, DynamicLevel
from dottednotes.bana_symbols import TABLE_29_ENGLISH

_HAIRPIN_END_LEVELS = (DynamicLevel.CRESCENDO_END, DynamicLevel.DECRESCENDO_END)


def _hairpin_effective_note(item: Any) -> Optional[Note]:
    """The Note that dynamics attach to for a given measure item: the
    item itself if it's a Note, or a Chord's written note (`notes[0]`,
    where `musicxml_parser.translate_measure` puts a chord's dynamics).
    Rests never carry dynamics (see braille_parser.py); anything else
    (Tuplet, InAccord) is handled by the flattening step below, not here."""
    if isinstance(item, Note):
        return item
    if isinstance(item, Chord) and item.notes:
        return item.notes[0]
    return None


def _flatten_staff_for_hairpins(staff: Staff) -> list[tuple[Any, Measure]]:
    """Flatten a staff's measures into a single ordered (item, measure)
    sequence, drilling into Tuplet groups and (taking the first part of)
    InAccord passages, so hairpin-termination decisions can look at
    "the very next item" across tuplet/measure boundaries without
    duplicating BANAValidator's own (differently-shaped) voice-flattening."""
    flat: list[tuple[Any, Measure]] = []

    def add_items(items: list, measure: Measure) -> None:
        for item in items:
            if isinstance(item, Tuplet):
                add_items(item.items, measure)
            elif isinstance(item, InAccord) and item.parts:
                add_items(item.parts[0], measure)
            else:
                flat.append((item, measure))

    for measure in staff.measures:
        add_items(measure.notes, measure)
    return flat


@dataclass
class HairpinTerminatorDecision:
    """Whether one hairpin-end `Dynamic` (CRESCENDO_END/DECRESCENDO_END)
    should be omitted, and why. Shared by `BrailleRenderer` (to actually
    drop it) and `BANAValidator` (to report which reason applied) so the
    two can't drift apart -- neither mutates the `staff` passed in."""
    note: Note
    dynamic: Dynamic
    measure_number: int
    omit: bool
    reason: str  # "another_dynamic" | "extensive_rest" | "final_double_bar" | ""


def hairpin_terminator_decisions(staff: Staff) -> list[HairpinTerminatorDecision]:
    """BANA Music Braille Code 2015, Par. 22.3.3(b) -- confirmed directly
    against the primary PDF text (Table 22(C)'s ">3"/">4" signs, which
    decode letter-for-letter to this codebase's existing `crescendo_end`/
    `decrescendo_end` cells): "A 'lowered C' >3 or 'lowered D' >4 sign
    that indicates the termination of a hairpin may be omitted if the
    marking is immediately followed by some definite mark of conclusion
    or contradiction such as another dynamic, an extensive rest, or a
    final double bar." Note this is narrower than an ordinary mid-piece
    barline: only a *final* double bar (the actual end of the piece or a
    major section) qualifies, not every measure separator.

    Returns one decision per hairpin-end dynamic found in this staff, in
    score order.
    """
    flat = _flatten_staff_for_hairpins(staff)
    decisions: list[HairpinTerminatorDecision] = []

    for idx, (item, measure) in enumerate(flat):
        note = _hairpin_effective_note(item)
        if note is None or not note.dynamics:
            continue
        for dyn in note.dynamics:
            if dyn.level not in _HAIRPIN_END_LEVELS:
                continue

            omit = False
            reason = ""
            if idx + 1 < len(flat):
                next_item, _next_measure = flat[idx + 1]
                if isinstance(next_item, Rest) and (next_item.is_full_measure or next_item.multi_measure_count > 1):
                    omit, reason = True, "extensive_rest"
                else:
                    next_note = _hairpin_effective_note(next_item)
                    if next_note is not None and any(d.level not in _HAIRPIN_END_LEVELS for d in next_note.dynamics):
                        omit, reason = True, "another_dynamic"
            elif measure.bar_line_type == 'final_double_bar':
                omit, reason = True, "final_double_bar"

            decisions.append(HairpinTerminatorDecision(
                note=note, dynamic=dyn, measure_number=measure.number,
                omit=omit, reason=reason,
            ))

    return decisions

_INT_TO_LITERARY_DIGIT = {
    1: '⠁', 2: '⠃', 3: '⠉', 4: '⠙', 5: '⠑', 6: '⠋', 7: '⠛', 8: '⠓', 9: '⠊', 0: '⠚'
}


def encode_literary_braille(text: str) -> str:
    """Encode standard ASCII text to BANA Unicode braille cells."""
    from dottednotes.parser.input_pipeline import ASCII_TO_DOTS
    text_to_encode = text.rstrip('.')

    def encode_word(word: str) -> str:
        letters = [c for c in word if c.isalpha()]
        result = []
        # A whole word of 2+ uppercase letters takes the double capital
        # sign once, not a single capital sign before every letter.
        if len(letters) >= 2 and all(c.isupper() for c in letters):
            result.append('⠠⠠')
            word = word.lower()
        for char in word:
            if char.isupper():
                result.append('⠠')
                char = char.lower()
            dots = ASCII_TO_DOTS.get(char.upper(), 0)
            result.append(chr(0x2800 + dots))
        return ''.join(result)

    blank_cell = chr(0x2800)
    encoded = blank_cell.join(encode_word(w) for w in text_to_encode.split(' '))
    return encoded + '⠲'


def center_line(text: str, width: int) -> str:
    """Center a braille line within the specified width."""
    if len(text) >= width:
        return text
    left_padding = (width - len(text)) // 2
    return ' ' * left_padding + text


def join_tempo_and_signature(tempo_brl: str, *signature_parts: str) -> str:
    """Join a tempo/expression marking with the combined clef/key/time
    signature unit, separated by one space when both are present. The
    signature parts themselves stay joined with no space between them
    (they're a single combined unit); only the tempo marking, a
    separate word-sign expression, is set off from it."""
    combined = "".join(signature_parts)
    if tempo_brl and combined:
        return tempo_brl + " " + combined
    return tempo_brl or combined


def _table29_lookup(staff_name: str) -> Optional[str]:
    """Resolve `staff_name` against BANA Table 29, tolerating the
    plural/section-style part names real MusicXML exports use (e.g.
    "Violins I", "Violas", "Double Basses") against the table's singular
    solo-instrument keys ("Violin I", "Viola", "Double bass")."""
    abbrev = TABLE_29_ENGLISH.get(staff_name)
    if abbrev:
        return abbrev

    numeral_match = re.match(r'^(.+?)\s+([IVXLCDM]+)$', staff_name)
    if numeral_match:
        head, numeral_suffix = numeral_match.group(1), numeral_match.group(2)
    else:
        head, numeral_suffix = staff_name, None

    words = head.split()
    if not words:
        return None
    last_word = words[-1]
    candidates = []
    if last_word.endswith('es'):
        candidates.append(last_word[:-2])
    if last_word.endswith('s'):
        candidates.append(last_word[:-1])

    lower_table = {key.lower(): val for key, val in TABLE_29_ENGLISH.items()}
    for candidate in candidates:
        singular_head = ' '.join(words[:-1] + [candidate])
        full_name = f"{singular_head} {numeral_suffix}" if numeral_suffix else singular_head
        abbrev = lower_table.get(full_name.lower())
        if abbrev:
            return abbrev
    return None


def staff_abbreviation(staff_name: str) -> str:
    """Look up a staff's BANA Table 29 abbreviation, falling back to its
    first two letters (or "ms" for an unnamed staff) when not in the table."""
    abbrev = _table29_lookup(staff_name)
    if abbrev:
        return abbrev
    words = [w for w in staff_name.split() if w]
    return words[0][:2].lower() if words else "ms"


def abbrev_to_brl(abbrev: str) -> str:
    """Encode an instrument abbreviation (e.g. "v1", "fl") to braille
    cells: letters through the standard literary alphabet cells, digits
    through the same lower-cell digit forms as ASCII_TO_DOTS ('1' -> dot
    2, etc.) -- BANA 33.2.2 requires instrument numbers in abbreviations
    to be lower-cell digits with no numeric indicator, not upper-cell
    digits behind a number sign."""
    from dottednotes.parser.input_pipeline import ASCII_TO_DOTS
    return ''.join(chr(0x2800 + ASCII_TO_DOTS.get(c.upper(), 0)) for c in abbrev)


def wrap_run_over_line(line: str, width: int) -> list[str]:
    """Split one staff's parallel line into BANA 28.1.2/33.4.7 run-over
    lines when it's too long to fit alone: the music hyphen (dot 5, BANA
    1.11) is appended directly to the last cell that fits (no space
    before it) to mark the interruption, and the remainder continues on
    a new line indented two cells beyond the parallel's margin -- with
    no re-stated abbreviation, since it's a continuation of the same
    line, not a new instrument line."""
    if len(line) <= width:
        return [line]
    result = []
    remaining = line
    indent = ""
    while len(indent) + len(remaining) > width:
        content_width = width - len(indent) - 1  # reserve 1 cell for ⠐
        result.append(indent + remaining[:content_width] + '⠐')
        remaining = remaining[content_width:]
        indent = "  "
    result.append(indent + remaining)
    return result


def ensemble_abbrev_prefixes(staff_names: list[str], music_strs: Optional[list[str]] = None) -> list[str]:
    """Build the '⠜XX' abbreviation prefixes for one system's staff lines,
    aligned to a common column (BANA 33.4: "the music of each line begins
    one space beyond the end of the longest abbreviation"). A staff whose
    abbreviation is shorter than the widest one in this group gets a dot 3
    (BANA 33.4.1: "the dot 3 that terminates the abbreviation") right
    after its abbreviation, then blank cells for the rest of the gap --
    the dot 3 takes up the first blank cell rather than adding an extra
    one, so every staff's music still starts at the same column.

    The staff(s) already at the widest abbreviation have no gap to fill,
    so they normally get no dot 3 -- except when the very next cell (the
    first cell of that staff's own music, from `music_strs`) sets dot 1,
    2, or 3, which would otherwise read as a continuation of the
    abbreviation's letters rather than the start of the music; that
    staff still gets a dot 3 to disambiguate, even with no gap to fill."""
    bare_prefixes = ['⠜' + abbrev_to_brl(staff_abbreviation(name)) for name in staff_names]
    max_len = max((len(p) for p in bare_prefixes), default=0)
    if music_strs is None:
        music_strs = [""] * len(staff_names)
    prefixes = []
    for bare, music_str in zip(bare_prefixes, music_strs):
        gap = max_len - len(bare)
        if gap > 0:
            prefixes.append(bare + '⠄' + chr(0x2800) * (gap - 1))
        elif music_str and (ord(music_str[0]) - 0x2800) & 0x07 != 0:
            prefixes.append(bare + '⠄')
        else:
            prefixes.append(bare)
    return prefixes


def pad_to_boundary(text: str, width: int) -> str:
    """Right-pad `text` to `width` cells so the next measure's content
    starts at a consistent column across every staff of a parallel
    (BANA 33.4), like a table column. A gap of 6 or fewer blank cells is
    plain blank cells; a larger gap is guide dots with a blank cell on
    each side -- one separating them from this staff's own music, one
    separating them from the next measure -- per BANA 28.1.3/33.4 and
    Example 33.4.6-1."""
    gap = width - len(text)
    if gap <= 0:
        return text
    blank = chr(0x2800)
    if gap > 6:
        return text + blank + '⠄' * (gap - 2) + blank
    return text + blank * gap


def render_measure_slice(
    measures: list[Measure],
    start_idx: int,
    size: int,
    prev_note: Optional[Note],
    time_sig,
    compression_level: str = "full"
) -> tuple[list[str], Optional[Note]]:
    """Helper to render a slice of measures. Only the first measure of the slice is treated as a line start."""
    rendered = []
    curr_prev = prev_note
    for k in range(size):
        m = measures[start_idx + k]
        is_start = (k == 0)
        m_brl, curr_prev = m.to_braille(prev_note=curr_prev, is_measure_start=is_start, time_signature=time_sig, compression_level=compression_level)
        rendered.append(m_brl)
    return rendered, curr_prev


class BrailleRenderer:
    def __init__(
        self,
        line_width: int = 40,
        show_measure_numbers: bool = True,
        compression_level: str = "full",
        omit_redundant_hairpin_terminators: bool = True,
    ):
        self.line_width = line_width
        self.show_measure_numbers = show_measure_numbers
        self.compression_level = compression_level
        # BANA 22.3.3(b): override/disable if a caller wants every hairpin
        # terminator brailled explicitly regardless of what follows it --
        # independent of `compression_level`, since this is a transcription
        # rule rather than one of the optional space-saving passes below.
        self.omit_redundant_hairpin_terminators = omit_redundant_hairpin_terminators

    def render(self, score: Score) -> str:
        if not score.staves:
            return ""

        import copy
        score = copy.deepcopy(score)

        if self.omit_redundant_hairpin_terminators:
            self._omit_redundant_hairpin_terminators(score)

        if self.compression_level != "none":
            # Pass 1: Articulation carry shorthand pass
            self._compress_articulations(score)

        # BANA 33.1's tacet-staff omission (see active_staff_indices in
        # _render_ensemble) needs to know whether a measure's *real*
        # content is a bare rest -- captured here, before the measure-repeat
        # pass below overwrites a repeated rest measure's notes with a
        # MeasureRepeat sign, which is not itself a Rest instance and would
        # otherwise be mistaken for "has music to play".
        rest_only_grid = [
            [all(isinstance(item, Rest) for item in m.notes) for m in staff.measures]
            for staff in score.staves
        ]

        if self.compression_level != "none":
            # Pass 2: Measure repeat compression pass
            self._compress_measure_repeats(score)

        # Determine layout type. is_piano is computed first and independent of
        # isinstance(score, OrchestraScore): LilypondParser tags any parsed
        # score containing "PianoStaff" as an OrchestraScore, so a 2-staff
        # piano score must not automatically fall into ensemble layout.
        from dottednotes.models.instrument import InstrumentFamily, get_instrument_family
        is_piano = len(score.staves) == 2 and any(
            get_instrument_family(s.name) == InstrumentFamily.KEYBOARD_HARP for s in score.staves
        )
        is_ensemble = not is_piano and (isinstance(score, OrchestraScore) or len(score.staves) > 2)

        if is_ensemble:
            return self._render_ensemble(score, rest_only_grid)
        elif is_piano:
            return self._render_piano(score)
        else:
            return self._render_solo(score)

    def _render_solo(self, score: Score) -> str:
        lines = []
        # Title
        if score.title:
            lines.append(center_line(encode_literary_braille(score.title), self.line_width))

        # Signatures line
        staff = score.staves[0]
        signature_parts = []
        if staff.clef:
            signature_parts.append(staff.clef.to_braille())
        if staff.key_signature:
            signature_parts.append(staff.key_signature.to_braille())
        if staff.time_signature:
            signature_parts.append(staff.time_signature.to_braille())
        tempo_brl = staff.tempo.to_braille() if staff.tempo else ""
        sig_line = join_tempo_and_signature(tempo_brl, *signature_parts)

        if sig_line:
            # BANA solo signature line starts with 8 spaces indentation
            lines.append("        " + sig_line)

        # Pack measures on the fly
        current_line = ""
        prev_note = None

        for idx, m in enumerate(staff.measures):
            # Render both possibilities
            brl_start, prev_start = m.to_braille(prev_note=prev_note, is_measure_start=True, time_signature=staff.time_signature, compression_level=self.compression_level)
            brl_no_start, prev_no_start = m.to_braille(prev_note=prev_note, is_measure_start=False, time_signature=staff.time_signature, compression_level=self.compression_level)

            if not current_line:
                num_str = "".join(_INT_TO_LITERARY_DIGIT[int(d)] for d in str(m.number))
                prefix = (num_str + " ") if self.show_measure_numbers else ""
                current_line = prefix + brl_start
                prev_note = prev_start
            else:
                if len(current_line) + len(brl_no_start) <= self.line_width:
                    current_line += brl_no_start
                    prev_note = prev_no_start
                else:
                    lines.append(current_line)
                    num_str = "".join(_INT_TO_LITERARY_DIGIT[int(d)] for d in str(m.number))
                    prefix = (num_str + " ") if self.show_measure_numbers else ""
                    current_line = prefix + brl_start
                    prev_note = prev_start

        if current_line:
            lines.append(current_line)

        return "\n".join(lines) + "\n"

    def _render_piano(self, score: Score) -> str:
        lines = []
        # Title
        if score.title:
            lines.append(center_line(encode_literary_braille(score.title), self.line_width))

        # Signatures line
        rh_staff = score.staves[0]
        signature_parts = []
        if rh_staff.key_signature:
            signature_parts.append(rh_staff.key_signature.to_braille())
        if rh_staff.time_signature:
            signature_parts.append(rh_staff.time_signature.to_braille())
        tempo_brl = rh_staff.tempo.to_braille() if rh_staff.tempo else ""
        sig_line = join_tempo_and_signature(tempo_brl, *signature_parts)

        if sig_line:
            lines.append("        " + sig_line)

        # Render measures for both hands
        lh_staff = score.staves[1]
        
        idx = 0
        n_measures = len(rh_staff.measures)
        prev_note_rh = None
        prev_note_lh = None
        
        while idx < n_measures:
            group_size = 1
            best_rh_lines = []
            best_lh_lines = []
            best_prev_rh = prev_note_rh
            best_prev_lh = prev_note_lh
            
            while idx + group_size <= n_measures:
                rh_slice_strs, tmp_prev_rh = render_measure_slice(rh_staff.measures, idx, group_size, prev_note_rh, rh_staff.time_signature, self.compression_level)
                lh_slice_strs, tmp_prev_lh = render_measure_slice(lh_staff.measures, idx, group_size, prev_note_lh, lh_staff.time_signature, self.compression_level)
                
                m_num = rh_staff.measures[idx].number
                test_rh = self._build_piano_line_from_strings(m_num, rh_slice_strs, is_right=True)
                test_lh = self._build_piano_line_from_strings(m_num, lh_slice_strs, is_right=False)
                
                if len(test_rh) <= self.line_width and len(test_lh) <= self.line_width:
                    best_rh_lines = test_rh
                    best_lh_lines = test_lh
                    best_prev_rh = tmp_prev_rh
                    best_prev_lh = tmp_prev_lh
                    group_size += 1
                else:
                    break
            
            if not best_rh_lines:
                # Force at least one measure to avoid infinite loop
                rh_slice_strs, best_prev_rh = render_measure_slice(rh_staff.measures, idx, 1, prev_note_rh, rh_staff.time_signature, self.compression_level)
                lh_slice_strs, best_prev_lh = render_measure_slice(lh_staff.measures, idx, 1, prev_note_lh, lh_staff.time_signature, self.compression_level)
                m_num = rh_staff.measures[idx].number
                best_rh_lines = self._build_piano_line_from_strings(m_num, rh_slice_strs, is_right=True)
                best_lh_lines = self._build_piano_line_from_strings(m_num, lh_slice_strs, is_right=False)
                fit_size = 1
            else:
                fit_size = group_size - 1
                
            lines.append(best_rh_lines)
            lines.append(best_lh_lines)
            prev_note_rh = best_prev_rh
            prev_note_lh = best_prev_lh
            idx += fit_size

        return "\n".join(lines) + "\n"

    def _build_piano_line_from_strings(self, measure_num: int, measure_strs: list[str], is_right: bool) -> str:
        if self.show_measure_numbers:
            num_str = "".join(_INT_TO_LITERARY_DIGIT[int(d)] for d in str(measure_num))
            prefix = num_str + " "
        else:
            prefix = ""
        
        hand_sign = '⠨⠜' if is_right else '⠸⠜'
        music_str = "".join(measure_strs)
        if music_str:
            first_cell = music_str[0]
            if (ord(first_cell) - 0x2800) & 0x07 != 0:
                hand_sign += '⠄'

        if is_right:
            return prefix + hand_sign + music_str
        else:
            return " " * len(prefix) + hand_sign + music_str

    def _render_ensemble(self, score: Score, rest_only_grid: list[list[bool]]) -> str:
        lines = []
        # Title
        if score.title:
            lines.append(center_line(encode_literary_braille(score.title), self.line_width))

        # Instrument list
        for staff in score.staves:
            abbrev = staff_abbreviation(staff.name)

            name_brl = encode_literary_braille(staff.name)
            if len(name_brl) < 12:
                padding = '⠐' * (12 - len(name_brl))
            else:
                padding = ""
            
            abbrev_brl = '⠜' + abbrev_to_brl(abbrev) + '⠄'
            lines.append(name_brl + padding + "  " + abbrev_brl)

        # Signature line
        first_staff = score.staves[0]
        signature_parts = []
        if first_staff.key_signature:
            signature_parts.append(first_staff.key_signature.to_braille())
        if first_staff.time_signature:
            signature_parts.append(first_staff.time_signature.to_braille())
        tempo_brl = first_staff.tempo.to_braille() if first_staff.tempo else ""
        sig_line = join_tempo_and_signature(tempo_brl, *signature_parts)

        if sig_line:
            lines.append("       " + sig_line)

        # Pack measures into systems on the fly. Per BANA 33.4, the first
        # signs of each measure must be vertically aligned across every
        # part of the parallel, and the music of every line must start
        # one space beyond the longest instrument abbreviation -- so a
        # candidate system is built for ALL staves together (not staff by
        # staff), padding each staff's shorter measures/abbreviation up
        # to the widest rendering of that measure/abbreviation across the
        # whole parallel, before checking whether it fits line_width.
        n_measures = len(score.staves[0].measures) if score.staves else 0
        n_staves = len(score.staves)
        idx = 0
        prev_notes = [None] * n_staves

        def active_staff_indices(group_size: int) -> list[int]:
            # BANA 33.1: "each parallel contain[s] only the music of the
            # instruments that have music to play in those measures. An
            # instrument that has only rests in those measures is omitted
            # from the parallel." A staff qualifies as active for this
            # candidate system only if at least one of its measures in the
            # range has something other than a bare rest -- checked against
            # rest_only_grid (captured before measure-repeat compression),
            # not the current score's notes, since a run of repeated rest
            # measures is by then a MeasureRepeat sign, not a Rest.
            active = [
                s_idx for s_idx in range(n_staves)
                if any(
                    not rest_only_grid[s_idx][m_idx]
                    for m_idx in range(idx, idx + group_size)
                )
            ]
            # A measure range where every staff is tacet can't happen in
            # real orchestral music (nothing would be there to transcribe),
            # but fall back to showing everything rather than an empty
            # system if it ever does.
            return active or list(range(n_staves))

        def render_candidate(group_size: int, active: list[int]):
            slices = []
            prevs = []
            for s_idx in active:
                staff = score.staves[s_idx]
                slice_strs, tmp_prev = render_measure_slice(
                    staff.measures, idx, group_size, prev_notes[s_idx], staff.time_signature, self.compression_level
                )
                slices.append(slice_strs)
                prevs.append(tmp_prev)

            prefixes = ensemble_abbrev_prefixes(
                [score.staves[s].name for s in active],
                ["".join(slice_strs) for slice_strs in slices],
            )
            max_prefix_len = max(len(p) for p in prefixes)

            # Every measure but the last in the system is a fixed table
            # column: its width is the widest rendering of that measure
            # across all active staves, plus 2 cells -- the next measure
            # starts exactly 2 cells after the longest staff's content for
            # this one, and shorter staves get that same width filled with
            # guide dots (or plain blanks for a small gap), never packed
            # flush against the next measure (BANA 33.4, like how the
            # instrument list aligns names to a fixed column).
            measure_widths = [
                max(len(slices[k][m]) for k in range(len(active))) + 2
                for m in range(group_size - 1)
            ]

            staff_lines = []
            for k in range(len(active)):
                prefix = prefixes[k] + chr(0x2800) * (max_prefix_len - len(prefixes[k]))
                body = "".join(
                    pad_to_boundary(slices[k][m], measure_widths[m])
                    for m in range(group_size - 1)
                )
                body += slices[k][group_size - 1]
                staff_lines.append(prefix + body)

            return staff_lines, prevs, max_prefix_len, measure_widths

        while idx < n_measures:
            group_size = 1
            best = None

            while idx + group_size <= n_measures:
                active = active_staff_indices(group_size)
                staff_lines, prevs, max_prefix_len, measure_widths = render_candidate(group_size, active)
                if any(len(line) > self.line_width for line in staff_lines):
                    break
                best = (group_size, staff_lines, prevs, max_prefix_len, measure_widths, active)
                group_size += 1

            if best is None:
                # Force 1 measure even if it doesn't fit.
                active = active_staff_indices(1)
                best = (1, *render_candidate(1, active), active)

            fit_size, best_staff_lines, best_prev_notes, max_prefix_len, measure_widths, best_active = best

            if idx > 0:
                lines.append("")
            if self.show_measure_numbers:
                heading_chars = [" "] * self.line_width
                # BANA 33.4.6: the marking is "indented one cell beyond
                # the first music signs of the parallel" -- one column
                # past wherever each measure's own (now cross-staff
                # aligned) content starts, not directly above it.
                col = max_prefix_len + 1
                for k in range(fit_size):
                    m = score.staves[0].measures[idx + k]
                    num_str = "⠼" + "".join(_INT_TO_LITERARY_DIGIT[int(d)] for d in str(m.number))
                    for char_idx, char in enumerate(num_str):
                        if col + char_idx < self.line_width:
                            heading_chars[col + char_idx] = char
                    if k < len(measure_widths):
                        col += measure_widths[k]
                heading_line = "".join(heading_chars).rstrip()
                lines.append(heading_line)

            for staff_line in best_staff_lines:
                lines.extend(wrap_run_over_line(staff_line, self.line_width))
            for k, s_idx in enumerate(best_active):
                prev_notes[s_idx] = best_prev_notes[k]
            idx += fit_size

        return "\n".join(lines) + "\n"

    def _omit_redundant_hairpin_terminators(self, score: Score) -> None:
        """Apply `hairpin_terminator_decisions()` to the (already
        deep-copied) score: drop each hairpin-end `Dynamic` it flags as
        omittable. Mirrors the other rendering-time passes here (mutates
        in place, doesn't touch the caller's original `score`)."""
        for staff in score.staves:
            for decision in hairpin_terminator_decisions(staff):
                if decision.omit:
                    decision.note.dynamics = [
                        d for d in decision.note.dynamics if d is not decision.dynamic
                    ]

    def _compress_articulations(self, score: Score) -> None:
        from dottednotes.models.note import Note, Rest
        from dottednotes.models.chord import Chord
        for staff in score.staves:
            voices = self._get_staff_voices_raw(staff)
            for voice in voices:
                n_notes = len(voice)
                i = 0
                while i < n_notes:
                    def get_note_art(item):
                        n = item.notes[0] if isinstance(item, Chord) else item
                        if isinstance(n, Note) and len(n.articulations) == 1:
                            return n.articulations[0].type
                        return None

                    art_type = get_note_art(voice[i])
                    if art_type is not None:
                        run = [voice[i]]
                        j = i + 1
                        while j < n_notes:
                            nxt = voice[j]
                            if isinstance(nxt, Rest):
                                break
                            if get_note_art(nxt) == art_type:
                                run.append(nxt)
                                j += 1
                            else:
                                break
                        
                        if len(run) >= 4:
                            # Apply carry
                            first_n = run[0].notes[0] if isinstance(run[0], Chord) else run[0]
                            first_n.articulation_format = "start_carry"
                            for item in run[1:-1]:
                                mid_n = item.notes[0] if isinstance(item, Chord) else item
                                mid_n.articulation_format = "inside_carry"
                            last_n = run[-1].notes[0] if isinstance(run[-1], Chord) else run[-1]
                            last_n.articulation_format = "stop_carry"
                        i = j
                    else:
                        i += 1

    def _get_staff_voices_raw(self, staff: Staff) -> list[list[Any]]:
        from dottednotes.models.in_accord import InAccord
        max_parts = 1
        for m in staff.measures:
            for item in m.notes:
                if isinstance(item, InAccord):
                    max_parts = max(max_parts, len(item.parts))

        voices = [[] for _ in range(max_parts)]
        for m in staff.measures:
            in_accord = None
            for item in m.notes:
                if isinstance(item, InAccord):
                    in_accord = item
                    break

            if in_accord:
                for i in range(max_parts):
                    part_idx = min(i, len(in_accord.parts) - 1)
                    voices[i].extend(self._flatten_items_raw(in_accord.parts[part_idx]))
            else:
                measure_notes = self._flatten_items_raw(m.notes)
                for i in range(max_parts):
                    voices[i].extend(measure_notes)
        return voices

    def _flatten_items_raw(self, items: list) -> list[Any]:
        from dottednotes.models.note import Note, Rest
        from dottednotes.models.chord import Chord
        from dottednotes.models.tuplet import Tuplet
        flat = []
        for item in items:
            if isinstance(item, (Note, Rest, Chord)):
                flat.append(item)
            elif isinstance(item, Tuplet):
                flat.extend(self._flatten_items_raw(item.items))
        return flat

    def _compress_measure_repeats(self, score: Score) -> None:
        import copy
        from dottednotes.models.measure_repeat import MeasureRepeat
        for staff in score.staves:
            if not staff.measures:
                continue
            i = 1
            last_non_repeat_measure = copy.deepcopy(staff.measures[0])
            while i < len(staff.measures):
                curr_m = staff.measures[i]
                if curr_m.musical_equals(last_non_repeat_measure):
                    curr_m.notes = [MeasureRepeat(count=1, line=1)]
                else:
                    last_non_repeat_measure = copy.deepcopy(curr_m)
                i += 1
