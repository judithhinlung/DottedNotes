import re
import unicodedata
from dataclasses import dataclass
from enum import Enum, auto
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
from dottednotes.exceptions import BrailleParseError
from dottednotes.parser.ensemble_parser import (
    group_pitched_elements_by_slur, _LYRIC_PUNCTUATION, _ACCENT_MODIFIERS,
)
from dottednotes.parser.input_pipeline import ASCII_TO_DOTS

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


_REVERSE_ACCENT_MODIFIERS: dict[str, tuple[str, str]] = {
    mark: (prefix, selector)
    for prefix, group in _ACCENT_MODIFIERS.items()
    for selector, mark in group.items()
}


def _encode_accented_letter(char: str, all_caps: bool) -> str:
    """Encode one accented letter (e.g. "é", "Ö") to its UEB 4.2
    accent-modifier prefix + selector + base-letter cells -- the inverse
    of `ensemble_parser._decode_accented_letter()`, built from that same
    `_ACCENT_MODIFIERS` table (so it covers exactly what that decoder
    covers, not a separate guess). Per UEB 4.2.2, a capitalized accented
    letter places the capital indicator *before* the accent prefix, not
    where a plain letter's capital indicator would go."""
    decomposed = unicodedata.normalize('NFD', char)
    if len(decomposed) != 2 or decomposed[1] not in _REVERSE_ACCENT_MODIFIERS:
        raise BrailleParseError(
            f"Cannot encode lyric character {char!r} to braille -- not a "
            "plain letter, basic punctuation, or a UEB 4.2 accented letter "
            "this codebase's accent table covers."
        )
    base, mark = decomposed
    if base.upper() not in ASCII_TO_DOTS:
        raise BrailleParseError(f"Cannot encode lyric character {char!r} to braille.")
    prefix, selector = _REVERSE_ACCENT_MODIFIERS[mark]
    result = []
    if char.isupper() and not all_caps:
        result.append('⠠')
    result.append(chr(0x2800 + ASCII_TO_DOTS[prefix]))
    result.append(chr(0x2800 + ASCII_TO_DOTS[selector]))
    result.append(chr(0x2800 + ASCII_TO_DOTS[base.upper()]))
    return ''.join(result)


def _encode_lyric_word(word: str) -> str:
    """Encode one lyric word to BANA §35.1.1 braille cells: capital
    indicator(s), letters, hyphens, UEB 4.2 accented letters (BANA
    §35.1.1(d): "foreign words in an English language context"), and the
    UEB 7.1/7.6.6 punctuation `_LYRIC_PUNCTUATION` (in
    `ensemble_parser.py`) already decodes. This is that decoder's inverse,
    so it only covers what it covers -- quotation marks and numerals
    (which `parse_lyrics()` also decodes) are not emitted here, since
    those are rare in the plain-text lyrics DottedNotes itself renders
    (from MusicXML/LilyPond import); extend this if that changes."""
    reverse_punctuation = {v: k for k, v in _LYRIC_PUNCTUATION.items()}
    letters_only = [c for c in word if c.isalpha()]
    all_caps = len(letters_only) >= 2 and all(c.isupper() for c in letters_only)

    result = []
    if all_caps:
        result.append('⠠⠠')
    for char in word:
        # MusicXML/LilyPond sources routinely spell a contraction apostrophe
        # as the Unicode "smart" right single quotation mark (U+2019, e.g.
        # "sagen's") rather than a plain ASCII "'" -- treated the same as
        # a plain apostrophe here (BANA's single apostrophe cell, dot 3),
        # since a genuine closing single quotation mark (which decodes
        # differently, via the two-cell `,0` sign) is comparatively rare
        # in song lyrics.
        if char == '’':
            char = "'"
        if char.isalpha() and char.upper() in ASCII_TO_DOTS:
            if not all_caps and char.isupper():
                result.append('⠠')
            result.append(chr(0x2800 + ASCII_TO_DOTS[char.upper()]))
        elif char.isalpha():
            result.append(_encode_accented_letter(char, all_caps))
        elif char == '-':
            result.append(chr(0x2800 + ASCII_TO_DOTS['-']))
        elif char in reverse_punctuation:
            result.append(chr(0x2800 + ASCII_TO_DOTS[reverse_punctuation[char]]))
        else:
            raise BrailleParseError(
                f"Cannot encode lyric character {char!r} to braille -- only "
                "letters, hyphens, UEB 4.2 accented letters, and basic UEB "
                "7.1/7.6.6 punctuation (,.;:!') are supported."
            )
    return ''.join(result)


def encode_lyric_line(lyrics: list[str]) -> str:
    """Encode a staff's `lyrics` into one line of BANA §35.1.1 lyric
    braille: words separated by a blank cell.

    `lyrics` entries follow the convention `map_syllables_to_groups()` (and
    `Score.to_lilypond()`) already use: a trailing `" --"` marks a syllable
    that continues directly into the next entry (both are syllables of one
    word divided across notes by a syllabic slur, BANA §35.2). Per
    §35.1.1(a), a print hyphen dividing one word's syllables is *not*
    written in braille at all, so continuations are joined with no space
    and no braille hyphen -- only genuine word boundaries get the blank
    cell."""
    blank_cell = chr(0x2800)
    parts: list[str] = []
    pending_continuation = False
    for entry in lyrics:
        continues = entry.endswith(' --')
        text = entry[:-3] if continues else entry
        if parts and not pending_continuation:
            parts.append(blank_cell)
        parts.append(_encode_lyric_word(text))
        pending_continuation = continues
    return ''.join(parts)


def center_line(text: str, width: int) -> str:
    """Center a braille line within the specified width."""
    if len(text) >= width:
        return text
    left_padding = (width - len(text)) // 2
    return '⠀' * left_padding + text


def join_tempo_and_signature(tempo_brl: str, *signature_parts: str) -> str:
    """Join a tempo/expression marking with the combined clef/key/time
    signature unit, separated by one space when both are present. The
    signature parts themselves stay joined with no space between them
    (they're a single combined unit); only the tempo marking, a
    separate word-sign expression, is set off from it."""
    combined = "".join(signature_parts)
    if tempo_brl and combined:
        return tempo_brl + '⠀' + combined
    return tempo_brl or combined


_ROMAN_NUMERALS = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X']

# A bare transposition/key name used as a leading qualifier in real
# MusicXML part names (e.g. "Bb Clarinet", "C Tuba", "F Horn") -- BANA
# Sec. 33.2.1's own Example 33.2.1-1 abbreviates "Trumpet in B-flat" as
# just "tp", the key dropped entirely, so the same qualifier fronting the
# name instead of trailing it must be dropped the same way before
# resolving against Table 29.
_KEY_QUALIFIER_RE = re.compile(r'^[A-G](?:-?(?:flat|sharp)|[b#])?$', re.IGNORECASE)


def _roman_to_arabic(numeral: str) -> Optional[str]:
    upper = numeral.upper()
    if upper in _ROMAN_NUMERALS:
        return str(_ROMAN_NUMERALS.index(upper) + 1)
    return None


def _arabic_to_roman(numeral: str) -> Optional[str]:
    if numeral.isdigit():
        idx = int(numeral) - 1
        if 0 <= idx < len(_ROMAN_NUMERALS):
            return _ROMAN_NUMERALS[idx]
    return None


def _singular_forms(name: str) -> list[str]:
    """Plausible singular forms of a plural/section instrument name (e.g.
    "Violins" -> "Violin", "Basses" -> "Bass"), stripping only the last word."""
    words = name.split()
    if not words:
        return []
    last_word = words[-1]
    forms = []
    if last_word.endswith('es'):
        forms.append(' '.join(words[:-1] + [last_word[:-2]]))
    if last_word.endswith('s'):
        forms.append(' '.join(words[:-1] + [last_word[:-1]]))
    return forms


def _strip_leading_key_qualifier(name: str) -> Optional[str]:
    """Drop a leading bare key/transposition qualifier word (e.g. "Bb" in
    "Bb Clarinet", "C" in "C Tuba"), or None if `name` doesn't start with one."""
    words = name.split()
    if len(words) > 1 and _KEY_QUALIFIER_RE.match(words[0]):
        return ' '.join(words[1:])
    return None


def _table29_lookup(staff_name: str) -> Optional[str]:
    """Resolve `staff_name` against BANA Table 29, tolerating the
    plural/section-style part names real MusicXML exports use (e.g.
    "Violins I", "Violas", "Double Basses") against the table's singular
    solo-instrument keys ("Violin I", "Viola", "Double bass"), a leading
    key/transposition qualifier ("Bb Clarinet", "C Tuba" -- Sec. 33.2.1),
    and a numbered part given as an Arabic digit rather than the table's
    Roman numeral ("Violin I") or with no dedicated table entry at all
    ("Flute 1", "Horn 1" -- Sec. 33.2.2 appends the part number, as a
    lower-cell digit, directly after the base abbreviation)."""
    lower_table = {key.lower(): val for key, val in TABLE_29_ENGLISH.items()}

    abbrev = lower_table.get(staff_name.lower())
    if abbrev:
        return abbrev

    numeral_match = re.match(r'^(.+?)\s+(\d+|[IVXLCDM]+)$', staff_name)
    if not numeral_match:
        words = staff_name.split()
        if not words:
            return None
        no_numeral_candidates = _singular_forms(staff_name)
        qualifier_stripped = _strip_leading_key_qualifier(staff_name)
        if qualifier_stripped:
            no_numeral_candidates.append(qualifier_stripped)
            no_numeral_candidates.extend(_singular_forms(qualifier_stripped))
        for candidate in no_numeral_candidates:
            abbrev = lower_table.get(candidate.lower())
            if abbrev:
                return abbrev
        return None

    head, numeral = numeral_match.group(1), numeral_match.group(2)
    is_arabic = numeral.isdigit()
    roman = numeral if not is_arabic else _arabic_to_roman(numeral)
    arabic = numeral if is_arabic else _roman_to_arabic(numeral)

    base_candidates = [head] + _singular_forms(head)
    qualifier_stripped = _strip_leading_key_qualifier(head)
    if qualifier_stripped:
        base_candidates.append(qualifier_stripped)
        base_candidates.extend(_singular_forms(qualifier_stripped))

    if roman:
        for base in base_candidates:
            abbrev = lower_table.get(f"{base} {roman}".lower())
            if abbrev:
                return abbrev

    if arabic:
        for base in base_candidates:
            abbrev = lower_table.get(base.lower())
            if abbrev:
                return abbrev + arabic

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


# BANA §35.1: a vocal solo's music line begins in cell 3 (2 blank cells) --
# distinct from an instrumental solo's cell-1 start.
_MUSIC_LINE_MARGIN = '⠀⠀'


def wrap_run_over_line(line: str, width: int, indent_cells: int = 2) -> list[str]:
    """Split one staff's parallel line into BANA 28.1.2/33.4.7 run-over
    lines when it's too long to fit alone: the music hyphen (dot 5, BANA
    1.11) is appended directly to the last cell that fits (no space
    before it) to mark the interruption, and the remainder continues on
    a new line indented `indent_cells` cells beyond the parallel's margin
    (2, BANA 28.1.2/33.4.7's default, unless a caller's format uses a
    different run-over cell -- e.g. BANA §35.1's vocal line-by-line format
    indents both word-line and music-line run-overs to cell 5, 4 cells) --
    with no re-stated abbreviation, since it's a continuation of the same
    line, not a new instrument line."""
    if len(line) <= width:
        return [line]
    result = []
    remaining = line
    indent = ""
    run_over_indent = '⠀' * indent_cells
    while len(indent) + len(remaining) > width:
        content_width = width - len(indent) - 1  # reserve 1 cell for ⠐
        result.append(indent + remaining[:content_width] + '⠐')
        remaining = remaining[content_width:]
        indent = run_over_indent
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
    but still get a dot 3 whenever the caller knows what comes next
    (`music_strs`): a real music cell -- whether it sets dots 1-3 (e.g. a
    note/rest/accidental) or only dots 4-6 (e.g. an octave mark) -- is
    never blank, and every worked example in BANA 33.4/33.4.1/33.4.2/
    33.4.4/33.4.6 shows dot 3 present regardless of which sign follows;
    none of them show a bare abbreviation running straight into music.
    Only a caller with no music info at all (`music_strs` omitted, or an
    empty string for a given staff) gets no dot 3 for a zero-gap staff,
    since there's nothing to confirm real content follows."""
    bare_prefixes = ['⠜' + abbrev_to_brl(staff_abbreviation(name)) for name in staff_names]
    max_len = max((len(p) for p in bare_prefixes), default=0)
    if music_strs is None:
        music_strs = [""] * len(staff_names)
    prefixes = []
    for bare, music_str in zip(bare_prefixes, music_strs):
        gap = max_len - len(bare)
        if gap > 0:
            prefixes.append(bare + '⠄' + chr(0x2800) * (gap - 1))
        elif music_str:
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


def key_signature_changes_by_index(measures: list[Measure], initial_key: int) -> dict[int, int]:
    """Map absolute measure index -> new sharps/flats count, for every
    measure whose effective key signature differs from the previous
    measure's (S11-3, BANA Par. 6.5's "a change of key is placed wherever
    it occurs"). `initial_key` is the key already stated in the header
    (`Staff.key_signature`), so a first measure matching it correctly gets
    no (redundant) change entry. Pure function of the static measure list
    -- computed once per staff before any line-packing/lookahead, so it
    can be looked up by absolute index regardless of how measures end up
    grouped into lines."""
    changes: dict[int, int] = {}
    last = initial_key
    for i, m in enumerate(measures):
        if m.key_signature != last:
            changes[i] = m.key_signature
            last = m.key_signature
    return changes


def render_measure_slice(
    measures: list[Measure],
    start_idx: int,
    size: int,
    prev_note: Optional[Note],
    time_sig,
    compression_level: str = "full",
    force_all_starts: bool = False,
    key_changes: Optional[dict[int, int]] = None,
) -> tuple[list[str], Optional[Note]]:
    """Helper to render a slice of measures. Only the first measure of the
    slice is treated as a line start, unless `force_all_starts` is set (the
    "octave mark on every measure" reader preference), in which case every
    measure in the slice is."""
    rendered = []
    curr_prev = prev_note
    for k in range(size):
        idx = start_idx + k
        m = measures[idx]
        is_start = (k == 0) or force_all_starts
        m_brl, curr_prev = m.to_braille(
            prev_note=curr_prev, is_measure_start=is_start, time_signature=time_sig,
            compression_level=compression_level,
            key_signature_change=(key_changes.get(idx) if key_changes else None),
        )
        rendered.append(m_brl)
    return rendered, curr_prev


def _strip_note_item_for_outline(item) -> None:
    """Recursively clear every per-note marking BANA §29.8 excludes from a
    keyboard accompaniment's solo-outline line ("nuances, slurs, word-sign
    expressions, or ... lyrics") from `item` in place, leaving only what
    §29.8 says the outline keeps: "notes, ties, rests, and other essential
    marks such as fermatas." """
    if isinstance(item, Tuplet):
        for sub in item.items:
            _strip_note_item_for_outline(sub)
    elif isinstance(item, InAccord):
        for part in item.parts:
            for sub in part:
                _strip_note_item_for_outline(sub)
    elif isinstance(item, Chord):
        for note in item.notes:
            _strip_note_item_for_outline(note)
    elif isinstance(item, Note):
        item.dynamics = []
        item.articulations = []
        item.ornaments = []
        item.grace_note = None
        item.slur_start = False
        item.slur_end = False
        item.slur_bracket_open = False
        item.slur_bracket_close = False
        item.fingerings = []
    elif isinstance(item, Rest):
        item.pedal_sustain = None


def build_solo_outline_measures(measures: list[Measure]) -> list[Measure]:
    """Build a BANA §29.8 solo-outline projection of `measures`: a deep
    copy with every note/chord's dynamics, articulations, ornaments, grace
    notes, slurs, and fingerings cleared (ties and fermatas survive
    untouched), for use as the outline line placed above a keyboard
    accompaniment's right hand."""
    import copy as _copy
    stripped = _copy.deepcopy(measures)
    for measure in stripped:
        for note_item in measure.notes:
            _strip_note_item_for_outline(note_item)
    return stripped


class TranscriptionMode(Enum):
    """Which of BANA's braille layouts a score gets transcribed in. This is
    an explicit, named result of structural detection (staff count/family/
    OrchestraScore-ness) rather than the ad hoc `is_piano`/`is_ensemble`
    booleans re-derived inline that used to live in `render()` -- detection
    itself is unchanged, only now it produces one value instead of two
    booleans callers had to keep consistent by hand.

    Placement of measure numbers (margin vs. a blank line above the system
    of parallels) is *derived from* this mode, not an independent setting:
    SINGLE_LINE and PIANO both use margin placement (BANA 24.1.1 / 29.3(b)
    -- they differ only in whether the numeral sign is included, already
    handled by each render method), ENSEMBLE uses the blank-line heading
    (BANA 33.4.6).

    SINGLE_LINE (BANA Sec. 24, "Instrumental Solos and Ensemble Parts") is
    the mode for a single instrumental part -- a solo BRF/BRL's own single
    staff, an extracted ensemble/piano part, or a solo MusicXML/LilyPond
    piece -- named for BANA's own Sec. 24.1 heading ("Single-Line Format"),
    not just "solo": that section is purely about segment/measure-number
    layout, and applies identically regardless of where the single staff
    came from (S12-3, renamed from SOLO for that reason).

    TODO(product): a user who wants margin-style placement in ensemble mode
    (or blank-line placement in single-line/piano mode) would need
    placement decoupled from transcription mode as its own setting. Not
    built here -- it wasn't requested, and doing it well needs product
    input on how BANA would even describe such a layout (neither
    24.1.1/29.3(b) nor 33.4.6 anticipates it). Revisit only on an explicit
    future request.
    """
    SINGLE_LINE = auto()
    PIANO = auto()
    ENSEMBLE = auto()
    VOCAL_SOLO = auto()
    SOLO_WITH_ACCOMPANIMENT = auto()
    CHORAL_ENSEMBLE = auto()


def _item_has_ensemble_resolved_chord(item: Any) -> bool:
    """True if `item` is (or contains) a Chord whose interval note(s) were
    resolved under BANA 33.4.2's ensemble "read upward" rule -- recurses
    into InAccord voices and Tuplet items, the two MeasureItem containers
    a Chord can be nested inside (see measure.py's MeasureItem union)."""
    if isinstance(item, Chord):
        return item.resolved_ensemble_upward
    if isinstance(item, InAccord):
        return any(
            _item_has_ensemble_resolved_chord(sub)
            for part in item.parts
            for sub in part
        )
    if isinstance(item, Tuplet):
        return any(_item_has_ensemble_resolved_chord(sub) for sub in item.items)
    return False


def _staff_has_ensemble_resolved_chord(staff: Staff) -> bool:
    """True if any measure in `staff` contains a Chord/interval resolved
    under the ensemble-upward rule (see `Chord.resolved_ensemble_upward`).
    Used by `_detect_transcription_mode` (S10d-13) to keep a single
    extracted part in ENSEMBLE transcription when downgrading it to
    SINGLE_LINE would misread that content."""
    return any(
        _item_has_ensemble_resolved_chord(item)
        for measure in staff.measures
        for item in measure.notes
    )


# "auto": engine numbers measures sequentially from 1, ignoring whatever
# Measure.number carries in from the source file. "print_score": use
# Measure.number as the source parser assigned it -- MusicXML's own
# <measure number="..."> (already threaded straight through by
# musicxml_parser.translate_measure), a BRF's explicit margin numbers where
# given (braille_parser.py's _handle_measure_number), or a LilyPond import's
# sequential count (lilypond_parser.py currently has no source-side bar-
# number annotation to read, so it produces the same numbers either way --
# see the TODO on _display_measure_number below). Matches compression_level/
# validation `profile`'s existing plain-string-choice convention rather than
# introducing a new pattern for a user-facing setting.
MEASURE_NUMBERING_MODES = ("auto", "print_score")

# "off": disable full-measure repeat-sign compression (BANA Par. 18.2)
# entirely. "single-voice": only compress measures with no in-accord
# (multi-voice) content. "multi-voice": also allow compressing in-accord-
# containing measures (relies on InAccord.musical_equals -- see
# _compress_measure_repeats below). Independent of `compression_level`,
# which continues to gate the unrelated articulation-carry-shorthand pass;
# `compression_level == "none"` remains a hard override disabling both.
FULL_MEASURE_REPEAT_MODES = ("off", "single-voice", "multi-voice")


class BrailleRenderer:
    def __init__(
        self,
        line_width: int = 40,
        show_measure_numbers: bool = True,
        compression_level: str = "full",
        omit_redundant_hairpin_terminators: bool = True,
        measure_numbering: str = "auto",
        octave_mark_every_measure: bool = False,
        full_measure_repeat: str = "single-voice",
        min_repeated_measures: int = 2,
        include_clef_sign: bool = False,
    ):
        self.line_width = line_width
        self.show_measure_numbers = show_measure_numbers
        self.compression_level = compression_level
        # BANA 22.3.3(b): override/disable if a caller wants every hairpin
        # terminator brailled explicitly regardless of what follows it --
        # independent of `compression_level`, since this is a transcription
        # rule rather than one of the optional space-saving passes below.
        self.omit_redundant_hairpin_terminators = omit_redundant_hairpin_terminators
        if measure_numbering not in MEASURE_NUMBERING_MODES:
            raise ValueError(
                f"measure_numbering must be one of {MEASURE_NUMBERING_MODES}, "
                f"got {measure_numbering!r}"
            )
        self.measure_numbering = measure_numbering
        # BANA 3.2.1 already forces the octave mark at a line's first note
        # (and at other required trigger points); this is an additive
        # reader preference that widens that reset to every measure's
        # first note, never suppressing a mark that was already required.
        self.octave_mark_every_measure = octave_mark_every_measure
        if full_measure_repeat not in FULL_MEASURE_REPEAT_MODES:
            raise ValueError(
                f"full_measure_repeat must be one of {FULL_MEASURE_REPEAT_MODES}, "
                f"got {full_measure_repeat!r}"
            )
        self.full_measure_repeat = full_measure_repeat
        if min_repeated_measures < 2:
            raise ValueError(
                "min_repeated_measures must be >= 2 (a repeat needs at "
                f"least one original plus one repetition), got {min_repeated_measures!r}"
            )
        self.min_repeated_measures = min_repeated_measures
        # BANA Par. 4.1: "Clef signs are routinely omitted in braille music
        # transcription" -- off by default. When a caller wants a facsimile
        # transcription (Par. 4.1's stated exception: "for the benefit of
        # the blind teacher with sighted pupils"), the clef sign is placed
        # once, right after the first measure's number and before that
        # measure's own signs (dynamics/articulations/ornaments/octave
        # mark/note) -- not glued onto the key/time signature line, per
        # Par. 10.1.2's ordering ("measure number, hand signs, clefs...
        # time or key signatures" all precede everything else) and Par.
        # 6.5.1's analogous "hand or clef sign" placement before the
        # accidental/octave-mark/note sequence. Single-line output only for
        # now (_render_single_line) -- _render_piano/_render_ensemble don't
        # emit a clef sign at all today regardless of this setting, an
        # existing gap this doesn't attempt to close.
        self.include_clef_sign = include_clef_sign

    def _detect_transcription_mode(self, score: Score) -> TranscriptionMode:
        # is_piano is computed first and independent of isinstance(score,
        # OrchestraScore): LilypondParser tags any parsed score containing
        # "PianoStaff" as an OrchestraScore, so a 2-staff piano score must
        # not automatically fall into ensemble layout.
        from dottednotes.models.instrument import InstrumentFamily, get_instrument_family
        # `all`, not `any`: a genuine 2-hand piano solo has *both* staves
        # KEYBOARD_HARP. A solo instrument plus a single-staff keyboard
        # reduction (one non-keyboard staff + one keyboard staff) is BANA
        # §29.8's solo-with-accompaniment shape instead (checked below),
        # not a piano solo -- treating it as PIANO would read the solo
        # instrument's own staff as if it were a piano right hand.
        is_piano = len(score.staves) == 2 and all(
            get_instrument_family(s.name) == InstrumentFamily.KEYBOARD_HARP for s in score.staves
        )
        if is_piano:
            return TranscriptionMode.PIANO
        # BANA §29.8: a solo (vocal or instrumental) part with a keyboard
        # accompaniment is transcribed as two separate blocks -- the solo
        # part transcribed individually, the keyboard part transcribed
        # separately with a solo-outline line above the right hand -- never
        # as one flat ENSEMBLE parallel. Checked before the
        # isinstance(OrchestraScore) / staff-count ENSEMBLE branch below
        # since EnsembleParser always returns an OrchestraScore, which
        # would otherwise force ENSEMBLE first for exactly this shape (the
        # bug this mode exists to fix).
        if (
            len(score.staves) in (2, 3)
            and get_instrument_family(score.staves[0].name) != InstrumentFamily.KEYBOARD_HARP
            and all(
                get_instrument_family(s.name) == InstrumentFamily.KEYBOARD_HARP
                for s in score.staves[1:]
            )
        ):
            return TranscriptionMode.SOLO_WITH_ACCOMPANIMENT
        # BANA §37.1: a vocal ensemble (2+ all-vocal staves, no
        # accompaniment) is its own "expanded bar-over-bar format" --
        # word lines then music lines per parallel -- never the generic
        # §33 ENSEMBLE layout. Checked before the isinstance(OrchestraScore)
        # branch below for the same reason as SOLO_WITH_ACCOMPANIMENT above.
        if (
            len(score.staves) >= 2
            and all(get_instrument_family(s.name) == InstrumentFamily.VOCAL for s in score.staves)
            and any(s.lyrics for s in score.staves)
        ):
            return TranscriptionMode.CHORAL_ENSEMBLE
        # BANA §35.1: a lone vocal staff with lyrics is its own dedicated
        # line-by-line format (words at cell 1, music at cell 3), never the
        # generic instrumental SINGLE_LINE layout -- checked before the
        # ENSEMBLE/staff-count branch below since it's a 1-staff case.
        if (
            len(score.staves) == 1
            and get_instrument_family(score.staves[0].name) == InstrumentFamily.VOCAL
            and score.staves[0].lyrics
        ):
            return TranscriptionMode.VOCAL_SOLO
        if isinstance(score, OrchestraScore) or len(score.staves) > 2:
            return TranscriptionMode.ENSEMBLE
        # S10d-13: a single staff can still need ENSEMBLE transcription --
        # Score.extract_part() always wraps its result in a plain
        # single-staff Score, regardless of the original score's type, but
        # if that staff carries any Chord resolved under BANA 33.4.2's
        # ensemble "read upward" rule (Chord.resolved_ensemble_upward),
        # downgrading it to SINGLE_LINE's clef-based direction would have a
        # reader reconstruct the wrong pitch letter for that interval, not
        # just the wrong octave. Rendering it as ENSEMBLE instead (its own
        # one-row instrument-list header + per-line abbreviation prefix)
        # keeps the "always read upward" convention intact for the reader,
        # which is what the chord's actual pitches were built under.
        if len(score.staves) == 1 and _staff_has_ensemble_resolved_chord(score.staves[0]):
            return TranscriptionMode.ENSEMBLE
        return TranscriptionMode.SINGLE_LINE

    @staticmethod
    def _measure_span(measure: Measure) -> int:
        """How many real BANA measures `measure` stands for. Always 1,
        except a `_compress_multi_measure_rests`-merged measure (S11c-7):
        one rendered Measure slot representing `multi_measure_count`
        real, consecutive whole-measure rests collapsed into BANA Par.
        5.3's compact sign."""
        if (
            len(measure.notes) == 1
            and isinstance(measure.notes[0], Rest)
            and measure.notes[0].multi_measure_count > 1
        ):
            return measure.notes[0].multi_measure_count
        return 1

    def _display_measure_number(self, measures: list[Measure], position: int) -> int:
        """The number to show at `measures[position]`'s margin/heading
        position.

        "auto" renumbers sequentially from 1, ignoring whatever
        `Measure.number` carries in from the source -- not simply
        `position + 1`: a `_compress_multi_measure_rests`-merged measure
        earlier in `measures` (S11c-7) stands for more than one real
        measure (`_measure_span`), so every measure after it must count
        that span, not just its own single list slot, to keep numbering
        real measures rather than rendered slots. "print_score" uses
        `Measure.number` as-is -- the source parser's own numbering,
        however it was assigned (see MEASURE_NUMBERING_MODES above for
        what that means per input format) -- unaffected by list
        compaction, since it's read straight off the surviving measure.

        TODO(lilypond-roundtrip): `to_lilypond()` doesn't currently emit
        anything (e.g. `\\set Score.currentBarNumber`) that would let
        `lilypond_parser.py` recover an irregular source numbering (a
        pickup measure numbered 0, a renumbered section) on import --
        until that exists, "print_score" and "auto" are equivalent for a
        LilyPond source, both falling back to the parser's own sequential
        count. MusicXML and BRF sources are unaffected: both already carry
        real per-measure numbering into `Measure.number` independently of
        this renderer.
        """
        if self.measure_numbering == "auto":
            return 1 + sum(self._measure_span(m) for m in measures[:position])
        return measures[position].number

    def render(self, score: Score) -> str:
        if not score.staves:
            return ""

        import copy
        score = copy.deepcopy(score)

        if len(score.staves) == 1:
            # BANA Par. 5.3 (S11c-7): mandatory, unconditional multi-
            # measure-rest compaction -- see _compress_multi_measure_rests's
            # own docstring for why this needs to run only when there is
            # exactly one staff (no cross-staff measure-index alignment to
            # desync), regardless of whether that one staff ends up
            # rendered as SINGLE_LINE or as a single-staff ENSEMBLE layout
            # (S10d-13). Runs before hairpin-terminator omission just
            # below so a hairpin ending right before a rest run it merges
            # is correctly seen as needing an "extensive_rest" (BANA Par.
            # 22.3.3(b)) via multi_measure_count, not just is_full_measure.
            self._compress_multi_measure_rests(score.staves[0])

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

        mode = self._detect_transcription_mode(score)

        from dottednotes.models.instrument import InstrumentFamily, get_instrument_family

        # Never compress a lyric-bearing staff's measures into a
        # measure-repeat sign: the sign has no discrete notes for §35.1's
        # "syllables and notes must always be exactly paired" rule to align
        # lyrics against, and a musically-identical measure sung to
        # different words (a very common case -- e.g. a repeated melodic
        # phrase with new lyrics) would be actively wrong to collapse.
        skip_staff_indices: frozenset[int] = frozenset()
        if mode == TranscriptionMode.VOCAL_SOLO:
            skip_staff_indices = frozenset({0})
        elif (
            mode == TranscriptionMode.SOLO_WITH_ACCOMPANIMENT
            and get_instrument_family(score.staves[0].name) == InstrumentFamily.VOCAL
            and score.staves[0].lyrics
        ):
            skip_staff_indices = frozenset({0})
        elif mode == TranscriptionMode.CHORAL_ENSEMBLE:
            skip_staff_indices = frozenset(
                i for i, staff in enumerate(score.staves) if staff.lyrics
            )

        measure_repeat_originals: dict[tuple[int, int], list] = {}
        if self.compression_level != "none" and self.full_measure_repeat != "off":
            # Pass 2: Measure repeat compression pass
            measure_repeat_originals = self._compress_measure_repeats(score, skip_staff_indices)

        if mode == TranscriptionMode.ENSEMBLE:
            return self._render_ensemble(score, rest_only_grid, measure_repeat_originals)
        elif mode == TranscriptionMode.PIANO:
            return self._render_piano(score)
        elif mode == TranscriptionMode.VOCAL_SOLO:
            return self._render_vocal_solo(score)
        elif mode == TranscriptionMode.SOLO_WITH_ACCOMPANIMENT:
            return self._render_solo_with_accompaniment(score)
        elif mode == TranscriptionMode.CHORAL_ENSEMBLE:
            return self._render_choral_ensemble(score, rest_only_grid)
        else:
            return self._render_single_line(score)

    def _render_single_line(self, score: Score) -> str:
        lines = []
        # Title
        if score.title:
            lines.append(center_line(encode_literary_braille(score.title), self.line_width))

        # Signatures line -- clef sign deliberately excluded here (BANA
        # Par. 4.1/10.1.2, S-facsimile-clef): it does not belong next to
        # the key/time signature at all; see the first-measure clef
        # injection below instead.
        staff = score.staves[0]
        signature_parts = []
        if staff.key_signature:
            signature_parts.append(staff.key_signature.to_braille())
        if staff.time_signature:
            signature_parts.append(staff.time_signature.to_braille())
        tempo_brl = staff.tempo.to_braille() if staff.tempo else ""
        sig_line = join_tempo_and_signature(tempo_brl, *signature_parts)

        if sig_line:
            # BANA single-line-format signature line starts with 8 spaces indentation
            lines.append('⠀' * 8 + sig_line)

        # Pack measures on the fly
        current_line = ""
        prev_note = None
        key_changes = key_signature_changes_by_index(
            staff.measures, staff.key_signature.sharps_or_flats if staff.key_signature else 0
        )

        for idx, m in enumerate(staff.measures):
            # Render both possibilities
            brl_start, prev_start = m.to_braille(prev_note=prev_note, is_measure_start=True, time_signature=staff.time_signature, compression_level=self.compression_level, key_signature_change=key_changes.get(idx))
            # A measure that fits mid-line only forces the octave-mark
            # reset when the reader-preference setting asks for it --
            # a line-starting measure (above) always forces it regardless.
            brl_no_start, prev_no_start = m.to_braille(prev_note=prev_note, is_measure_start=self.octave_mark_every_measure, time_signature=staff.time_signature, compression_level=self.compression_level, key_signature_change=key_changes.get(idx))

            if not current_line:
                # BANA 24.1.1: "Each segment is introduced at the margin by
                # the number of its first measure" -- Example 24.1.1-1 shows
                # this margin number with the numeral sign (⠼), unlike a
                # keyboard bar-over-bar parallel's margin number (BANA
                # 29.3(b): "given without the numeric indicator").
                num_str = '⠼' + "".join(_INT_TO_LITERARY_DIGIT[int(d)] for d in str(self._display_measure_number(staff.measures, idx)))
                prefix = (num_str + '⠀') if self.show_measure_numbers else ""
                # Facsimile clef sign (BANA 4.1): stated once, right after
                # the first measure's number, before that measure's own
                # signs -- never restated at later line starts (unlike the
                # octave mark), so this only ever applies to idx == 0, the
                # one time this branch fires for the very first measure of
                # the whole staff. Par. 4.2 requires a dot-3 separator
                # between the clef and whatever follows if that first sign
                # contains dot 1, 2, or 3 (an octave mark alone never does
                # -- all seven octave-mark cells use only dots 4/5/6 --
                # but a dynamic/articulation/ornament/accidental on the
                # very first note, rendered before its octave mark per
                # Note.to_braille()'s own sign ordering, can).
                clef_brl = staff.clef.to_braille() if (self.include_clef_sign and idx == 0 and staff.clef) else ""
                if clef_brl and brl_start and (ord(brl_start[0]) - 0x2800) & 0b111:
                    clef_brl += '⠄'
                current_line = prefix + clef_brl + brl_start
                prev_note = prev_start
            else:
                if len(current_line) + len(brl_no_start) <= self.line_width:
                    current_line += brl_no_start
                    prev_note = prev_no_start
                else:
                    lines.append(current_line)
                    num_str = '⠼' + "".join(_INT_TO_LITERARY_DIGIT[int(d)] for d in str(self._display_measure_number(staff.measures, idx)))
                    prefix = (num_str + '⠀') if self.show_measure_numbers else ""
                    current_line = prefix + brl_start
                    prev_note = prev_start

        if current_line:
            lines.append(current_line)

        return "\n".join(lines) + "\n"

    def _render_vocal_solo(self, score: Score) -> str:
        """BANA §35.1 solo-vocal line-by-line format: a lyric line at cell
        1 paired with its music line at cell 3, one parallel at a time, no
        instrument-abbreviation prefix (§35.1.2: "No part identifier is
        necessary")."""
        staff = score.staves[0]
        lines = []
        if score.title:
            lines.append(center_line(encode_literary_braille(score.title), self.line_width))

        signature_parts = []
        if staff.key_signature:
            signature_parts.append(staff.key_signature.to_braille())
        if staff.time_signature:
            signature_parts.append(staff.time_signature.to_braille())
        tempo_brl = staff.tempo.to_braille() if staff.tempo else ""
        sig_line = join_tempo_and_signature(tempo_brl, *signature_parts)
        if sig_line:
            # BANA §31.5/S11c-2: solo-format signature line starts in cell 9
            # (8 blank cells) -- same convention as _render_single_line's
            # header, and no blank line is needed before the first parallel
            # (§35.1: "A music heading is centered above the first line of
            # lyrics; no blank line is needed between the two").
            lines.append('⠀' * 8 + sig_line)

        key_changes = key_signature_changes_by_index(
            staff.measures, staff.key_signature.sharps_or_flats if staff.key_signature else 0
        )

        syllables_remaining = list(staff.lyrics)
        idx = 0
        n_measures = len(staff.measures)
        prev_note = None

        while idx < n_measures:
            # Pack as many measures as fit the music line (cell 3) into one
            # parallel, mirroring _render_single_line's own line-packing --
            # §35.1.3 would prefer breaking at phrase boundaries instead,
            # but the internal model has no phrase-boundary concept to
            # break on (only a flat syllable list and a flat measure list),
            # so packing by available width is the tractable simplification
            # here; a genuine phrase-aware line-breaker is future work.
            group_size = 1
            best = None
            while idx + group_size <= n_measures:
                slice_strs, tmp_prev = render_measure_slice(
                    staff.measures, idx, group_size, prev_note, staff.time_signature,
                    self.compression_level, force_all_starts=self.octave_mark_every_measure,
                    key_changes=key_changes,
                )
                music_str = _MUSIC_LINE_MARGIN + "".join(slice_strs)
                if len(music_str) > self.line_width:
                    break
                best = (group_size, slice_strs, tmp_prev, music_str)
                group_size += 1

            if best is None:
                slice_strs, tmp_prev = render_measure_slice(
                    staff.measures, idx, 1, prev_note, staff.time_signature,
                    self.compression_level, force_all_starts=self.octave_mark_every_measure,
                    key_changes=key_changes,
                )
                music_str = _MUSIC_LINE_MARGIN + "".join(slice_strs)
                best = (1, slice_strs, tmp_prev, music_str)

            fit_size, slice_strs, tmp_prev, music_str = best

            # §35.1: "The syllables of the lyrics and the notes of the
            # music must always be exactly paired" -- a syllabic slur
            # (§35.2) groups several notes under one syllable, so the
            # number of syllables this parallel consumes is the number of
            # slur groups in its measures, not its raw note count.
            n_slots = len(group_pitched_elements_by_slur(staff.measures[idx:idx + fit_size]))
            phrase_syllables = syllables_remaining[:n_slots]
            syllables_remaining = syllables_remaining[n_slots:]
            lyric_str = encode_lyric_line(phrase_syllables)

            lines.extend(wrap_run_over_line(lyric_str, self.line_width, indent_cells=4))
            lines.extend(wrap_run_over_line(music_str, self.line_width, indent_cells=4))

            prev_note = tmp_prev
            idx += fit_size

        return "\n".join(lines) + "\n"

    def _render_solo_with_accompaniment(self, score: Score) -> str:
        """BANA §29.8: "the solo or instrumental parts are transcribed
        individually, and the accompaniment is transcribed separately" --
        two blocks, not one ENSEMBLE parallel. `score.staves[0]` is the
        solo (vocal or instrumental); `score.staves[1:]` are 1-2 keyboard
        staves (right hand, and optionally left hand)."""
        from dottednotes.models.instrument import InstrumentFamily, get_instrument_family

        solo_staff = score.staves[0]
        keyboard_staves = score.staves[1:]
        if len(keyboard_staves) not in (1, 2):
            raise ValueError(
                "BANA §29.8 keyboard-accompaniment rendering expects 1 or 2 "
                f"keyboard staves after the solo staff, got {len(keyboard_staves)}."
            )

        solo_score = Score(title=score.title)
        solo_score.add_staff(solo_staff)
        if get_instrument_family(solo_staff.name) == InstrumentFamily.VOCAL and solo_staff.lyrics:
            solo_block = self._render_vocal_solo(solo_score)
        else:
            solo_block = self._render_single_line(solo_score)

        rh_staff = keyboard_staves[0]
        lh_staff = keyboard_staves[1] if len(keyboard_staves) > 1 else None
        if lh_staff is not None and len(lh_staff.measures) != len(rh_staff.measures):
            raise ValueError(
                "BANA §29.8 keyboard-accompaniment rendering expects the right- "
                f"and left-hand staves to share the same measure count, got "
                f"{len(rh_staff.measures)} and {len(lh_staff.measures)}."
            )
        if len(rh_staff.measures) != len(solo_staff.measures):
            raise ValueError(
                "BANA §29.8 keyboard-accompaniment rendering expects the solo "
                f"and accompaniment staves to share the same measure count, got "
                f"{len(solo_staff.measures)} and {len(rh_staff.measures)}."
            )
        outline_measures = build_solo_outline_measures(solo_staff.measures)
        accompaniment_block = self._render_accompaniment_with_outline(rh_staff, lh_staff, outline_measures)

        # Two separate transcriptions (§29.8), not one parallel -- a single
        # blank line marks the section break, matching the blank-line-
        # before-a-new-heading convention already used elsewhere (S11c-2).
        return solo_block.rstrip("\n") + "\n\n" + accompaniment_block

    def _render_accompaniment_with_outline(
        self, rh_staff: Staff, lh_staff: Optional[Staff], outline_measures: list[Measure],
    ) -> str:
        """BANA §29.8's keyboard-accompaniment block: a solo-outline line
        (bare ⠜, carrying the measure number) above the right hand (⠨⠜),
        with the left hand (⠸⠜, if present) below."""
        lines = []
        signature_parts = []
        if rh_staff.key_signature:
            signature_parts.append(rh_staff.key_signature.to_braille())
        if rh_staff.time_signature:
            signature_parts.append(rh_staff.time_signature.to_braille())
        tempo_brl = rh_staff.tempo.to_braille() if rh_staff.tempo else ""
        sig_line = join_tempo_and_signature(tempo_brl, *signature_parts)
        if sig_line:
            lines.append('⠀' * 8 + sig_line)

        rh_key_changes = key_signature_changes_by_index(
            rh_staff.measures, rh_staff.key_signature.sharps_or_flats if rh_staff.key_signature else 0
        )
        lh_key_changes = key_signature_changes_by_index(
            lh_staff.measures, lh_staff.key_signature.sharps_or_flats if lh_staff.key_signature else 0
        ) if lh_staff is not None else {}
        outline_key_changes = key_signature_changes_by_index(
            outline_measures, rh_staff.key_signature.sharps_or_flats if rh_staff.key_signature else 0
        )

        idx = 0
        n_measures = len(rh_staff.measures)
        prev_rh = prev_lh = prev_outline = None

        while idx < n_measures:
            group_size = 1
            best = None

            while idx + group_size <= n_measures:
                rh_strs, tmp_rh = render_measure_slice(
                    rh_staff.measures, idx, group_size, prev_rh, rh_staff.time_signature,
                    self.compression_level, force_all_starts=self.octave_mark_every_measure,
                    key_changes=rh_key_changes,
                )
                lh_strs, tmp_lh = (render_measure_slice(
                    lh_staff.measures, idx, group_size, prev_lh, lh_staff.time_signature,
                    self.compression_level, force_all_starts=self.octave_mark_every_measure,
                    key_changes=lh_key_changes,
                ) if lh_staff is not None else ([], None))
                outline_strs, tmp_outline = render_measure_slice(
                    outline_measures, idx, group_size, prev_outline, rh_staff.time_signature,
                    self.compression_level, force_all_starts=self.octave_mark_every_measure,
                    key_changes=outline_key_changes,
                )

                m_num = self._display_measure_number(rh_staff.measures, idx)
                test_outline = self._build_outline_line_from_strings(m_num, outline_strs)
                test_rh = self._build_piano_line_from_strings(m_num, rh_strs, is_right=True, show_number=False)
                test_lh = (
                    self._build_piano_line_from_strings(m_num, lh_strs, is_right=False, show_number=False)
                    if lh_staff is not None else None
                )

                fits = (
                    len(test_outline) <= self.line_width
                    and len(test_rh) <= self.line_width
                    and (test_lh is None or len(test_lh) <= self.line_width)
                )
                if fits:
                    best = (group_size, test_outline, test_rh, test_lh, tmp_rh, tmp_lh, tmp_outline)
                    group_size += 1
                else:
                    break

            if best is None:
                # Force at least one measure to avoid an infinite loop.
                rh_strs, tmp_rh = render_measure_slice(
                    rh_staff.measures, idx, 1, prev_rh, rh_staff.time_signature,
                    self.compression_level, force_all_starts=self.octave_mark_every_measure,
                    key_changes=rh_key_changes,
                )
                lh_strs, tmp_lh = (render_measure_slice(
                    lh_staff.measures, idx, 1, prev_lh, lh_staff.time_signature,
                    self.compression_level, force_all_starts=self.octave_mark_every_measure,
                    key_changes=lh_key_changes,
                ) if lh_staff is not None else ([], None))
                outline_strs, tmp_outline = render_measure_slice(
                    outline_measures, idx, 1, prev_outline, rh_staff.time_signature,
                    self.compression_level, force_all_starts=self.octave_mark_every_measure,
                    key_changes=outline_key_changes,
                )
                m_num = self._display_measure_number(rh_staff.measures, idx)
                test_outline = self._build_outline_line_from_strings(m_num, outline_strs)
                test_rh = self._build_piano_line_from_strings(m_num, rh_strs, is_right=True, show_number=False)
                test_lh = (
                    self._build_piano_line_from_strings(m_num, lh_strs, is_right=False, show_number=False)
                    if lh_staff is not None else None
                )
                best = (1, test_outline, test_rh, test_lh, tmp_rh, tmp_lh, tmp_outline)

            fit_size, outline_line, rh_line, lh_line, tmp_rh, tmp_lh, tmp_outline = best
            lines.append(outline_line)
            lines.append(rh_line)
            if lh_line is not None:
                lines.append(lh_line)
            prev_rh, prev_lh, prev_outline = tmp_rh, tmp_lh, tmp_outline
            idx += fit_size

        return "\n".join(lines) + "\n"

    def _render_choral_ensemble(self, score: Score, rest_only_grid: list[list[bool]]) -> str:
        """BANA §37.1 "Expanded Bar-over-Bar Format": a vocal ensemble
        parallel with all word lines given first, then all music lines
        (never interleaved per staff the way §33's ENSEMBLE format is).
        Word lines begin at cell 1 (run-overs at cell 5); music lines begin
        at cell 3 (run-overs at cell 5) -- §37.1(d)/(e). Word-line content
        (shared-vs-per-voice) is decided by `_build_choral_word_lines`
        (S11c-13/S11c-14)."""
        lines = []
        if score.title:
            lines.append(center_line(encode_literary_braille(score.title), self.line_width))

        first_staff = score.staves[0]
        signature_parts = []
        if first_staff.key_signature:
            signature_parts.append(first_staff.key_signature.to_braille())
        if first_staff.time_signature:
            signature_parts.append(first_staff.time_signature.to_braille())
        tempo_brl = first_staff.tempo.to_braille() if first_staff.tempo else ""
        sig_line = join_tempo_and_signature(tempo_brl, *signature_parts)
        if sig_line:
            # §37 has no §33.2 instrument-list header to align a signature
            # line's indent against (unlike ENSEMBLE's cell-8 convention);
            # cell 9 matches the general solo/vocal signature placement
            # (S11c-2) absent a more specific citation for choral ensembles.
            lines.append('⠀' * 8 + sig_line)

        n_measures = len(first_staff.measures)
        n_staves = len(score.staves)
        idx = 0
        prev_notes: list[Optional[Note]] = [None] * n_staves
        syllables_remaining = [list(staff.lyrics) for staff in score.staves]

        def active_staff_indices(group_size: int) -> list[int]:
            # BANA §37.1(c): "A part that has rests throughout the music
            # included in a parallel is omitted in that parallel" -- same
            # rule and mechanism as §33.1's ensemble tacet-staff omission.
            active = [
                s_idx for s_idx in range(n_staves)
                if any(
                    not rest_only_grid[s_idx][m_idx]
                    for m_idx in range(idx, idx + group_size)
                )
            ]
            return active or list(range(n_staves))

        def render_candidate(group_size: int, active: list[int]):
            slices = []
            prevs = []
            for s_idx in active:
                staff = score.staves[s_idx]
                # §37.1(i): "The first note of every music line requires an
                # octave mark" -- already exactly what render_measure_slice
                # gives by default (is_start at k==0, i.e. the first
                # measure of this line/parallel), with no extra forcing
                # needed beyond the reader's own octave_mark_every_measure
                # preference.
                slice_strs, tmp_prev = render_measure_slice(
                    staff.measures, idx, group_size, prev_notes[s_idx], staff.time_signature,
                    self.compression_level, force_all_starts=self.octave_mark_every_measure,
                )
                slices.append(slice_strs)
                prevs.append(tmp_prev)

            prefixes = ensemble_abbrev_prefixes(
                [score.staves[s].name for s in active],
                ["".join(slice_strs) for slice_strs in slices],
            )
            max_prefix_len = max(len(p) for p in prefixes)
            measure_widths = [
                max(len(slices[k][m]) for k in range(len(active))) + 2
                for m in range(group_size - 1)
            ]

            music_lines = []
            for k in range(len(active)):
                prefix = prefixes[k] + chr(0x2800) * (max_prefix_len - len(prefixes[k]))
                body = "".join(
                    pad_to_boundary(slices[k][m], measure_widths[m])
                    for m in range(group_size - 1)
                )
                body += slices[k][group_size - 1]
                # §37.1(e): music lines begin in cell 3.
                music_lines.append(_MUSIC_LINE_MARGIN + prefix + body)

            return music_lines, prevs, prefixes

        while idx < n_measures:
            group_size = 1
            best = None
            while idx + group_size <= n_measures:
                active = active_staff_indices(group_size)
                music_lines, prevs, prefixes = render_candidate(group_size, active)
                if any(len(l) > self.line_width for l in music_lines):
                    break
                best = (group_size, active, music_lines, prevs, prefixes)
                group_size += 1

            if best is None:
                active = active_staff_indices(1)
                music_lines, prevs, prefixes = render_candidate(1, active)
                best = (1, active, music_lines, prevs, prefixes)

            fit_size, active, music_lines, prevs, prefixes = best

            word_lines = self._build_choral_word_lines(
                score, active, prefixes, fit_size, idx, syllables_remaining,
            )
            for wl in word_lines:
                lines.extend(wrap_run_over_line(wl, self.line_width, indent_cells=4))
            for ml in music_lines:
                lines.extend(wrap_run_over_line(ml, self.line_width, indent_cells=4))

            for k, s_idx in enumerate(active):
                prev_notes[s_idx] = prevs[k]
            idx += fit_size

        return "\n".join(lines) + "\n"

    def _build_choral_word_lines(
        self,
        score: Score,
        active: list[int],
        music_line_prefixes: list[str],
        fit_size: int,
        idx: int,
        syllables_remaining: list[list[str]],
    ) -> list[str]:
        """BANA §37.3 baseline: one identified word line per active voice
        (S11c-13 adds the §37.2 shared-single-line case on top of this).
        `music_line_prefixes` are reused as-is: §37.1(f)'s word-line and
        music-line identifiers use the same abbreviation, just with a
        mandatory trailing space (word lines) instead of a conditional
        dot-3-only gap (music lines)."""
        def _with_mandatory_space(prefix: str) -> str:
            stripped = prefix.rstrip(chr(0x2800))
            if not stripped.endswith('⠄'):
                stripped += '⠄'
            return stripped + chr(0x2800)

        word_prefixes = [_with_mandatory_space(prefix) for prefix in music_line_prefixes]
        max_len = max(len(p) for p in word_prefixes)
        word_prefixes = [p + chr(0x2800) * (max_len - len(p)) for p in word_prefixes]

        word_lines = []
        for k, s_idx in enumerate(active):
            staff = score.staves[s_idx]
            n_slots = len(group_pitched_elements_by_slur(staff.measures[idx:idx + fit_size]))
            consumed = syllables_remaining[s_idx][:n_slots]
            syllables_remaining[s_idx] = syllables_remaining[s_idx][n_slots:]
            lyric_str = encode_lyric_line(consumed) if consumed else ""
            word_lines.append(word_prefixes[k] + lyric_str)
        return word_lines

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
            lines.append('⠀' * 8 + sig_line)

        # Render measures for both hands
        lh_staff = score.staves[1]
        rh_key_changes = key_signature_changes_by_index(
            rh_staff.measures, rh_staff.key_signature.sharps_or_flats if rh_staff.key_signature else 0
        )
        lh_key_changes = key_signature_changes_by_index(
            lh_staff.measures, lh_staff.key_signature.sharps_or_flats if lh_staff.key_signature else 0
        )

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
                rh_slice_strs, tmp_prev_rh = render_measure_slice(rh_staff.measures, idx, group_size, prev_note_rh, rh_staff.time_signature, self.compression_level, force_all_starts=self.octave_mark_every_measure, key_changes=rh_key_changes)
                lh_slice_strs, tmp_prev_lh = render_measure_slice(lh_staff.measures, idx, group_size, prev_note_lh, lh_staff.time_signature, self.compression_level, force_all_starts=self.octave_mark_every_measure, key_changes=lh_key_changes)

                m_num = self._display_measure_number(rh_staff.measures, idx)
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
                rh_slice_strs, best_prev_rh = render_measure_slice(rh_staff.measures, idx, 1, prev_note_rh, rh_staff.time_signature, self.compression_level, force_all_starts=self.octave_mark_every_measure, key_changes=rh_key_changes)
                lh_slice_strs, best_prev_lh = render_measure_slice(lh_staff.measures, idx, 1, prev_note_lh, lh_staff.time_signature, self.compression_level, force_all_starts=self.octave_mark_every_measure, key_changes=lh_key_changes)
                m_num = self._display_measure_number(rh_staff.measures, idx)
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

    def _build_piano_line_from_strings(
        self, measure_num: int, measure_strs: list[str], is_right: bool, show_number: bool = True,
    ) -> str:
        num_str = "".join(_INT_TO_LITERARY_DIGIT[int(d)] for d in str(measure_num))
        if self.show_measure_numbers and show_number:
            prefix = num_str + '⠀'
        elif self.show_measure_numbers and not show_number:
            # BANA §29.8: in a keyboard-accompaniment-with-outline layout,
            # "the marginal measure number is placed in [the outline] line
            # instead of in the right-hand line" -- both hands still need
            # blank padding of the width the number would otherwise have
            # taken, so their content stays aligned under the outline's.
            prefix = '⠀' * (len(num_str) + 1)
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
            return '⠀' * len(prefix) + hand_sign + music_str

    def _build_outline_line_from_strings(self, measure_num: int, measure_strs: list[str]) -> str:
        """BANA §29.8: the solo-outline line above the right hand, marked
        with the bare solo-outline indicator (⠜, "treated as a hand sign")
        and carrying the measure number that would otherwise sit on the
        right-hand line."""
        if self.show_measure_numbers:
            num_str = "".join(_INT_TO_LITERARY_DIGIT[int(d)] for d in str(measure_num))
            prefix = num_str + '⠀'
        else:
            prefix = ""

        hand_sign = '⠜'
        music_str = "".join(measure_strs)
        if music_str:
            first_cell = music_str[0]
            if (ord(first_cell) - 0x2800) & 0x07 != 0:
                hand_sign += '⠄'

        return prefix + hand_sign + music_str

    def _render_ensemble(
        self,
        score: Score,
        rest_only_grid: list[list[bool]],
        measure_repeat_originals: dict[tuple[int, int], list],
    ) -> str:
        lines = []
        # Title
        if score.title:
            lines.append(center_line(encode_literary_braille(score.title), self.line_width))

        # Instrument list. BANA 33.2: instrument names take no trailing
        # period (unlike the title line above, which does) -- strip the
        # one `encode_literary_braille` always appends, exactly one
        # trailing character (not `.rstrip('⠲')`: the digit '4' encodes
        # to that same dots-2,5,6 cell, so an instrument name that
        # actually ends in "4" -- e.g. "Horn 4" -- would lose that digit
        # too). The abbreviation column is "left-aligned beginning two
        # cells beyond the last cell of the longest of the names",
        # computed here from this score's actual instrument list, not a
        # fixed width.
        name_brls = [encode_literary_braille(staff.name)[:-1] for staff in score.staves]
        max_name_len = max((len(n) for n in name_brls), default=0)
        blank_cell = chr(0x2800)
        for staff, name_brl in zip(score.staves, name_brls):
            abbrev = staff_abbreviation(staff.name)

            # BANA 33.2(d): "Two or more dot-5 guide dots are inserted to
            # fill out the width of a column when an instrument name ends
            # three or more cells before the end of the longest name. One
            # space separates the end of the name and the beginning of
            # the guide dots." A smaller deficit (1-2 cells) is plain
            # blank fill instead -- not "two or more" guide dots' worth --
            # but the abbreviation column still lands in the same place
            # either way.
            deficit = max_name_len - len(name_brl)
            if deficit >= 3:
                padding = blank_cell + '⠐' * (deficit - 1)
            else:
                padding = blank_cell * deficit

            abbrev_brl = '⠜' + abbrev_to_brl(abbrev) + '⠄'
            lines.append(name_brl + padding + '⠀⠀' + abbrev_brl)

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
            lines.append('⠀' * 7 + sig_line)

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
                # Mid-piece key changes are not wired in for ensemble
                # rendering (key_changes omitted, so no key_signature_change
                # is ever passed) -- BANA Par. 33.4.1's per-part differing-
                # key-signature header rule is explicitly out of scope for
                # S11-3 and left to its own follow-up ticket (Sprint 11's
                # notes); wiring only the "all parts change together" case
                # here without that rule would be inconsistent with
                # whatever that ticket ends up designing for the header.
                slice_strs, tmp_prev = render_measure_slice(
                    staff.measures, idx, group_size, prev_notes[s_idx], staff.time_signature, self.compression_level,
                    force_all_starts=self.octave_mark_every_measure,
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
            # BANA 33.4.3: "Very obvious measure or part-measure repeats
            # may be used when they occur on the same braille line as the
            # original passage." `_compress_measure_repeats` ran before
            # line-breaking was known, so any measure it compressed purely
            # on musical identity must be restored to its real content
            # here if it's about to start a new system -- its "original"
            # is, by construction, always in the previously-committed
            # system, i.e. a different braille line (the very first
            # system, idx == 0, has no earlier line to violate this).
            if idx > 0:
                for s_idx, staff in enumerate(score.staves):
                    original = measure_repeat_originals.get((s_idx, idx))
                    if original is not None:
                        staff.measures[idx].notes = original

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
                heading_chars = ['⠀'] * self.line_width
                # BANA 33.4.6: the marking is "indented one cell beyond
                # the first music signs of the parallel" -- one column
                # past wherever each measure's own (now cross-staff
                # aligned) content starts, not directly above it.
                col = max_prefix_len + 1
                for k in range(fit_size):
                    m = score.staves[0].measures[idx + k]
                    num_str = "⠼" + "".join(_INT_TO_LITERARY_DIGIT[int(d)] for d in str(self._display_measure_number(score.staves[0].measures, idx + k)))
                    for char_idx, char in enumerate(num_str):
                        if col + char_idx < self.line_width:
                            heading_chars[col + char_idx] = char
                    if k < len(measure_widths):
                        col += measure_widths[k]
                heading_line = "".join(heading_chars).rstrip('⠀')
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

    def _compress_measure_repeats(
        self, score: Score, skip_staff_indices: frozenset[int] = frozenset(),
    ) -> dict[tuple[int, int], list]:
        """Replace runs of `self.min_repeated_measures` or more consecutive
        musically-identical measures with `MeasureRepeat` signs (every
        member but the run's first). Returns a `(staff_index,
        measure_index) -> original notes` map for every measure this
        compresses, so a later layout pass (`_render_ensemble`, per BANA
        33.4.3) can restore a measure's real content if it turns out to
        start a new braille line -- this pass runs before line-breaking is
        known, so it can't make that call itself.

        `skip_staff_indices` excludes staves that must keep every measure's
        real notes regardless of repetition -- e.g. a solo-with-
        accompaniment score's lyric-bearing solo staff (BANA §29.8/S11c-9):
        a measure-repeat sign has no discrete notes for lyrics to align
        against, so it must never replace a texted staff's measure even
        when the melody repeats verbatim (a very common case, since the
        words usually differ each time)."""
        from dottednotes.models.measure_repeat import MeasureRepeat
        from dottednotes.models.in_accord import InAccord

        original_notes: dict[tuple[int, int], list] = {}
        if self.full_measure_repeat == "off":
            return original_notes

        def is_whole_measure_rest(measure: Measure) -> bool:
            return (
                len(measure.notes) == 1
                and isinstance(measure.notes[0], Rest)
                and measure.notes[0].is_full_measure
            )

        def has_in_accord(measure: Measure) -> bool:
            return any(isinstance(item, InAccord) for item in measure.notes)

        def can_repeat(measure: Measure) -> bool:
            # BANA Par. 18.2: "It is never, however, used to represent a
            # full measure of rest; the measure rest sign must be used" --
            # never collapse a whole-measure rest into a repeat sign, even
            # when it repeats an identical whole-measure rest.
            if is_whole_measure_rest(measure):
                return False
            # "single-voice" mode: an in-accord (multi-voice) measure never
            # participates in a repeat run at all.
            if self.full_measure_repeat == "single-voice" and has_in_accord(measure):
                return False
            return True

        for staff_idx, staff in enumerate(score.staves):
            if staff_idx in skip_staff_indices:
                continue
            measures = staff.measures
            n = len(measures)
            i = 0
            while i < n:
                if not can_repeat(measures[i]):
                    i += 1
                    continue
                j = i + 1
                while j < n and can_repeat(measures[j]) and measures[j].musical_equals(measures[i]):
                    j += 1
                if j - i >= self.min_repeated_measures:
                    for k in range(i + 1, j):
                        original_notes[(staff_idx, k)] = measures[k].notes
                        measures[k].notes = [MeasureRepeat(count=1, line=1)]
                i = j
        return original_notes

    def _compress_multi_measure_rests(self, staff: Staff) -> None:
        """BANA Music Braille Code 2015, Par. 5.3: 2 or more consecutive
        whole-measure rests always braille as one compact sign
        (`Rest.to_braille()` branches on `multi_measure_count`), never one
        whole-rest cell per measure -- mandatory transcription, not an
        optional `compression_level`/`full_measure_repeat`-style shorthand,
        so this always runs regardless of those settings. Confirmed with a
        real-world repro (S11c-7): a 78-measure rest run in an extracted
        orchestral part braille'd as 78 individual `⠍` cells instead of
        BANA's `78m` count sign.

        Mutates `staff.measures` in place, REMOVING the run's later
        measures rather than keeping one list slot per real measure (unlike
        `_compress_measure_repeats` above, which always keeps every slot --
        a measure-repeat sign still occupies its own one measure, while
        BANA's compact rest sign genuinely collapses N real measures into
        one rendered unit with one margin number). `_display_measure_number`
        accounts for the resulting shorter list in "auto" numbering mode via
        `_measure_span`.

        Only ever called (from `render()`) when `score` has exactly one
        staff -- covering both a plain SINGLE_LINE score and a single-staff
        ENSEMBLE layout (S10d-13, an extracted orchestral part that still
        needs BANA 33.4.2's "read upward" convention -- exactly the
        real-world repro this ticket confirmed, a Piccolo/Flutes I/II part
        with both a long rest run and ensemble-resolved interval chords).
        A *multi*-staff PIANO/ENSEMBLE score is deliberately left alone:
        `_render_piano`/`_render_ensemble` walk several staves in lockstep
        by shared measure index (e.g. `rh_staff.measures[idx]`/
        `lh_staff.measures[idx]`, or `score.staves[0].measures` as the
        authority for every staff's system boundaries) -- removing
        measures from just one staff's list would desync that alignment
        for every other staff. Compacting a rest run that one staff shares
        with real content in a piano/ensemble partner staff needs its own
        design (rendering the compact sign across a multi-measure-wide
        column span without shortening any staff's list), not attempted
        here -- filed as a follow-up.
        """
        def is_mergeable(m: Measure) -> bool:
            return (
                len(m.notes) == 1
                and isinstance(m.notes[0], Rest)
                and m.notes[0].is_full_measure
                and m.notes[0].pedal_sustain is None
                and not m.text_markings
                and not m.ending_numbers
            )

        measures = staff.measures
        n = len(measures)
        merged: list[Measure] = []
        i = 0
        while i < n:
            run: list[Measure] = []
            j = i
            while j < n:
                m = measures[j]
                if not is_mergeable(m):
                    break
                if run and m.notes[0].duration != run[0].notes[0].duration:
                    break
                # A key change mid-run must not be silently absorbed into
                # the compact rest sign (S11-3) -- same shape as the
                # duration-break check above and Staff.to_lilypond()'s
                # equivalent guard.
                if run and m.key_signature != run[0].key_signature:
                    break
                run.append(m)
                if m.bar_line_type != 'measure_separator':
                    # A special bar line (repeat/double bar) mid-run still
                    # needs its own sign after the compact rest content --
                    # keep it as the run's last member, then stop (mirrors
                    # Staff.to_lilypond()'s equivalent lookahead pass).
                    j += 1
                    break
                j += 1

            if len(run) >= 2:
                first_rest = run[0].notes[0]
                last = run[-1]
                compressed_rest = Rest(
                    dots=first_rest.dots,
                    category=first_rest.category,
                    raw_brl=first_rest.raw_brl,
                    duration=first_rest.duration,
                    is_full_measure=True,
                    multi_measure_count=len(run),
                )
                merged.append(Measure(
                    number=run[0].number,
                    notes=[compressed_rest],
                    time_signature=run[0].time_signature,
                    key_signature=run[0].key_signature,
                    key_signature_mode=run[0].key_signature_mode,
                    clef=run[0].clef,
                    bar_line_type=last.bar_line_type,
                    bar_line_fermata=last.bar_line_fermata,
                    line=run[0].line,
                ))
                i = j
            elif run:
                merged.append(run[0])
                i = j
            else:
                merged.append(measures[i])
                i += 1

        staff.measures = merged
