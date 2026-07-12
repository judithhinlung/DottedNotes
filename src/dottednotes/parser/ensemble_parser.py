from __future__ import annotations

import copy
import re

from ..bana_symbols import (
    SymbolCategory,
    OCTAVE_MARKS,
    LOWER_DIGIT_CELLS,
    LITERARY_DIGITS,
    NUMBER_SIGN,
)
from ..models.instrument import InstrumentInfo
from ..models.orchestra_score import OrchestraScore
from ..models.staff import Staff
from ..models.measure import Measure
from ..models.note import Note, Rest
from ..models.chord import Chord
from ..models.in_accord import InAccord
from ..models.tuplet import Tuplet
from .input_pipeline import BRLInputPipeline, decode_literary_braille
from .tokenizer import BrailleTokenizer, BrailleToken
from .braille_parser import BrailleParser
from .instrument_list import parse_instrument_list

# Match optional octave mark (1 or 2 octave cells), followed by ⠤, optionally followed by an abbreviation in ⠜...⠄
PARALLEL_MOVEMENT_REGEX = re.compile(
    r'^([⠈⠘⠸⠐⠨⠰⠠]{1,2})?⠤(⠜[^⠄]+⠄)?$'
)

LITERARY_DIGIT_MAP = {
    '⠁': '1', '⠃': '2', '⠉': '3', '⠙': '4', '⠑': '5',
    '⠋': '6', '⠛': '7', '⠓': '8', '⠊': '9', '⠚': '0'
}


def extract_measure_number(line_str: str) -> tuple[int | None, str]:
    """Extract a leading measure number and return (measure_number, remaining_line).

    Two conventions are recognized (BANA Sec. 33.4.6, "Measure Numbers and
    Rehearsal References" -- "if it is an actual measure number it is not
    enclosed [between word signs]"):

    1. NUMBER_SIGN (⠼) + literary digit-letter(s), alone on its own line (the
       parallel's instrument lines follow on subsequent lines). This is
       disambiguated from a time signature (which also starts with ⠼) by the
       fact that every TIME_SIGNATURE_CELLS entry's second cell is never a
       literary digit -- so a genuine time signature never leaves `remaining`
       empty/whitespace-only after consuming leading digit cells.
    2. Legacy: a bare literary digit directly at the line start, glued to the
       same line as the first instrument's abbreviation and content.
    """
    stripped = line_str.lstrip('⠀ ')

    if stripped.startswith(NUMBER_SIGN):
        digits = []
        i = 1
        while i < len(stripped) and stripped[i] in LITERARY_DIGIT_MAP:
            digits.append(LITERARY_DIGIT_MAP[stripped[i]])
            i += 1
        if digits:
            remaining = stripped[i:]
            if not remaining or remaining.startswith(' ') or remaining.startswith('⠀'):
                return int(''.join(digits)), remaining.lstrip('⠀ ')

    digits = []
    i = 0
    while i < len(stripped) and stripped[i] in LITERARY_DIGIT_MAP:
        digits.append(LITERARY_DIGIT_MAP[stripped[i]])
        i += 1

    if digits:
        remaining = stripped[i:]
        if not remaining or remaining.startswith(' ') or remaining.startswith('⠀'):
            return int(''.join(digits)), remaining.lstrip('⠀ ')

    return None, line_str


def extract_line_abbreviation(line_str: str) -> tuple[str | None, str]:
    """Find the first instrument abbreviation on the line, return (abbrev_cells, music_cells)."""
    stripped = line_str.lstrip('⠀ ')

    # The abbreviation must end with END_WORD_SIGN (⠄)
    end = stripped.find('⠄')
    if end != -1:
        abbrev_cells = stripped[:end+1]
        music_cells = stripped[end+1:]
        return abbrev_cells, music_cells

    return None, line_str


def _line_has_word_sign(line: str) -> bool:
    """True if `line` contains a genuine standalone WORD_SIGN token, as
    opposed to merely containing the same dot pattern as the second cell
    of a HAND_SIGN_CELLS sequence (e.g. a two-hand piano piece's ⠨⠜/⠸⠜
    hand sign followed later in the line by an unrelated END_WORD_SIGN-
    shaped cell). Raw substring matching on WORD_SIGN/END_WORD_SIGN can't
    tell these apart; the tokenizer's positional HAND_SIGN vs WORD_SIGN
    classification (tokenizer.py) can. `line` must already be normalized
    Unicode braille, same precondition as extract_measure_number.
    """
    tokens = BrailleTokenizer().tokenize(line)
    return any(t.category == SymbolCategory.WORD_SIGN for t in tokens)


def has_ensemble_header(text: str) -> bool:
    """True if `text` (normalized Unicode braille) contains a BANA §33.2
    instrument-list header line. Used to dispatch between EnsembleParser
    and the solo BrailleParser/tokenizer path (see cli.py)."""
    for line in text.splitlines():
        m_num, _ = extract_measure_number(line)
        if m_num is None and _line_has_word_sign(line):
            return True
    return False


def decode_instrument_abbreviation(cells: str) -> tuple[str, list[str]]:
    """Decode a BANA instrument abbreviation like `⠜⠧⠂⠆⠄` into (prefix, part_numbers)."""
    if cells.startswith('⠜'):
        cells = cells[1:]
    if cells.endswith('⠄'):
        cells = cells[:-1]

    # Find the index of the first lower-cell digit
    i = 0
    while i < len(cells) and cells[i] not in LOWER_DIGIT_CELLS:
        i += 1

    letters_part = cells[:i]
    digits_part = cells[i:]

    prefix = "".join(decode_literary_braille(c) for c in letters_part)

    digits = []
    for c in digits_part:
        if c in LOWER_DIGIT_CELLS:
            digits.append(str(LOWER_DIGIT_CELLS[c]))
        elif c in LITERARY_DIGITS:
            digits.append(str(LITERARY_DIGITS[c]))

    return prefix, digits


def split_tokens_into_measures(tokens: list[BrailleToken]) -> list[list[BrailleToken]]:
    measures = []
    current = []
    for token in tokens:
        if token.category == SymbolCategory.BAR_LINE:
            if current:
                measures.append(current)
                current = []
        else:
            current.append(token)
    if current:
        measures.append(current)
    return measures


def parse_parallel_movement_tokens(measure_toks: list[BrailleToken]) -> tuple[bool, int | None, str | None]:
    """Check if measure_toks represents a parallel movement sign.
    Returns (is_parallel, target_octave, source_abbrev).
    """
    i = 0
    octave_tokens = []
    while i < len(measure_toks) and measure_toks[i].category == SymbolCategory.OCTAVE_MARK:
        octave_tokens.append(measure_toks[i].character)
        i += 1

    if octave_tokens:
        octave_str = "".join(octave_tokens)
        if octave_str == '⠈⠈':
            target_octave = 0
        elif octave_str in OCTAVE_MARKS:
            target_octave = OCTAVE_MARKS[octave_str]
        else:
            target_octave = None
    else:
        target_octave = None

    if i < len(measure_toks) and measure_toks[i].category == SymbolCategory.INTERVAL and measure_toks[i].character == '⠤':
        i += 1
        source_abbrev = None
        if i < len(measure_toks) and measure_toks[i].category == SymbolCategory.WORD_SIGN:
            source_abbrev = measure_toks[i].character
            i += 1

        if i == len(measure_toks):
            return True, target_octave, source_abbrev

    return False, None, None


def find_instrument_by_abbrev(abbrev: str | None, instruments: list[InstrumentInfo], current_inst: InstrumentInfo) -> InstrumentInfo | None:
    if abbrev is None:
        idx = instruments.index(current_inst)
        if idx > 0:
            return instruments[idx - 1]
        return None

    prefix, digits = decode_instrument_abbreviation(abbrev)
    for inst in instruments:
        if inst.abbreviation.lower() == prefix.lower():
            if not digits or inst.part_number in digits:
                return inst
    return None


def get_first_note_octave(measure: Measure) -> int | None:
    for note in measure.notes:
        if isinstance(note, Note):
            return note.octave
        elif isinstance(note, Chord):
            if note.notes:
                return note.notes[0].octave
        elif isinstance(note, InAccord):
            for part in note.parts:
                for item in part:
                    if isinstance(item, Note):
                        return item.octave
                    elif isinstance(item, Chord) and item.notes:
                        return item.notes[0].octave
        elif isinstance(note, Tuplet):
            for item in note.items:
                if isinstance(item, Note):
                    return item.octave
                elif isinstance(item, Chord) and item.notes:
                    return item.notes[0].octave
    return None


def transpose_note_octaves(note, octave_diff: int):
    if isinstance(note, Note):
        note.octave += octave_diff
    elif isinstance(note, Chord):
        for sub_note in note.notes:
            transpose_note_octaves(sub_note, octave_diff)
    elif isinstance(note, InAccord):
        for part in note.parts:
            for item in part:
                transpose_note_octaves(item, octave_diff)
    elif isinstance(note, Tuplet):
        for item in note.items:
            transpose_note_octaves(item, octave_diff)


def transpose_measure_octaves(measure: Measure, octave_diff: int) -> Measure:
    if octave_diff == 0:
        return copy.deepcopy(measure)

    new_measure = copy.deepcopy(measure)
    for note in new_measure.notes:
        transpose_note_octaves(note, octave_diff)
    return new_measure


def match_instruments(prefix: str, digits: list[str], instruments: list[InstrumentInfo]) -> list[InstrumentInfo]:
    matched = []
    for inst in instruments:
        if inst.abbreviation.lower() == prefix.lower():
            if not digits:
                matched.append(inst)
            elif inst.part_number in digits:
                matched.append(inst)
    return matched


class ParallelSystem:
    def __init__(self, measure_number: int):
        self.measure_number = measure_number
        self.end_measure_number = measure_number
        # abbrev_cells -> raw music cells
        self.parts: dict[str, str] = {}
        self.last_abbrev: str | None = None

    def add_line(self, line_str: str) -> bool:
        """Process a line within the system. Returns True if successfully handled."""
        abbrev_cells, music_cells = extract_line_abbreviation(line_str)
        if abbrev_cells is not None:
            self.parts[abbrev_cells] = music_cells
            self.last_abbrev = abbrev_cells
            return True
        elif self.last_abbrev is not None:
            self.parts[self.last_abbrev] += " " + music_cells.lstrip('⠀ ')
            return True
        return False


class EnsembleParser:
    def __init__(self, overrides: dict[str, str] | None = None):
        self.overrides = overrides or {}

    def parse(self, text: str) -> OrchestraScore:
        pipeline = BRLInputPipeline()
        if pipeline._detect_encoding(text) == "ascii":
            normalized = pipeline._ascii_to_unicode(text)
        else:
            normalized = text

        lines = normalized.splitlines()
        inst_lines = []
        i = 0
        while i < len(lines):
            line = lines[i]
            m_num, _ = extract_measure_number(line)
            if m_num is None and _line_has_word_sign(line):
                inst_lines.append(line)
            elif inst_lines:
                break
            i += 1

        if not inst_lines:
            raise ValueError("No instrument list header found in ensemble score.")

        instruments = parse_instrument_list("\n".join(inst_lines))

        heading_lines = []
        while i < len(lines):
            line = lines[i]
            m_num, _ = extract_measure_number(line)
            if m_num is not None:
                break
            if line.strip():
                heading_lines.append(line)
            i += 1

        header_str = " ".join(heading_lines).strip()

        # Keep only tokens that are genuine header directives (key/time
        # signature, clef, tempo/expression word-signs). Free-standing
        # literary text without a capital indicator (e.g. an ASCII-sourced
        # "ALLEGRO" heading -- BRLInputPipeline._ascii_to_unicode never
        # emits CAPITAL_INDICATOR, by design, see test_brl_ascii_to_unicode_dot1)
        # gets misclassified cell-by-cell as NOTE/UNKNOWN/BAR_LINE by the
        # tokenizer, which would otherwise inject phantom notes and measure
        # breaks into every instrument's reconstructed measure 1. Filtering
        # to known-safe categories drops that stray prose instead of
        # smuggling it into the music stream.
        if header_str:
            header_tokens = BrailleTokenizer().tokenize(header_str)
            safe_categories = {
                SymbolCategory.KEY_SIGNATURE,
                SymbolCategory.TIME_SIGNATURE,
                SymbolCategory.CLEF,
                SymbolCategory.WORD_SIGN,
            }
            header_str = "".join(
                t.raw for t in header_tokens if t.category in safe_categories
            )

        parallel_lines = lines[i:]
        systems: list[ParallelSystem] = []
        current_system: ParallelSystem | None = None
        for line in parallel_lines:
            if not line.strip():
                continue
            m_num, remaining = extract_measure_number(line)
            if m_num is not None:
                current_system = ParallelSystem(m_num)
                systems.append(current_system)
                current_system.add_line(remaining)
            else:
                if current_system is not None:
                    current_system.add_line(line)

        if not systems:
            raise ValueError("No parallel systems found in ensemble score.")

        systems.sort(key=lambda s: s.measure_number)

        last_system_measures = 0
        for abbrev, music_cells_str in systems[-1].parts.items():
            # at_line_start=False: this is a per-instrument music-cell fragment
            # (abbreviation already stripped), not a genuine physical line
            # start -- otherwise a real first note that doubles as a literary
            # digit cell gets misread as a measure-number token and dropped.
            tokens = BrailleTokenizer().tokenize(music_cells_str, at_line_start=False)
            measures = split_tokens_into_measures(tokens)
            last_system_measures = max(last_system_measures, len(measures))
        if not last_system_measures:
            last_system_measures = 1

        for idx, sys in enumerate(systems):
            if idx + 1 < len(systems):
                sys.end_measure_number = systems[idx + 1].measure_number - 1
            else:
                sys.end_measure_number = sys.measure_number + last_system_measures - 1

        total_measures = systems[-1].end_measure_number

        # Build measure cells list and resolution rules
        measure_cells_list = {inst.name: [] for inst in instruments}
        resolutions = {inst.name: {} for inst in instruments}

        for sys in systems:
            sys_measure_toks = {}
            for key, music_cells in sys.parts.items():
                # at_line_start=False: same reason as above -- this fragment's
                # first cell is real music content, not a line-start context.
                tokens = BrailleTokenizer().tokenize(music_cells, at_line_start=False)
                measure_tokens = split_tokens_into_measures(tokens)
                sys_measure_toks[key] = measure_tokens

            inst_to_key = {}
            for inst in instruments:
                matched_key = None
                for key in sys.parts:
                    prefix, digits = decode_instrument_abbreviation(key)
                    if inst.abbreviation.lower() == prefix.lower():
                        if not digits or inst.part_number in digits:
                            matched_key = key
                            break
                inst_to_key[inst.name] = matched_key

            key_primary_inst = {}
            for key in sys.parts:
                prefix, digits = decode_instrument_abbreviation(key)
                matched_insts = match_instruments(prefix, digits, instruments)
                if matched_insts:
                    key_primary_inst[key] = matched_insts[0]

            for measure_idx in range(sys.end_measure_number - sys.measure_number + 1):
                m_num = sys.measure_number + measure_idx

                for inst in instruments:
                    key = inst_to_key[inst.name]
                    if key is None:
                        measure_cells_list[inst.name].append("⠍")
                        resolutions[inst.name][m_num] = ('normal', None, None)
                    else:
                        measure_tokens = sys_measure_toks[key]
                        if measure_idx < len(measure_tokens):
                            toks = measure_tokens[measure_idx]
                        else:
                            toks = []

                        is_parallel, target_octave, source_abbrev = parse_parallel_movement_tokens(toks)
                        if is_parallel:
                            measure_cells_list[inst.name].append("⠍")
                            resolutions[inst.name][m_num] = ('parallel', target_octave, source_abbrev)
                        else:
                            primary_inst = key_primary_inst[key]
                            if inst.name == primary_inst.name:
                                # Reconstruct the original cell string from each
                                # token's raw cells -- no per-category special-
                                # casing needed since `raw` always holds the
                                # true, undecoded braille (see BrailleToken.raw).
                                cells_str = "".join(t.raw for t in toks)
                                if not cells_str.strip():
                                    cells_str = "⠍"
                                measure_cells_list[inst.name].append(cells_str)
                                resolutions[inst.name][m_num] = ('normal', None, None)
                            else:
                                measure_cells_list[inst.name].append("⠍")
                                resolutions[inst.name][m_num] = ('consolidated', primary_inst.name, None)

        # Parse each instrument's concatenated stream
        instrument_staves = {}
        for inst in instruments:
            cells_stream = "⠀".join(measure_cells_list[inst.name])
            if header_str:
                cells_stream = header_str + "⠀" + cells_stream

            # at_line_start=False: this reconstructed stream never contains
            # real measure-number cells (those are tracked separately via
            # `resolutions`), so the bare-literary-digit measure-number
            # heuristic should never fire here, regardless of whether
            # header_str is present.
            tokens = BrailleTokenizer().tokenize(cells_stream, at_line_start=False)
            parser = BrailleParser(tokens=tokens, instruments=instruments, ensemble=True)
            score = parser.parse()

            if score.staves:
                staff = score.staves[0]
            else:
                staff = Staff(name=inst.name)
            staff.name = inst.name
            instrument_staves[inst.name] = staff

        # Resolve all measures recursively post-parsing
        resolved_measures = {}
        resolving = set()

        def get_resolved_measure(inst_name: str, m_num: int) -> Measure:
            state_key = (inst_name, m_num)
            if state_key in resolved_measures:
                return resolved_measures[state_key]

            if state_key in resolving:
                raise ValueError(f"Circular parallel movement dependency for {inst_name} at measure {m_num}")
            resolving.add(state_key)

            res_type, val1, val2 = resolutions[inst_name][m_num]
            if res_type == 'normal':
                staff = instrument_staves[inst_name]
                measure_obj = next((m for m in staff.measures if m.number == m_num), None)
                if measure_obj is None:
                    measure_obj = Measure(number=m_num)
            elif res_type == 'consolidated':
                primary_inst_name = val1
                source_measure = get_resolved_measure(primary_inst_name, m_num)
                measure_obj = copy.deepcopy(source_measure)
                measure_obj.number = m_num
            elif res_type == 'parallel':
                target_octave = val1
                source_abbrev = val2

                inst_info = next(i for i in instruments if i.name == inst_name)
                source_inst = find_instrument_by_abbrev(source_abbrev, instruments, inst_info)
                if source_inst is None:
                    raise ValueError(f"Source instrument for parallel movement not found for {inst_name} at measure {m_num}")

                source_measure = get_resolved_measure(source_inst.name, m_num)

                original_octave = get_first_note_octave(source_measure)
                if target_octave is not None and original_octave is not None:
                    octave_diff = target_octave - original_octave
                else:
                    octave_diff = 0

                measure_obj = transpose_measure_octaves(source_measure, octave_diff)
                measure_obj.number = m_num

            resolved_measures[state_key] = measure_obj
            resolving.remove(state_key)
            return measure_obj

        # Assign resolved measures back to staves
        for inst in instruments:
            staff = instrument_staves[inst.name]
            resolved_list = []
            for m_num in range(1, total_measures + 1):
                resolved_list.append(get_resolved_measure(inst.name, m_num))
            staff.measures = resolved_list

        # Copy global attributes from the first staff to all other staves if not set
        first_staff = instrument_staves[instruments[0].name]
        for inst in instruments[1:]:
            staff = instrument_staves[inst.name]
            if staff.key_signature is None:
                staff.key_signature = first_staff.key_signature
            if staff.time_signature is None:
                staff.time_signature = first_staff.time_signature
            if staff.clef is None:
                staff.clef = first_staff.clef
            if staff.tempo is None:
                staff.tempo = first_staff.tempo

        score = OrchestraScore()
        for inst in instruments:
            score.add_staff(instrument_staves[inst.name])

        return score
