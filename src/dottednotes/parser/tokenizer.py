from dataclasses import dataclass

from dottednotes.bana_symbols import (
    ACCIDENTAL_CELLS,
    BAR_LINE_CELLS,
    NOTE_CELLS,
    OCTAVE_MARKS,
    REST_CELLS,
    SymbolCategory,
)


@dataclass
class BrailleToken:
    """A single classified braille cell with its location in the source text."""
    character: str          # the raw Unicode braille character (U+2800–U+28FF)
    category: SymbolCategory
    position: int           # 0-based character index in the source string
    line: int               # 1-based line number


class BrailleTokenizer:
    """
    Converts a normalized Unicode braille string into a flat list of BrailleToken objects.

    Each braille cell becomes exactly one token. Multi-cell sequences (e.g. two-cell
    bar lines, the sub-contra octave mark ⠈⠈) are left for the parser to combine from
    adjacent tokens — the tokenizer classifies cells individually.

    Newline characters increment the line counter but do not produce tokens.
    Carriage returns and tabs are skipped silently.
    Unrecognized cells produce a token with category UNKNOWN rather than raising.
    """

    def tokenize(self, text: str) -> list[BrailleToken]:
        tokens = []
        line = 1
        for position, char in enumerate(text):
            if char == '\n':
                line += 1
                continue
            if char in ('\r', '\t'):
                continue
            tokens.append(BrailleToken(
                character=char,
                category=self._classify(char),
                position=position,
                line=line,
            ))
        return tokens

    def _classify(self, char: str) -> SymbolCategory:
        if char in NOTE_CELLS and NOTE_CELLS[char] is not None:
            return SymbolCategory.NOTE
        if char in REST_CELLS:
            return SymbolCategory.REST
        if char in OCTAVE_MARKS:
            return SymbolCategory.OCTAVE_MARK
        if char in ACCIDENTAL_CELLS:
            return SymbolCategory.ACCIDENTAL
        if char in BAR_LINE_CELLS:
            return SymbolCategory.BAR_LINE
        return SymbolCategory.UNKNOWN
