"""Parses a BANA Sec. 27 instrumental lead sheet (S8b-5): a single melody
line paired with a chord-symbol line beneath it (a "two-line parallel"),
alternating per segment -- BANA 27.1: "a two-line parallel is used, and the
chord symbols are brailled in a line below the music line...Every two-line
parallel must begin a new segment."

Scope: this module assumes an optional leading header line (key signature
and/or time signature, no notes -- BANA's usual instrumental-header
convention, matching the plain-solo-score header handled by
`BrailleParser`), followed by strict alternation (melody, chords, melody,
chords, ...) of a single (non-ensemble, non-chorded) melody staff --
`BrailleParseError` is raised for anything else rather than guessing. There
is no unambiguous structural marker (unlike the ensemble format's §33.2
instrument-list header) to detect a lead sheet from raw content alone, so
callers must invoke this explicitly -- `dottednotes convert` does so via
`--category "Lead Sheet"` (see `cli.py`'s `_parse_score()`).
"""

from __future__ import annotations

from ..bana_symbols import SymbolCategory
from ..exceptions import BrailleParseError
from ..models.chord_names import ChordNamesTrack
from ..models.chord_symbol import ChordSymbol
from ..models.duration import Duration
from ..models.note import Note, Rest
from ..models.score import Score
from .braille_parser import BrailleParser
from .chord_symbol_parser import parse_chord_symbol_line
from .tokenizer import BrailleTokenizer


_HEADER_ONLY_CATEGORIES = frozenset({
    SymbolCategory.KEY_SIGNATURE,
    SymbolCategory.TIME_SIGNATURE,
    SymbolCategory.CLEF,
})


def _is_header_line(line: str) -> bool:
    """True if `line` is a BANA instrumental header: key/time signature
    (and/or clef) cells only, no notes -- so it precedes the melody/chord
    alternation rather than being the first melody line."""
    if not line.strip():
        return False
    tokens = BrailleTokenizer().tokenize(line)
    # Leading/trailing blank cells tokenize as BAR_LINE (they're spacing, not
    # a real bar line -- see bana_symbols.py's comment on '⠀'); ignore those
    # when checking whether the rest of the line is header-only content.
    content_tokens = [tok for tok in tokens if tok.character != '⠀']
    return bool(content_tokens) and all(
        tok.category in _HEADER_ONLY_CATEGORIES for tok in content_tokens
    )


def parse_lead_sheet(text: str) -> Score:
    """Parse a BANA Sec. 27 lead sheet into a Score with `chord_names` set."""
    lines = text.split('\n')
    while lines and lines[-1] == '':
        lines.pop()

    header_lines: list[str] = []
    while lines and _is_header_line(lines[0]):
        header_lines.append(lines.pop(0))

    if len(lines) % 2 != 0 or not lines:
        raise BrailleParseError(
            "Lead sheet input must be an optional header line followed by "
            "pairs of (melody line, chord-symbol line) per BANA Sec. 27.1; "
            f"got {len(lines)} non-trailing-blank line(s) after the header."
        )

    music_lines = lines[0::2]
    chord_lines = lines[1::2]

    music_text = '\n'.join(header_lines + music_lines)
    tokens = BrailleTokenizer().tokenize(music_text, margin_numbers_use_number_sign=True)
    score = BrailleParser(tokens=tokens).parse()

    if len(score.staves) != 1:
        raise BrailleParseError(
            "Lead-sheet chord symbols are only supported for a single melody "
            f"staff; parsed {len(score.staves)}."
        )
    staff = score.staves[0]

    # within-line column offsets, since BrailleToken.position is an absolute
    # index into the whole (multi-line) music_text, not a per-line column.
    # tok.line counts physical lines of music_text (header lines included),
    # so note_positions' line numbers are shifted back down to the logical
    # (header-excluded) melody-line index used by `chord_lines` below.
    header_count = len(header_lines)
    line_start: dict[int, int] = {}
    offset = sum(len(h) + 1 for h in header_lines)  # +1 per '\n' joiner
    for idx, music_line in enumerate(music_lines, start=1):
        line_start[header_count + idx] = offset
        offset += len(music_line) + 1

    # A note's "first cell" (BANA 27.1's alignment point for the chord
    # symbol below it) is its own cell, or -- when present -- the earliest
    # of any octave-mark/accidental cells immediately preceding it on the
    # same line, since those are part of the note's compound braille symbol,
    # not separate content a chord could be aligned to.
    _PREFIX_CATEGORIES = (SymbolCategory.OCTAVE_MARK, SymbolCategory.ACCIDENTAL)
    note_positions: list[tuple[int, int]] = []
    for idx, tok in enumerate(tokens):
        if tok.category not in (SymbolCategory.NOTE, SymbolCategory.REST):
            continue
        first_cell = tok.position
        j = idx - 1
        while j >= 0 and tokens[j].line == tok.line and tokens[j].category in _PREFIX_CATEGORIES:
            first_cell = tokens[j].position
            j -= 1
        note_positions.append((tok.line - header_count, first_cell - line_start[tok.line]))

    flat_notes: list[Note | Rest] = []
    for measure in staff.measures:
        for item in measure.notes:
            if not isinstance(item, (Note, Rest)):
                raise BrailleParseError(
                    "Lead-sheet chord-symbol alignment does not yet support "
                    f"{type(item).__name__} (measure {measure.number}) -- only "
                    "plain notes and rests."
                )
            flat_notes.append(item)

    if len(flat_notes) != len(note_positions):
        raise BrailleParseError(
            "Internal error aligning chord symbols: melody note/rest count "
            f"({len(flat_notes)}) does not match tokenized NOTE/REST count "
            f"({len(note_positions)})."
        )

    chord_for_note_index: dict[int, ChordSymbol] = {}
    for music_line_no, chord_line in enumerate(chord_lines, start=1):
        line_note_indices = [
            gi for gi, (ln, _) in enumerate(note_positions) if ln == music_line_no
        ]
        for col, chord in parse_chord_symbol_line(chord_line):
            candidates = [gi for gi in line_note_indices if note_positions[gi][1] <= col]
            if not candidates:
                raise BrailleParseError(
                    f"Chord symbol at column {col} on chord-symbol line "
                    f"{music_line_no} does not align with any note/rest on its "
                    "paired melody line (BANA 27.1)."
                )
            chord_for_note_index[max(candidates)] = chord

    if flat_notes and not chord_for_note_index:
        raise BrailleParseError(
            "Lead sheet has notes/rests but no chord symbols at all "
            "(BANA 27.1 requires at least one)."
        )
    # Note 0 itself may have no coincident chord -- e.g. a pickup/anacrusis
    # note before the lead sheet's first chord symbol -- in which case
    # ChordNamesTrack.to_lilypond() renders it as a spacer rest.

    entries: list[tuple[Duration, ChordSymbol | None]] = [
        (note.duration, chord_for_note_index.get(gi))
        for gi, note in enumerate(flat_notes)
    ]
    score.chord_names = ChordNamesTrack(entries=entries)
    return score
