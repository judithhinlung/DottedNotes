"""Parses the BANA §29.8 keyboard-accompaniment block of a solo-with-
accompaniment score: right-hand (⠨⠜) and optional left-hand (⠸⠜) lines,
each measure group optionally preceded by a solo-outline line (⠐⠜ -- dots
5, 3-4-5, "treated as a hand sign", per Music Braille Code 2015 Example
29.8-2). The solo block, parsed separately (see `vocal_solo_parser.py`),
already carries the authoritative pitch data the outline echoes in
stripped-down form (no dynamics, slurs, word-sign expressions, or lyrics
-- see `braille_renderer.build_solo_outline_measures()`), so nothing is
lost by not re-parsing the outline's own content here; only its margin
measure number is kept (BANA §29.8: "The marginal measure number is
placed in this line instead of in the right-hand line").

Per §29.3(b)/(h), a single right-hand/left-hand line pair can hold more
than one measure's worth of music ("the procedure continues until there
is not room in both lines for a complete measure"), and §29.3.1/29.3.2
describe a measure dividing across that line boundary (or a run-over
line, when it can't be divided), marked by a trailing music-hyphen (dot
5) as the last sign of the line in each part -- the measure simply
continues on that same hand's next line, no new bar line in between.

That rules out concatenating right- and left-hand content into one
token stream in document order (right-hand line, then its left-hand
line, then the next group's right-hand line, ...) and letting
`BrailleParser`'s inline hand-sign switching multiplex between them:
`BrailleParser` has no way to know a hand's trailing unbarred notes
should keep accumulating through the *other* hand's entire intervening
line rather than merging with whatever that other hand writes next --
which is exactly what happened before this module split the two hands
into their own independent streams (right-hand lines concatenated in
order across every group, left-hand lines concatenated separately), each
parsed as its own single-hand piece. A hand's own trailing content then
naturally glues onto that same hand's next line with nothing in between,
and `BrailleParser`'s existing margin-number cross-check
(`_handle_measure_number`) still applies per hand, since each group's
margin number (extracted from its outline line, or already on its own
right-hand line when there's no outline) is carried onto that hand's
first line in the flattened stream.

A group can legitimately have no right-hand line at all (the right hand
rests for that stretch) -- `_fill_missing_measures_with_rests` backfills
a whole-measure rest for any measure number the other hand has that this
one doesn't, so both staves end up the same length. This is a parser-
level accommodation for real data gaps, not a transcription convention;
callers that care should treat a backfilled rest as something to flag to
the transcriber, not as confirmed musical content.
"""

from __future__ import annotations

from ..bana_symbols import LITERARY_DIGITS, SymbolCategory
from ..exceptions import BrailleParseError
from ..models.measure import Measure
from ..models.note import Rest
from ..models.score import Score
from ..models.staff import Staff
from ..models.time_signature import TimeSignature
from .braille_parser import BrailleParser
from .lead_sheet_parser import _is_header_line
from .tokenizer import BrailleTokenizer

_RIGHT_HAND_SIGN = '⠨⠜'
_LEFT_HAND_SIGN = '⠸⠜'
_OUTLINE_SIGN = '⠐⠜'


def _margin_number_prefix(line: str) -> str:
    """Return just the leading literary-digit margin number of `line`
    (e.g. '⠃' for margin "B", 2), or '' if it has none. Unlike
    `_strip_margin_prefix`, this does not consume the line's own leading
    blank cells or the blank cell that follows the number -- only the
    digit run itself, so the caller can splice it onto a different line."""
    i, n = 0, len(line)
    while i < n and line[i] == '⠀':
        i += 1
    start = i
    while i < n and line[i] in LITERARY_DIGITS:
        i += 1
    return line[start:i]


def _strip_margin_prefix(line: str) -> str:
    """Strip a line's leading blank cells and/or literary-digit measure
    number (with its trailing blank cell), matching the fixed-width
    prefixes `braille_renderer.py`'s accompaniment-with-outline layout
    functions produce, so the hand-sign/outline marker that follows can be
    checked without the margin column in the way."""
    i, n = 0, len(line)
    while i < n and line[i] == '⠀':
        i += 1
    while i < n and line[i] in LITERARY_DIGITS:
        i += 1
    if i < n and line[i] == '⠀':
        i += 1
    return line[i:]


class _Group:
    __slots__ = ("margin_number", "rh_lines", "lh_lines")

    def __init__(self) -> None:
        self.margin_number = ''
        self.rh_lines: list[str] = []
        self.lh_lines: list[str] = []


def _split_into_groups(lines: list[str]) -> list[_Group]:
    """Split `lines` (header already removed) into §29.3/29.8 parallel
    groups: each an optional outline line (margin number only, rest
    discarded), followed by 0+ right-hand lines and 0+ left-hand lines."""
    groups: list[_Group] = []
    i, n = 0, len(lines)
    while i < n:
        line = lines[i]
        if not line.strip('⠀'):
            i += 1
            continue
        content = _strip_margin_prefix(line)
        group = _Group()
        if content.startswith(_OUTLINE_SIGN):
            group.margin_number = _margin_number_prefix(line)
            i += 1
        elif content.startswith(_RIGHT_HAND_SIGN):
            group.margin_number = _margin_number_prefix(line)
            group.rh_lines.append(content)
            i += 1
        elif content.startswith(_LEFT_HAND_SIGN):
            # A group with no right hand at all (the right hand rests for
            # this group) -- still a valid shape, see module docstring.
            pass
        else:
            raise BrailleParseError(
                "Keyboard accompaniment line does not start with a "
                "right-hand (⠨⠜), left-hand (⠸⠜), or solo-outline (⠐⠜) sign "
                "after its margin: " + repr(line)
            )
        while i < n and _strip_margin_prefix(lines[i]).startswith(_RIGHT_HAND_SIGN):
            group.rh_lines.append(_strip_margin_prefix(lines[i]))
            i += 1
        while i < n and _strip_margin_prefix(lines[i]).startswith(_LEFT_HAND_SIGN):
            group.lh_lines.append(_strip_margin_prefix(lines[i]))
            i += 1
        if not group.rh_lines and not group.lh_lines:
            raise BrailleParseError(
                "Keyboard accompaniment: solo-outline line at margin "
                f"{group.margin_number!r} is followed by neither a "
                "right-hand nor a left-hand line."
            )
        groups.append(group)
    return groups


def _hand_text(header_lines: list[str], groups: list[_Group], attr: str, carry_margin_number: bool) -> str:
    """Flatten every group's lines for one hand (`attr` is 'rh_lines' or
    'lh_lines') into a single continuous stream, in document order, so a
    measure divided across groups (§29.3.1) glues onto this same hand's
    very next line, with no content from the other hand in between.
    `carry_margin_number` prefixes each group's margin number onto that
    group's first line for this hand -- only ever true for the right
    hand: BANA always places the margin number on the outline line (or,
    with no outline, the right-hand line itself), never on the left-hand
    line (§29.3(d)/(e)), so the left hand has no number of its own to
    cross-check against and must rely purely on its own bar-line count."""
    text_lines: list[str] = []
    for group in groups:
        hand_lines: list[str] = getattr(group, attr)
        if not hand_lines:
            continue
        first, *rest = hand_lines
        if carry_margin_number and group.margin_number:
            first = group.margin_number + '⠀' + first
        text_lines.append(first)
        text_lines.extend(rest)
    if not text_lines:
        return ''
    return '\n'.join(header_lines + text_lines)


def _fill_missing_measures_with_rests(staff: Staff, reference: Staff) -> list[int]:
    """Insert a whole-measure rest into `staff` for every measure number
    present in `reference` but missing from `staff`, so both end up the
    same length. Returns the list of measure numbers that were
    backfilled this way, so the caller can report them rather than treat
    them as confirmed content."""
    existing = {m.number for m in staff.measures}
    missing = [m.number for m in reference.measures if m.number not in existing]
    if not missing:
        return []

    by_number = {m.number: m for m in reference.measures}
    for number in missing:
        ref_measure = by_number[number]
        numerator, denominator = ref_measure.time_signature or (
            (staff.time_signature.numerator, staff.time_signature.denominator)
            if staff.time_signature else (4, 4)
        )
        full_measure_duration = TimeSignature(
            dots=frozenset(), category=None, raw_brl='',
            numerator=numerator, denominator=denominator,
        ).get_full_measure_duration()
        rest = Rest(
            dots=frozenset(), category=None, raw_brl='',
            duration=full_measure_duration, is_full_measure=True,
        )
        measure = Measure(
            number=number,
            key_signature=ref_measure.key_signature,
            time_signature=ref_measure.time_signature,
        )
        measure.add_note(rest)
        staff.measures.append(measure)
    staff.measures.sort(key=lambda m: m.number)
    return missing


def _parse_single_hand(text: str, staff_name: str) -> Staff:
    """Parse one hand's already-isolated stream as a plain single-staff
    piece. The hand-sign token is dropped before parsing: once the two
    hands are split into independent streams, nothing needs it to decide
    which staff a measure belongs to -- and `BrailleParser`'s own
    left-hand measure-numbering (`_next_measure_number_for`) only ever
    mirrors a right-hand staff parsed in the *same* pass, so letting a
    left-hand sign set `_current_hand` here would leave its counter stuck
    forever, never mirroring anything (see module docstring)."""
    tokens = [
        t for t in BrailleTokenizer().tokenize(text)
        if t.category != SymbolCategory.HAND_SIGN
    ]
    score = BrailleParser(tokens=tokens).parse()
    if len(score.staves) != 1:
        raise BrailleParseError(
            f"Keyboard accompaniment {staff_name} parsing expected a single "
            f"staff, got {len(score.staves)}."
        )
    staff = score.staves[0]
    staff.name = staff_name
    return staff


def parse_keyboard_accompaniment(text: str) -> Score:
    """Parse a §29.8 keyboard-accompaniment block into a `Score` with 1
    staff (right hand only) or 2 (right hand, then left hand)."""
    lines = text.split('\n')
    while lines and lines[-1] == '':
        lines.pop()

    header_lines: list[str] = []
    while lines and _is_header_line(lines[0]):
        header_lines.append(lines.pop(0))

    groups = _split_into_groups(lines)

    rh_text = _hand_text(header_lines, groups, 'rh_lines', carry_margin_number=True)
    lh_text = _hand_text(header_lines, groups, 'lh_lines', carry_margin_number=False)

    if not rh_text and not lh_text:
        raise BrailleParseError(
            "Keyboard accompaniment input has no right-/left-hand content "
            "(⠨⠜/⠸⠜) -- only solo-outline lines or blanks."
        )

    rh_staff = _parse_single_hand(rh_text, "right hand") if rh_text else None
    lh_staff = _parse_single_hand(lh_text, "left hand") if lh_text else None

    if rh_staff is not None and lh_staff is not None:
        _fill_missing_measures_with_rests(rh_staff, lh_staff)
        _fill_missing_measures_with_rests(lh_staff, rh_staff)

    score = Score()
    for staff in (rh_staff, lh_staff):
        if staff is not None:
            score.add_staff(staff)

    if len(score.staves) not in (1, 2):
        raise BrailleParseError(
            f"Keyboard accompaniment parsing expected 1 or 2 staves, got {len(score.staves)}."
        )
    return score
