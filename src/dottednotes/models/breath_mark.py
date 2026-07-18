from dataclasses import dataclass
from enum import Enum, auto


class BreathMarkVariant(Enum):
    """BANA Music Braille Code 2015, Par. 22.2, Table 22(B) gives two
    breath/break mark signs, "(a)" and "(b)", with no stated rule in Table
    22(B) itself for which print glyph maps to which. Table 31 ("Signs in
    Music Lines", the vocal-music chapter) names the same two ASCII codes
    "Half breath" (sign (a)) and "Full breath" (sign (b)) -- cross-referenced
    with the standard notation convention that a comma-shaped breath mark
    denotes a shorter pause than a caesura ("railroad tracks"), giving:
    (a) -> the ordinary comma breath mark, (b) -> a caesura. Confirmed with
    the developer before implementing (not an unchecked assumption).
    """
    HALF = auto()  # sign (a), Table 31 "Half breath" -> comma breath mark
    FULL = auto()  # sign (b), Table 31 "Full breath" -> caesura


# LilyPond Notation Reference (v2.26), "Breath marks" (Sec. 3.2.3): \breathe
# is a standalone music event (NOT a postfix articulation glued to the
# note -- "any expressive marks pertaining to the preceding note... must be
# placed before \breathe"), and breathMarkType is a context property
# controlling which symbol it draws ('comma' is the default/plain breath
# mark, 'caesura' is listed in "List of breath marks"). Always setting
# breathMarkType explicitly (rather than relying on whatever a previous
# \breathe left it as) so one note's caesura doesn't leak into a later
# note's plain breath mark. Visually confirmed by compiling
# "\breathe" vs. "\set breathMarkType = #'caesura \breathe" through the
# real lilypond 2.24.4 binary: the former renders the ordinary comma tick,
# the latter the double-slash caesura mark.
_BREATH_MARK_TO_LILYPOND: dict[BreathMarkVariant, str] = {
    BreathMarkVariant.HALF: r"\set breathMarkType = #'comma \breathe",
    BreathMarkVariant.FULL: r"\set breathMarkType = #'caesura \breathe",
}

# BANA dot patterns (Par. 22.2, Table 22(B)), decoded from the manual's own
# ASCII against ASCII_TO_DOTS (parser/input_pipeline.py) -- derived, not yet
# developer-confirmed against a real fixture:
#   (a) >1  = dots 3,4,5 + dot 2   = ⠨⠂
#   (b) ,/  = dot 6 + dots 3,4     = ⠠⠌
_BREATH_MARK_TO_BRL: dict[BreathMarkVariant, str] = {
    BreathMarkVariant.HALF: '⠨⠂',
    BreathMarkVariant.FULL: '⠠⠌',
}


@dataclass
class BreathMark:
    variant: BreathMarkVariant = BreathMarkVariant.HALF

    def to_lilypond(self) -> str:
        return _BREATH_MARK_TO_LILYPOND[self.variant]

    def to_braille(self) -> str:
        return _BREATH_MARK_TO_BRL[self.variant]
