from dataclasses import dataclass

from dottednotes.bana_symbols import (
    ACCIDENTAL_CELLS,
    BAR_LINE_CELLS,
    BAR_LINE_SEQUENCES,
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

    Most braille cells become exactly one token.  The exception is the set of
    multi-cell bar line sequences that all start with ⠣ (dots 1,2,6 = U+2823):
    the tokenizer peeks ahead up to two cells and emits a single BAR_LINE token
    carrying the full multi-character sequence when a match is found.  If ⠣ is
    not followed by a bar line second cell it is classified as ACCIDENTAL (flat).

    Newline characters increment the line counter but do not produce tokens.
    Carriage returns and tabs are skipped silently.
    Unrecognized cells produce a token with category UNKNOWN rather than raising.
    """

    _BAR_LINE_PREFIX = '⠣'  # U+2823 — starts every multi-cell bar line

    def tokenize(self, text: str) -> list[BrailleToken]:
        tokens: list[BrailleToken] = []
        line = 1
        i = 0
        while i < len(text):
            char = text[i]
            if char == '\n':
                line += 1
                i += 1
                continue
            if char in ('\r', '\t'):
                i += 1
                continue

            # Lookahead for multi-cell bar line sequences starting with ⠣
            if char == self._BAR_LINE_PREFIX:
                three = text[i:i + 3]
                two = text[i:i + 2]
                if three in BAR_LINE_SEQUENCES:
                    tokens.append(BrailleToken(
                        character=three,
                        category=SymbolCategory.BAR_LINE,
                        position=i,
                        line=line,
                    ))
                    i += 3
                    continue
                if two in BAR_LINE_SEQUENCES:
                    tokens.append(BrailleToken(
                        character=two,
                        category=SymbolCategory.BAR_LINE,
                        position=i,
                        line=line,
                    ))
                    i += 2
                    continue
                # Not a bar line sequence — fall through to classify as flat

            tokens.append(BrailleToken(
                character=char,
                category=self._classify(char),
                position=i,
                line=line,
            ))
            i += 1
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
