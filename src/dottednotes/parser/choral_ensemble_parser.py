"""Parses a BANA §37.1 "Expanded Bar-over-Bar Format" vocal ensemble: word
lines (cell 1, run-overs at cell 5) for every voice given first, followed
by that parallel's music lines (cell 3, run-overs at cell 5) -- never
interleaved per voice the way the §33 ensemble format is. §37.1(f):
"Each word line and each music line ... is introduced with the appropriate
identifier" -- this module always expects (and the renderer always emits)
that identifier, matching this codebase's existing "always restate"
simplification for §33 abbreviations (BANA's "need not be restated" wording
is permissive, not mandatory).

Scope: this module assumes every voice is active in every parallel --
BANA §37.1(c)'s tacet-voice omission (a voice's music simply absent from a
parallel) is not yet supported on the parse side; a mismatched final
measure count across voices raises rather than silently misaligning them.
See TICKETS.md for the follow-up ticket. §37.2's shared single word line
(no identifier at all) is not yet recognized either -- every word line
here must carry its voice's identifier (§37.3's per-voice shape).
"""

from __future__ import annotations

from ..exceptions import BrailleParseError
from ..models.orchestra_score import OrchestraScore
from ..models.score import Score
from .braille_parser import BrailleParser
from .ensemble_parser import group_pitched_elements_by_slur, map_syllables_to_groups, parse_lyrics
from .input_pipeline import decode_literary_braille
from .lead_sheet_parser import _is_header_line
from .tokenizer import BrailleTokenizer

_MUSIC_LINE_INDENT = '⠀⠀'      # cell 3 (2 blank cells)
_RUNOVER_INDENT = '⠀⠀⠀⠀'      # cell 5 (4 blank cells)
_BRAILLE_PARSER_RUNOVER_INDENT = '⠀⠀'  # BrailleParser's own cell-3 run-over convention
_CONTINUATION_MARKER = '⠐'    # BANA 1.11 music hyphen, appended by wrap_run_over_line


def _split_leading_identifier(line: str) -> tuple[str, str]:
    """Split a §37 word/music line into (lowercase voice abbreviation,
    content after the identifier's dot-3 terminator)."""
    if not line.startswith('⠜'):
        raise BrailleParseError(
            f"Expected a BANA §37 voice identifier (⠜...⠄) at the start of: {line!r}"
        )
    i = 1
    while i < len(line) and line[i] != '⠄':
        i += 1
    if i >= len(line):
        raise BrailleParseError(
            f"§37 voice identifier has no terminating dot-3 (⠄): {line!r}"
        )
    abbrev = "".join(decode_literary_braille(c) for c in line[1:i]).lower()
    return abbrev, line[i + 1:]


def parse_choral_ensemble(text: str) -> Score:
    """Parse BANA §37.1 choral-ensemble content into a `Score` with one
    staff per voice, `staff.lyrics` populated from that voice's word
    lines."""
    lines = text.split('\n')
    while lines and lines[-1] == '':
        lines.pop()

    header_lines: list[str] = []
    while lines and _is_header_line(lines[0]):
        header_lines.append(lines.pop(0))

    word_by_voice: dict[str, list[str]] = {}
    music_by_voice: dict[str, list[str]] = {}
    voice_order: list[str] = []
    glue_next: dict[str, bool] = {}

    def ensure_voice(abbrev: str) -> None:
        if abbrev not in word_by_voice:
            word_by_voice[abbrev] = []
            music_by_voice[abbrev] = []
            voice_order.append(abbrev)
            glue_next[abbrev] = False

    current_kind: str | None = None
    current_abbrev: str | None = None

    def add_word_chunk(abbrev: str, content: str, is_continuation: bool) -> None:
        will_glue = content.endswith(_CONTINUATION_MARKER)
        if will_glue:
            content = content[:-1]
        lst = word_by_voice[abbrev]
        glued_to_previous = is_continuation and glue_next[abbrev]
        if lst and not glued_to_previous:
            lst.append('⠀')
        lst.append(content)
        glue_next[abbrev] = will_glue

    for line in lines:
        if not line.strip('⠀'):
            continue
        if line.startswith(_RUNOVER_INDENT):
            content = line[len(_RUNOVER_INDENT):]
            if current_kind is None or current_abbrev is None:
                raise BrailleParseError(
                    "Choral ensemble input has a cell-5 run-over line "
                    "before any word or music line has started."
                )
            if current_kind == 'word':
                add_word_chunk(current_abbrev, content, is_continuation=True)
            else:
                music_by_voice[current_abbrev].append(_BRAILLE_PARSER_RUNOVER_INDENT + content)
        elif line.startswith(_MUSIC_LINE_INDENT):
            abbrev, remaining = _split_leading_identifier(line[len(_MUSIC_LINE_INDENT):])
            ensure_voice(abbrev)
            music_by_voice[abbrev].append(remaining)
            current_kind, current_abbrev = 'music', abbrev
        else:
            abbrev, remaining = _split_leading_identifier(line)
            ensure_voice(abbrev)
            if remaining.startswith('⠀'):
                remaining = remaining[1:]
            add_word_chunk(abbrev, remaining, is_continuation=False)
            current_kind, current_abbrev = 'word', abbrev

    if not music_by_voice:
        raise BrailleParseError(
            "Choral ensemble input has no music lines (cell 3) -- expected "
            "word-line/music-line parallels per BANA §37.1."
        )

    staves = []
    for abbrev in voice_order:
        music_text = '\n'.join(header_lines + music_by_voice[abbrev])
        tokens = BrailleTokenizer().tokenize(music_text)
        voice_score = BrailleParser(tokens=tokens).parse()
        if len(voice_score.staves) != 1:
            raise BrailleParseError(
                f"Choral ensemble voice '{abbrev}' expected a single staff, "
                f"got {len(voice_score.staves)}."
            )
        staff = voice_score.staves[0]

        word_text = ''.join(word_by_voice[abbrev])
        syllables = parse_lyrics(word_text) if word_text.strip('⠀') else []
        groups = group_pitched_elements_by_slur(staff.measures)
        staff.lyrics = map_syllables_to_groups(syllables, groups, abbrev)
        staves.append(staff)

    measure_counts = {len(s.measures) for s in staves}
    if len(measure_counts) > 1:
        counts_by_voice = {abbrev: len(s.measures) for abbrev, s in zip(voice_order, staves)}
        raise BrailleParseError(
            "Choral ensemble voices have mismatched measure counts "
            f"({counts_by_voice}) -- a mid-piece tacet-voice omission "
            "(BANA §37.1(c)) is not yet supported by this parser."
        )

    score = OrchestraScore()
    for staff in staves:
        score.add_staff(staff)
    return score
