from typing import Optional, Union
from dottednotes.models.score import Score
from dottednotes.models.orchestra_score import OrchestraScore
from dottednotes.models.staff import Staff
from dottednotes.models.measure import Measure
from dottednotes.models.note import Note
from dottednotes.bana_symbols import TABLE_29_ENGLISH

_INT_TO_LITERARY_DIGIT = {
    1: '⠁', 2: '⠃', 3: '⠉', 4: '⠙', 5: '⠑', 6: '⠋', 7: '⠛', 8: '⠓', 9: '⠊', 0: '⠚'
}


def encode_literary_braille(text: str) -> str:
    """Encode standard ASCII text to BANA Unicode braille cells."""
    from dottednotes.parser.input_pipeline import ASCII_TO_DOTS
    result = []
    text_to_encode = text.rstrip('.')
    for char in text_to_encode:
        if char.isupper():
            result.append('⠠')
            char = char.lower()
        dots = ASCII_TO_DOTS.get(char.upper(), 0)
        result.append(chr(0x2800 + dots))
    result.append('⠲')
    return ''.join(result)


def center_line(text: str, width: int) -> str:
    """Center a braille line within the specified width."""
    if len(text) >= width:
        return text
    left_padding = (width - len(text)) // 2
    return ' ' * left_padding + text


def render_measure_slice(
    measures: list[Measure],
    start_idx: int,
    size: int,
    prev_note: Optional[Note],
    time_sig
) -> tuple[list[str], Optional[Note]]:
    """Helper to render a slice of measures. Only the first measure of the slice is treated as a line start."""
    rendered = []
    curr_prev = prev_note
    for k in range(size):
        m = measures[start_idx + k]
        is_start = (k == 0)
        m_brl, curr_prev = m.to_braille(prev_note=curr_prev, is_measure_start=is_start, time_signature=time_sig)
        rendered.append(m_brl)
    return rendered, curr_prev


class BrailleRenderer:
    def __init__(self, line_width: int = 40, show_measure_numbers: bool = True):
        self.line_width = line_width
        self.show_measure_numbers = show_measure_numbers

    def render(self, score: Score) -> str:
        if not score.staves:
            return ""

        # Determine layout type
        is_ensemble = isinstance(score, OrchestraScore) or len(score.staves) > 2
        is_piano = not is_ensemble and len(score.staves) == 2 and any(
            "piano" in s.name.lower() or "harp" in s.name.lower() for s in score.staves
        )

        if is_ensemble:
            return self._render_ensemble(score)
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
        sig_parts = []
        if staff.tempo:
            sig_parts.append(staff.tempo.to_braille())
        if staff.clef:
            sig_parts.append(staff.clef.to_braille())
        if staff.key_signature:
            sig_parts.append(staff.key_signature.to_braille())
        if staff.time_signature:
            sig_parts.append(staff.time_signature.to_braille())

        if sig_parts:
            # BANA solo signature line starts with 8 spaces indentation
            lines.append("        " + "".join(sig_parts))

        # Pack measures on the fly
        current_line = ""
        prev_note = None

        for idx, m in enumerate(staff.measures):
            # Render both possibilities
            brl_start, prev_start = m.to_braille(prev_note=prev_note, is_measure_start=True, time_signature=staff.time_signature)
            brl_no_start, prev_no_start = m.to_braille(prev_note=prev_note, is_measure_start=False, time_signature=staff.time_signature)

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
        sig_parts = []
        if rh_staff.tempo:
            sig_parts.append(rh_staff.tempo.to_braille())
        if rh_staff.key_signature:
            sig_parts.append(rh_staff.key_signature.to_braille())
        if rh_staff.time_signature:
            sig_parts.append(rh_staff.time_signature.to_braille())

        if sig_parts:
            lines.append("        " + "".join(sig_parts))

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
                rh_slice_strs, tmp_prev_rh = render_measure_slice(rh_staff.measures, idx, group_size, prev_note_rh, rh_staff.time_signature)
                lh_slice_strs, tmp_prev_lh = render_measure_slice(lh_staff.measures, idx, group_size, prev_note_lh, lh_staff.time_signature)
                
                test_rh = self._build_piano_line_from_strings(idx, rh_slice_strs, is_right=True)
                test_lh = self._build_piano_line_from_strings(idx, lh_slice_strs, is_right=False)
                
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
                rh_slice_strs, best_prev_rh = render_measure_slice(rh_staff.measures, idx, 1, prev_note_rh, rh_staff.time_signature)
                lh_slice_strs, best_prev_lh = render_measure_slice(lh_staff.measures, idx, 1, prev_note_lh, lh_staff.time_signature)
                best_rh_lines = self._build_piano_line_from_strings(idx, rh_slice_strs, is_right=True)
                best_lh_lines = self._build_piano_line_from_strings(idx, lh_slice_strs, is_right=False)
                fit_size = 1
            else:
                fit_size = group_size - 1
                
            lines.append(best_rh_lines)
            lines.append(best_lh_lines)
            prev_note_rh = best_prev_rh
            prev_note_lh = best_prev_lh
            idx += fit_size

        return "\n".join(lines) + "\n"

    def _build_piano_line_from_strings(self, idx: int, measure_strs: list[str], is_right: bool) -> str:
        first_num = idx + 1
        num_str = "".join(_INT_TO_LITERARY_DIGIT[int(d)] for d in str(first_num))
        prefix = num_str + " "
        
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

    def _render_ensemble(self, score: Score) -> str:
        lines = []
        # Title
        if score.title:
            lines.append(center_line(encode_literary_braille(score.title), self.line_width))

        # Instrument list
        for staff in score.staves:
            abbrev = TABLE_29_ENGLISH.get(staff.name)
            if not abbrev:
                words = [w for w in staff.name.split() if w]
                abbrev = words[0][:2].lower() if words else "ms"
            
            name_brl = encode_literary_braille(staff.name)
            if len(name_brl) < 12:
                padding = '⠐' * (12 - len(name_brl))
            else:
                padding = ""
            
            abbrev_brl = '⠜' + abbrev.upper() + '⠄'
            lines.append(name_brl + padding + "  " + abbrev_brl)

        # Signature line
        first_staff = score.staves[0]
        sig_parts = []
        if first_staff.tempo:
            sig_parts.append(first_staff.tempo.to_braille())
        if first_staff.key_signature:
            sig_parts.append(first_staff.key_signature.to_braille())
        if first_staff.time_signature:
            sig_parts.append(first_staff.time_signature.to_braille())

        if sig_parts:
            lines.append("       " + "".join(sig_parts))

        # Pack measures into systems on the fly
        n_measures = len(score.staves[0].measures) if score.staves else 0
        idx = 0
        prev_notes = [None] * len(score.staves)
        
        while idx < n_measures:
            group_size = 1
            best_staff_lines = []
            best_prev_notes = list(prev_notes)
            
            while idx + group_size <= n_measures:
                # Try to render candidate slice
                all_fit = True
                temp_staff_lines = []
                temp_prev_notes = []
                
                for s_idx, staff in enumerate(score.staves):
                    slice_strs, tmp_prev = render_measure_slice(staff.measures, idx, group_size, prev_notes[s_idx], staff.time_signature)
                    music_str = "".join(slice_strs)
                    
                    abbrev = TABLE_29_ENGLISH.get(staff.name)
                    if not abbrev:
                        words = [w for w in staff.name.split() if w]
                        abbrev = words[0][:2].lower() if words else "ms"
                    abbrev_prefix = '⠜' + abbrev.upper()
                    if music_str:
                        first_cell = music_str[0]
                        if (ord(first_cell) - 0x2800) & 0x07 != 0:
                            abbrev_prefix += '⠄'
                            
                    test_line = abbrev_prefix + music_str
                    if len(test_line) > self.line_width:
                        all_fit = False
                        break
                    
                    temp_staff_lines.append(test_line)
                    temp_prev_notes.append(tmp_prev)
                    
                if all_fit:
                    best_staff_lines = temp_staff_lines
                    best_prev_notes = temp_prev_notes
                    group_size += 1
                else:
                    break
                    
            if not best_staff_lines:
                # Force 1 measure
                best_staff_lines = []
                best_prev_notes = []
                for s_idx, staff in enumerate(score.staves):
                    slice_strs, tmp_prev = render_measure_slice(staff.measures, idx, 1, prev_notes[s_idx], staff.time_signature)
                    music_str = "".join(slice_strs)
                    abbrev = TABLE_29_ENGLISH.get(staff.name)
                    if not abbrev:
                        words = [w for w in staff.name.split() if w]
                        abbrev = words[0][:2].lower() if words else "ms"
                    abbrev_prefix = '⠜' + abbrev.upper()
                    if music_str:
                        first_cell = music_str[0]
                        if (ord(first_cell) - 0x2800) & 0x07 != 0:
                            abbrev_prefix += '⠄'
                    best_staff_lines.append(abbrev_prefix + music_str)
                    best_prev_notes.append(tmp_prev)
                fit_size = 1
            else:
                fit_size = group_size - 1
                
            # Print heading
            first_num = idx + 1
            heading_line = "     ⠼" + "".join(_INT_TO_LITERARY_DIGIT[int(d)] for d in str(first_num))
            lines.append(heading_line)
            
            lines.extend(best_staff_lines)
            prev_notes = best_prev_notes
            idx += fit_size

        return "\n".join(lines) + "\n"
