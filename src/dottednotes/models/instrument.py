from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class InstrumentFamily(Enum):
    WOODWIND = "Woodwind"
    BRASS = "Brass"
    PERCUSSION = "Percussion"
    KEYBOARD_HARP = "KeyboardHarp"
    STRING = "String"
    VOCAL = "Vocal"


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
    'Soprano': InstrumentFamily.VOCAL,
    'Alto': InstrumentFamily.VOCAL,
    'Tenor': InstrumentFamily.VOCAL,
    'Bass': InstrumentFamily.VOCAL,
    'Voice': InstrumentFamily.VOCAL,
    'Vocal': InstrumentFamily.VOCAL,
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

    # Vocal
    # Note: bare 'bass' is deliberately excluded here (unlike the exact-match
    # 'Bass': VOCAL entry above) -- it would misclassify names like "Basso
    # continuo" or an orchestral "Bass" (double bass) shorthand.
    if any(k in lower_name for k in ['voice', 'vocal', 'soprano', 'alto', 'tenor', 'baritone', 'contralto', 'mezzo', 'cantus', 'singing', 'chorus', 'choir']):
        return InstrumentFamily.VOCAL

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


# ---------------------------------------------------------------------------
# MIDI instrument names (S5b-8, "\set Staff.midiInstrument = ...").
#
# These are General MIDI Program Names as defined by the MIDI standard
# itself (not a BANA convention), verified against the LilyPond Notation
# Reference's MIDI instruments list (Documentation/notation/midi-instruments)
# rather than assumed from memory, per CLAUDE.md's mandate for LilyPond
# syntax. General MIDI has no dedicated patch for every orchestral
# instrument (e.g. bass clarinet, double bassoon) -- those fall back to
# the closest available GM instrument (clarinet, bassoon).
# ---------------------------------------------------------------------------

_NAME_TO_MIDI_INSTRUMENT: dict[str, str] = {
    'Piccolo': 'piccolo',
    'Flute': 'flute',
    'Oboe': 'oboe',
    'English horn': 'english horn',
    'Clarinet': 'clarinet',
    'Bass clarinet': 'clarinet',       # no dedicated GM patch
    'Bassoon': 'bassoon',
    'Double bassoon': 'bassoon',       # no dedicated GM patch
    'Horn': 'french horn',
    'Trumpet': 'trumpet',
    'Trombone': 'trombone',
    'Tuba': 'tuba',
    'Kettledrums': 'timpani',
    'Harp right hand': 'orchestral harp',
    'Harp left hand': 'orchestral harp',
    'Piano right hand': 'acoustic grand',
    'Piano left hand': 'acoustic grand',
    'Violin I': 'violin',
    'Violin II': 'violin',
    'Viola': 'viola',
    'Violoncello': 'cello',
    'Double bass': 'contrabass',
}


def get_midi_instrument_name(name: str) -> str | None:
    """Resolve an instrument name to a General MIDI instrument name string
    for \\set Staff.midiInstrument, or None if there's no reasonable match.

    Uses an exact Table-29-style name match first (case-insensitive), then
    falls back to family-based keyword matching (mirroring
    get_instrument_family's fallback) for names outside that roster --
    e.g. a bare "Violin" or "Cello" without a part number.
    """
    normalized_name = name.strip()
    for known_name, midi_name in _NAME_TO_MIDI_INSTRUMENT.items():
        if known_name.lower() == normalized_name.lower():
            return midi_name

    lower_name = normalized_name.lower()
    if 'piccolo' in lower_name:
        return 'piccolo'
    if 'flute' in lower_name:
        return 'flute'
    if 'english horn' in lower_name:
        return 'english horn'
    if 'oboe' in lower_name:
        return 'oboe'
    if 'clarinet' in lower_name:
        return 'clarinet'
    if 'bassoon' in lower_name:
        return 'bassoon'
    if 'horn' in lower_name:
        return 'french horn'
    if 'trumpet' in lower_name:
        return 'trumpet'
    if 'trombone' in lower_name:
        return 'trombone'
    if 'tuba' in lower_name:
        return 'tuba'
    if 'timpani' in lower_name or 'kettledrum' in lower_name:
        return 'timpani'
    if 'harp' in lower_name:
        return 'orchestral harp'
    if 'piano' in lower_name:
        return 'acoustic grand'
    if 'violin' in lower_name or 'fiddle' in lower_name:
        return 'violin'
    if 'viola' in lower_name:
        return 'viola'
    if 'violoncello' in lower_name or 'cello' in lower_name:
        return 'cello'
    if 'double bass' in lower_name or 'contrabass' in lower_name:
        return 'contrabass'

    return None
