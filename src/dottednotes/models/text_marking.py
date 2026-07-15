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

    def to_lilypond(self) -> str:
        if self.type == TextMarkingType.TEMPO:
            return f'\\tempo "{self.text}"'
        return f'\\mark \\markup {{ "{self.text}" }}'

    def to_braille(self) -> str:
        from dottednotes.parser.input_pipeline import ASCII_TO_DOTS
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
