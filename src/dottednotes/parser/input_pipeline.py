from pathlib import Path
from typing import Union

from ..exceptions import BrailleParseError

# North American Braille ASCII (BRF) encoding.
# Maps each ASCII character to a 6-bit dot pattern where bit N-1 = dot N.
# That bitmask is also the offset into the Unicode braille block (U+2800+).
ASCII_TO_DOTS = {
    ' ': 0b000000,  # blank cell
    '!': 0b101110,  # dots 2,3,4,6
    '"': 0b010000,  # dot 5
    '#': 0b111100,  # dots 3,4,5,6
    '$': 0b101011,  # dots 1,2,4,6
    '%': 0b101001,  # dots 1,4,6
    '&': 0b101111,  # dots 1,2,3,4,6
    "'": 0b000100,  # dot 3
    '(': 0b110111,  # dots 1,2,3,5,6
    ')': 0b111110,  # dots 2,3,4,5,6
    '*': 0b100001,  # dots 1,6
    '+': 0b101100,  # dots 3,4,6
    ',': 0b100000,  # dot 6
    '-': 0b100100,  # dots 3,6
    '.': 0b101000,  # dots 4,6
    '/': 0b001100,  # dots 3,4
    '0': 0b110100,  # dots 3,5,6
    '1': 0b000010,  # dot 2
    '2': 0b000110,  # dots 2,3
    '3': 0b010010,  # dots 2,5
    '4': 0b110010,  # dots 2,5,6
    '5': 0b100010,  # dots 2,6
    '6': 0b010110,  # dots 2,3,5
    '7': 0b110110,  # dots 2,3,5,6
    '8': 0b100110,  # dots 2,3,6
    '9': 0b010100,  # dots 3,5
    ':': 0b110001,  # dots 1,5,6
    ';': 0b110000,  # dots 5,6
    '<': 0b100011,  # dots 1,2,6
    '=': 0b111111,  # dots 1,2,3,4,5,6
    '>': 0b011100,  # dots 3,4,5
    '?': 0b111001,  # dots 1,4,5,6
    '@': 0b001000,  # dot 4
    'A': 0b000001,  # dot 1
    'B': 0b000011,  # dots 1,2
    'C': 0b001001,  # dots 1,4
    'D': 0b011001,  # dots 1,4,5
    'E': 0b010001,  # dots 1,5
    'F': 0b001011,  # dots 1,2,4
    'G': 0b011011,  # dots 1,2,4,5
    'H': 0b010011,  # dots 1,2,5
    'I': 0b001010,  # dots 2,4
    'J': 0b011010,  # dots 2,4,5
    'K': 0b000101,  # dots 1,3
    'L': 0b000111,  # dots 1,2,3
    'M': 0b001101,  # dots 1,3,4
    'N': 0b011101,  # dots 1,3,4,5
    'O': 0b010101,  # dots 1,3,5
    'P': 0b001111,  # dots 1,2,3,4
    'Q': 0b011111,  # dots 1,2,3,4,5
    'R': 0b010111,  # dots 1,2,3,5
    'S': 0b001110,  # dots 2,3,4
    'T': 0b011110,  # dots 2,3,4,5
    'U': 0b100101,  # dots 1,3,6
    'V': 0b100111,  # dots 1,2,3,6
    'W': 0b111010,  # dots 2,4,5,6
    'X': 0b101101,  # dots 1,3,4,6
    'Y': 0b111101,  # dots 1,3,4,5,6
    'Z': 0b110101,  # dots 1,3,5,6
    '[': 0b101010,  # dots 2,4,6
    '\\': 0b110011,  # dots 1,2,5,6
    ']': 0b111011,  # dots 1,2,4,5,6
    '^': 0b011000,  # dots 4,5
    '_': 0b111000,  # dots 4,5,6
}


def ascii_braille_char_to_unicode(char: str) -> str:
    """Convert a single ASCII braille character to its Unicode braille equivalent."""
    dots = ASCII_TO_DOTS.get(char.upper(), 0)
    return chr(0x2800 + dots)


# Reverse mapping: Unicode braille cell offset → lowercase letter.
# Built from ASCII_TO_DOTS (letters only); blank cell (offset 0) maps to space.
_BRAILLE_TO_LETTER: dict[int, str] = {
    v: k.lower() for k, v in ASCII_TO_DOTS.items() if k.isalpha()
}
_BRAILLE_TO_LETTER[0] = ' '   # blank cell = word separator
_BRAILLE_TO_LETTER[ASCII_TO_DOTS['-']] = '-'  # dots 3,6 -- literary hyphen (e.g. "Left-Hand")
_BRAILLE_TO_LETTER[ASCII_TO_DOTS["'"]] = "'"  # dot 3 -- literary apostrophe (e.g. "Children's")


def decode_literary_braille(cells: str) -> str:
    """Decode a sequence of Unicode braille cells as literary braille (a–z, space, hyphen).

    Each cell is mapped via _BRAILLE_TO_LETTER.  Cells that do not correspond
    to a letter, space, or hyphen are replaced with '?' so callers can detect them.
    """
    return ''.join(_BRAILLE_TO_LETTER.get(ord(c) - 0x2800, '?') for c in cells)


class BRLInputPipeline:
    """Loads a .brf or .brl file and normalizes it to Unicode braille (U+2800–U+28FF)."""

    def load(self, filepath: Union[str, Path]) -> str:
        """Return file contents as normalized Unicode braille."""
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Braille file not found: {filepath}")
        raw = path.read_text(encoding="utf-8", errors="replace")
        if self._detect_encoding(raw) == "ascii":
            return self._ascii_to_unicode(raw)
        return raw

    def _detect_encoding(self, content: str) -> str:
        """Return 'unicode', 'ascii', or 'unknown' based on first non-whitespace character."""
        for char in content:
            if char.strip():
                if 0x2800 <= ord(char) <= 0x28FF:
                    return "unicode"
                return "ascii"
        return "unknown"

    def _ascii_to_unicode(self, text: str) -> str:
        """Convert ASCII braille text to Unicode braille, preserving newlines and tabs.

        Raises on a character outside the North American Braille ASCII table
        rather than silently treating it as a blank cell -- a blank cell
        reads downstream as a bar line, so a single stray/corrupted
        character used to inject a spurious mid-measure bar line with no
        error at all (found via a real corrupted-file repro: two stray
        'Ï' (U+00CF) characters silently fragmented two measures and threw
        off octave tracking for the rest of the piece). Matches CLAUDE.md's
        "never silent failures" rule.
        """
        result = []
        line = 1
        col = 0
        for char in text:
            if char in ("\n", "\r", "\t"):
                if char == "\n":
                    line += 1
                    col = 0
                result.append(char)
                continue
            col += 1
            if char.upper() not in ASCII_TO_DOTS:
                raise BrailleParseError(
                    f"Line {line}, column {col}: '{char}' is not a valid "
                    "North American Braille ASCII character. Check the "
                    "source file for a typo or a corrupted character at "
                    "this position."
                )
            result.append(ascii_braille_char_to_unicode(char))
        return "".join(result)
