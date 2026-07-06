from dataclasses import dataclass

from dottednotes.bana_symbols import (
    ACCIDENTAL_CELLS,
    ACCIACCATURA_INDICATOR,
    ARTICULATION_CELLS,
    BAR_LINE_CELLS,
    BAR_LINE_SEQUENCES,
    CAPITAL_INDICATOR,
    CLEF_CELLS,
    DYNAMIC_CELLS,
    END_WORD_SIGN,
    GRACE_NOTE_INDICATOR,
    KEY_SIGNATURE_CELLS,
    LITERARY_PERIOD,
    NOTE_CELLS,
    OCTAVE_MARKS,
    ORNAMENT_CELLS,
    REST_CELLS,
    SLUR_CELLS,
    TIME_SIGNATURE_CELLS,
    SymbolCategory,
)
from dottednotes.parser.input_pipeline import decode_literary_braille


@dataclass
class BrailleToken:
    """A single classified braille cell (or multi-cell sequence) with source location."""
    character: str          # raw Unicode braille character(s) U+2800–U+28FF
    category: SymbolCategory
    position: int           # 0-based character index in the source string
    line: int               # 1-based line number


class BrailleTokenizer:
    """
    Converts a normalized Unicode braille string into a flat list of BrailleToken objects.

    Multi-cell sequences
    --------------------
    Several BANA cell types require lookahead to tokenize correctly:

    ⠣ (dots 1,2,6) — bar-line prefix:
        ⠣⠅⠄  section double bar
        ⠣⠅   final double bar
        ⠣⠶   forward repeat
        ⠣⠆   end repeat
        If none of the above match and the tokenizer is at a measure boundary,
        ⠣⠣⠣ / ⠣⠣ are flat key signatures (2–3 flats).
        ⠣ alone at a measure boundary: KEY_SIGNATURE only if followed by the
        number sign ⠼ (time sig on the same line) or whitespace/end-of-input
        (key sig alone on a line).  Otherwise ACCIDENTAL (flat).

    ⠩ (dots 1,4,6) — at a measure boundary:
        ⠩⠩⠩  3 sharps, ⠩⠩  2 sharps → KEY_SIGNATURE.
        ⠩ alone: KEY_SIGNATURE only if followed by ⠼ or whitespace/end-of-input.
        Otherwise → ACCIDENTAL (sharp).

    ⠼ (dots 3,4,5,6 = NUMBER_SIGN):
        3-char lookup in KEY_SIGNATURE_CELLS → KEY_SIGNATURE  (4–7 sharps/flats)
        3-char lookup in TIME_SIGNATURE_CELLS → TIME_SIGNATURE
        Otherwise → UNKNOWN.

    ⠜ (dots 3,4,5) — word sign / clef prefix:
        4-char lookup in CLEF_CELLS → CLEF
        3-char lookup in CLEF_CELLS → CLEF
        Otherwise → greedy collect until END_WORD_SIGN (⠄) or octave mark:
          buffer in DYNAMIC_CELLS → DYNAMIC
          otherwise → decode as literary braille → WORD_SIGN

    Measure-start tracking
    ----------------------
    `at_measure_start` is True at the beginning of the piece and after every
    BAR_LINE token.  It becomes False when a NOTE or OCTAVE_MARK is emitted.
    Key / time / clef tokens leave it unchanged (they all precede notes).

    Newlines increment the line counter; carriage returns and tabs are skipped.
    Unrecognized cells produce UNKNOWN rather than raising.
    """

    _BAR_LINE_PREFIX: str = '⠣'   # U+2823  dots 1,2,6
    _CLEF_PREFIX: str = '⠜'       # U+281C  dots 3,4,5
    _NUMBER_SIGN: str = '⠼'       # U+283C  dots 3,4,5,6
    _SHARP_CELL: str = '⠩'        # U+2829  dots 1,4,6

    def tokenize(self, text: str) -> list[BrailleToken]:
        tokens: list[BrailleToken] = []
        line = 1
        i = 0
        at_measure_start = True   # True at start-of-piece and after bar lines
        # True until the first key sig / time sig / clef / note / rest / bar line
        # is emitted.  CAPITAL_INDICATOR (⠠) is only valid as a literary capital
        # in the piece header; after that point ⠠ reverts to the octave-7 mark.
        header_active = True

        while i < len(text):
            char = text[i]

            # --- whitespace / control ---
            if char == '\n':
                if not at_measure_start:
                    # In BANA music braille each physical line holds a segment of
                    # measures separated by blank cells within the line.  The line
                    # break itself is the bar-line separator between the last measure
                    # on the line and the first measure on the next line.
                    tokens.append(BrailleToken('⠀', SymbolCategory.BAR_LINE, i, line))
                    at_measure_start = True
                line += 1
                i += 1
                continue
            if char in ('\r', '\t'):
                i += 1
                continue

            # --- word sign ⠜: clef (3–4 cells), dynamic, or literary text ---
            #
            # Clef sequences use fixed-width lookahead (tenor clef contains ⠐ which
            # has no dots 1/2/3 and would break greedy collection).  Everything else
            # uses a greedy collect-then-classify strategy:
            #
            #   1. Collect cells until END_WORD_SIGN (⠄, dot 3) or an octave mark.
            #      The BANA rule that "a note following a word-sign expression must be
            #      preceded by an octave mark" makes octave marks a reliable terminator.
            #      END_WORD_SIGN is consumed; the octave mark is left for the note parser.
            #   2. Classify the collected buffer:
            #      a. Match in DYNAMIC_CELLS → DYNAMIC token (all standard abbreviations).
            #      b. No match → decode cells as literary braille → WORD_SIGN token.
            #
            # This naturally handles multi-word expressions (e.g. "con moto"): the blank
            # cell between words is not an octave mark and not dot 3, so it is collected
            # and decoded as a space character.
            if char == self._CLEF_PREFIX:
                four = text[i:i + 4]
                three = text[i:i + 3]
                if four in CLEF_CELLS:
                    tokens.append(BrailleToken(four, SymbolCategory.CLEF, i, line))
                    i += 4
                    header_active = False
                    continue
                if three in CLEF_CELLS:
                    tokens.append(BrailleToken(three, SymbolCategory.CLEF, i, line))
                    i += 3
                    header_active = False
                    continue
                # Not a clef — collect greedily until end word sign or octave mark.
                start_pos = i
                buf = char
                i += 1
                while i < len(text):
                    c = text[i]
                    if c == END_WORD_SIGN:
                        i += 1  # consume end word sign, exclude from buffer
                        break
                    if c in OCTAVE_MARKS:
                        break  # leave octave mark for note parsing
                    buf += c
                    i += 1
                # Classify the collected buffer.
                if buf in DYNAMIC_CELLS:
                    tokens.append(BrailleToken(buf, SymbolCategory.DYNAMIC, start_pos, line))
                else:
                    decoded = decode_literary_braille(buf[1:])  # strip ⠜ prefix
                    tokens.append(BrailleToken(decoded, SymbolCategory.WORD_SIGN, start_pos, line))
                continue

            # --- number sign ⠼: key signature (4–7 acc.) or time signature ---
            elif char == self._NUMBER_SIGN:
                three = text[i:i + 3]
                if three in KEY_SIGNATURE_CELLS:
                    tokens.append(BrailleToken(
                        three, SymbolCategory.KEY_SIGNATURE, i, line))
                    i += 3
                    header_active = False
                    continue
                if three in TIME_SIGNATURE_CELLS:
                    tokens.append(BrailleToken(
                        three, SymbolCategory.TIME_SIGNATURE, i, line))
                    i += 3
                    header_active = False
                    continue
                # Unrecognized number-sign sequence
                tokens.append(BrailleToken(char, SymbolCategory.UNKNOWN, i, line))
                i += 1
                continue

            # --- bar-line prefix ⠣: bar lines, flat key sigs, or flat accidental ---
            elif char == self._BAR_LINE_PREFIX:
                three = text[i:i + 3]
                two = text[i:i + 2]
                # Bar line sequences take priority (longest match first)
                if three in BAR_LINE_SEQUENCES:
                    tokens.append(BrailleToken(
                        three, SymbolCategory.BAR_LINE, i, line))
                    i += 3
                    at_measure_start = True
                    header_active = False
                    continue
                if two in BAR_LINE_SEQUENCES:
                    tokens.append(BrailleToken(
                        two, SymbolCategory.BAR_LINE, i, line))
                    i += 2
                    at_measure_start = True
                    header_active = False
                    continue
                # At a measure boundary: check for flat key signatures
                if at_measure_start:
                    if three in KEY_SIGNATURE_CELLS:
                        tokens.append(BrailleToken(
                            three, SymbolCategory.KEY_SIGNATURE, i, line))
                        i += 3
                        header_active = False
                        continue
                    if two in KEY_SIGNATURE_CELLS:
                        tokens.append(BrailleToken(
                            two, SymbolCategory.KEY_SIGNATURE, i, line))
                        i += 2
                        header_active = False
                        continue
                    if char in KEY_SIGNATURE_CELLS:
                        # Single flat: KEY_SIGNATURE only when followed by the number
                        # sign (time sig on same line) or whitespace/end-of-input (key
                        # sig alone on a line).  Otherwise it's a flat accidental.
                        next_char = text[i + 1] if i + 1 < len(text) else ''
                        if next_char == self._NUMBER_SIGN or next_char in ('\n', '\r', '\t', ''):
                            tokens.append(BrailleToken(
                                char, SymbolCategory.KEY_SIGNATURE, i, line))
                            i += 1
                            header_active = False
                            continue
                # Not a bar line or key sig → flat accidental
                tokens.append(BrailleToken(char, SymbolCategory.ACCIDENTAL, i, line))
                i += 1
                continue

            # --- sharp cell ⠩ at a measure boundary: key signature ---
            elif char == self._SHARP_CELL and at_measure_start:
                three = text[i:i + 3]
                two = text[i:i + 2]
                if three in KEY_SIGNATURE_CELLS:
                    tokens.append(BrailleToken(
                        three, SymbolCategory.KEY_SIGNATURE, i, line))
                    i += 3
                    header_active = False
                    continue
                if two in KEY_SIGNATURE_CELLS:
                    tokens.append(BrailleToken(
                        two, SymbolCategory.KEY_SIGNATURE, i, line))
                    i += 2
                    header_active = False
                    continue
                if char in KEY_SIGNATURE_CELLS:
                    # Single sharp: KEY_SIGNATURE only when followed by the number
                    # sign (time sig on same line) or whitespace/end-of-input (key
                    # sig alone on a line).  Otherwise it's a sharp accidental.
                    next_char = text[i + 1] if i + 1 < len(text) else ''
                    if next_char == self._NUMBER_SIGN or next_char in ('\n', '\r', '\t', ''):
                        tokens.append(BrailleToken(
                            char, SymbolCategory.KEY_SIGNATURE, i, line))
                        i += 1
                        header_active = False
                        continue
                # ⠩ not classified as key sig → sharp accidental

            # --- ornaments / articulations / slur-tie: longest match first ---
            # Several ornament, articulation, and slur pairs begin with cells
            # that are also OCTAVE_MARKS (⠐, ⠰, ⠸, ⠨, ⠘, ⠠, ⠈).
            # Ornament 3-cell sequences must be checked before their 2-cell prefixes,
            # and all ornament multi-cell forms must be checked before articulations
            # and octave marks so that e.g. ⠐⠖⠇ (lower mordent) takes priority
            # over ⠐ (octave 4) and ⠐⠦ (mezzo staccato).
            three = text[i:i + 3]
            two = text[i:i + 2]

            # Ornament 3-cell sequences
            if three in ORNAMENT_CELLS:
                tokens.append(BrailleToken(three, SymbolCategory.ORNAMENT, i, line))
                i += 3
                continue
            # Ornament 2-cell sequences (including long appoggiatura ⠐⠢)
            if two in ORNAMENT_CELLS or two == ACCIACCATURA_INDICATOR:
                tokens.append(BrailleToken(two, SymbolCategory.ORNAMENT, i, line))
                i += 2
                continue
            # Articulation 2-cell sequences
            if two in ARTICULATION_CELLS:
                tokens.append(BrailleToken(two, SymbolCategory.ARTICULATION, i, line))
                i += 2
                continue
            # Slur/tie 2-cell sequences
            if two in SLUR_CELLS:
                tokens.append(BrailleToken(two, SymbolCategory.SLUR, i, line))
                i += 2
                continue
            # Ornament 1-cell sequences (short appoggiatura ⠢, trill ⠖, turn ⠲)
            if char in ORNAMENT_CELLS or char == GRACE_NOTE_INDICATOR:
                tokens.append(BrailleToken(char, SymbolCategory.ORNAMENT, i, line))
                i += 1
                continue
            if char in ARTICULATION_CELLS:
                tokens.append(BrailleToken(char, SymbolCategory.ARTICULATION, i, line))
                i += 1
                continue
            if char in SLUR_CELLS:
                tokens.append(BrailleToken(char, SymbolCategory.SLUR, i, line))
                i += 1
                continue

            # --- capital letter indicator ⠠: literary text in piece header ---
            # ⠠⠦ (staccatissimo) was already consumed by the 2-cell articulation check
            # above.  In the piece header (before the first key sig / time sig / note),
            # any remaining ⠠ is a capital letter indicator starting a literary-braille
            # text marking (e.g. "Allegro moderato.").  Collect cells until the literary
            # period ⠲ (dots 2,5,6) or end of line; decode each cell as a letter and
            # capitalise the first letter after each ⠠ capital indicator.
            # Once header_active is False (musical content has started), ⠠ falls through
            # to _classify() and is treated as the octave-7 mark.
            if char == CAPITAL_INDICATOR and header_active:
                start_pos = i
                i += 1  # consume the capital indicator
                text_chars: list[str] = []
                capitalize_next = True  # the indicator just consumed → next letter uppercase
                while i < len(text):
                    c = text[i]
                    if c == LITERARY_PERIOD:
                        i += 1  # consume and discard the period terminator
                        break
                    if c in ('\n', '\r'):
                        break   # end of line terminates without consuming
                    if c == CAPITAL_INDICATOR:
                        capitalize_next = True
                        i += 1
                        continue
                    letter = decode_literary_braille(c)
                    if capitalize_next and letter.isalpha():
                        letter = letter.upper()
                        capitalize_next = False
                    text_chars.append(letter)
                    i += 1
                decoded_text = ''.join(text_chars).strip()
                tokens.append(BrailleToken(decoded_text, SymbolCategory.WORD_SIGN, start_pos, line))
                continue

            # --- general single-cell classification ---
            cat = self._classify(char)
            tokens.append(BrailleToken(char, cat, i, line))
            if cat in (SymbolCategory.NOTE, SymbolCategory.OCTAVE_MARK):
                at_measure_start = False
                header_active = False
            elif cat == SymbolCategory.BAR_LINE:
                at_measure_start = True
                if char != '⠀':  # blank cells are spacing, not musical content
                    header_active = False
            elif cat == SymbolCategory.REST:
                header_active = False
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
