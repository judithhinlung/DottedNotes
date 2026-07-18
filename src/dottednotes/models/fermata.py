from dataclasses import dataclass
from enum import Enum, auto


class FermataShape(Enum):
    """BANA Music Braille Code 2015, Par. 22.2, Table 22(B) -- "Symbols
    That Follow the Note in Braille." Table 22(B) lists 7 fermata
    variants total; the 3 bar-line-attached ones (above/below a plain bar
    line, a sectional double bar, or a final double bar) live on `Measure`
    instead of here -- see `Measure.bar_line_fermata`.
    """
    NORMAL = auto()         # over or under a note
    BETWEEN_NOTES = auto()  # between notes -- attaches to the preceding note
    SQUARED = auto()        # squared shape
    TENT = auto()           # tent-shaped


# LilyPond Notation Reference (v2.26), "List of articulations" (App. B.13.3,
# "Fermata scripts") -- \fermata confirmed as a bare postfix command (no
# leading hyphen), same convention already verified for \downbow/\upbow
# elsewhere in this codebase (see articulation.py). The squared/tent-shaped
# mapping to \henzelongfermata/\henzeshortfermata is NOT from the LilyPond
# manual itself (it doesn't describe each command's visual shape in text) --
# it's cross-referenced from the Fermata Wikipedia article and the MEI
# encoding guidelines, which both describe Hans Werner Henze's square
# fermata as indicating a *longer* hold and his triangular/angled fermata a
# *shorter* hold, matching BANA's "squared"/"tent-shaped" naming, AND
# visually confirmed by compiling `c'4\henzelongfermata d'4\henzeshortfermata`
# through the real `lilypond` 2.24.4 binary: henzelongfermata renders as a
# rounder/bracket-ish shape, henzeshortfermata as a more angular/pointed one
# -- consistent with "squared" vs. "tent-shaped". Still flag for
# developer confirmation if this ever looks wrong in real output.
_FERMATA_TO_LILYPOND: dict[FermataShape, str] = {
    FermataShape.NORMAL: r'\fermata',
    FermataShape.BETWEEN_NOTES: r'\fermata',  # no distinct print shape, only a braille positional distinction
    FermataShape.SQUARED: r'\henzelongfermata',
    FermataShape.TENT: r'\henzeshortfermata',
}

# BANA dot patterns (Table 22(B)), decoded from the manual's own ASCII
# transcription against this repo's ASCII_TO_DOTS (parser/input_pipeline.py)
# -- derived, not yet developer-confirmed against a real fixture:
#   over/under a note      <l    = dots 1,2,6 + dots 1,2,3   = ⠣⠇
#   between notes          "<l   = dot 5 + (the above)       = ⠐⠣⠇
#   squared shape          ;<l   = dots 5,6 + (the above)     = ⠰⠣⠇
#   tent-shaped            ^<l   = dots 4,5 + (the above)     = ⠘⠣⠇
_FERMATA_TO_BRL: dict[FermataShape, str] = {
    FermataShape.NORMAL: '⠣⠇',
    FermataShape.BETWEEN_NOTES: '⠐⠣⠇',
    FermataShape.SQUARED: '⠰⠣⠇',
    FermataShape.TENT: '⠘⠣⠇',
}


@dataclass
class Fermata:
    shape: FermataShape = FermataShape.NORMAL

    def to_lilypond(self) -> str:
        return _FERMATA_TO_LILYPOND[self.shape]

    def to_braille(self) -> str:
        return _FERMATA_TO_BRL[self.shape]
