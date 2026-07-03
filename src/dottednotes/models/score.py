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
        Single-staff scores are wrapped directly; multi-staff scores
        will be supported in a later sprint.
        """
        version_line = f'\\version "{_LILYPOND_VERSION}"'
        if not self.staves:
            return version_line + '\n'

        staff_content = self.staves[0].to_lilypond(start_midi=_C4_MIDI)
        lines = [
            version_line,
            "\\relative c' {",
            staff_content,
            '}',
        ]
        return '\n'.join(lines) + '\n'
