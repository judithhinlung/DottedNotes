from ..models.score import Score


class BrailleParser:
    """Parses braille music notation (BANA standard) into a Score."""

    def parse(self, text: str) -> Score:
        score = Score()
        # TODO: implement full BANA braille music parsing
        return score
