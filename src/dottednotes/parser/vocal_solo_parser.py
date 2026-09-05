"""Parses a BANA §35.1 solo-vocal line-by-line score: lyrics and melody
paired one parallel at a time, the words beginning at the margin (cell 1)
and the corresponding music in the third cell of the following line (cell
3), with run-over lines of either indented to cell 5 -- §35.1: "Instrumental
accompaniments are not included in the transcription and are brailled
separately, as described in Par. 29.8." §35.1.2: "No part identifier is
necessary."

Scope: this module assumes the input is already isolated to a single vocal
part's §35.1 content (an optional cell-9 tempo/signature header, the same
convention plain solo scores use, followed by alternating word-line/
music-line parallels) -- callers must invoke this explicitly, the same way
`parse_lead_sheet` is (there is no unambiguous structural marker to detect
this format from raw content the way §33.2's instrument-list header
detects an ensemble score).
"""

from __future__ import annotations

from ..bana_symbols import LITERARY_DIGITS
from ..exceptions import BrailleParseError
from ..models.score import Score
from .braille_parser import BrailleParser
from .ensemble_parser import (
    group_pitched_elements_by_slur, map_syllables_to_groups, parse_lyrics, extract_stage_directions,
)
from .lead_sheet_parser import _is_header_line
from .tokenizer import BrailleTokenizer

_MUSIC_LINE_INDENT = '⠀⠀'      # cell 3 (2 blank cells)
_RUNOVER_INDENT = '⠀⠀⠀⠀'      # cell 5 (4 blank cells)

# BrailleParser's own plain-solo-format convention (S11c-2 rule 7): main
# music lines start in cell 1, run-over lines are indented to cell 3. A
# vocal music line's own first line (cell 3 here) is remapped to cell 1 for
# BrailleParser; a vocal run-over continuation (cell 5 here) is remapped to
# BrailleParser's own cell-3 run-over indent -- so BrailleParser sees
# exactly the shape it already expects and treats the continuation as a
# continuation, not a fresh measure-line start (which would wrongly force
# another octave mark, per §35.1.2's "first note of every music line
# requires an octave mark" -- that must fire once per parallel, not once
# per physical line of a wrapped one).
_BRAILLE_PARSER_RUNOVER_INDENT = '⠀⠀'

# BANA 1.11's music hyphen (dot 5): `wrap_run_over_line()` appends this to
# the last cell that fits before a run-over, to mark that the line was
# interrupted mid-content. A wrapped *word* line's continuation must be
# glued back on with no space (it's a break inside one line's content, not
# a new word), unlike a genuine word-line-to-word-line boundary.
_CONTINUATION_MARKER = '⠐'


def _strip_leading_measure_number(line: str) -> str:
    """Strip a real BANA §35.9/§35.10 measure number (bare literary
    digits, no word signs, immediately followed by a blank cell) from the
    start of a fresh word line. Only called when the caller has opted in
    via `has_measure_numbers=True` -- otherwise a short lyric word like
    "A" or "I" immediately followed by a space at the start of a line
    would be ambiguous with a single-digit measure number, and this
    module has no way to tell them apart from content alone."""
    i = 0
    n = len(line)
    while i < n and line[i] in LITERARY_DIGITS:
        i += 1
    if i > 0 and i < n and line[i] == '⠀':
        return line[i + 1:]
    return line


def parse_vocal_solo(text: str, has_measure_numbers: bool = False) -> Score:
    """Parse BANA §35.1 solo-vocal content into a `Score` with one staff,
    `staff.lyrics` populated from the word lines.

    `has_measure_numbers` (§35.9/§35.10, S11c-16): set when the source is
    known to place a real measure number at the start of some word lines
    -- the caller must know this from context (e.g. it asked
    `BrailleRenderer` to render with `vocal_measure_number_every` set),
    since the content alone can't safely distinguish a measure number from
    a short lyric word at the start of a line (see
    `_strip_leading_measure_number`)."""
    lines = text.split('\n')
    while lines and lines[-1] == '':
        lines.pop()

    header_lines: list[str] = []
    while lines and _is_header_line(lines[0]):
        header_lines.append(lines.pop(0))

    music_lines: list[str] = []
    lyric_parts: list[str] = []
    glue_next_word_chunk = False

    def add_word_chunk(content: str) -> None:
        nonlocal glue_next_word_chunk
        will_glue = content.endswith(_CONTINUATION_MARKER)
        if will_glue:
            content = content[:-1]
        if lyric_parts and not glue_next_word_chunk:
            lyric_parts.append('⠀')
        lyric_parts.append(content)
        glue_next_word_chunk = will_glue

    # None until the first word/music line of a parallel is seen; 'word' or
    # 'music' thereafter, so a cell-5 continuation is routed to whichever
    # line it's continuing (word lines and music lines can each run over
    # independently -- §35.1.3: "almost never in both within the same
    # parallel", but nothing here depends on that being true).
    current: str | None = None
    for line in lines:
        if not line.strip('⠀'):
            continue
        if line.startswith(_RUNOVER_INDENT):
            content = line[len(_RUNOVER_INDENT):]
            if current == 'word':
                add_word_chunk(content)
            elif current == 'music':
                # BrailleParser already understands its own cell-3 run-over
                # convention (including the music-hyphen marker), so the
                # content is passed through unchanged, just re-indented.
                music_lines.append(_BRAILLE_PARSER_RUNOVER_INDENT + content)
            else:
                raise BrailleParseError(
                    "Vocal solo input has a cell-5 run-over line before any "
                    "word or music line has started a parallel."
                )
        elif line.startswith(_MUSIC_LINE_INDENT):
            music_lines.append(line[len(_MUSIC_LINE_INDENT):])
            current = 'music'
        else:
            add_word_chunk(_strip_leading_measure_number(line) if has_measure_numbers else line)
            current = 'word'

    if not music_lines:
        raise BrailleParseError(
            "Vocal solo input has no music line (cell 3) -- expected "
            "alternating word-line/music-line parallels per BANA §35.1."
        )

    music_text = '\n'.join(header_lines + music_lines)
    tokens = BrailleTokenizer().tokenize(music_text)
    score = BrailleParser(tokens=tokens).parse()

    if len(score.staves) != 1:
        raise BrailleParseError(
            f"Vocal solo parsing expected a single staff, got {len(score.staves)}."
        )
    staff = score.staves[0]

    lyric_text = ''.join(lyric_parts)
    lyric_text, stage_directions = extract_stage_directions(lyric_text)
    syllables = parse_lyrics(lyric_text) if lyric_text.strip('⠀') else []
    groups = group_pitched_elements_by_slur(staff.measures)
    staff.lyrics = map_syllables_to_groups(syllables, groups, staff.name or "Vocal solo")
    staff.stage_directions = stage_directions

    return score
