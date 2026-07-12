from dataclasses import dataclass, field

from .staff import Staff
from .transposition import get_transposition

_LILYPOND_VERSION = "2.24.0"


@dataclass
class Score:
    title: str = ""
    composer: str = ""
    staves: list[Staff] = field(default_factory=list)

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

    def to_lilypond(self, concert_pitch: bool = True) -> str:
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
        version_line = f'\\version "{_LILYPOND_VERSION}"'
        if not self.staves:
            return version_line + '\n'

        if len(self.staves) == 1:
            staff = self.staves[0]
            anchor, start_midi = staff.relative_anchor()
            staff_content = staff.to_lilypond(start_midi=start_midi)
            relative_block = [f"\\relative {anchor} {{", staff_content, '}']
            body = self._wrap_transpose(staff, relative_block, '', concert_pitch)
            lines = [version_line, *body]
            return '\n'.join(lines) + '\n'

        from .instrument import InstrumentFamily

        runs = self._group_by_family(self.staves)

        top_level_blocks: list[list[str]] = []
        for family, run_staves in runs:
            if len(run_staves) == 1:
                staff = run_staves[0]
                anchor, start_midi = staff.relative_anchor()
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

        lines = [version_line]
        if len(top_level_blocks) == 1:
            lines.extend(top_level_blocks[0])
        else:
            lines.append("<<")
            for block in top_level_blocks:
                lines.extend("  " + line if line.strip() else line for line in block)
            lines.append(">>")
        return '\n'.join(lines) + '\n'

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
