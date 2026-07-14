from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .chord_names import ChordNamesTrack
from .staff import Staff
from .transposition import get_transposition

_LILYPOND_VERSION = "2.24.0"


@dataclass
class Score:
    title: str = ""
    composer: str = ""
    copyright: str = ""
    tagline: str = ""
    staves: list[Staff] = field(default_factory=list)
    # BANA Sec. 27 lead-sheet chord symbols (S8b-5), rendered as a ChordNames
    # context alongside the single melody staff. None for every other score.
    chord_names: Optional[ChordNamesTrack] = None

    def add_staff(self, staff: Staff) -> None:
        self.staves.append(staff)

    @staticmethod
    def _group_by_family(staves: list[Staff]) -> list[tuple["InstrumentFamily | None", list[Staff]]]:
        """Group staves into contiguous runs by instrument family (e.g. winds,
        brass, strings, keyboard/harp), preserving order. A None family never
        merges with a neighboring run, even another None -- each such staff
        gets its own single-staff run. Shared by Score.to_lilypond() and
        OrchestraScore.to_lilypond() (S5b-8).
        """
        from .instrument import get_instrument_family, InstrumentFamily

        runs: list[tuple[InstrumentFamily | None, list[Staff]]] = []
        current_run: list[Staff] = []
        current_family: InstrumentFamily | None = None

        for staff in staves:
            family = get_instrument_family(staff.name)
            if not current_run:
                current_run = [staff]
                current_family = family
            elif family == current_family and family is not None:
                current_run.append(staff)
            else:
                runs.append((current_family, current_run))
                current_run = [staff]
                current_family = family
        if current_run:
            runs.append((current_family, current_run))
        return runs

    @staticmethod
    def _escape_header_field(value: str) -> str:
        """Escape backslash and double-quote characters so `value` can be
        embedded in a LilyPond \\header string field without breaking out
        of the surrounding quotes."""
        return value.replace('\\', '\\\\').replace('"', '\\"')

    def _header_lines(self) -> list[str]:
        """Return \\header {} block lines, or [] if no header fields are set."""
        fields: list[str] = []
        if self.title:
            fields.append(f'  title = "{self._escape_header_field(self.title)}"')
        if self.composer:
            fields.append(f'  composer = "{self._escape_header_field(self.composer)}"')
        if self.copyright:
            fields.append(f'  copyright = "{self._escape_header_field(self.copyright)}"')
        if self.tagline:
            fields.append(f'  tagline = "{self._escape_header_field(self.tagline)}"')
        if not fields:
            return []
        return [r'\header {', *fields, '}']

    @staticmethod
    def _indent_lines(lines: list[str], prefix: str = '  ') -> list[str]:
        """Indent every line by `prefix`, including lines embedded inside
        multi-line strings (e.g. a staff's rendered measures), so nested
        \\score {} content lines up correctly. Blank lines are left as-is."""
        result: list[str] = []
        for line in lines:
            for sub in line.split('\n'):
                result.append(prefix + sub if sub.strip() else sub)
        return result

    @staticmethod
    def _wrap_transpose(
        staff: Staff, relative_block: list[str], indent: str, concert_pitch: bool
    ) -> list[str]:
        """Wrap a \\relative-mode block in \\transpose (S5b-6) if `staff.name`
        is a recognized transposing-instrument key and concert_pitch is True.
        Returns relative_block unchanged otherwise (unknown/non-transposing
        instrument, or concert_pitch=False for written-pitch output).
        """
        if not concert_pitch:
            return relative_block
        transposition = get_transposition(staff.name)
        if transposition is None:
            return relative_block
        written, concert = transposition
        if written == concert:
            return relative_block
        return [
            f"{indent}\\transpose {written} {concert} {{",
            *(f"  {line}" for line in relative_block),
            f"{indent}}}",
        ]

    def to_lilypond(
        self,
        concert_pitch: bool = True,
        paper_size: Optional[str] = None,
        category_override: Optional[str] = None,
        format_overrides: Optional[dict] = None,
    ) -> str:
        """Return a complete LilyPond document string for this score.

        Uses \\relative c' mode (reference pitch = C4) for all staves.
        Single-staff scores are wrapped directly. Multiple staves are grouped
        by instrument families (e.g. winds, brass, strings, keyboard/harp)
        and wrapped in \\new StaffGroup or \\new PianoStaff contexts.

        Per CLAUDE.md Key Design Decision #4, concert pitch is the default:
        a staff whose name is a recognized transposing-instrument key (e.g.
        "Horn in F", "Clarinet in B-flat" -- see models/transposition.py)
        has its \\relative block wrapped in \\transpose to convert the
        parsed *written* pitch into concert (sounding) pitch. Pass
        concert_pitch=False to emit written pitch as-is (e.g. for
        generating an individual player's part).
        """
        from ..renderers.lilypond_formatter import LilyPondFormatter
        formatter = LilyPondFormatter()
        settings = formatter.get_settings(self, category_override=category_override)

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

        if len(self.staves) == 1:
            staff = self.staves[0]
            anchor, start_midi = staff.relative_anchor()
            staff_content = staff.to_lilypond(start_midi=start_midi)
            if staff.lyrics and self.chord_names is not None:
                raise NotImplementedError(
                    "Chord symbols alongside lyrics (BANA Sec. 36) are not supported; "
                    "Sec. 27 lead sheets are melody-only."
                )
            if staff.lyrics:
                relative_block = [f"  \\relative {anchor} {{", staff_content, '  }']
                transposed = self._wrap_transpose(staff, relative_block, '  ', concert_pitch)
                voice_name = f"vocals_{staff.name.lower().replace(' ', '_')}"
                lyrics_content = " ".join(staff.lyrics)
                body = [
                    "\\new Staff <<",
                    f"  \\new Voice = \"{voice_name}\" {{",
                    *transposed,
                    "  }",
                    f"  \\new Lyrics \\lyricsto \"{voice_name}\" {{ {lyrics_content} }}",
                    ">>"
                ]
            elif self.chord_names is not None:
                relative_block = [f"  \\relative {anchor} {{", staff_content, '  }']
                transposed = self._wrap_transpose(staff, relative_block, '  ', concert_pitch)
                body = [
                    "<<",
                    "  " + self.chord_names.to_lilypond().replace('\n', '\n  '),
                    "  \\new Staff {",
                    *transposed,
                    "  }",
                    ">>",
                ]
            else:
                relative_block = [f"\\relative {anchor} {{", staff_content, '}']
                body = self._wrap_transpose(staff, relative_block, '', concert_pitch)
            score_lines = [
                r'\score {',
                *self._indent_lines(body),
                '  \\layout { }',
                '  \\midi { }',
                '}',
            ]
            parts.append("\n".join(score_lines))
            return "\n\n".join(parts) + "\n"

        from .instrument import InstrumentFamily

        runs = self._group_by_family(self.staves)

        top_level_blocks: list[list[str]] = []
        for family, run_staves in runs:
            if len(run_staves) == 1:
                staff = run_staves[0]
                anchor, start_midi = staff.relative_anchor()
                if staff.lyrics:
                    relative_block = [
                        f"    \\relative {anchor} {{",
                        staff.to_lilypond(start_midi=start_midi),
                        "    }",
                    ]
                    transposed = self._wrap_transpose(staff, relative_block, '    ', concert_pitch)
                    voice_name = f"vocals_{staff.name.lower().replace(' ', '_')}"
                    lyrics_content = " ".join(staff.lyrics)
                    block_lines = [
                        "\\new Staff <<",
                        f"  \\new Voice = \"{voice_name}\" {{",
                        *transposed,
                        "  }",
                        f"  \\new Lyrics \\lyricsto \"{voice_name}\" {{ {lyrics_content} }}",
                        ">>"
                    ]
                else:
                    relative_block = [
                        f"  \\relative {anchor} {{",
                        staff.to_lilypond(start_midi=start_midi),
                        "  }",
                    ]
                    block_lines = [
                        "\\new Staff {",
                        *self._wrap_transpose(staff, relative_block, '  ', concert_pitch),
                        "}"
                    ]
                top_level_blocks.append(block_lines)
            else:
                group_context = "PianoStaff" if family == InstrumentFamily.KEYBOARD_HARP else "StaffGroup"
                block_lines = [f"\\new {group_context} <<"]
                for staff in run_staves:
                    anchor, start_midi = staff.relative_anchor()
                    if staff.lyrics:
                        relative_block = [f"      \\relative {anchor} {{"]
                        staff_ly = staff.to_lilypond(start_midi=start_midi)
                        for line in staff_ly.splitlines():
                            relative_block.append("        " + line.strip())
                        relative_block.append("      }")
                        transposed = self._wrap_transpose(staff, relative_block, '      ', concert_pitch)
                        voice_name = f"vocals_{staff.name.lower().replace(' ', '_')}"
                        lyrics_content = " ".join(staff.lyrics)
                        block_lines.append("  \\new Staff <<")
                        block_lines.append(f"    \\new Voice = \"{voice_name}\" {{")
                        block_lines.extend(transposed)
                        block_lines.append("    }")
                        block_lines.append(f"    \\new Lyrics \\lyricsto \"{voice_name}\" {{ {lyrics_content} }}")
                        block_lines.append("  >>")
                    else:
                        block_lines.append("  \\new Staff {")
                        relative_block = [f"    \\relative {anchor} {{"]
                        staff_ly = staff.to_lilypond(start_midi=start_midi)
                        for line in staff_ly.splitlines():
                            relative_block.append("      " + line.strip())
                        relative_block.append("    }")
                        block_lines.extend(self._wrap_transpose(staff, relative_block, '    ', concert_pitch))
                        block_lines.append("  }")
                block_lines.append(">>")
                top_level_blocks.append(block_lines)

        if len(top_level_blocks) == 1:
            body = top_level_blocks[0]
        else:
            body = ["<<"]
            for block in top_level_blocks:
                body.extend("  " + line if line.strip() else line for line in block)
            body.append(">>")

        score_lines = [
            r'\score {',
            *self._indent_lines(body),
            '  \\layout { }',
            '  \\midi { }',
            '}',
        ]
        parts.append("\n".join(score_lines))
        return "\n\n".join(parts) + "\n"

    def reconstruct_omitted_rests(self) -> None:
        """Fill in any missing measures across all staves with full-measure rests,
        aligning all staves to have the same number of measures.
        """
        if not self.staves:
            return

        # 1. Find the maximum measure number across all staves
        max_measure_num = 0
        for staff in self.staves:
            for m in staff.measures:
                max_measure_num = max(max_measure_num, m.number)

        if max_measure_num == 0:
            return

        # 2. For each staff, fill in any missing measures
        for staff in self.staves:
            # Map existing measures by their measure number
            existing_measures = {m.number: m for m in staff.measures}

            # Get active time signature
            time_sig = staff.time_signature
            if time_sig is None:
                for other in self.staves:
                    if other.time_signature is not None:
                        time_sig = other.time_signature
                        break

            from .time_signature import TimeSignature
            from .note import Rest
            from .measure import Measure
            from dottednotes.bana_symbols import SymbolCategory

            if time_sig is None:
                time_sig = TimeSignature(
                    dots=frozenset(),
                    category=SymbolCategory.TIME_SIGNATURE,
                    raw_brl='',
                    numerator=4,
                    denominator=4,
                )

            dur = time_sig.get_full_measure_duration()

            new_measures = []
            for num in range(1, max_measure_num + 1):
                if num in existing_measures:
                    new_measures.append(existing_measures[num])
                else:
                    m = Measure(number=num)
                    rest_obj = Rest(
                        dots=frozenset(),
                        category=SymbolCategory.REST,
                        raw_brl='⠍',
                        duration=dur,
                        is_full_measure=True,
                    )
                    m.add_note(rest_obj)
                    new_measures.append(m)
            staff.measures = new_measures
