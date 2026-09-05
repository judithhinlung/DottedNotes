"""Parses a BANA §37.1 "Expanded Bar-over-Bar Format" vocal ensemble: word
lines (cell 1, run-overs at cell 5) for every voice given first, followed
by that parallel's music lines (cell 3, run-overs at cell 5) -- never
interleaved per voice the way the §33 ensemble format is. §37.1(f):
"Each word line and each music line ... is introduced with the appropriate
identifier" -- this module always expects (and the renderer always emits)
that identifier on *music* lines, matching this codebase's existing
"always restate" simplification for §33 abbreviations (BANA's "need not be
restated" wording is permissive, not mandatory). A *word* line may instead
be a single unidentified line shared by every voice active in the
parallel (§37.2: "It is not necessary to show an identifier in the word
line") -- recognized here by the absence of a leading ⠜.

Scope: this module assumes every voice is active in every parallel --
BANA §37.1(c)'s tacet-voice omission (a voice's music simply absent from a
parallel) is not yet supported on the parse side; a mismatched final
measure count across voices raises rather than silently misaligning them.
See TICKETS.md (S11c-20) for the follow-up ticket.
"""

from __future__ import annotations

from ..exceptions import BrailleParseError
from ..models.orchestra_score import OrchestraScore
from ..models.score import Score
from .braille_parser import BrailleParser
from .ensemble_parser import (
    group_pitched_elements_by_slur, map_syllables_to_groups, parse_lyrics, extract_stage_directions,
)
from .input_pipeline import decode_literary_braille
from .instrument_list import parse_instrument_list
from .instrument_list import _parse_line as _parse_character_list_line
from .lead_sheet_parser import _is_header_line
from .tokenizer import BrailleTokenizer

_MUSIC_LINE_INDENT = '⠀⠀'      # cell 3 (2 blank cells)
_RUNOVER_INDENT = '⠀⠀⠀⠀'      # cell 5 (4 blank cells)
_BRAILLE_PARSER_RUNOVER_INDENT = '⠀⠀'  # BrailleParser's own cell-3 run-over convention
_CONTINUATION_MARKER = '⠐'    # BANA 1.11 music hyphen, appended by wrap_run_over_line


def _split_leading_identifier(line: str) -> tuple[str, str]:
    """Split a §37 identified word/music line into (lowercase voice
    abbreviation, content after the identifier's dot-3 terminator)."""
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


class _ChunkAccumulator:
    """Builds one decoded lyric-cell string from a sequence of raw braille
    chunks, gluing a chunk directly onto the previous one (no blank cell
    inserted) whenever the previous chunk ended in the run-over
    continuation marker -- otherwise inserting a blank cell between them,
    since they're separate words/phrases, not a mid-word break."""

    def __init__(self) -> None:
        self._parts: list[str] = []
        self._glue_next = False

    def add(self, content: str) -> None:
        will_glue = content.endswith(_CONTINUATION_MARKER)
        if will_glue:
            content = content[:-1]
        if self._parts and not self._glue_next:
            self._parts.append('⠀')
        self._parts.append(content)
        self._glue_next = will_glue

    def text(self) -> str:
        return ''.join(self._parts)


def parse_choral_ensemble(text: str) -> Score:
    """Parse BANA §37.1 choral-ensemble content into a `Score` with one
    staff per voice, `staff.lyrics` populated from that voice's word
    lines (shared §37.2 lines applied to every voice active in the same
    parallel, per-voice §37.3 lines applied to their own voice only)."""
    lines = text.split('\n')
    while lines and lines[-1] == '':
        lines.pop()

    # §38.2 (S11c-17): an optional "List of Characters" table at the very
    # start (name + ⠜abbrev⠄ per line, identical shape to §33.2's
    # instrument-list header) -- reused verbatim via parse_instrument_list().
    # A genuine word/music line never matches this (both start directly
    # with the ⠜ identifier, no real name text before it, which
    # _parse_line() requires).
    character_names_by_abbrev: dict[str, str] = {}
    table_lines: list[str] = []
    while lines and _parse_character_list_line(lines[0]) is not None:
        table_lines.append(lines.pop(0))
    if table_lines:
        for info in parse_instrument_list('\n'.join(table_lines)):
            character_names_by_abbrev[info.abbreviation.lower()] = info.name

    header_lines: list[str] = []
    while lines and _is_header_line(lines[0]):
        header_lines.append(lines.pop(0))

    # Pass 1: classify each physical line and split it into parallels --
    # a maximal run of word-block lines followed by a maximal run of
    # music-block lines. Continuations (cell 5) stay tagged with whichever
    # kind they continue; they don't yet know which voice they belong to.
    Entry = tuple[str, str]  # (kind, raw_content) where kind in {'word','word_cont','music','music_cont'}
    parallels: list[tuple[list[Entry], list[Entry]]] = []
    word_block: list[Entry] = []
    music_block: list[Entry] = []
    current_kind: str | None = None

    def flush_parallel() -> None:
        nonlocal word_block, music_block
        if word_block or music_block:
            parallels.append((word_block, music_block))
        word_block, music_block = [], []

    for line in lines:
        if not line.strip('⠀'):
            continue
        if line.startswith(_RUNOVER_INDENT):
            content = line[len(_RUNOVER_INDENT):]
            if current_kind is None:
                raise BrailleParseError(
                    "Choral ensemble input has a cell-5 run-over line "
                    "before any word or music line has started."
                )
            (word_block if current_kind == 'word' else music_block).append(
                (current_kind + '_cont', content)
            )
        elif line.startswith(_MUSIC_LINE_INDENT):
            music_block.append(('music', line[len(_MUSIC_LINE_INDENT):]))
            current_kind = 'music'
        else:
            if current_kind == 'music':
                flush_parallel()
            word_block.append(('word', line))
            current_kind = 'word'
    flush_parallel()

    if not any(music for _, music in parallels):
        raise BrailleParseError(
            "Choral ensemble input has no music lines (cell 3) -- expected "
            "word-line/music-line parallels per BANA §37.1."
        )

    # Pass 2: decode each parallel's music block into (voice, content)
    # entries -- this also tells us which voices are active in this
    # parallel, needed to apply a §37.2 shared word line to all of them.
    word_by_voice: dict[str, list[str]] = {}
    music_by_voice: dict[str, list[str]] = {}
    voice_order: list[str] = []
    word_accumulators: dict[str, _ChunkAccumulator] = {}

    def ensure_voice(abbrev: str) -> None:
        if abbrev not in word_by_voice:
            word_by_voice[abbrev] = []
            music_by_voice[abbrev] = []
            voice_order.append(abbrev)
            word_accumulators[abbrev] = _ChunkAccumulator()

    for word_block, music_block in parallels:
        active_voices: list[str] = []
        last_music_voice: str | None = None
        for kind, content in music_block:
            if kind == 'music':
                abbrev, remaining = _split_leading_identifier(content)
                ensure_voice(abbrev)
                if abbrev not in active_voices:
                    active_voices.append(abbrev)
                music_by_voice[abbrev].append(remaining)
                last_music_voice = abbrev
            else:  # music_cont
                if last_music_voice is None:
                    raise BrailleParseError(
                        "Choral ensemble input has a music run-over line "
                        "before any music line has started this parallel."
                    )
                music_by_voice[last_music_voice].append(_BRAILLE_PARSER_RUNOVER_INDENT + content)

        if not word_block:
            continue

        first_kind, first_content = word_block[0]
        is_shared = first_kind == 'word' and not first_content.startswith('⠜')
        if is_shared:
            # §37.2: one unidentified line (plus any of its own
            # continuations) applies to every voice active in this
            # parallel's music block.
            acc = _ChunkAccumulator()
            for kind, content in word_block:
                acc.add(content)
            shared_text = acc.text()
            for abbrev in active_voices:
                lst = word_by_voice[abbrev]
                if lst:
                    lst.append('⠀')
                lst.append(shared_text)
        else:
            last_word_voice: str | None = None
            for kind, content in word_block:
                if kind == 'word':
                    abbrev, remaining = _split_leading_identifier(content)
                    ensure_voice(abbrev)
                    if remaining.startswith('⠀'):
                        remaining = remaining[1:]
                    word_accumulators[abbrev] = _ChunkAccumulator()
                    word_accumulators[abbrev].add(remaining)
                    last_word_voice = abbrev
                else:  # word_cont
                    if last_word_voice is None:
                        raise BrailleParseError(
                            "Choral ensemble input has a word run-over line "
                            "before any word line has started this parallel."
                        )
                    word_accumulators[last_word_voice].add(content)
            for abbrev, acc in word_accumulators.items():
                text_chunk = acc.text()
                if not text_chunk:
                    continue
                lst = word_by_voice[abbrev]
                if lst:
                    lst.append('⠀')
                lst.append(text_chunk)
                word_accumulators[abbrev] = _ChunkAccumulator()

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
        word_text, stage_directions = extract_stage_directions(word_text)
        syllables = parse_lyrics(word_text) if word_text.strip('⠀') else []
        groups = group_pitched_elements_by_slur(staff.measures)
        staff.lyrics = map_syllables_to_groups(syllables, groups, abbrev)
        staff.stage_directions = stage_directions
        # §38.2's character-list table is the only place a real name
        # exists in the content for a choral voice -- without it (a plain
        # SATB-style ensemble), the name isn't recoverable at all (same
        # limitation as S11c-9's vocal solo), so it's left as the bare
        # abbreviation.
        staff.name = character_names_by_abbrev.get(abbrev, abbrev)
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
