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
    HAND_SIGN_CELLS,
    IN_ACCORD_CELLS,
    INTERVAL_CELLS,
    LITERARY_DIGITS,
    LITERARY_HYPHEN,
    KEY_SIGNATURE_CELLS,
    LITERARY_PERIOD,
    LOWER_DIGIT_CELLS,
    MEASURE_REPEAT_CELL,
    NOTE_CELLS,
    OCTAVE_MARKS,
    ORNAMENT_CELLS,
    REST_CELLS,
    SLUR_CELLS,
    TIME_SIGNATURE_CELLS,
    TRIPLET_INDICATOR,
    SymbolCategory,
)
from dottednotes.parser.input_pipeline import decode_literary_braille


@dataclass
class BrailleToken:
    """A single classified braille cell (or multi-cell sequence) with source location."""
    character: str          # decoded/classified value (raw cells for most categories;
                             # plain decoded text for WORD_SIGN)
    category: SymbolCategory
    position: int           # 0-based character index in the source string
    line: int               # 1-based line number
    raw: str = ""           # original, undecoded Unicode braille cells this token came
                             # from. Defaults to `character` (already raw for every
                             # category except WORD_SIGN, where `character` is decoded
                             # plain text and `raw` must be set explicitly at creation).

    def __post_init__(self) -> None:
        if not self.raw:
            self.raw = self.character


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
        ⠣⠃   down-bow (BANA Sec. 25.3) → ARTICULATION
        ⠣⠄   up-bow (BANA Sec. 25.3) → ARTICULATION
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
        ⠼ + LITERARY_DIGITS (+ ⠍) → MULTI_MEASURE_REST
        ⠼ + LITERARY_DIGITS (+ ⠼ + LITERARY_DIGITS), between spaces →
            NUMERAL_REPEAT (backward-numeral repeat, BANA Sec. 19.1.1 — not
            supported; BrailleParser raises on this token)
        ⠼ + LOWER_DIGIT_CELLS (+ LITERARY_HYPHEN + LOWER_DIGIT_CELLS), between
            spaces → NUMERAL_REPEAT (measure-number repeat, BANA Sec. 19.1.2 —
            same as above)
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

    def tokenize(
        self,
        text: str,
        at_line_start: bool = True,
        margin_numbers_use_number_sign: bool = False,
    ) -> list[BrailleToken]:
        tokens: list[BrailleToken] = []
        line = 1
        i = 0
        at_measure_start = True   # True at start-of-piece and after bar lines
        # True at start-of-piece and after each newline. Callers tokenizing a
        # fragment that is known NOT to be a genuine physical line start (e.g.
        # EnsembleParser re-tokenizing an abbreviation-stripped mid-stream
        # measure fragment) should pass at_line_start=False -- otherwise a
        # real first note that happens to share a cell with a literary digit
        # gets misread as a measure-number token and silently dropped.
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
                at_line_start = True
                i += 1
                continue
            if char in ('\r', '\t'):
                i += 1
                continue

            # --- measure number at line start ---
            # BANA music braille places an explicit measure number at the left
            # margin of each system.  It uses literary braille letter-digits
            # (A–J = 1–0) WITHOUT a number-sign prefix, followed by at least one
            # blank cell (⠀) before the musical content.
            #
            # Disambiguation: digits 4–9 and 0 share dot patterns with 8th-note
            # cells, and digit 3 shares with the slur cell.  Position state
            # (at_line_start) is the primary discriminator.  A look-ahead
            # confirming that a blank cell (⠀) follows the digit sequence
            # distinguishes a measure number from a musical cell at column 0 in
            # a score that uses no measure numbers.
            if at_line_start and char in LITERARY_DIGITS:
                j = i
                digit_values: list[int] = []
                while j < len(text) and text[j] in LITERARY_DIGITS:
                    digit_values.append(LITERARY_DIGITS[text[j]])
                    j += 1
                # Emit MEASURE_NUMBER when at least one digit is found.
                # BANA rule: an octave mark is required before the first note at
                # line start, so a bare note-class cell at column 0 is always a
                # measure-number digit, never a musical note.
                if digit_values:
                    number = int(''.join(str(d) for d in digit_values))
                    # Store decoded integer as string (consistent with WORD_SIGN convention).
                    tokens.append(BrailleToken(str(number), SymbolCategory.MEASURE_NUMBER, i, line))
                    i = j
                    # Consume any trailing blank cells (measure-number separator).
                    while i < len(text) and text[i] == '⠀':
                        i += 1
                    at_line_start = False
                    continue
                # No digits found — fall through and process normally.
            elif at_line_start and margin_numbers_use_number_sign and char == self._NUMBER_SIGN:
                # Lead-sheet margin measure numbers (BANA Sec. 27) are written
                # WITH the number-sign prefix, unlike plain-score margins
                # above -- confirmed by the developer. Opt-in only
                # (`margin_numbers_use_number_sign`) so solo/ensemble parsing
                # keeps reading a line-start NUMBER_SIGN+digits run as a BANA
                # Sec. 19 numeral repeat (the generic ⠼ handling below).
                j = i + 1
                digit_values = []
                while j < len(text) and text[j] in LITERARY_DIGITS:
                    digit_values.append(LITERARY_DIGITS[text[j]])
                    j += 1
                next_char = text[j] if j < len(text) else ''
                if digit_values and next_char in (' ', '⠀', '\n', '\r', '\t', ''):
                    number = int(''.join(str(d) for d in digit_values))
                    tokens.append(BrailleToken(str(number), SymbolCategory.MEASURE_NUMBER, i, line))
                    i = j
                    while i < len(text) and text[i] == '⠀':
                        i += 1
                    at_line_start = False
                    continue
                # Not a margin number after all — fall through and process normally.
            at_line_start = False

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
                consumed_end_word_sign = False
                while i < len(text):
                    c = text[i]
                    if c == END_WORD_SIGN:
                        i += 1  # consume end word sign, exclude from buffer
                        consumed_end_word_sign = True
                        break
                    if c in OCTAVE_MARKS:
                        break  # leave octave mark for note parsing
                    if c in ARTICULATION_CELLS or c == MEASURE_REPEAT_CELL:
                        # A word-sign/dynamic expression missing its closing
                        # END_WORD_SIGN (a real transcription gap -- confirmed
                        # against Fengyang_Flower_Drum.brf, e.g. an unclosed
                        # ">MP" immediately followed by a staccato mark or a
                        # measure-repeat sign) must not swallow an unrelated
                        # articulation/repeat cell into the buffer: neither
                        # ever legitimately appears inside literary word text
                        # or any DYNAMIC_CELLS entry, so treat them as
                        # terminators too, leaving them for note parsing.
                        break
                    buf += c
                    i += 1
                # raw_cells preserves the true original cells (including the
                # end word sign, when present) so callers that need to
                # round-trip this token back to braille (e.g. EnsembleParser
                # reconstructing a per-instrument stream) don't have to
                # re-encode already-decoded text — see BrailleToken.raw.
                raw_cells = buf + (END_WORD_SIGN if consumed_end_word_sign else "")
                # Classify the collected buffer.
                if buf in DYNAMIC_CELLS:
                    tokens.append(BrailleToken(buf, SymbolCategory.DYNAMIC, start_pos, line, raw=raw_cells))
                else:
                    decoded = decode_literary_braille(buf[1:])  # strip ⠜ prefix
                    tokens.append(BrailleToken(decoded, SymbolCategory.WORD_SIGN, start_pos, line, raw=raw_cells))
                continue

            # --- number sign ⠼: key/time signature at measure boundary;
            #     4th interval when mid-measure (not at_measure_start) ---
            elif char == self._NUMBER_SIGN:
                if at_measure_start:
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

                    # Check for multi-measure rest: ⠼ followed by literary digits followed by ⠍
                    j = i + 1
                    while j < len(text) and text[j] in LITERARY_DIGITS:
                        j += 1
                    if j > i + 1 and j < len(text) and text[j] == '⠍':
                        next_char = text[j+1] if j+1 < len(text) else ''
                        if next_char in (' ', '⠀', '\n', '\r', '\t', ''):
                            seq = text[i:j + 1]
                            tokens.append(BrailleToken(seq, SymbolCategory.MULTI_MEASURE_REST, i, line))
                            i = j + 1
                            at_measure_start = False
                            header_active = False
                            continue

                    # Braille numeral repeats (S8-5, BANA Sec. 19, Table 19) --
                    # not supported (BrailleParser raises on this category).
                    # Backward-numeral repeat: NUMBER_SIGN + one-or-more
                    # LITERARY_DIGITS, optionally followed immediately by a
                    # second NUMBER_SIGN + LITERARY_DIGITS run (the disjunct
                    # form, e.g. "#e#d" = 5 measures back, repeat 4),
                    # terminated by a blank cell/newline/end-of-input (Sec.
                    # 19.1.1: "between blank spaces").
                    j = i + 1
                    while j < len(text) and text[j] in LITERARY_DIGITS:
                        j += 1
                    if j > i + 1:
                        k = j
                        if k < len(text) and text[k] == self._NUMBER_SIGN:
                            k2 = k + 1
                            while k2 < len(text) and text[k2] in LITERARY_DIGITS:
                                k2 += 1
                            if k2 > k + 1:
                                j = k2
                        next_char = text[j] if j < len(text) else ''
                        if next_char in (' ', '⠀', '\n', '\r', '\t', ''):
                            tokens.append(BrailleToken(
                                text[i:j], SymbolCategory.NUMERAL_REPEAT, i, line))
                            i = j
                            at_measure_start = False
                            header_active = False
                            continue

                    # Measure-number repeat: NUMBER_SIGN + one-or-more
                    # LOWER_DIGIT_CELLS digits, optionally + LITERARY_HYPHEN +
                    # more LOWER_DIGIT_CELLS digits (inclusive range, e.g.
                    # "#2-4"), terminated the same way (Sec. 19.1.2: "brailled,
                    # between spaces, using lower-cell numerals").
                    if i + 1 < len(text) and text[i + 1] in LOWER_DIGIT_CELLS:
                        j = i + 1
                        while j < len(text) and text[j] in LOWER_DIGIT_CELLS:
                            j += 1
                        if j < len(text) and text[j] == LITERARY_HYPHEN:
                            k = j + 1
                            while k < len(text) and text[k] in LOWER_DIGIT_CELLS:
                                k += 1
                            if k > j + 1:
                                j = k
                        next_char = text[j] if j < len(text) else ''
                        if next_char in (' ', '⠀', '\n', '\r', '\t', ''):
                            tokens.append(BrailleToken(
                                text[i:j], SymbolCategory.NUMERAL_REPEAT, i, line))
                            i = j
                            at_measure_start = False
                            header_active = False
                            continue

                    # Unrecognized number-sign sequence at measure boundary
                    tokens.append(BrailleToken(char, SymbolCategory.UNKNOWN, i, line))
                    i += 1
                    continue
                else:
                    # Mid-measure: ⠼ is the 4th interval sign
                    tokens.append(BrailleToken(char, SymbolCategory.INTERVAL, i, line))
                    i += 1
                    continue

            # --- bar-line prefix ⠣: bar lines, flat key sigs, or flat accidental ---
            elif char == self._BAR_LINE_PREFIX:
                three = text[i:i + 3]
                two = text[i:i + 2]
                # Piano damper pedal down: ⠣⠉
                if two == '⠣⠉':
                    tokens.append(BrailleToken(two, SymbolCategory.PEDAL, i, line))
                    i += 2
                    continue
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
                # Full-measure in-accord (⠣⠜): must be checked before flat key sigs
                # and flat accidental fallthrough.  ⠣⠜ is never a bar line or key sig.
                if two == '⠣⠜':
                    tokens.append(BrailleToken(two, SymbolCategory.IN_ACCORD, i, line))
                    i += 2
                    continue
                # Bowing marks (S8b-2, down-bow ⠣⠃ / up-bow ⠣⠄): must be checked
                # before flat key sigs and flat accidental fallthrough for the
                # same reason as ⠣⠜ above -- neither is ever a bar line or key
                # sig, and KEY_SIGNATURE_CELLS' own ⠣-prefixed keys (⠣, ⠣⠣, ⠣⠣⠣)
                # never collide with these two 2-char sequences.
                if two in ARTICULATION_CELLS:
                    tokens.append(BrailleToken(two, SymbolCategory.ARTICULATION, i, line))
                    i += 2
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

            # --- natural cell ⠡: pedal up / change / natural accidental ---
            elif char == '⠡':
                three = text[i:i + 3]
                two = text[i:i + 2]
                if three == '⠡⠣⠉':
                    tokens.append(BrailleToken(three, SymbolCategory.PEDAL, i, line))
                    i += 3
                    continue
                if two == '⠡⠉':
                    tokens.append(BrailleToken(two, SymbolCategory.PEDAL, i, line))
                    i += 2
                    continue

            # --- ornaments / articulations / slur-tie: longest match first ---
            # Several ornament, articulation, and slur pairs begin with cells
            # that are also OCTAVE_MARKS (⠐, ⠰, ⠸, ⠨, ⠘, ⠠, ⠈).
            # Ornament 3-cell sequences must be checked before their 2-cell prefixes,
            # and all ornament multi-cell forms must be checked before articulations
            # and octave marks so that e.g. ⠐⠖⠇ (lower mordent) takes priority
            # over ⠐ (octave 4) and ⠐⠦ (mezzo staccato).
            three = text[i:i + 3]
            two = text[i:i + 2]

            # Piano pedal signs: half pedal ⠐⠣⠉, pedal up after strike ⠐⠡⠉, pedal down after strike ⠠⠣⠉
            if three in ('⠐⠣⠉', '⠐⠡⠉', '⠠⠣⠉'):
                tokens.append(BrailleToken(three, SymbolCategory.PEDAL, i, line))
                i += 3
                continue

            # Hand-sign 2-cell sequences (right ⠨⠜, left ⠸⠜), marking which
            # physical staff the following line's measures belong to. Must be
            # checked before single-cell octave-mark fallback because ⠨ and ⠸
            # are also OCTAVE_MARKS, and before IN_ACCORD_CELLS so that ⠨⠜
            # (right hand) is never confused with ⠨⠅ (measure_division) —
            # exact 2-character dict-key lookup already disambiguates both.
            if two in HAND_SIGN_CELLS:
                tokens.append(BrailleToken(HAND_SIGN_CELLS[two], SymbolCategory.HAND_SIGN, i, line))
                i += 2
                header_active = False
                if i < len(text) and text[i] == END_WORD_SIGN:
                    i += 1  # consume disambiguating end-word-sign; no token emitted
                continue

            # In-accord 2-cell sequences (part_measure ⠐⠂ and measure_division ⠨⠅).
            # Must be checked before single-cell octave-mark / ornament / articulation
            # fallback because ⠐ and ⠨ are also OCTAVE_MARKS.
            # The full-measure sign ⠣⠜ is handled above in the ⠣ block.
            if two in IN_ACCORD_CELLS:
                tokens.append(BrailleToken(two, SymbolCategory.IN_ACCORD, i, line))
                i += 2
                continue

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
                tokens.append(BrailleToken(decoded_text, SymbolCategory.WORD_SIGN, start_pos, line, raw=text[start_pos:i]))
                continue

            # --- multi-measure rests ⠍⠍, ⠍⠍⠍ at measure start ---
            if at_measure_start:
                if text[i:i+3] == '⠍⠍⠍':
                    next_char = text[i+3] if i+3 < len(text) else ''
                    if next_char in (' ', '⠀', '\n', '\r', '\t', ''):
                        tokens.append(BrailleToken('⠍⠍⠍', SymbolCategory.MULTI_MEASURE_REST, i, line))
                        i += 3
                        at_measure_start = False
                        header_active = False
                        continue
                elif text[i:i+2] == '⠍⠍':
                    next_char = text[i+2] if i+2 < len(text) else ''
                    if next_char in (' ', '⠀', '\n', '\r', '\t', ''):
                        tokens.append(BrailleToken('⠍⠍', SymbolCategory.MULTI_MEASURE_REST, i, line))
                        i += 2
                        at_measure_start = False
                        header_active = False
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
        # Interval cells (⠼ is handled above in the NUMBER_SIGN block;
        # the remaining six are unambiguous at any position)
        if char in INTERVAL_CELLS and char != '⠼':
            return SymbolCategory.INTERVAL
        if char == END_WORD_SIGN:
            return SymbolCategory.AUGMENTATION_DOT
        if char == TRIPLET_INDICATOR:
            return SymbolCategory.TRIPLET_INDICATOR
        if char == MEASURE_REPEAT_CELL:
            return SymbolCategory.REPEAT
        return SymbolCategory.UNKNOWN
