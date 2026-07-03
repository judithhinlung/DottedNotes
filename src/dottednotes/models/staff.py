from dataclasses import dataclass, field

from .measure import Measure


@dataclass
class Staff:
    name: str
    measures: list[Measure] = field(default_factory=list)

    def add_measure(self, measure: Measure) -> None:
        self.measures.append(measure)

    def to_lilypond(self, start_midi: int = 60) -> str:
        """Return indented LilyPond lines for all measures in relative mode."""
        prev_midi = start_midi
        lines: list[str] = []
        for measure in self.measures:
            ly_str, prev_midi = measure.to_lilypond(prev_midi=prev_midi)
            lines.append('    ' + ly_str)
        return '\n'.join(lines)
