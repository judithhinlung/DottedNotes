from ..models.measure import Measure
from ..models.note import Note
from ..models.score import Score
from ..models.staff import Staff


class LilypondRenderer:
    """Renders a Score as LilyPond source text."""

    def render(self, score: Score) -> str:
        lines = ['\\version "2.24.0"']
        if score.title or score.composer:
            lines.append(
                f'\\header {{\n  title = "{score.title}"\n  composer = "{score.composer}"\n}}'
            )
        for staff in score.staves:
            lines.append(self._render_staff(staff))
        return "\n".join(lines)

    def _render_staff(self, staff: Staff) -> str:
        tokens = [
            token
            for measure in staff.measures
            for token in self._render_measure(measure)
        ]
        return "{ " + " ".join(tokens) + " }"

    def _render_measure(self, measure: Measure) -> list[str]:
        return [self._render_note(n) for n in measure.notes]

    def _render_note(self, note: Note) -> str:
        dur = note.duration.to_lilypond()
        if note.is_rest:
            return f"r{dur}"
        # LilyPond octave marks: middle C is c', each ' raises by one octave
        octave_marks = "'" * max(0, note.octave - 3) or "," * max(0, 3 - note.octave)
        return f"{note.pitch}{octave_marks}{dur}"
