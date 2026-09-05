from __future__ import annotations

import copy
import re
import unicodedata
import warnings

from ..bana_symbols import (
    SymbolCategory,
    OCTAVE_MARKS,
    LOWER_DIGIT_CELLS,
    LITERARY_DIGITS,
    NUMBER_SIGN,
    KEY_SIGNATURE_CELLS,
    TIME_SIGNATURE_CELLS,
    TABLE_29_ENGLISH,
)
from ..exceptions import BrailleParseError
from ..models.instrument import InstrumentInfo, InstrumentFamily
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
from .instrument_list import parse_instrument_list, _parse_line as _parse_instrument_line

# Match optional octave mark (1 or 2 octave cells), followed by ⠤, optionally followed by an abbreviation in ⠜...⠄
PARALLEL_MOVEMENT_REGEX = re.compile(
    r'^([⠈⠘⠸⠐⠨⠰⠠]{1,2})?⠤(⠜[^⠄]+⠄)?$'
)

LITERARY_DIGIT_MAP = {
    '⠁': '1', '⠃': '2', '⠉': '3', '⠙': '4', '⠑': '5',
    '⠋': '6', '⠛': '7', '⠓': '8', '⠊': '9', '⠚': '0'
}

# Note-prefix categories only -- see the group-boundaries carry-forward
# logic below (search "swallowed") for why overflow tokens are only ever
# carried across a system boundary when every one of them is one of these.
# KEY_SIGNATURE is included because a lone flat/sharp cell stranded at the
# very end of a column-sliced chunk (with nothing left in that isolated
# chunk to look ahead at) is read by BrailleTokenizer's own
# end-of-input/whitespace rule as a 1-accidental key signature even when
# it's really just a flat/sharp accidental that got cut off from the note
# it belongs to -- carrying its raw cells forward and letting the final,
# fully-reconstructed per-instrument stream get re-tokenized with full
# context (in BrailleParser) resolves it correctly either way.
_CARRIABLE_PREFIX_CATEGORIES = frozenset({
    SymbolCategory.ACCIDENTAL,
    SymbolCategory.DYNAMIC,
    SymbolCategory.OCTAVE_MARK,
    SymbolCategory.KEY_SIGNATURE,
})

# The word-sign/clef opener cell (⠜, dots 3,4,5 -- BrailleTokenizer's
# `_CLEF_PREFIX`). A genuine word-sign/dynamic construct always decodes to
# more than just this one cell (BrailleTokenizer greedily collects until an
# END_WORD_SIGN, octave mark, or other terminator); a WORD_SIGN token whose
# `raw` is *only* this cell can only mean the tokenizer ran out of chunk
# before finding one -- i.e. it's a truncation artifact, never a complete
# construct in its own right -- so it's carriable too, unlike WORD_SIGN in
# general (see _is_carriable_overflow below).
_BARE_WORD_SIGN_OPENER = '⠜'


def _is_carriable_overflow(token: BrailleToken) -> bool:
    if token.category in _CARRIABLE_PREFIX_CATEGORIES:
        return True
    return token.category == SymbolCategory.WORD_SIGN and token.raw == _BARE_WORD_SIGN_OPENER

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


def extract_all_measure_numbers(line_str: str) -> list[tuple[int, int]] | None:
    """Detect Sao Mai Braille software's inline multi-measure-number
    convention (S5b-9): a header line carrying *several* NUMBER_SIGN+digit
    markers spaced out across one physical line -- e.g.
    `⠼⠁⠀⠀⠀⠼⠃⠀⠀⠼⠙⠀⠀⠼⠑` -- each marking where a later measure's content
    begins further along the same line, rather than BANA Sec. 33.4.6's own
    convention of exactly one measure number alone on its own line
    (`extract_measure_number`, convention 1).

    Returns a list of (column, measure_number) pairs, sorted left to
    right, only when the *entire* line is nothing but blank cells/spaces
    and such markers -- any other content (an instrument abbreviation,
    real music) means this isn't a pure header line, so callers should
    fall back to `extract_measure_number`. Returns None if fewer than two
    markers are found, since a single marker is already handled by that
    existing convention.
    """
    positions: list[tuple[int, int]] = []
    i = 0
    n = len(line_str)
    while i < n:
        ch = line_str[i]
        if ch in ('⠀', ' '):
            i += 1
            continue
        if ch == NUMBER_SIGN:
            j = i + 1
            digits = []
            while j < n and line_str[j] in LITERARY_DIGIT_MAP:
                digits.append(LITERARY_DIGIT_MAP[line_str[j]])
                j += 1
            if digits:
                positions.append((i, int(''.join(digits))))
                i = j
                continue
        return None

    if len(positions) >= 2:
        return positions
    return None


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


_SIGNATURE_CELLS = tuple(KEY_SIGNATURE_CELLS) + tuple(TIME_SIGNATURE_CELLS)


def _is_music_heading_line(line: str) -> bool:
    """True if `line` contains a key- or time-signature cell sequence.

    This is the one unambiguous structural signal of BANA Sec. 1.7's Music
    Heading (tempo/mood text, optional metronome, then key and time
    signature together) -- a key/time signature can only ever appear
    there, never in Sec. 1.4's preliminary/title-page text. Deliberately a
    raw substring check rather than routing through `BrailleTokenizer`:
    the tokenizer's bare-capital-indicator literary-text path (used for
    tempo text not wrapped in a word sign, e.g. a plain "Moderato e
    simplice") only terminates on a literary period or newline, so it
    swallows a same-line, unseparated key/time signature into the
    preceding WORD_SIGN token instead of emitting it as its own token --
    a raw scan sidesteps that without touching the shared tokenizer.
    """
    return any(cell in line for cell in _SIGNATURE_CELLS)


def _find_instrument_list(lines: list[str]) -> tuple[list[str], int]:
    """Scan `lines` for a BANA Sec. 33.2 instrument-list header, bounded to
    the region between the title (Sec. 1.4) and the Music Heading (Sec.
    1.7). Sec. 33.2: "Immediately following the title, a two-column table
    lists all of the instruments" -- a real header, if present, is a short
    block right after the title, never something found deep inside actual
    measures. Bounding the search this way (rather than scanning the whole
    file for anything that merely looks header-shaped) is what lets a
    headerless ensemble score be reliably detected as such, instead of
    accidentally matching scattered mid-piece lines that share a header
    entry's word-sign-wrapped-abbreviation shape (a per-line abbreviation
    prefix followed later on the same line by an unrelated word-sign
    expression, e.g. a dynamic like "dolce", can otherwise look like one).

    Returns `(inst_lines, i)`: the collected header lines (empty if none
    found) and the index of the first unconsumed line in `lines` -- either
    right after a genuine header, or at the Music Heading line itself if
    no header was found (left unconsumed for the caller's own heading
    handling).

    Both checks in the loop's match condition are required, for two
    independent false-positive reasons:
     - _line_has_word_sign (tokenizer-based) rules out a hand-sign line
       (⠨⠜/⠸⠜) whose second cell is the same dot pattern as WORD_SIGN,
       which _parse_instrument_line's raw substring search alone can't
       tell apart from a real word-sign (S7-2).
     - _parse_instrument_line rules out a free-text title/attribution line
       above the real instrument list, which also tokenizes as WORD_SIGN
       (any literary text does) but doesn't parse as a genuine
       NAME...ABBREV entry -- found via
       Bartok_Bella_Romanian_Folk_Dances_for_Orchestra.brl, whose title
       line was getting collected as a fake "instrument" (S5b-9).
    """
    inst_lines: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        m_num, _ = extract_measure_number(line)
        if (
            m_num is None
            and _line_has_word_sign(line)
            and _parse_instrument_line(line) is not None
        ):
            inst_lines.append(line)
        elif inst_lines:
            break
        elif _is_music_heading_line(line):
            break
        i += 1
    return inst_lines, i


_KNOWN_ABBREVIATION_PREFIXES = {
    re.sub(r'[0-9]+$', '', abbrev) for abbrev in TABLE_29_ENGLISH.values()
}


def _has_known_abbreviation_prefixes(text: str) -> bool:
    """True if at least two lines in `text` begin (after margin blanks)
    with a per-line instrument-abbreviation prefix matching a known BANA
    Table 29 abbreviation (e.g. "v1'", "vl'"), ignoring any part number.

    This is a narrow, low-false-positive signal that `text` is BANA §33.4
    ensemble body content -- a per-line abbreviation prefix followed by
    music, repeated system after system -- even when no §33.2 header is
    present. Used so a score like a headerless "open score" string
    quartet still routes to `EnsembleParser` (whose `parse()` then raises
    a clear, BANA-cited error naming the missing header) instead of being
    silently misrouted to the solo `BrailleParser`, which would misparse
    it differently. Requires *two distinct* known abbreviations (not just
    one) so a single incidental line elsewhere in solo content can't
    trigger it -- confirmed against `children_s_piece.brf` and
    `fingering_melody.brf` (no match) and the existing
    `test_ensemble_parser_raises_clear_error_on_hand_sign_only_text`
    input (no match, since it has no genuine abbreviations at all).
    """
    seen: set[str] = set()
    for line in text.splitlines():
        abbrev_cells, _ = extract_line_abbreviation(line)
        if not abbrev_cells:
            continue
        prefix, _digits = decode_instrument_abbreviation(abbrev_cells)
        if prefix in _KNOWN_ABBREVIATION_PREFIXES:
            seen.add(prefix)
            if len(seen) >= 2:
                return True
    return False


def has_ensemble_header(text: str) -> bool:
    """True if `text` (normalized Unicode braille) looks like a BANA §33
    ensemble score -- either a genuine §33.2 instrument-list header, or
    (its header missing) recognizable per-line instrument-abbreviation
    prefixes in the body. Used to dispatch between EnsembleParser and the
    solo BrailleParser/tokenizer path (see cli.py): either way, this must
    route to EnsembleParser, whose `parse()` raises a clear, BANA-cited
    error if the header itself turns out to be missing -- never silently
    fall through to the solo parser, which would misparse ensemble body
    content in a different, equally silent way. The header-shaped check
    shares `_find_instrument_list`'s bounded scan with
    `EnsembleParser.parse()` itself, so it's never looser than what
    `parse()` will actually find."""
    inst_lines, _ = _find_instrument_list(text.splitlines())
    if inst_lines:
        return True
    return _has_known_abbreviation_prefixes(text)


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
        # A word (lyric) line, per BANA Sec. 35.1, has no instrument
        # abbreviation at all when there's only one voice (Sec. 37.2) --
        # it's plain literary text at the margin, immediately followed by
        # its paired music line. `pending_word_line` holds such a line
        # until the next abbreviated line arrives and tells us (via
        # `word_lines`, keyed the same way as `.parts`) which vocal
        # instrument it belongs to.
        self.pending_word_lines: list[str] = []
        self.word_lines: dict[str, list[str]] = {}

    def add_line(
        self,
        line_str: str,
        instruments: list[InstrumentInfo] | None = None,
        category_override: str | None = None,
    ) -> bool:
        """Process a line within the system. Returns True if successfully handled.

        `instruments` (when supplied) resolves pending word lines: once the
        next abbreviated line arrives, if its instrument is
        `InstrumentFamily.VOCAL`, the stashed lines become that instrument's
        lyrics (`word_lines`); otherwise they're dropped.
        """
        abbrev_cells, music_cells = extract_line_abbreviation(line_str)
        if abbrev_cells is not None:
            if self.pending_word_lines:
                if instruments is not None:
                    prefix, digits = decode_instrument_abbreviation(abbrev_cells)
                    matched = match_instruments(prefix, digits, instruments)
                    is_vocal = False
                    if matched and matched[0].family == InstrumentFamily.VOCAL:
                        is_vocal = True
                        if category_override is not None and category_override not in ("Art Song", "Vocal"):
                            is_vocal = False
                    if is_vocal:
                        self.word_lines[abbrev_cells] = list(self.pending_word_lines)
                self.pending_word_lines.clear()
            self.parts[abbrev_cells] = music_cells
            self.last_abbrev = abbrev_cells
            return True
        elif self.last_abbrev is not None:
            self.parts[self.last_abbrev] += " " + music_cells.lstrip('⠀ ')
            return True
        elif music_cells.strip('⠀ '):
            # No abbreviation yet established for this system -- this is a
            # candidate word line (Sec. 35.1), stashed until the next line
            # resolves it.
            self.pending_word_lines.append(music_cells.lstrip('⠀ '))
            return True
        return False


# ASCII BRF characters for one-cell UEB literary punctuation signs that
# double as LOWER_DIGIT_CELLS in a numbering context (UEB 2024 3rd ed.,
# Section 7 "Punctuation"). Lyrics are always literary prose, never a
# numbering context outside an explicit numeral sign ('#', handled
# separately below), so these always read as punctuation. Dot patterns
# confirmed against the actual Unicode braille glyphs in the official
# rulebook (iceb.org), converted through this module's own ASCII_TO_DOTS --
# not guessed. Comma and period were already confirmed against a real
# fixture (vocal_test.brf); the rest follow the identical digit-cell reuse
# pattern documented in UEB 7.1's own examples.
_LYRIC_PUNCTUATION = {
    '1': ',',   # dot 2       -- comma (UEB 7.1)
    '2': ';',   # dots 2,3    -- semicolon (UEB 7.1)
    '3': ':',   # dots 2,5    -- colon (UEB 7.1)
    '4': '.',   # dots 2,5,6  -- period (UEB 7.1)
    '6': '!',   # dots 2,3,5  -- exclamation mark (UEB 7.1)
    "'": "'",   # dot 3       -- apostrophe / nondirectional single quote (UEB 7.6.6)
}

# UEB 7.6.7: the single cell '⠦' (dots 2,3,6, ASCII '8') is read as an
# opening double quotation mark only at the start of a word; anywhere else
# it is a question mark. We approximate "start of a word" as "nothing
# accumulated into the current word yet" -- this matches ordinary usage but,
# per 7.5.3, doesn't attempt to disambiguate a question mark "standing
# alone" as its own word (that case would need the grade 1 symbol
# indicator, which this decoder doesn't track).
_AMBIGUOUS_QUESTION_OR_OPEN_QUOTE = '8'  # dots 2,3,6

# UEB Section 4.2 "Modifiers": each accent is a 1- or 2-cell prefix written
# immediately before the (separately encoded) base letter it applies to.
# Values are Unicode combining marks; _decode_accented_letter() below
# composes base letter + mark and NFC-normalizes so common precomposed
# letters (é, ñ, ü, ç, ...) come out as a single codepoint. Digitized from
# the actual glyphs in "Rules of Unified English Braille", 3rd ed. 2024
# (iceb.org), converted through ASCII_TO_DOTS -- not guessed. Per UEB 4.2.7,
# these are for occasional foreign words/names in an English-language lyric
# (BANA §35.1.1(d)), not full foreign-language braille codes (§35.1.1(e),
# which uses that language's own braille alphabet entirely -- out of scope
# here) and not the three transcriber-defined modifiers (⠘⠸⠂/⠆/⠤), which
# require a symbols-page note we have no way to surface from this decoder.
_ACCENT_MODIFIERS = {
    '@': {  # dots 4 prefix group (UEB 4.2)
        '*': '̸',  # solidus overlay
        '3': '̶',  # horizontal stroke overlay (e.g. ø)
        '+': '̆',  # breve
        '-': '̄',  # macron
    },
    '^': {  # dots 4,5 prefix group (UEB 4.2)
        '&': '̧',  # cedilla
        '*': '̀',  # grave accent
        '%': '̂',  # circumflex
        '$': '̊',  # ring (circle)
        ']': '̃',  # tilde
        '3': '̈',  # diaeresis (umlaut)
        '/': '́',  # acute accent
        '+': '̌',  # caron (hacek, wedge)
    },
}

# UEB Section 6: a numeral sign ('#', dots 3,4,5,6) followed by one or more
# a-j-shaped letter cells reads as digits 1-9,0; numeral mode ends at the
# first cell that isn't one of these (UEB 6.5.1: space, hyphen, or dash).
_DIGIT_CELLS = {
    'A': '1', 'B': '2', 'C': '3', 'D': '4', 'E': '5',
    'F': '6', 'G': '7', 'H': '8', 'I': '9', 'J': '0',
}


def _decode_accented_letter(ascii_str: str, i: int, n: int) -> tuple[str, int]:
    """Consume a UEB 4.2 accent-modifier prefix at ascii_str[i] (one of the
    keys of _ACCENT_MODIFIERS) plus the base letter it applies to, and
    return (composed_letter, index_just_past_the_base_letter).
    """
    group = _ACCENT_MODIFIERS[ascii_str[i]]
    if i + 1 >= n or ascii_str[i + 1] not in group:
        raise BrailleParseError(
            "Unrecognized UEB accent-modifier selector in lyric text "
            f"after {ascii_str[i]!r}"
        )
    combining_mark = group[ascii_str[i + 1]]
    if i + 2 >= n or not ascii_str[i + 2].isalpha():
        raise BrailleParseError(
            "UEB accent modifier in lyric text is not followed by a letter"
        )
    composed = unicodedata.normalize('NFC', ascii_str[i + 2].lower() + combining_mark)
    return composed, i + 3


def group_pitched_elements_by_slur(measures: list[Measure]) -> list[list]:
    """Group a staff's pitched elements (Note/Chord, recursing through
    Tuplet/InAccord) into BANA §35.2 syllable slots: a run of notes joined
    by a syllabic slur is one slot (one syllable is sung across all of
    them), everything else is its own slot. Rests are excluded -- a rest
    never carries a syllable."""
    pitched_elements = []

    def collect_pitched(item):
        if isinstance(item, (Note, Chord)):
            pitched_elements.append(item)
        elif isinstance(item, Tuplet):
            for sub in item.items:
                collect_pitched(sub)
        elif isinstance(item, InAccord):
            if item.parts:
                for sub in item.parts[0]:
                    collect_pitched(sub)

    for measure in measures:
        for note_item in measure.notes:
            collect_pitched(note_item)

    groups = []
    current_group = []
    in_slur = False
    for elem in pitched_elements:
        if elem.slur_start:
            if current_group:
                groups.append(current_group)
            current_group = [elem]
            in_slur = True
        elif in_slur:
            current_group.append(elem)
            if elem.slur_end:
                groups.append(current_group)
                current_group = []
                in_slur = False
        else:
            groups.append([elem])
    if current_group:
        groups.append(current_group)
    return groups


def map_syllables_to_groups(
    syllables: list[tuple[str, bool]],
    groups: list[list],
    owner_name: str,
    verse_label: str = "Verse 1",
) -> list[str]:
    """Zip `syllables` (from `parse_lyrics()`) 1:1 onto `groups` (from
    `group_pitched_elements_by_slur()`), appending the lyric-continuation
    marker (" --") for a hyphenated syllable. Warns (rather than raising)
    on a count mismatch, truncating to the shorter of the two -- a
    transcription error shouldn't be fatal, but should not be silent
    either."""
    mapped_lyrics = []
    num_mappings = min(len(syllables), len(groups))
    if len(syllables) != len(groups):
        warnings.warn(
            f"{owner_name} ({verse_label}): {len(syllables)} lyric syllable(s) "
            f"but {len(groups)} note/slur-group(s) -- lyrics "
            "will be misaligned past the shorter of the two. "
            "Check for a missing syllable or an extra/missing "
            "syllabic slur.",
            stacklevel=2,
        )
    for idx in range(num_mappings):
        syllable, has_hyphen = syllables[idx]
        ly_syllable = syllable
        if has_hyphen:
            ly_syllable += " --"
        mapped_lyrics.append(ly_syllable)
    return mapped_lyrics


def parse_lyrics(lyric_cells: str) -> list[tuple[str, bool]]:
    """Decode a sequence of BANA Unicode braille cells as uncontracted (UEB
    Grade 1) literary lyrics per BANA §35.1.1: the full alphabet,
    capitalization, hyphens, word repetition, UEB Section 7 punctuation,
    UEB Section 6 numbers, and UEB 4.2 accent modifiers for foreign words in
    an English-language lyric. Contracted (Grade 2) braille is not
    supported. Returns a list of (syllable_text, has_hyphen) tuples.
    """
    from .input_pipeline import ASCII_TO_DOTS
    dots_to_ascii = {v: k for k, v in ASCII_TO_DOTS.items()}

    ascii_chars = []
    for c in lyric_cells:
        offset = ord(c) - 0x2800
        if 0 <= offset < 64:
            ascii_chars.append(dots_to_ascii.get(offset, ' '))
        else:
            ascii_chars.append(' ')

    ascii_str = "".join(ascii_chars)

    # Process capital indicators and reconstruct words
    words = []
    current_word = []
    i = 0
    n = len(ascii_str)
    cap_next_char = False
    cap_all_word = False

    while i < n:
        char = ascii_str[i]

        if char == ' ':
            if current_word:
                words.append("".join(current_word))
                current_word = []
            cap_all_word = False
            cap_next_char = False
            i += 1
            continue

        if char == ',':  # UEB Capital indicator (dot 6), also the prefix for
            # several two-cell signs (UEB 4.2.2, 7.6.2, 7.6.5)
            nxt = ascii_str[i + 1] if i + 1 < n else ''
            if nxt == ',':
                cap_all_word = True
                i += 2
                continue
            if nxt == '8':  # UEB 7.6.2 -- opening single quotation mark ⠠⠦
                current_word.append('‘')
                i += 2
                continue
            if nxt == '0':  # UEB 7.6.2 -- closing single quotation mark ⠠⠴
                current_word.append('’')
                i += 2
                continue
            if nxt == '7':  # UEB 7.6.5 -- nondirectional double quotation mark ⠠⠶ (rare)
                current_word.append('"')
                i += 2
                continue
            if nxt in _ACCENT_MODIFIERS:  # UEB 4.2.2 -- capitalized accented letter
                accented, i = _decode_accented_letter(ascii_str, i + 1, n)
                current_word.append(accented.upper())
                cap_next_char = False
                continue
            cap_next_char = True
            i += 1
            continue

        if char == '-':
            current_word.append('-')
            cap_all_word = False
            cap_next_char = False
            i += 1
            continue

        if char == '^' and i + 1 < n and ascii_str[i + 1] in ('8', '0'):
            # UEB 7.6.7/7.6.8 -- unambiguous two-cell open/close double
            # quote (⠘⠦/⠘⠴). Shares the dots-4,5 prefix with the accent
            # group below, but '8'/'0' are never valid accent selectors,
            # so there's no ambiguity.
            current_word.append('“' if ascii_str[i + 1] == '8' else '”')
            i += 2
            continue

        if char in _ACCENT_MODIFIERS:  # UEB 4.2 -- accented letter
            accented, i = _decode_accented_letter(ascii_str, i, n)
            if cap_all_word:
                accented = accented.upper()
            current_word.append(accented)
            continue

        if char == '#':  # UEB Section 6 -- numeral sign
            i += 1
            digits = []
            while i < n and ascii_str[i] in _DIGIT_CELLS:
                digits.append(_DIGIT_CELLS[ascii_str[i]])
                i += 1
            if not digits:
                raise BrailleParseError(
                    "Numeral sign in lyric text is not followed by a digit cell"
                )
            current_word.append("".join(digits))
            continue

        if char == '0':  # UEB 7.6.1 -- closing double quotation mark ⠴
            current_word.append('”')
            i += 1
            continue

        if char == _AMBIGUOUS_QUESTION_OR_OPEN_QUOTE:  # UEB 7.6.7
            current_word.append('“' if not current_word else '?')
            i += 1
            continue

        if char == '7':  # dots 2,3,5,6 -- BANA_symbols.MEASURE_REPEAT_CELL /
            # CHORD_PAREN_CELL, not a UEB literary sign at all: this
            # codebase's own verse-number-prefix convention (S8b-11) reuses
            # it as a bracket around the verse digit, e.g. "⠶⠼⠁⠶" = "[1]".
            # Rendered as '[' at the start of a word and ']' otherwise, so
            # clean_and_parse_verse_number()'s existing
            # .strip('.:,;()[]') already strips it correctly.
            current_word.append('[' if not current_word else ']')
            i += 1
            continue

        if char in _LYRIC_PUNCTUATION:
            current_word.append(_LYRIC_PUNCTUATION[char])
            i += 1
            continue

        if char.isalpha():
            char_lower = char.lower()
            if cap_all_word or cap_next_char:
                current_word.append(char_lower.upper())
                cap_next_char = False
            else:
                current_word.append(char_lower)
            i += 1
            continue

        if char == '9':  # dots 3,5 -- word/phrase repetition marker
            # (BANA §35.4), expanded in the pass below
            current_word.append('9')
            i += 1
            continue

        raise BrailleParseError(
            f"Unrecognized braille cell in lyric text: ASCII braille {char!r}"
        )

    if current_word:
        words.append("".join(current_word))
        
    # Expand repetitions (dots 3-5 / ASCII '9')
    expanded_words = []
    for word in words:
        if word and all(c == '9' for c in word):
            rep_count = len(word)
            if expanded_words:
                prev_word = expanded_words[-1]
                for _ in range(rep_count):
                    expanded_words.append(prev_word)
        else:
            expanded_words.append(word)
            
    # Split words into syllables (text, has_hyphen)
    syllables = []
    for word in expanded_words:
        parts = word.split('-')
        for idx, part in enumerate(parts):
            if not part:
                continue
            is_last = (idx == len(parts) - 1)
            syllables.append((part, not is_last))
            
    return syllables


def clean_and_parse_verse_number(word: str) -> str | None:
    # Look for number sign
    idx = word.find('#')
    if idx == -1:
        # Check if it is a plain digit
        digits = "".join(c for c in word if c.isdigit())
        if digits and digits == word.strip('.:,;()[]'):
            return digits
        return None
        
    digit_map = {'a': '1', 'b': '2', 'c': '3', 'd': '4', 'e': '5', 'f': '6', 'g': '7', 'h': '8', 'i': '9', 'j': '0'}
    translated = ""
    i = idx + 1
    while i < len(word):
        char = word[i].lower()
        if char in digit_map:
            translated += digit_map[char]
            i += 1
        else:
            break
            
    if translated.isdigit():
        return translated
    return None


def extract_stanza_prefix(syllables: list[tuple[str, bool]]) -> tuple[str | None, list[tuple[str, bool]]]:
    if not syllables:
        return None, syllables
        
    first_syl, has_hyphen = syllables[0]
    # Stanza prefixes do not have a hyphen at the end.
    if has_hyphen:
        return None, syllables
        
    verse_num = clean_and_parse_verse_number(first_syl)
    if verse_num:
        return f"{verse_num}.", syllables[1:]
        
    cleaned = first_syl.strip('.:,;()[]')
    if cleaned.lower() in ('refrain', 'chorus', 'ref', 'cho'):
        return f"{cleaned}.", syllables[1:]
        
    return None, syllables


class EnsembleParser:
    def __init__(self, overrides: dict[str, str] | None = None, category_override: str | None = None):
        self.overrides = overrides or {}
        self.category_override = category_override

    def parse(self, text: str) -> OrchestraScore:
        pipeline = BRLInputPipeline()
        if pipeline._detect_encoding(text) == "ascii":
            normalized = pipeline._ascii_to_unicode(text)
        else:
            normalized = text

        lines = normalized.splitlines()
        inst_lines, i = _find_instrument_list(lines)

        if not inst_lines:
            hint = ""
            seen: list[str] = []
            for line in lines[i:]:
                abbrev_cells, _ = extract_line_abbreviation(line)
                if not abbrev_cells:
                    continue
                prefix, digits = decode_instrument_abbreviation(abbrev_cells)
                if prefix in _KNOWN_ABBREVIATION_PREFIXES:
                    display = prefix + "".join(digits)
                    if display not in seen:
                        seen.append(display)
                if len(seen) >= 8:
                    break
            if seen:
                hint = f" Found per-line abbreviation prefixes: {', '.join(seen)}."
            raise BrailleParseError(
                "No instrument list header found before the music heading "
                '(BANA Music Braille Code 2015, Sec. 33.2: "Immediately '
                "following the title, a two-column table lists all of the "
                'instruments included in the score."). Add the '
                "instrument-list header to the source file before "
                "converting." + hint
            )

        instruments = parse_instrument_list("\n".join(inst_lines))

        heading_lines = []
        while i < len(lines):
            line = lines[i]
            m_num, _ = extract_measure_number(line)
            if m_num is not None:
                break
            if extract_all_measure_numbers(line) is not None:
                break
            # BANA Sec. 35.9: vocal music commonly omits measure numbers
            # entirely, so a margin-start (column 0) unprefixed line is
            # also a genuine system boundary (a word line, Sec. 35.1) --
            # same rule as the parallel_lines loop below, needed here too
            # so the heading-collection loop doesn't swallow the whole
            # rest of the piece when no measure number ever appears.
            if line.strip() and line[0] not in ('⠀', ' ') and extract_line_abbreviation(line)[0] is None:
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
        # Sao Mai's inline multi-measure-number convention (S5b-9): once a
        # header line declares several markers at once, every content line
        # that follows is column-sliced at those same marker positions and
        # distributed across `group_systems` instead of going wholesale to
        # a single system -- this coexists with BANA's own one-number-per-
        # line convention (Fengyang) purely because `group_boundaries`
        # stays None for files that never emit a multi-marker header line.
        group_boundaries: list[tuple[int, int]] | None = None
        group_systems: list[ParallelSystem] = []
        for line in parallel_lines:
            if not line.strip():
                continue

            markers = extract_all_measure_numbers(line)
            if markers is not None:
                group_boundaries = markers
                group_systems = []
                for _, m_num in markers:
                    marker_system = ParallelSystem(m_num)
                    systems.append(marker_system)
                    group_systems.append(marker_system)
                current_system = None
                continue

            m_num = None
            if current_system is None or len(current_system.parts) > 0:
                m_num, remaining = extract_measure_number(line)
            if m_num is not None:
                group_boundaries = None
                group_systems = []
                current_system = ParallelSystem(m_num)
                systems.append(current_system)
                current_system.add_line(remaining, instruments, self.category_override)
            elif group_boundaries is not None:
                abbrev_cells, _ = extract_line_abbreviation(line)
                # BANA Sec. 33.4.6 says a measure-number indication is
                # "indented one cell beyond the first music signs of the
                # parallel" -- but that rule describes BANA's own one-
                # marker-alone-per-line convention (`extract_measure_number`),
                # not this inline multi-marker layout, which is a Sao Mai
                # software extension with no official BANA text governing
                # it. Real files disagree on whether it still applies here:
                # some are exactly column-registered with their header row
                # (marker column == content's first cell), others carry the
                # Sec. 33.4.6 offset through (content starts one cell left
                # of the marker) -- see the carry-forward repair below,
                # which recovers either case from the content itself rather
                # than assuming a fixed offset.
                cols = [col for col, _ in group_boundaries]
                # The very first marker's column can suffer the same
                # one-cell offset as any interior boundary, but with no
                # *previous* measure's chunk for the carry-forward repair
                # below to have caught it in -- there's nothing before the
                # first marker to spill from. Recover it directly here
                # instead: widen the first chunk to start right after the
                # abbreviation (never later than the marker column, so a
                # flush-registered header -- abbrev end == marker column --
                # is unaffected).
                if cols and abbrev_cells is not None:
                    leading_ws = len(line) - len(line.lstrip('⠀ '))
                    abbrev_end = leading_ws + len(abbrev_cells)
                    cols[0] = min(cols[0], abbrev_end)

                # The column offset between a marker and its measure's real
                # content isn't always the same one cell the carry-forward
                # repair below is built to recover -- some files misalign by
                # several cells, differently per instrument/boundary, which
                # can drop a whole NOTE/REST as unrecoverable overflow (not
                # just a prefix modifier) and silently desync every later
                # measure number for that instrument. Real BAR_LINE tokens
                # in the content are the actual ground truth for where
                # measures divide, independent of column position: tokenize
                # this instrument's *entire* line content once and split it
                # on its own bar lines. If that yields exactly as many
                # sub-measures as this header group has markers, assign them
                # 1:1 in order and skip column-slicing entirely. Otherwise
                # fall back to the column-sliced + carry-forward path below
                # unchanged, for lines that don't fit this shape.
                assigned_whole_line = False
                if cols and abbrev_cells is not None:
                    whole_tokens = BrailleTokenizer().tokenize(
                        line[cols[0]:], at_line_start=False
                    )
                    whole_measures = split_tokens_into_measures(whole_tokens)
                    if len(whole_measures) == len(group_systems):
                        for marker_system, toks in zip(group_systems, whole_measures):
                            marker_system.parts[abbrev_cells] = "".join(t.raw for t in toks)
                            marker_system.last_abbrev = abbrev_cells
                        assigned_whole_line = True

                if not assigned_whole_line:
                    for idx, marker_system in enumerate(group_systems):
                        start = cols[idx]
                        end = cols[idx + 1] if idx + 1 < len(cols) else len(line)
                        chunk = line[start:end].lstrip('⠀ ')
                        if abbrev_cells is not None:
                            marker_system.parts[abbrev_cells] = chunk
                            marker_system.last_abbrev = abbrev_cells
                        elif marker_system.last_abbrev is not None:
                            marker_system.parts[marker_system.last_abbrev] += " " + chunk
            elif (
                line[0] not in ('⠀', ' ')
                and extract_line_abbreviation(line)[0] is None
                and (current_system is None or len(current_system.parts) > 0)
            ):
                # BANA Sec. 35.9: measure numbers are commonly omitted
                # entirely in vocal music ("the word text serving as the
                # point of reference") -- when a file never emits one, a
                # new system boundary is instead recognized the same way a
                # human reader would: a word line always begins at the
                # margin (Sec. 35.1), while every content/continuation
                # line is indented (this codebase's own convention, cell 3+
                # for music lines). Auto-number systems 1, 2, 3... in the
                # order they appear.
                next_num = (systems[-1].measure_number + 1) if systems else 1
                current_system = ParallelSystem(next_num)
                systems.append(current_system)
                current_system.add_line(line, instruments, self.category_override)
            elif current_system is not None:
                current_system.add_line(line, instruments, self.category_override)

        if not systems:
            raise BrailleParseError("No parallel systems found in ensemble score.")

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

        # Column slicing under the Sao Mai group-boundaries convention (see
        # the `elif group_boundaries is not None:` branch above) cuts each
        # instrument's per-measure chunk at the *next* marker's column, but
        # real-world files don't always keep every instrument's content
        # column-registered with the header row that precisely -- a note's
        # leading accidental or dynamic marking can land one column early,
        # inside the *previous* marker's slice. `split_tokens_into_measures`
        # then reports that slice as more than one measure's worth of
        # tokens even though a span-1 (group-boundary) system is only ever
        # supposed to hold one. Rather than silently dropping that overflow
        # (which reads as "the first character of the next measure got
        # swallowed"), carry it forward and prepend it to the very next
        # system's tokens for the same instrument key.
        carry_tokens: dict[str, list[BrailleToken]] = {}
        prev_end_measure_number: int | None = None
        for sys in systems:
            if prev_end_measure_number != sys.measure_number - 1:
                carry_tokens = {}

            sys_measure_toks = {}
            for key, music_cells in sys.parts.items():
                # at_line_start=False: same reason as above -- this fragment's
                # first cell is real music content, not a line-start context.
                tokens = BrailleTokenizer().tokenize(music_cells, at_line_start=False)
                measure_tokens = split_tokens_into_measures(tokens)
                leftover = carry_tokens.pop(key, None)
                if leftover:
                    if measure_tokens:
                        measure_tokens[0] = leftover + measure_tokens[0]
                    else:
                        measure_tokens = [leftover]
                sys_measure_toks[key] = measure_tokens

            if sys.end_measure_number == sys.measure_number:
                for key, measure_tokens in sys_measure_toks.items():
                    if len(measure_tokens) > 1:
                        overflow: list[BrailleToken] = []
                        for extra in measure_tokens[1:]:
                            overflow.extend(extra)
                        # Only ever carry a bare run of note-prefix modifiers
                        # (an accidental/dynamic/octave mark with no note or
                        # rest of its own) or a truncated word-sign opener --
                        # a self-contained construct (NOTE, REST,
                        # NUMERAL_REPEAT, a *complete* WORD_SIGN, ...) in the
                        # overflow means this isn't a stray column-boundary
                        # split of one note's prefix, and gluing it onto the
                        # next system's tokens with no blank-cell separator
                        # would corrupt constructs that rely on being
                        # terminated by a blank cell (e.g. NUMERAL_REPEAT,
                        # BANA Sec. 19) -- so leave those to the old
                        # (drop the overflow) behavior instead.
                        if overflow and all(_is_carriable_overflow(t) for t in overflow):
                            carry_tokens[key] = overflow
                        sys_measure_toks[key] = measure_tokens[:1]

            prev_end_measure_number = sys.end_measure_number

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
            parser = BrailleParser(
                tokens=tokens,
                instruments=instruments,
                ensemble=True,
                active_instrument=inst
            )
            try:
                score = parser.parse()
            except BrailleParseError as e:
                # Re-raise with the instrument name attached so a reader
                # of the error knows which part failed, alongside the
                # measure number BrailleParser's own message already
                # carries (e.g. "Instrument 'Violin I': Measure 12: ...").
                # type(e), not a hardcoded BrailleParseError: preserves
                # whichever specific subclass (NumeralRepeatError,
                # TripletDurationError, ...) BrailleParser actually raised,
                # so callers catching a specific subclass still can. A
                # non-BrailleParseError (TypeError, KeyError, ...) is a
                # real bug, not malformed input -- let it keep failing
                # loudly with its own traceback instead of being relabeled
                # as an expected parse failure (see exceptions.py).
                raise type(e)(f"Instrument '{inst.name}': {e}") from e

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
                raise BrailleParseError(f"Circular parallel movement dependency for {inst_name} at measure {m_num}")
            resolving.add(state_key)

            res_type, val1, val2 = resolutions[inst_name][m_num]
            if res_type == 'normal':
                staff = instrument_staves[inst_name]
                measure_obj = next((m for m in staff.measures if m.number == m_num), None)
                if measure_obj is None:
                    warnings.warn(
                        f"{inst_name}: Measure {m_num} could not be recovered "
                        "from this instrument's own reconstructed content -- "
                        "emitting an empty measure with no key signature "
                        "carried over. Check the source for a missing bar "
                        "line, mismatched measure-number markers, or other "
                        "notation this parser could not reconcile.",
                        stacklevel=2,
                    )
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
                    raise BrailleParseError(f"Source instrument for parallel movement not found for {inst_name} at measure {m_num}")

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

        # Collect and parse lyrics for vocal instruments
        for inst in instruments:
            if self.category_override is not None and self.category_override not in ("Art Song", "Vocal"):
                continue
            if inst.family == InstrumentFamily.VOCAL:
                staff = instrument_staves[inst.name]
                # A word line (Sec. 35.1) was stashed on `sys.word_lines`,
                # keyed by the same abbreviation as this instrument's own
                # `.parts` music-line entry (see ParallelSystem.add_line).
                max_verses = 0
                for sys in systems:
                    for key in sys.parts:
                        prefix, digits = decode_instrument_abbreviation(key)
                        if inst.abbreviation.lower() == prefix.lower():
                            if not digits or inst.part_number in digits:
                                if key in sys.word_lines:
                                    max_verses = max(max_verses, len(sys.word_lines[key]))
                                break

                verse_syllables_list = [[] for _ in range(max_verses)]
                verses_prefixes = [None] * max_verses
                has_any_lyrics = False
                for sys in systems:
                    for key in sys.parts:
                        prefix, digits = decode_instrument_abbreviation(key)
                        if inst.abbreviation.lower() == prefix.lower():
                            if not digits or inst.part_number in digits:
                                if key in sys.word_lines:
                                    chunks = sys.word_lines[key]
                                    has_any_lyrics = True
                                    if len(chunks) == 1 and max_verses > 1:
                                        chunks = [chunks[0]] * max_verses
                                    for v_idx in range(max_verses):
                                        chunk = chunks[v_idx] if v_idx < len(chunks) else ""
                                        if not chunk.strip():
                                            continue
                                        syllables = parse_lyrics(chunk)
                                        prefix_val, remaining_syllables = extract_stanza_prefix(syllables)
                                        if prefix_val is not None:
                                            if not verse_syllables_list[v_idx]:
                                                # This verse's very first contribution: its prefix is
                                                # the overall stanza label for the whole verse, which
                                                # rendering (Score.to_lilypond() / OrchestraScore.to_
                                                # lilypond()) already adds once from
                                                # staff.verse_prefixes -- baking it into the syllable
                                                # text here too used to double it up (S8b-13).
                                                if verses_prefixes[v_idx] is None:
                                                    verses_prefixes[v_idx] = prefix_val
                                            elif remaining_syllables:
                                                # A later system (e.g. a refrain) introducing a new
                                                # stanza label partway through this verse's lyrics.
                                                # Rendering only emits one `\set stanza` at the very
                                                # start of the line, so a mid-stream label change has
                                                # nowhere else to go -- bake it into the syllable text.
                                                first_syl, has_hyphen = remaining_syllables[0]
                                                remaining_syllables[0] = (
                                                    f"\\set stanza = \"{prefix_val} \" {first_syl}", has_hyphen
                                                )
                                        verse_syllables_list[v_idx].extend(remaining_syllables)
                                break

                if has_any_lyrics:
                    groups = group_pitched_elements_by_slur(staff.measures)

                    mapped_verses = []
                    for v_idx in range(max_verses):
                        mapped_verses.append(map_syllables_to_groups(
                            verse_syllables_list[v_idx], groups, inst.name, f"Verse {v_idx+1}",
                        ))

                    if mapped_verses:
                        staff.lyrics = mapped_verses[0]
                        staff.verses = mapped_verses
                        staff.verse_prefixes = verses_prefixes

        score = OrchestraScore()
        for inst in instruments:
            score.add_staff(instrument_staves[inst.name])

        return score
