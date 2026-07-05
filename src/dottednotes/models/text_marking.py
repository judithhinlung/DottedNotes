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
