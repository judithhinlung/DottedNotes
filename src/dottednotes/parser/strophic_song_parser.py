"""Parses a BANA solo vocal strophic song (Secs. 35.1, 35.7, 35.7.2, and 36):
verse 1 given in full as repeating (lyric line, optional chord line, melody
line) groups -- BANA 35.1: "the words begin at the margin and the
corresponding music in the third cell of the following line" -- optionally
followed by a refrain (introduced by the literal word "REFRAIN" or "CHORUS",
BANA 35.7.2), and then any further verses (2, 3, ...) as lyrics-only
overflow blocks after the music, each introduced at the margin by its verse
number between literary parentheses (BANA 35.7: `"<#b">`, `"<#c">`, ...).

Scope: unlike BANA 36's general chord-with-lyrics format, chords are
optional per group here (BANA 35's solo-song format doesn't require them at
all; 36 layers them on top) -- a group with no chord line simply has no
`ChordSymbol` for that stretch of melody. Overflow verses (2+) never carry
their own melody or chords (BANA 35.7: "only the first one is written with
the chords and melody"); a bare "REFRAIN"/"CHORUS" line inside an overflow
verse reuses the already-parsed refrain lyric syllables rather than
re-parsing new content (BANA 35.7.2). There is no unambiguous structural
marker (unlike the ensemble format's Sec. 33.2 instrument-list header) to
detect this format from raw content alone, so callers must invoke it
explicitly -- `dottednotes convert` does so via `--category "Strophic Song"`
(see `cli.py`'s `_parse_score()`).
"""

from __future__ import annotations

from dataclasses import dataclass

from ..bana_symbols import LITERARY_DIGITS, NUMBER_SIGN, SymbolCategory
from ..exceptions import BrailleParseError
from ..models.chord_names import ChordNamesTrack
from ..models.chord_symbol import ChordSymbol
from ..models.duration import Duration
from ..models.note import Note, Rest
from ..models.score import Score
from .braille_parser import BrailleParser
from .chord_symbol_parser import parse_chord_symbol_line
from .ensemble_parser import extract_stanza_prefix, parse_lyrics
from .input_pipeline import ASCII_TO_DOTS
from .tokenizer import BrailleTokenizer

# BANA 35.7's verse-number marker: literary open-parenthesis (ASCII '"<'),
# NUMBER_SIGN, one or more lower-cell digit-letters, literary close-
# parenthesis (ASCII '">') -- e.g. `"<#b">` for verse 2. Built from
# ASCII_TO_DOTS rather than hardcoded so it stays in sync with that table.
_VERSE_PAREN_OPEN = ''.join(chr(0x2800 + ASCII_TO_DOTS[c]) for c in '"<')
_VERSE_PAREN_CLOSE = ''.join(chr(0x2800 + ASCII_TO_DOTS[c]) for c in '">')

_HEADER_ONLY_CATEGORIES = frozenset({
    SymbolCategory.KEY_SIGNATURE,
    SymbolCategory.TIME_SIGNATURE,
    SymbolCategory.CLEF,
})


def _is_header_line(line: str) -> bool:
    """True if `line` is a header line: key/time signature (and/or clef)
    cells only, no notes -- same convention as lead_sheet_parser.py."""
    if not line.strip():
        return False
    tokens = BrailleTokenizer().tokenize(line)
    content_tokens = [tok for tok in tokens if tok.character != '⠀']
    return bool(content_tokens) and all(
        tok.category in _HEADER_ONLY_CATEGORIES for tok in content_tokens
    )


def _indent(line: str) -> int:
    """Number of leading blank cells (BANA's braille "cells" == columns).
    Line role in the main block is decided by this, per BANA 35.1: the
    lyric/chord lines sit at the margin (cell 1, indent 0), the melody
    line at cell 3 (indent 2), and a run-over of either at cell 5 (indent
    4). A run-over's own content can't reliably distinguish it from
    melody -- it's often mid-word/mid-sentence text with no
    CAPITAL_INDICATOR of its own, which tokenizes indistinguishably from
    stray music cells (S8b-14) -- so indentation is the only robust
    signal here, not content-sniffing."""
    return len(line) - len(line.lstrip('⠀'))


def _try_parse_chord_line(line: str) -> list[tuple[int, ChordSymbol]] | None:
    """Return (column, ChordSymbol) pairs if `line` (stripped of leading
    blank cells) parses entirely as BANA chord symbols, else None (it's
    lyric text instead)."""
    stripped = line.lstrip('⠀')
    if not stripped:
        return None
    try:
        result = parse_chord_symbol_line(stripped)
    except BrailleParseError:
        return None
    return result or None


def _verse_marker(line: str) -> tuple[int, str] | None:
    """If `line` starts with a BANA 35.7 verse-number marker (`"<#b">` for
    verse 2, etc.), return (verse_number, rest_of_line_after_marker).
    Otherwise None."""
    if not line.startswith(_VERSE_PAREN_OPEN + NUMBER_SIGN):
        return None
    i = len(_VERSE_PAREN_OPEN) + 1
    digits = ''
    while i < len(line) and line[i] in LITERARY_DIGITS:
        digits += str(LITERARY_DIGITS[line[i]])
        i += 1
    if not digits or not line[i:].startswith(_VERSE_PAREN_CLOSE):
        return None
    verse_num = int(digits)
    rest = line[i + len(_VERSE_PAREN_CLOSE):]
    return verse_num, rest.lstrip('⠀')


def _refrain_label(syllables: list[tuple[str, bool]]) -> tuple[str | None, list[tuple[str, bool]]]:
    """Wraps extract_stanza_prefix to detect a leading "REFRAIN"/"CHORUS"
    word (BANA 35.7.2). Returns (label, remaining_syllables); label is None
    if `syllables` doesn't start with one of those words."""
    prefix, remaining = extract_stanza_prefix(syllables)
    if prefix is not None and prefix.rstrip('.').lower() in ('refrain', 'chorus'):
        return prefix, remaining
    return None, syllables


def _strip_trailing_refrain_marker(
    syllables: list[tuple[str, bool]]
) -> tuple[bool, list[tuple[str, bool]]]:
    """An overflow verse's bare trailing "REFRAIN"/"CHORUS" (BANA 35.7.2:
    "the text of the refrain is not restated but is supplanted by the word
    'Refrain' ... again") sits at the *end* of that verse's lyric text, not
    the start -- unlike the main block's refrain marker (see
    _refrain_label), which introduces a whole new system. Returns
    (found, syllables_with_marker_removed)."""
    if not syllables:
        return False, syllables
    last_word, has_hyphen = syllables[-1]
    if has_hyphen:
        return False, syllables
    cleaned = last_word.strip('.:,;()[]').lower()
    if cleaned in ('refrain', 'chorus', 'ref', 'cho'):
        return True, syllables[:-1]
    return False, syllables


@dataclass
class _Group:
    """One (lyric, optional chord, melody) unit within verse 1 or the
    refrain."""
    lyric_text: str = ''
    first_lyric_line: str = ''
    chord_line: str | None = None
    melody_line: str = ''


def _word_start_columns(line: str) -> list[int]:
    """Column (0-based) where each blank-cell-separated word starts in
    `line` -- used to match a chord symbol's column to the word it's
    aligned under (BANA 36.3)."""
    cols = []
    in_word = False
    for i, ch in enumerate(line):
        if ch != '⠀' and not in_word:
            cols.append(i)
            in_word = True
        elif ch == '⠀':
            in_word = False
    return cols


def _split_lines(text: str) -> list[str]:
    lines = text.split('\n')
    while lines and lines[-1] == '':
        lines.pop()
    return lines


def _group_notes_by_slur(notes: list[Note | Rest]) -> list[list[Note | Rest]]:
    """Group notes into syllable slots: a syllabic slur (BANA 35.2) groups
    several notes under one syllable; every other note/rest is its own slot."""
    result: list[list[Note | Rest]] = []
    current: list[Note | Rest] = []
    in_slur = False
    for note in notes:
        if isinstance(note, Rest):
            if current:
                result.append(current)
                current = []
            in_slur = False
            result.append([note])
            continue
        if getattr(note, 'slur_start', False):
            current = [note]
            in_slur = True
        elif in_slur:
            current.append(note)
            if getattr(note, 'slur_end', False):
                result.append(current)
                current = []
                in_slur = False
        else:
            result.append([note])
    if current:
        result.append(current)
    return result


def _map_syllables(syllables: list[tuple[str, bool]], note_group_count: int) -> list[str]:
    """Pair syllables 1:1 with note-groups in order (BANA 35.1), appending
    ' --' for a syllable that continues via a syllabic slur/hyphen."""
    n = min(len(syllables), note_group_count)
    mapped = []
    for idx in range(n):
        syl, has_hyphen = syllables[idx]
        mapped.append(syl + ' --' if has_hyphen else syl)
    return mapped


def parse_strophic_song(text: str) -> Score:
    """Parse a BANA solo vocal strophic song (Secs. 35.1/35.7/35.7.2/36)
    into a Score with a single melody staff (lyrics/verses/verse_prefixes
    set) and, if any chord lines were present, `chord_names` set too."""
    lines = _split_lines(text)

    header_lines: list[str] = []
    while lines and _is_header_line(lines[0]):
        header_lines.append(lines.pop(0))

    # -- Pass 1: split into the main block (verse 1 + refrain groups, in
    # the order they're written) and the overflow-verse blocks that follow.
    main_lines: list[str] = []
    overflow_lines: list[str] = []
    in_overflow = False
    for line in lines:
        if not in_overflow and _verse_marker(line) is not None:
            in_overflow = True
        (overflow_lines if in_overflow else main_lines).append(line)

    # -- Pass 2: walk the main block, building (lyric, chord?, melody)
    # groups. A run of consecutive non-melody, non-chord lines is lyric
    # text for one group (joined -- a run-over continuation, BANA 35.1.3).
    groups: list[_Group] = []
    refrain_starts_at: int | None = None
    i = 0
    while i < len(main_lines):
        line = main_lines[i]
        if not line.strip():
            i += 1
            continue
        lyric_parts = [line]
        i += 1
        # A run-over of the lyric line (BANA 35.1: "beginning in cell 5")
        # continues the same lyric text -- distinguished from the group's
        # chord line (cell 1/margin, indent 0) purely by indentation, since
        # a run-over line often lacks its own CAPITAL_INDICATOR to mark it
        # as literary text (it's mid-word/mid-sentence), so its *content*
        # alone can't be told apart from stray music-shaped cells (S8b-14).
        while i < len(main_lines) and _indent(main_lines[i]) >= 4:
            lyric_parts.append(main_lines[i])
            i += 1
        lyric_text = ' '.join(lyric_parts)

        if refrain_starts_at is None:
            label, _ = _refrain_label(parse_lyrics(lyric_text))
            if label is not None:
                refrain_starts_at = len(groups)

        # The melody line always sits at cell 3 (indent 2, BANA 35.1); a
        # line at the margin (indent 0) here can only be the group's
        # (optional) chord line.
        chord_line: str | None = None
        if i < len(main_lines) and _indent(main_lines[i]) == 0:
            if _try_parse_chord_line(main_lines[i]) is None:
                raise BrailleParseError(
                    "Strophic song: line at the margin (indent 0) after the "
                    f"lyric text at input line {i} does not parse as BANA "
                    "chord symbols (Sec. 36.1) and isn't a new lyric/verse "
                    "line either."
                )
            chord_line = main_lines[i]
            i += 1

        if i >= len(main_lines) or _indent(main_lines[i]) != 2:
            raise BrailleParseError(
                "Strophic song: expected a melody line at cell 3 (BANA "
                "35.1: 'the corresponding music in the third cell of the "
                f"following line') after the lyric/chord group ending at "
                f"input line {i}."
            )
        melody_line = main_lines[i]
        i += 1

        groups.append(_Group(
            lyric_text=lyric_text,
            first_lyric_line=lyric_parts[0],
            chord_line=chord_line,
            melody_line=melody_line,
        ))

    if not groups:
        raise BrailleParseError("Strophic song input has no (lyric, melody) groups to parse.")
    if refrain_starts_at is None:
        refrain_starts_at = len(groups)

    # -- Build the melody staff by feeding header + every group's melody
    # line through the ordinary solo parser, exactly like lead_sheet_parser
    # does -- this reuses all of its measure/duration/slur resolution.
    melody_lines = [g.melody_line for g in groups]
    music_text = '\n'.join(header_lines + melody_lines)
    tokens = BrailleTokenizer().tokenize(music_text)
    score = BrailleParser(tokens=tokens).parse()
    if len(score.staves) != 1:
        raise BrailleParseError(
            "Strophic song is only supported for a single melody staff; "
            f"parsed {len(score.staves)}."
        )
    staff = score.staves[0]

    # -- Chord alignment: unlike a plain BANA 27 lead sheet (where the
    # chord line sits directly beneath the melody, both flush with the
    # margin, so chord and melody columns are directly comparable), Sec.
    # 36.1 places the chord line in relation to the *lyric* line above it
    # ("the chord symbols... are placed in relation to the syllables of
    # the words"), while the melody is placed independently at cell 3 "in
    # relation to the lyrics as directed in Sec. 35" (i.e. paired with
    # them 1:1 in order, not by column). So a chord's column is matched
    # against the group's own (first) lyric line's word-start columns to
    # get a word index, and that index is used to pick the note-group
    # (BANA 35.1's syllable/note pairing) at the same position within
    # that group's own melody -- not compared to the melody's column
    # directly. This approximates word-level alignment; it doesn't yet
    # implement Sec. 36.3's finer before/with/during/after-syllable
    # sub-word positioning (S8b-15 follow-up).
    header_count = len(header_lines)
    line_of_token: dict[int, int] = {}
    tok_idx_by_line: dict[int, list[int]] = {}
    for idx, tok in enumerate(tokens):
        if tok.category in (SymbolCategory.NOTE, SymbolCategory.REST):
            tok_idx_by_line.setdefault(tok.line, []).append(idx)

    flat_notes: list[Note | Rest] = []
    note_line_no: list[int] = []  # 1-indexed group number for each flat_notes entry
    for measure in staff.measures:
        for item in measure.notes:
            if not isinstance(item, (Note, Rest)):
                raise BrailleParseError(
                    "Strophic song chord alignment does not yet support "
                    f"{type(item).__name__} (measure {measure.number}) -- only "
                    "plain notes and rests."
                )
            flat_notes.append(item)

    note_lines = sorted(tok_idx_by_line.keys())
    if len(note_lines) != len(groups):
        raise BrailleParseError(
            "Internal error aligning chord symbols: found notes/rests on "
            f"{len(note_lines)} melody line(s) but parsed {len(groups)} group(s)."
        )
    flat_i = 0
    per_group_notes: list[list[Note | Rest]] = []
    for line_no in note_lines:
        count = len(tok_idx_by_line[line_no])
        per_group_notes.append(flat_notes[flat_i:flat_i + count])
        for _ in range(count):
            note_line_no.append(line_no)
        flat_i += count
    if flat_i != len(flat_notes):
        raise BrailleParseError(
            "Internal error aligning chord symbols: melody note/rest count "
            f"({len(flat_notes)}) does not match tokenized NOTE/REST count ({flat_i})."
        )

    group_start_index: list[int] = []
    running = 0
    for notes in per_group_notes:
        group_start_index.append(running)
        running += len(notes)

    chord_for_note_index: dict[int, ChordSymbol] = {}
    any_chords = False
    for gi, group in enumerate(groups):
        if group.chord_line is None:
            continue
        any_chords = True
        # Use only the group's first physical lyric line for column
        # matching -- a run-over continuation is a different physical
        # line the chord line was never drawn against.
        note_groups = _group_notes_by_slur(per_group_notes[gi])
        word_columns = _word_start_columns(group.first_lyric_line)
        if gi == refrain_starts_at:
            # This group's first word is the "REFRAIN"/"CHORUS" label
            # itself (BANA 35.7.2), not a sung syllable -- it isn't paired
            # with a note-group at all, so exclude it from column matching.
            # The chord line has no such label prefix of its own (chord
            # lines never carry structural labels), so its column 0 lines
            # up with the *label-free* lyric content's start, not with the
            # lyric line's raw column 0 -- shift the remaining word columns
            # down by the label's width so both lines share a zero-based
            # frame.
            label, _ = _refrain_label(parse_lyrics(group.lyric_text))
            if label is not None and len(word_columns) > 1:
                label_width = word_columns[1]
                word_columns = [wc - label_width for wc in word_columns[1:]]
        stripped_chord_line = group.chord_line.lstrip('⠀')
        col_shift = len(group.chord_line) - len(stripped_chord_line)
        for col, chord in parse_chord_symbol_line(stripped_chord_line):
            col += col_shift
            word_index = sum(1 for wc in word_columns if wc <= col) - 1
            word_index = max(0, min(word_index, len(note_groups) - 1))
            target_note = note_groups[word_index][0]
            chord_for_note_index[group_start_index[gi] + per_group_notes[gi].index(target_note)] = chord

    if any_chords:
        entries: list[tuple[Duration, ChordSymbol | None]] = [
            (note.duration, chord_for_note_index.get(gi))
            for gi, note in enumerate(flat_notes)
        ]
        score.chord_names = ChordNamesTrack(entries=entries)

    # -- Split flat_notes (and their note-groups) at the verse1/refrain
    # boundary, using each group's own already-partitioned notes
    # (per_group_notes) to know exactly where that boundary falls.
    verse1_notes = [n for grp in per_group_notes[:refrain_starts_at] for n in grp]
    refrain_notes = [n for grp in per_group_notes[refrain_starts_at:] for n in grp]
    verse1_note_groups = _group_notes_by_slur(verse1_notes)
    refrain_note_groups = _group_notes_by_slur(refrain_notes)

    verse1_syllables = parse_lyrics(' '.join(g.lyric_text for g in groups[:refrain_starts_at]))
    refrain_lyric_text = ' '.join(g.lyric_text for g in groups[refrain_starts_at:])
    refrain_syllables = parse_lyrics(refrain_lyric_text)
    if refrain_starts_at < len(groups):
        _, refrain_syllables = _refrain_label(refrain_syllables)

    mapped_refrain = (
        _map_syllables(refrain_syllables, len(refrain_note_groups)) if refrain_notes else []
    )

    verses: list[list[str]] = [
        _map_syllables(verse1_syllables, len(verse1_note_groups)) + mapped_refrain
    ]
    verse_prefixes: list[str | None] = [None]

    # -- Overflow verses (2+, BANA 35.7): lyrics only, reusing verse 1's
    # melody entirely -- a bare "REFRAIN"/"CHORUS" line reuses the already-
    # mapped refrain syllables rather than being re-parsed.
    idx = 0
    while idx < len(overflow_lines):
        marker = _verse_marker(overflow_lines[idx])
        if marker is None:
            raise BrailleParseError(
                f"Strophic song: expected a verse-number marker (BANA 35.7, "
                f'e.g. `"<#b">`) at overflow line {idx}.'
            )
        verse_num, first_rest = marker
        idx += 1
        text_parts = [first_rest] if first_rest.strip() else []
        while idx < len(overflow_lines) and _verse_marker(overflow_lines[idx]) is None:
            if overflow_lines[idx].strip():
                text_parts.append(overflow_lines[idx])
            idx += 1

        own_syllables = parse_lyrics(' '.join(text_parts))
        reuses_refrain, own_syllables = _strip_trailing_refrain_marker(own_syllables)
        mapped_own = _map_syllables(own_syllables, len(verse1_note_groups))
        verse_text = mapped_own + (mapped_refrain if reuses_refrain else [])
        verses.append(verse_text)
        verse_prefixes.append(f"{verse_num}.")

    staff.lyrics = verses[0]
    staff.verses = verses
    staff.verse_prefixes = verse_prefixes
    return score
