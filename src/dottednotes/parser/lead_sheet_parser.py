"""Parses a BANA Sec. 27 instrumental lead sheet (S8b-5): a single melody
line paired with a chord-symbol line beneath it (a "two-line parallel"),
alternating per segment -- BANA 27.1: "a two-line parallel is used, and the
chord symbols are brailled in a line below the music line...Every two-line
parallel must begin a new segment."

Scope: this module assumes strict alternation starting at physical line 0
(melody, chords, melody, chords, ...) with no header lines above the first
melody line, and a single (non-ensemble, non-chorded) melody staff --
`BrailleParseError` is raised for anything else rather than guessing. Wiring
this into the CLI's format auto-detection (`dottednotes convert`) is a
follow-up; there is no unambiguous structural marker (unlike the ensemble
format's §33.2 instrument-list header) to detect a lead sheet from raw
content alone, so callers must invoke `parse_lead_sheet()` explicitly.
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


def parse_lead_sheet(text: str) -> Score:
    """Parse a BANA Sec. 27 lead sheet into a Score with `chord_names` set."""
    lines = text.split('\n')
    while lines and lines[-1] == '':
        lines.pop()
    if len(lines) % 2 != 0 or not lines:
        raise BrailleParseError(
            "Lead sheet input must be pairs of (melody line, chord-symbol "
            f"line) per BANA Sec. 27.1; got {len(lines)} non-trailing-blank line(s)."
        )

    music_lines = lines[0::2]
    chord_lines = lines[1::2]

    music_text = '\n'.join(music_lines)
    tokens = BrailleTokenizer().tokenize(music_text)
    score = BrailleParser(tokens=tokens).parse()

    if len(score.staves) != 1:
        raise BrailleParseError(
            "Lead-sheet chord symbols are only supported for a single melody "
            f"staff; parsed {len(score.staves)}."
        )
    staff = score.staves[0]

    # within-line column offsets, since BrailleToken.position is an absolute
    # index into the whole (multi-line) music_text, not a per-line column.
    line_start: dict[int, int] = {}
    offset = 0
    for idx, music_line in enumerate(music_lines, start=1):
        line_start[idx] = offset
        offset += len(music_line) + 1  # +1 for the '\n' joiner

    note_positions: list[tuple[int, int]] = [
        (tok.line, tok.position - line_start[tok.line])
        for tok in tokens
        if tok.category in (SymbolCategory.NOTE, SymbolCategory.REST)
    ]

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

    if flat_notes and 0 not in chord_for_note_index:
        raise BrailleParseError(
            "Lead sheet's first note/rest has no coincident chord symbol "
            "(BANA 27.1 requires a symbol at or before the first note)."
        )

    entries: list[tuple[Duration, ChordSymbol | None]] = [
        (note.duration, chord_for_note_index.get(gi))
        for gi, note in enumerate(flat_notes)
    ]
    score.chord_names = ChordNamesTrack(entries=entries)
    return score
