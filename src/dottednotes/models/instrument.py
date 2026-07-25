from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .clef import ClefType


class InstrumentFamily(Enum):
    WOODWIND = "Woodwind"
    BRASS = "Brass"
    PERCUSSION = "Percussion"
    KEYBOARD_HARP = "KeyboardHarp"
    STRING = "String"
    PLUCKED_STRING = "PluckedString"
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
    'Guitar': InstrumentFamily.PLUCKED_STRING,
    'Banjo': InstrumentFamily.PLUCKED_STRING,
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

    # Plucked Strings
    if any(k in lower_name for k in ['guitar', 'banjo', 'mandolin', 'ukulele']) or \
       any(w == 'lute' for w in lower_name.replace('-', ' ').split()):
        return InstrumentFamily.PLUCKED_STRING
        
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


# ---------------------------------------------------------------------------
# Conventional clefs (S10d-12 fix): which clef an instrument is
# *conventionally* notated in, independent of the actual register any
# particular passage happens to sit in. Deliberately excludes Piano/Harp
# hands and unpitched percussion -- those have no single fixed clef (a
# piano left hand can legitimately cross into treble territory), so those
# fall through to Staff._resolve_clef()'s existing register-based heuristic
# instead.
# ---------------------------------------------------------------------------

_NAME_TO_CLEF: dict[str, ClefType] = {
    'Piccolo': ClefType.TREBLE,
    'Flute': ClefType.TREBLE,
    'Oboe': ClefType.TREBLE,
    'English horn': ClefType.TREBLE,
    'Clarinet': ClefType.TREBLE,
    'Bass clarinet': ClefType.TREBLE,
    'Bassoon': ClefType.BASS,
    'Double bassoon': ClefType.BASS,
    'Horn': ClefType.TREBLE,
    'Trumpet': ClefType.TREBLE,
    'Trombone': ClefType.BASS,
    'Tuba': ClefType.BASS,
    'Kettledrums': ClefType.BASS,
    'Violin I': ClefType.TREBLE,
    'Violin II': ClefType.TREBLE,
    'Viola': ClefType.ALTO,
    'Violoncello': ClefType.BASS,
    'Double bass': ClefType.BASS,
    'Guitar': ClefType.TREBLE,
    'Banjo': ClefType.TREBLE,
    'Soprano': ClefType.TREBLE,
    'Alto': ClefType.TREBLE,
    'Tenor': ClefType.TREBLE,
    'Bass': ClefType.BASS,
    'Voice': ClefType.TREBLE,
    'Vocal': ClefType.TREBLE,
}


def get_default_clef(name: str) -> ClefType | None:
    """Resolve an instrument name to its conventional clef, or None if the
    instrument has no single fixed convention (e.g. piano/harp hands,
    unpitched percussion) or isn't recognized.

    Uses a Table-29-style exact match first, then falls back to keyword
    matching (mirroring get_instrument_family's fallback) for names outside
    that roster -- e.g. a MusicXML part named "Cello" or "Vln. 2" rather
    than the canonical "Violoncello"/"Violin II".
    """
    normalized_name = name.strip()
    for known_name, clef_type in _NAME_TO_CLEF.items():
        if known_name.lower() == normalized_name.lower():
            return clef_type

    lower_name = normalized_name.lower()

    if 'viola' in lower_name:
        return ClefType.ALTO

    if any(k in lower_name for k in ['violoncello', 'cello', 'double bass', 'contrabass', 'bassoon', 'trombone', 'tuba']):
        return ClefType.BASS

    if any(k in lower_name for k in ['violin', 'guitar', 'banjo', 'trumpet', 'horn', 'flute', 'oboe', 'clarinet', 'piccolo', 'soprano', 'voice']):
        return ClefType.TREBLE

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


# ---------------------------------------------------------------------------
# Full General MIDI instrument list (S12-1, BANA Sec. 24 single-line format),
# in General MIDI program order, verified against the LilyPond Notation
# Reference's MIDI instruments list (Documentation/notation/midi-instruments)
# rather than assumed from memory. Unlike get_midi_instrument_name's name-
# based heuristic above (used when an instrument *name* is already known,
# e.g. from a BANA Sec. 33.2 ensemble header), this is the closed set of
# names --instrument/the web UI's instrument dropdown accept: a BANA Sec. 24
# single-line-format piece's braille never states which instrument it's
# for (Secs. 24.1-24.5 describe only segment/measure-number layout, never an
# in-line instrument name -- confirmed against the BANA manual), so the
# instrument must be supplied by the user from this exact list rather than
# parsed or guessed.
# ---------------------------------------------------------------------------

GENERAL_MIDI_INSTRUMENTS: tuple[str, ...] = (
    "acoustic grand", "bright acoustic", "electric grand", "honky-tonk",
    "electric piano 1", "electric piano 2", "harpsichord", "clav",
    "celesta", "glockenspiel", "music box", "vibraphone", "marimba",
    "xylophone", "tubular bells", "dulcimer", "drawbar organ",
    "percussive organ", "rock organ", "church organ", "reed organ",
    "accordion", "harmonica", "concertina", "acoustic guitar (nylon)",
    "acoustic guitar (steel)", "electric guitar (jazz)",
    "electric guitar (clean)", "electric guitar (muted)",
    "overdriven guitar", "distorted guitar", "guitar harmonics",
    "acoustic bass", "electric bass (finger)", "electric bass (pick)",
    "fretless bass", "slap bass 1", "slap bass 2", "synth bass 1",
    "synth bass 2", "violin", "viola", "cello", "contrabass",
    "tremolo strings", "pizzicato strings", "orchestral harp", "timpani",
    "string ensemble 1", "string ensemble 2", "synthstrings 1",
    "synthstrings 2", "choir aahs", "voice oohs", "synth voice",
    "orchestra hit", "trumpet", "trombone", "tuba", "muted trumpet",
    "french horn", "brass section", "synthbrass 1", "synthbrass 2",
    "soprano sax", "alto sax", "tenor sax", "baritone sax", "oboe",
    "english horn", "bassoon", "clarinet", "piccolo", "flute", "recorder",
    "pan flute", "blown bottle", "shakuhachi", "whistle", "ocarina",
    "lead 1 (square)", "lead 2 (sawtooth)", "lead 3 (calliope)",
    "lead 4 (chiff)", "lead 5 (charang)", "lead 6 (voice)",
    "lead 7 (fifths)", "lead 8 (bass+lead)", "pad 1 (new age)",
    "pad 2 (warm)", "pad 3 (polysynth)", "pad 4 (choir)", "pad 5 (bowed)",
    "pad 6 (metallic)", "pad 7 (halo)", "pad 8 (sweep)", "fx 1 (rain)",
    "fx 2 (soundtrack)", "fx 3 (crystal)", "fx 4 (atmosphere)",
    "fx 5 (brightness)", "fx 6 (goblins)", "fx 7 (echoes)",
    "fx 8 (sci-fi)", "sitar", "banjo", "shamisen", "koto", "kalimba",
    "bagpipe", "fiddle", "shanai", "tinkle bell", "agogo", "steel drums",
    "woodblock", "taiko drum", "melodic tom", "synth drum",
    "reverse cymbal", "guitar fret noise", "breath noise", "seashore",
    "bird tweet", "telephone ring", "helicopter", "applause", "gunshot",
)


# ---------------------------------------------------------------------------
# S12-3: a single-line-format (BANA Sec. 24) piece's braille never states
# its own instrument (Secs. 24.1-24.5 cover only segment/measure-number
# layout), so a solo BRF/BRL staff -- and an extracted piano hand, which
# never had an "instrument" of its own beyond "piano" -- keeps a fixed
# placeholder name from the parser rather than a real instrument name.
# Used to decide when to offer the CLI's/web UI's instrument selection.
# ---------------------------------------------------------------------------

PLACEHOLDER_STAFF_NAMES: frozenset[str] = frozenset({"right hand", "left hand", ""})


def is_placeholder_staff_name(name: str) -> bool:
    """True if `name` is one of BrailleParser's fixed non-instrument
    defaults ("right hand"/"left hand"), or blank -- never a real,
    user- or source-supplied instrument name."""
    return name.strip().lower() in PLACEHOLDER_STAFF_NAMES


def infer_instrument_from_title(title: str | None) -> str:
    """Best-effort default instrument for a single-line-format piece with
    no real instrument name: look for a recognizable instrument mentioned
    in the title (e.g. "Mystery Melody for Violin", "Flute Sonata"),
    falling back to piano ("acoustic grand") when none is found or no
    title exists at all. This is only ever a suggested default the CLI/
    web UI lets the user override -- BANA Sec. 24's braille never states
    an instrument itself (see PLACEHOLDER_STAFF_NAMES), so there is
    nothing to actually parse here, just a heuristic guess.
    """
    if title:
        midi_name = get_midi_instrument_name(title)
        if midi_name is not None:
            return midi_name
    return "acoustic grand"
