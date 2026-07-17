"""Parses a BANA §33.2 "List of Instruments" header (S5b-1).

Scope: this module only decodes the two-column instrument-list block itself
(name column + abbreviation column) into InstrumentInfo entries. Callers are
responsible for isolating that block from the title line above it and the
tempo/music content below it — see parse_instrument_list()'s docstring.
Wiring this into the full Score/Staff pipeline (removing the two-staff
ceiling) is out of scope here; that's S5b-7.
"""

from __future__ import annotations

import warnings

from ..bana_symbols import (
    CAPITAL_INDICATOR,
    END_WORD_SIGN,
    LOWER_DIGIT_CELLS,
    LITERARY_DIGITS,
    TABLE_29_ENGLISH,
    WORD_SIGN,
)
from ..models.instrument import InstrumentInfo
from .input_pipeline import decode_literary_braille

# Guide-dot fill cell (§33.2(d)): dots 5, the same cell as OCTAVE_MARKS[4].
# Only ever read as a guide dot within an instrument-list name column, never
# as an octave mark — that context is guaranteed by the caller isolating the
# header block before this module ever sees the text.
_GUIDE_DOT: str = '⠐'

_BLANK_CELL: str = '⠀'


def _decode_name_column(cells: str) -> str:
    """Decode a §33.2 name-column segment into display text.

    Single CAPITAL_INDICATOR capitalizes only the next letter (standard UEB);
    doubled CAPITAL_INDICATOR capitalizes the rest of the current word
    (§33.2.2 Example: ",,II" -> "II"). Guide-dot fill cells are dropped.
    """
    out: list[str] = []
    i = 0
    whole_word_capital = False
    capitalize_next = False
    while i < len(cells):
        c = cells[i]
        if c == CAPITAL_INDICATOR:
            if i + 1 < len(cells) and cells[i + 1] == CAPITAL_INDICATOR:
                whole_word_capital = True
                i += 2
            else:
                capitalize_next = True
                i += 1
            continue
        if c == _GUIDE_DOT:
            i += 1
            continue
        if c == _BLANK_CELL:
            out.append(' ')
            whole_word_capital = False
            capitalize_next = False
            i += 1
            continue
        letter = decode_literary_braille(c)
        if letter.isalpha() and (capitalize_next or whole_word_capital):
            letter = letter.upper()
            capitalize_next = False
        out.append(letter)
        i += 1
    return ''.join(out).strip()


def _decode_abbreviation(cells: str) -> tuple[str, str | None, str | None]:
    """Decode a §33.2.1/33.2.2 abbreviation segment (between WORD_SIGN and
    END_WORD_SIGN, exclusive) into (letters, part_number, sub_number)."""
    i = 0
    letters: list[str] = []
    while i < len(cells) and cells[i] not in LOWER_DIGIT_CELLS:
        letters.append(decode_literary_braille(cells[i]))
        i += 1

    part_number: str | None = None
    sub_number: str | None = None
    if i < len(cells) and cells[i] in LOWER_DIGIT_CELLS:
        part_number = str(LOWER_DIGIT_CELLS[cells[i]])
        i += 1
    if i < len(cells) and cells[i] in LITERARY_DIGITS:
        sub_number = str(LITERARY_DIGITS[cells[i]])
        i += 1

    return ''.join(letters), part_number, sub_number


def _parse_line(line: str) -> InstrumentInfo | None:
    """Parse one §33.2 header line, or return None if it doesn't contain a
    word-sign or capital-indicated abbreviation (i.e. isn't a header line)."""
    end = line.rfind(END_WORD_SIGN)
    if end == -1:
        return None

    # Scan backwards from end - 1 to find the start of the abbreviation block
    start = end
    for idx in range(end - 1, -1, -1):
        c = line[idx]
        if c == '⠀' or c == _GUIDE_DOT:
            break
        start = idx

    if start == end:
        return None

    name = _decode_name_column(line[:start])
    if not name:
        # A genuine §33.2 line always has real name-column text before its
        # abbreviation (e.g. "Piccolo, Flutes I&II" -- some real-world
        # transcriptions omit the leading WORD_SIGN cell entirely, so that
        # can't be required here). An *empty* name means the backward scan
        # never hit an earlier blank/guide-dot boundary at all -- i.e. `end`
        # just matched some other dot-3 cell with literary text running all
        # the way back to the start of the line (e.g. a literary apostrophe
        # near the start of a title, which shares END_WORD_SIGN's dot
        # pattern) -- not a real instrument line. See Children_s_piece.brf's
        # "Children's Piece" title.
        return None
    abbrev_cells = line[start:end]
    while abbrev_cells and abbrev_cells[0] in (WORD_SIGN, CAPITAL_INDICATOR):
        abbrev_cells = abbrev_cells[1:]
    if not abbrev_cells:
        return None

    abbreviation, part_number, sub_number = _decode_abbreviation(abbrev_cells)
    return InstrumentInfo(
        name=name,
        abbreviation=abbreviation,
        part_number=part_number,
        sub_number=sub_number,
    )


def parse_instrument_list(text: str) -> list[InstrumentInfo]:
    """Parse a BANA §33.2 instrument-list header into ordered entries.

    `text` must contain only the instrument-list block's lines (already
    isolated from the title line above and the tempo/music content below —
    this function does not detect that boundary itself). Lines within the
    block that don't contain a WORD_SIGN...END_WORD_SIGN abbreviation are
    skipped rather than raising, so a stray blank line is harmless.

    Each returned entry whose name is a Table 29(A) instrument has its
    abbreviation checked against the table; a mismatch produces a plain-text
    warning (not an error — a transcriber may deliberately deviate) rather
    than being silently accepted.
    """
    entries: list[InstrumentInfo] = []
    for line in text.splitlines():
        entry = _parse_line(line)
        if entry is None:
            continue
        expected = TABLE_29_ENGLISH.get(entry.name)
        if expected is not None:
            actual = entry.abbreviation + (entry.part_number or '')
            if actual != expected:
                warnings.warn(
                    f"Instrument '{entry.name}': abbreviation '{actual}' "
                    f"does not match Table 29(A)'s '{expected}'.",
                    stacklevel=2,
                )
        entries.append(entry)
    return entries


def resolve_abbreviation(name: str, overrides: dict[str, str] | None = None) -> str:
    """Return the BANA abbreviation for `name` (§33.2.1).

    Looks up Table 29(A) first, then `overrides`. Raises ValueError if
    neither has an entry — per §33.2.1, an abbreviation for an instrument
    outside Table 29 must be a deliberate 2-3 letter transcriber choice
    ("conveying an immediate suggestion of the name"), never a silent guess.
    """
    if name in TABLE_29_ENGLISH:
        return TABLE_29_ENGLISH[name]
    if overrides and name in overrides:
        return overrides[name]
    raise ValueError(
        f"No Table 29(A) abbreviation for '{name}' and none supplied via "
        "overrides. Per BANA §33.2.1, supply an explicit 2-3 letter "
        "abbreviation conveying an immediate suggestion of the name "
        "(e.g. 'glo' for glockenspiel, 'tt' for tam-tam) — it must not be "
        "invented silently."
    )
