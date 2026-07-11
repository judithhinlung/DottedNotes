from dataclasses import dataclass, field

from .staff import Staff

_LILYPOND_VERSION = "2.24.0"
# C4 (middle C) as MIDI pitch — the reference for \relative c' { ... }
_C4_MIDI = 60


@dataclass
class Score:
    title: str = ""
    composer: str = ""
    staves: list[Staff] = field(default_factory=list)

    def add_staff(self, staff: Staff) -> None:
        self.staves.append(staff)

    def to_lilypond(self) -> str:
        """Return a complete LilyPond document string for this score.

        Uses \\relative c' mode (reference pitch = C4) for all staves.
        Single-staff scores are wrapped directly. Multiple staves are grouped
        by instrument families (e.g. winds, brass, strings, keyboard/harp)
        and wrapped in \\new StaffGroup or \\new PianoStaff contexts.
        """
        version_line = f'\\version "{_LILYPOND_VERSION}"'
        if not self.staves:
            return version_line + '\n'

        if len(self.staves) == 1:
            staff_content = self.staves[0].to_lilypond(start_midi=_C4_MIDI)
            lines = [
                version_line,
                "\\relative c' {",
                staff_content,
                '}',
            ]
            return '\n'.join(lines) + '\n'

        from .instrument import get_instrument_family, InstrumentFamily

        runs: list[tuple[InstrumentFamily | None, list[Staff]]] = []
        current_run: list[Staff] = []
        current_family: InstrumentFamily | None = None

        for staff in self.staves:
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

        top_level_blocks: list[list[str]] = []
        for family, run_staves in runs:
            if len(run_staves) == 1:
                staff = run_staves[0]
                block_lines = [
                    "\\new Staff {",
                    "  \\relative c' {",
                    staff.to_lilypond(start_midi=_C4_MIDI),
                    "  }",
                    "}"
                ]
                top_level_blocks.append(block_lines)
            else:
                group_context = "PianoStaff" if family == InstrumentFamily.KEYBOARD_HARP else "StaffGroup"
                block_lines = [f"\\new {group_context} <<"]
                for staff in run_staves:
                    block_lines.append("  \\new Staff {")
                    block_lines.append("    \\relative c' {")
                    staff_ly = staff.to_lilypond(start_midi=_C4_MIDI)
                    for line in staff_ly.splitlines():
                        block_lines.append("      " + line.strip())
                    block_lines.append("    }")
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
