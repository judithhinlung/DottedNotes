"""Parses a BANA Sec. 23/27 (Table 23) lead-sheet chord-symbol line (S8b-5).

Scope: this module only decodes one physical line of already-normalized
Unicode braille containing chord symbols (e.g. the second line of a BANA
Sec. 27 two-line lead-sheet parallel) into ordered (column, ChordSymbol)
pairs. Aligning those columns to melody notes and building a ChordNamesTrack
is done by lead_sheet_parser.py, which is the only intended caller.

Every dot pattern and compositional rule used here is cross-checked against
the BANA manual's own Chart 23.1-1 worked examples -- see the module
docstring in bana_symbols.py for the worked derivations. Anything not
demonstrated by that chart (e.g. CHORD_TRIANGLE_BISECT_CELL) is rejected
with a clear error rather than guessed.
"""

from __future__ import annotations

from ..bana_symbols import (
    ACCIDENTAL_CELLS,
    CAPITAL_INDICATOR,
    CHORD_AUGMENTED_OR_RAISE_CELL,
    CHORD_BISECT_CELL,
    CHORD_DIMINISHED_CELL,
    CHORD_LOWER_CELL,
    CHORD_PAREN_CELL,
    CHORD_SLASH_CELL,
    CHORD_TRIANGLE_CELL,
    LITERARY_DIGITS,
    NUMBER_SIGN,
)
from ..exceptions import BrailleParseError
from ..models.chord_symbol import ChordSymbol
from .input_pipeline import decode_literary_braille

_BLANK_CELL = '⠀'
_ALTERATION_FROM_ACCIDENTAL = {'sharp': '+', 'flat': '-'}
_ROOT_LETTERS = set('abcdefg')


def _is_letter_cell(cell: str) -> bool:
    return decode_literary_braille(cell).isalpha()


def _read_number(line: str, i: int) -> tuple[int, int]:
    """`line[i]` must be NUMBER_SIGN. Returns (value, new_index)."""
    i += 1
    digits = ''
    while i < len(line) and line[i] in LITERARY_DIGITS:
        digits += str(LITERARY_DIGITS[line[i]])
        i += 1
    if not digits:
        raise BrailleParseError(
            f"Column {i}: NUMBER_SIGN in a chord symbol is not followed by a digit."
        )
    return int(digits), i


def _read_word(line: str, i: int) -> tuple[str, int]:
    start = i
    while i < len(line) and _is_letter_cell(line[i]):
        i += 1
    return decode_literary_braille(line[start:i]), i


def _read_root(line: str, i: int) -> tuple[str, str | None, int]:
    """`line[i]` must be a root letter cell (A-G). Returns (letter, accidental, new_index)."""
    letter = decode_literary_braille(line[i])
    if letter not in _ROOT_LETTERS:
        raise BrailleParseError(
            f"Column {i}: chord symbol root '{letter}' is not a note letter A-G."
        )
    i += 1
    accidental = None
    if i < len(line) and line[i] in ACCIDENTAL_CELLS:
        accidental = ACCIDENTAL_CELLS[line[i]]
        i += 1
    return letter.upper(), accidental, i


def _parse_symbol(line: str, i: int) -> tuple[ChordSymbol, int]:
    """`line[i]` must be CAPITAL_INDICATOR. Returns (ChordSymbol, new_index)."""
    doubled = line[i + 1:i + 2] == CAPITAL_INDICATOR
    i += 2 if doubled else 1

    if doubled:
        word, i = _read_word(line, i)
        if word == 'nc':
            return ChordSymbol(no_chord=True), i
        raise BrailleParseError(
            f"Column {i}: unrecognized whole-word-capital chord indication '{word}' "
            "(only NC/N.C. is defined, Par. 23.2)."
        )

    # Tacet is a single-capital whole-word indication, not a root+quality chord.
    tacet_word, after_word = _read_word(line, i)
    if tacet_word == 'tacet':
        return ChordSymbol(tacet=True), after_word

    root, accidental, i = _read_root(line, i)
    chord = ChordSymbol(root=root, accidental=accidental)
    pending_alteration: str | None = None

    while i < len(line) and line[i] not in (_BLANK_CELL, CAPITAL_INDICATOR):
        cell = line[i]

        if _is_letter_cell(cell):
            word, i = _read_word(line, i)
            if word in ('m', 'min'):
                chord.is_minor = True
            elif word == 'dim':
                chord.is_diminished = True
            elif word == 'maj':
                chord.has_explicit_maj = True
            elif word == 'aug':
                chord.is_augmented = True
            elif word == 'sus':
                if i + 1 < len(line) and line[i] == NUMBER_SIGN and line[i + 1] in LITERARY_DIGITS:
                    value, i = _read_number(line, i)
                    if value not in (2, 4):
                        raise BrailleParseError(f"Column {i}: 'sus{value}' is not sus2 or sus4.")
                    chord.suspended = value
                else:
                    chord.suspended = 4  # bare "sus" defaults to sus4 (common convention)
            else:
                raise BrailleParseError(
                    f"Column {i}: unrecognized chord-quality word '{word}' -- not one of "
                    "m/min, dim, maj, aug, sus (Sec. 23.1.1)."
                )
            continue

        if cell == NUMBER_SIGN:
            value, i = _read_number(line, i)
            chord.extensions.append((value, pending_alteration))
            pending_alteration = None
            continue

        if cell in ACCIDENTAL_CELLS:
            pending_alteration = _ALTERATION_FROM_ACCIDENTAL.get(ACCIDENTAL_CELLS[cell])
            if pending_alteration is None:
                raise BrailleParseError(
                    f"Column {i}: a 'natural' sign mid-chord-symbol has no defined "
                    "meaning here (Table 23 only demonstrates sharp/flat before an "
                    "extension digit)."
                )
            i += 1
            continue

        if cell == CHORD_AUGMENTED_OR_RAISE_CELL:
            if i + 1 < len(line) and line[i + 1] == NUMBER_SIGN:
                pending_alteration = '+'
                i += 1
            else:
                chord.is_augmented = True
                i += 1
            continue

        if cell == CHORD_LOWER_CELL:
            if i + 1 < len(line) and line[i + 1] == NUMBER_SIGN:
                pending_alteration = '-'
                i += 1
            else:
                raise BrailleParseError(
                    f"Column {i}: a standalone minus sign (not before a NUMBER_SIGN "
                    "extension) is not demonstrated anywhere in Chart 23.1-1 -- ask "
                    "the developer to confirm its meaning before parsing it."
                )
            continue

        if cell == CHORD_DIMINISHED_CELL:
            if i + 1 < len(line) and line[i + 1] == CHORD_BISECT_CELL:
                chord.is_half_diminished = True
                i += 2
            else:
                chord.is_diminished = True
                i += 1
            continue

        if cell == CHORD_TRIANGLE_CELL:
            if i + 1 < len(line) and line[i + 1] == CHORD_BISECT_CELL:
                raise BrailleParseError(
                    f"Column {i}: triangle-bisected sign's meaning is not confirmed by "
                    "any Chart 23.1-1 example (Par. 23.1.2 warns some signs are not "
                    "standardized) -- ask the developer before parsing it."
                )
            chord.is_major7_symbol = True
            i += 1
            continue

        if cell == CHORD_PAREN_CELL:
            i += 1  # parentheses are a no-op wrapper -- BANA reuses one cell for both (Sec. 23.1)
            continue

        if cell == CHORD_SLASH_CELL:
            i += 1
            if i >= len(line) or line[i] != CAPITAL_INDICATOR:
                raise BrailleParseError(
                    f"Column {i}: expected a capital-indicated bass note after the "
                    "slash (Par. 23.1.3)."
                )
            i += 1
            bass_letter, bass_accidental, i = _read_root(line, i)
            chord.bass_note = (bass_letter, bass_accidental)
            break  # bass note is always the final element of a chord symbol

        raise BrailleParseError(f"Column {i}: unrecognized cell in chord symbol.")

    return chord, i


def parse_chord_symbol_line(line: str) -> list[tuple[int, ChordSymbol]]:
    """Parse one BANA Sec. 27 chord-symbol line into (column, ChordSymbol) pairs,
    in left-to-right (i.e. chronological) order. `column` is the 0-based
    index of the symbol's initial CAPITAL_INDICATOR, for alignment against
    the coincident melody note/rest (BANA 27.1).
    """
    results: list[tuple[int, ChordSymbol]] = []
    i = 0
    while i < len(line):
        if line[i] == CAPITAL_INDICATOR:
            start = i
            chord, i = _parse_symbol(line, i)
            results.append((start, chord))
        else:
            i += 1
    return results
