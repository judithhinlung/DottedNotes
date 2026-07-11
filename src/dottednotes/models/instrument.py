from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class InstrumentFamily(Enum):
    WOODWIND = "Woodwind"
    BRASS = "Brass"
    PERCUSSION = "Percussion"
    KEYBOARD_HARP = "KeyboardHarp"
    STRING = "String"


_NAME_TO_FAMILY: dict[str, InstrumentFamily] = {
    'Piccolo': InstrumentFamily.WOODWIND,
    'Flute': InstrumentFamily.WOODWIND,
    'Oboe': InstrumentFamily.WOODWIND,
    'English horn': InstrumentFamily.WOODWIND,
    'Clarinet': InstrumentFamily.WOODWIND,
    'Bass clarinet': InstrumentFamily.WOODWIND,
    'Bassoon': InstrumentFamily.WOODWIND,
    'Double bassoon': InstrumentFamily.WOODWIND,
    'Horn': InstrumentFamily.BRASS,
    'Trumpet': InstrumentFamily.BRASS,
    'Trombone': InstrumentFamily.BRASS,
    'Tuba': InstrumentFamily.BRASS,
    'Kettledrums': InstrumentFamily.PERCUSSION,
    'Cymbals': InstrumentFamily.PERCUSSION,
    'Triangle': InstrumentFamily.PERCUSSION,
    'Snare drum': InstrumentFamily.PERCUSSION,
    'Bass drum': InstrumentFamily.PERCUSSION,
    'Harp right hand': InstrumentFamily.KEYBOARD_HARP,
    'Harp left hand': InstrumentFamily.KEYBOARD_HARP,
    'Piano right hand': InstrumentFamily.KEYBOARD_HARP,
    'Piano left hand': InstrumentFamily.KEYBOARD_HARP,
    'Violin I': InstrumentFamily.STRING,
    'Violin II': InstrumentFamily.STRING,
    'Viola': InstrumentFamily.STRING,
    'Violoncello': InstrumentFamily.STRING,
    'Double bass': InstrumentFamily.STRING,
}


def get_instrument_family(name: str) -> InstrumentFamily | None:
    """Resolve an instrument name to its InstrumentFamily.

    Uses Table 29 exact match first, then falls back to keyword matching
    for custom/overridden names, and returns None if no match.
    """
    normalized_name = name.strip()
    for known_name, family in _NAME_TO_FAMILY.items():
        if known_name.lower() == normalized_name.lower():
            return family

    lower_name = normalized_name.lower()
    
    # Keyboard & Harp
    if any(k in lower_name for k in ['piano', 'harp', 'organ', 'harpsichord', 'keyboard', 'clav', 'right hand', 'left hand', 'rh', 'lh', 'hand']):
        return InstrumentFamily.KEYBOARD_HARP
    
    # Strings
    if any(k in lower_name for k in ['violin', 'viola', 'violoncello', 'cello', 'double bass', 'contrabass', 'string', 'fiddle']):
        return InstrumentFamily.STRING
        
    # Woodwinds
    if any(k in lower_name for k in ['flute', 'oboe', 'clarinet', 'bassoon', 'piccolo', 'english horn', 'recorder', 'reed', 'pipe', 'woodwind']):
        return InstrumentFamily.WOODWIND
        
    # Brass
    if any(k in lower_name for k in ['horn', 'trumpet', 'trombone', 'tuba', 'cornet', 'euphonium', 'brass']):
        return InstrumentFamily.BRASS
        
    # Percussion
    if any(k in lower_name for k in ['drum', 'cymbal', 'triangle', 'percussion', 'timpani', 'kettledrum', 'xylophone', 'marimba', 'gong', 'snare', 'bass drum']):
        return InstrumentFamily.PERCUSSION

    return None


@dataclass
class InstrumentInfo:
    """One entry from a BANA §33.2 instrument-list header.

    part_number is the primary §33.2.2 numbering digit (e.g. "1" for
    "Violin I"); sub_number is the further-division digit (e.g. "1" for
    "Violins I-1"). Both are None when the instrument isn't numbered.
    """
    name: str
    abbreviation: str
    part_number: str | None = None
    sub_number: str | None = None

    @property
    def family(self) -> InstrumentFamily | None:
        """The InstrumentFamily for this instrument, inferred from name."""
        return get_instrument_family(self.name)
