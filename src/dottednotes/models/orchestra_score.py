from __future__ import annotations

from dataclasses import dataclass

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
    """
    words = [w for w in instrument_name.strip().split() if w]
    if not words:
        return 'music'
    if words[-1] in _ROMAN_TO_WORD:
        words[-1] = _ROMAN_TO_WORD[words[-1]]
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

    def to_lilypond(self, concert_pitch: bool = True) -> str:
        version_line = f'\\version "{_LILYPOND_VERSION}"'
        header_lines = self._header_lines()
        if not self.staves:
            lines = [version_line, *header_lines]
            return '\n'.join(lines) + '\n'

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
            staff_content = staff.to_lilypond(start_midi=start_midi, include_clef=False)
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
                top_level_blocks.append(self._staff_with_block(staff, var_names[id(staff)], '  '))
            else:
                group_context = 'PianoStaff' if family == InstrumentFamily.KEYBOARD_HARP else 'StaffGroup'
                block_lines = [f'\\new {group_context} <<']
                for staff in run_staves:
                    block_lines.extend(self._staff_with_block(staff, var_names[id(staff)], '    '))
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

        lines = [version_line, *header_lines, ''] + variable_defs + score_lines
        return '\n'.join(lines) + '\n'

    @staticmethod
    def _staff_with_block(staff: Staff, var_name: str, indent: str) -> list[str]:
        """Return the \\new Staff \\with {...} { ... } block for one staff,
        referencing its already-defined music variable by name."""
        abbrev = TABLE_29_ENGLISH.get(staff.name)

        lines = [f'{indent}\\new Staff \\with {{']
        lines.append(f'{indent}  instrumentName = "{staff.name}"')
        if abbrev is not None:
            lines.append(f'{indent}  shortInstrumentName = "{abbrev}"')
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
