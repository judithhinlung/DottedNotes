from dataclasses import dataclass
from enum import Enum, auto

TEMPO_TERMS: frozenset[str] = frozenset({
    'allegro', 'andante', 'adagio', 'presto', 'moderato',
    'largo', 'vivace', 'lento', 'prestissimo', 'allegretto',
    'andantino', 'grave', 'larghetto', 'allegro moderato',
    'poco allegro', 'con moto', 'a tempo',
})


class TextMarkingType(Enum):
    TEMPO = auto()
    EXPRESSION = auto()
    REHEARSAL = auto()
    GENERAL = auto()


@dataclass
class TextMarking:
    text: str
    type: TextMarkingType = TextMarkingType.GENERAL

    def is_longer_expression(self) -> bool:
        """True for a "longer expression" (BANA Par. 22.3.8: two or more
        words and/or abbreviations, so it necessarily contains a space) --
        False for a single word or abbreviation (Pars. 22.3.1/22.3.2)."""
        return ' ' in self.text.rstrip('.')

    def to_lilypond(self) -> str:
        if self.type == TextMarkingType.TEMPO:
            return f'\\tempo "{self.text}"'
        return f'\\mark \\markup {{ "{self.text}" }}'

    def to_braille(self, inline: bool = False) -> str:
        from dottednotes.parser.input_pipeline import ASCII_TO_DOTS

        if inline:
            # BANA Par. 22.3: a mid-piece word-sign expression ("dolce",
            # "rit.", "cresc.", etc.) is introduced by the word sign (dots
            # 3,4,5) and, per 22.3(b), is "brailled without capitalization"
            # regardless of how it's capitalized in print -- unlike the
            # header-tempo convention below, which does preserve
            # capitalization. The dot-3 separator 22.3(d) requires before an
            # ambiguous following sign is added by the caller (`Measure.
            # to_braille`), which is the one that knows what follows.
            from dottednotes.bana_symbols import WORD_SIGN
            text_to_encode = self.text.rstrip('.').lower()
            result = [WORD_SIGN]
            for char in text_to_encode:
                dots = ASCII_TO_DOTS.get(char.upper(), 0)
                result.append(chr(0x2800 + dots))
            # Par. 22.3.8: "An expression consisting of two or more words
            # and/or abbreviations...is enclosed between a pair of word
            # signs" -- a single word or abbreviation (Pars. 22.3.1/22.3.2)
            # gets only the one leading word sign above; a "longer
            # expression" (this text contains a space) needs the closing
            # word sign too. The required surrounding spaces (and, mid-
            # measure, a preceding music hyphen) are the caller's
            # responsibility (`Measure.to_braille`), which knows what's
            # adjacent to this marking.
            if self.is_longer_expression():
                result.append(WORD_SIGN)
            return ''.join(result)

        result = []
        text_to_encode = self.text.rstrip('.')
        for char in text_to_encode:
            if char.isupper():
                result.append('⠠')
                char = char.lower()
            dots = ASCII_TO_DOTS.get(char.upper(), 0)
            result.append(chr(0x2800 + dots))
        result.append('⠲')
        return ''.join(result)
