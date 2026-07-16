from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from dottednotes.bana_symbols import TABLE_29_ENGLISH

from .instrument import InstrumentFamily, get_midi_instrument_name
from .score import Score, _LILYPOND_VERSION
from .staff import Staff

_ROMAN_TO_WORD: dict[str, str] = {'I': 'One', 'II': 'Two', 'III': 'Three', 'IV': 'Four', 'V': 'Five'}


def _music_variable_name(instrument_name: str) -> str:
    """Derive a LilyPond music-variable identifier from an instrument name,
    e.g. "Violin I" -> "violinOneMusic", "Flute" -> "fluteMusic". A trailing
    Roman-numeral part number is spelled out since LilyPond identifiers can't
    contain digits or spaces. This is a mechanical, predictable scheme, not
    an attempt to reproduce a composer's own hand-chosen abbreviations (e.g.
    "cello"/"bass") -- those are cosmetic and don't affect the rendered
    output either way.

    Non-letter characters (digits, punctuation -- including a stray '?'
    from decode_literary_braille's fallback for a cell it doesn't know) are
    stripped from each word: LilyPond identifiers are letters only, and
    silently passing one through unfiltered produces music that doesn't
    compile rather than a clear error.
    """
    words = [w for w in instrument_name.strip().split() if w]
    if not words:
        return 'music'
    if words[-1] in _ROMAN_TO_WORD:
        words[-1] = _ROMAN_TO_WORD[words[-1]]
    words = [''.join(c for c in w if c.isalpha()) for w in words]
    words = [w for w in words if w]
    if not words:
        return 'music'
    camel = words[0].lower() + ''.join(w.capitalize() for w in words[1:])
    return camel + 'Music'


@dataclass
class OrchestraScore(Score):
    """An orchestra score containing staves for each instrument part.

    Unlike the plain Score.to_lilypond() (which inlines each staff's music
    directly inside its \\score block), this renders each staff's music into
    its own named LilyPond variable (e.g. `violinOneMusic = ...`) defined
    before the \\score block, then references it via \\<name>Music inside a
    \\new Staff \\with {...} block carrying instrumentName/shortInstrumentName
    and \\set directives for the engraved name and MIDI playback instrument.
    This is the standard LilyPond idiom for named parts in an orchestral
    score (LilyPond Learning Manual Sec. 4.4.5, "Scores and Parts") and
    matches tests/fixtures/fengyang_flower_drum.ly's hand-authored structure.
    """

    def to_lilypond(
        self,
        concert_pitch: bool = True,
        paper_size: Optional[str] = None,
        category_override: Optional[str] = None,
        format_overrides: Optional[dict] = None,
        measure_numbers: bool = False,
    ) -> str:
        from ..renderers.lilypond_formatter import LilyPondFormatter
        formatter = LilyPondFormatter()
        settings = formatter.get_settings(self, category_override=category_override)
        short_names = settings.short_instrument_names

        version_line = f'\\version "{_LILYPOND_VERSION}"'

        size_name = paper_size if paper_size is not None else ((format_overrides or {}).get("paper_size") or "letter")

        staff_size = (format_overrides or {}).get("staff_size", settings.staff_size)
        margin_mm = (format_overrides or {}).get("margin_mm", settings.margin_mm)
        basic_distance = (format_overrides or {}).get("basic_distance", settings.system_system_spacing_basic_distance)
        padding = (format_overrides or {}).get("padding", settings.system_system_spacing_padding)

        staff_size_line = f"#(set-global-staff-size {staff_size})"

        paper_lines = [
            r"\paper {",
            f'  #(set-paper-size "{size_name.lower().strip()}")',
            f"  top-margin = {margin_mm}\\mm",
            f"  bottom-margin = {margin_mm}\\mm",
            f"  left-margin = {margin_mm}\\mm",
            f"  right-margin = {margin_mm}\\mm",
            f"  system-system-spacing = #'((basic-distance . {basic_distance})",
            f"                             (minimum-distance . {basic_distance - 4.0})",
            f"                             (padding . {padding})",
            "                             (stretchability . 60))",
            "}"
        ]

        header_lines = self._header_lines()

        parts = [
            version_line,
            staff_size_line,
            "\n".join(paper_lines),
        ]
        if header_lines:
            parts.append("\n".join(header_lines))

        if not self.staves:
            return "\n\n".join(parts) + "\n"

        variable_defs: list[str] = []
        var_names: dict[int, str] = {}
        used_names: set[str] = set()

        for staff in self.staves:
            base_name = _music_variable_name(staff.name)
            var_name = base_name
            suffix = 2
            while var_name in used_names:
                var_name = f'{base_name}{suffix}'
                suffix += 1
            used_names.add(var_name)
            var_names[id(staff)] = var_name

            # \clef is emitted separately in the \score block's \with body
            # (see _staff_with_block), not inside the music variable.
            anchor, start_midi = staff.relative_anchor()
            staff_content = staff.to_lilypond(
                start_midi=start_midi, include_clef=False, measure_numbers=measure_numbers
            )
            relative_block = [f"\\relative {anchor} {{", staff_content, '}']
            wrapped = self._wrap_transpose(staff, relative_block, '', concert_pitch)
            variable_defs.append(f'{var_name} = ' + wrapped[0])
            variable_defs.extend(wrapped[1:])
            variable_defs.append('')

        runs = self._group_by_family(self.staves)

        top_level_blocks: list[list[str]] = []
        for family, run_staves in runs:
            if len(run_staves) == 1:
                staff = run_staves[0]
                top_level_blocks.append(self._staff_with_block(staff, var_names[id(staff)], '  ', short_names))
            else:
                group_context = 'PianoStaff' if family == InstrumentFamily.KEYBOARD_HARP else 'StaffGroup'
                block_lines = [f'\\new {group_context} <<']
                for staff in run_staves:
                    block_lines.extend(self._staff_with_block(staff, var_names[id(staff)], '    ', short_names))
                block_lines.append('>>')
                top_level_blocks.append(block_lines)

        score_lines = ['\\score {', '  <<']
        for block in top_level_blocks:
            score_lines.extend(block)
        score_lines.append('  >>')
        score_lines.append('')
        score_lines.append('  \\layout { }')
        score_lines.append('  \\midi { }')
        score_lines.append('}')

        parts.append("\n".join(variable_defs))
        parts.append("\n".join(score_lines))

        return "\n\n".join(parts) + "\n"

    @staticmethod
    def _staff_with_block(staff: Staff, var_name: str, indent: str, short_names: bool = True) -> list[str]:
        """Return the \\new Staff \\with {...} { ... } block for one staff,
        referencing its already-defined music variable by name."""
        abbrev = TABLE_29_ENGLISH.get(staff.name) if short_names else None

        lines = [f'{indent}\\new Staff \\with {{']
        lines.append(f'{indent}  instrumentName = "{staff.name}"')
        if abbrev is not None:
            lines.append(f'{indent}  shortInstrumentName = "{abbrev}"')

        if staff.lyrics:
            lines.append(f'{indent}}} <<')
            voice_name = f"vocals_{staff.name.lower().replace(' ', '_')}"
            lines.append(f'{indent}  \\new Voice = "{voice_name}" {{')
            clef = staff.resolve_clef()
            if clef is not None:
                lines.append(f'{indent}    {clef}')
            lines.append(f'{indent}    \\set Staff.instrumentName = "{staff.name}"')
            midi_name = get_midi_instrument_name(staff.name)
            if midi_name is not None:
                lines.append(f'{indent}    \\set Staff.midiInstrument = "{midi_name}"')
            lines.append(f'{indent}    \\{var_name}')
            lines.append(f'{indent}  }}')
            verses = staff.verses if staff.verses else [staff.lyrics]
            for v_idx, v in enumerate(verses):
                prefix_str = ""
                if staff.verse_prefixes and v_idx < len(staff.verse_prefixes) and staff.verse_prefixes[v_idx]:
                    prefix_str = f"\\set stanza = \"{staff.verse_prefixes[v_idx]} \" "
                lyrics_content = prefix_str + " ".join(v)
                lines.append(f'{indent}  \\new Lyrics \\lyricsto "{voice_name}" {{ {lyrics_content} }}')
            lines.append(f'{indent}>>')
        else:
            lines.append(f'{indent}}} {{')
            clef = staff.resolve_clef()
            if clef is not None:
                lines.append(f'{indent}  {clef}')
            lines.append(f'{indent}  \\set Staff.instrumentName = "{staff.name}"')
            midi_name = get_midi_instrument_name(staff.name)
            if midi_name is not None:
                lines.append(f'{indent}  \\set Staff.midiInstrument = "{midi_name}"')
            lines.append(f'{indent}  \\{var_name}')
            lines.append(f'{indent}}}')
        return lines
