"""Transposing-instrument interval table (S5b-6, BANA Sec. 33.2 + LilyPond
Learning Manual Sec. 4.4.5 "Scores and Parts").

BANA's Sec. 33.2 instrument-list header preserves a transposing instrument's
key as text (e.g. "Horn in F", "Clarinet in B-flat") -- see CLAUDE.md Key
Design Decision #4 -- but the note cells themselves encode *written* pitch,
what the performer reads. This module maps that key text to the interval
needed to render *concert* (sounding) pitch, DottedNotes' default output.

Direction check (the trap S5b-6's senior note calls out): the LilyPond
Learning Manual's own horn example, "\\transpose f c' \\hornNotes", transposes
*concert*-pitch hornNotes up a fifth into the horn's *written* part ("sounding
f is denoted by notated c'") -- i.e. \\transpose <concert> <written>.
DottedNotes needs the reverse: written pitch (already parsed from braille) to
concert pitch, i.e. \\transpose <written> <concert>. Each entry below was
derived from the corresponding "instrument sounds X [interval] [direction]
than written" fact (LilyPond Notation Reference's \\transpose semantics,
cross-checked against Wikipedia's "Transposing instrument" article), not
assumed from memory.
"""

from __future__ import annotations

import re

_ALT_KEY_SPELLING: dict[str, str] = {
    'b-flat': 'Bb', 'bb': 'Bb', 'b flat': 'Bb', 'b♭': 'Bb',
    'e-flat': 'Eb', 'eb': 'Eb', 'e flat': 'Eb', 'e♭': 'Eb',
}

_KEY_PATTERN = re.compile(r'^(.*?)\s+in\s+(.+)$', re.IGNORECASE)

# (written_pitch, concert_pitch), both in LilyPond absolute-pitch notation
# referenced from middle c' -- i.e. what a written c' sounds as on that
# instrument. "\transpose written concert" converts written-pitch music
# (DottedNotes' parsed representation) into concert (sounding) pitch.
_TRANSPOSITIONS: dict[tuple[str, str], tuple[str, str]] = {
    ('horn', 'F'): ("c'", 'f'),          # sounds a perfect 5th lower than written
    ('english horn', 'F'): ("c'", 'f'),  # sounds a perfect 5th lower than written
    ('clarinet', 'Bb'): ("c'", 'bes'),   # sounds a major 2nd lower than written
    ('clarinet', 'A'): ("c'", 'a'),      # sounds a minor 3rd lower than written
    ('trumpet', 'Bb'): ("c'", 'bes'),    # sounds a major 2nd lower than written
    ('trumpet', 'C'): ("c'", "c'"),      # non-transposing (identity)
}


def _canonical_key(raw_key: str) -> str:
    normalized = raw_key.strip().lower()
    return _ALT_KEY_SPELLING.get(normalized, raw_key.strip().upper())


def get_transposition(instrument_name: str) -> tuple[str, str] | None:
    """Return (written_pitch, concert_pitch) LilyPond absolute pitches for
    `instrument_name` (e.g. "Horn in F", "Clarinet in B-flat"), or None if
    it isn't a recognized transposing-instrument name.

    written_pitch == concert_pitch for a named non-transposing key (e.g.
    "Trumpet in C") -- callers should treat that the same as None, i.e. no
    \\transpose is needed.

    This name-string lookup is what the BRF/ensemble path uses (BANA's
    instrument-list header preserves the instrument's key as text -- see
    CLAUDE.md Key Design Decision #4), and it only covers the handful of
    instruments in `_TRANSPOSITIONS` above. `transposition_from_interval()`
    below is the general-purpose alternative used by the MusicXML import
    path (S10b-2), which can resolve any instrument's transposition from
    structured interval data instead of needing its exact name matched.
    """
    match = _KEY_PATTERN.match(instrument_name.strip())
    if match is None:
        return None
    base = match.group(1).strip().lower()
    key = _canonical_key(match.group(2))
    return _TRANSPOSITIONS.get((base, key))


# Matches models/note.py's _LILYPOND_OCTAVE_BASE (duplicated rather than
# imported to keep this module free of intra-package dependencies).
_LILYPOND_OCTAVE_BASE = 3

_STEP_ORDER = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
_STEP_SEMITONES = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
_STEP_TO_LILYPOND = {'C': 'c', 'D': 'd', 'E': 'e', 'F': 'f', 'G': 'g', 'A': 'a', 'B': 'b'}
_ALTER_TO_LILYPOND_SUFFIX = {-2: 'eses', -1: 'es', 0: '', 1: 'is', 2: 'isis'}

# c' (middle C) as (letter, DottedNotes octave number) -- matches
# Note._octave_marks()'s convention, where octave 3 = plain "c" and each
# octave above/below adds one "'"/"," (models/note.py's _LILYPOND_OCTAVE_BASE).
_REFERENCE_LETTER = 'C'
_REFERENCE_OCTAVE = 4


def transposition_from_interval(diatonic_steps: int, chromatic_semitones: int) -> tuple[str, str] | None:
    """Return (written_pitch, concert_pitch) LilyPond absolute pitches,
    computed generically from a signed interval instead of an instrument
    name -- for any instrument, not just the ones in `_TRANSPOSITIONS`.

    `diatonic_steps`/`chromatic_semitones` are a generic musical interval,
    e.g. music21's `Instrument.transposition` gives this directly as
    `interval.diatonic.generic.staffDistance` (diatonic_steps) and
    `interval.chromatic.semitones` (chromatic_semitones) -- this function
    takes plain ints rather than a music21 object so the `models/` layer
    doesn't need a music21 dependency.

    written_pitch is always "c'" (the reference pitch); concert_pitch is c'
    shifted by the interval, spelled using the correct diatonic letter (not
    just chromatically -- e.g. a major 2nd down from c' is spelled "bes",
    not the chromatically-equivalent "ais"), matching the sign convention
    documented in this module's docstring: DottedNotes' written pitch
    transposes *up* to concert pitch (`\\transpose written concert`).
    Verified against three of `_TRANSPOSITIONS`' entries (horn/F, clarinet/Bb,
    clarinet/A) via their real `music21.interval.Interval` diatonic/chromatic
    values before trusting the formula.

    Returns None for a zero interval (non-transposing).
    """
    if chromatic_semitones == 0:
        return None

    base_letter_idx = _STEP_ORDER.index(_REFERENCE_LETTER)
    new_letter_idx = (base_letter_idx + diatonic_steps) % 7
    octave_carry = (base_letter_idx + diatonic_steps) // 7
    new_letter = _STEP_ORDER[new_letter_idx]
    new_octave = _REFERENCE_OCTAVE + octave_carry

    base_abs_semitone = _REFERENCE_OCTAVE * 12 + _STEP_SEMITONES[_REFERENCE_LETTER]
    target_abs_semitone = base_abs_semitone + chromatic_semitones
    natural_abs_semitone = new_octave * 12 + _STEP_SEMITONES[new_letter]
    alter = target_abs_semitone - natural_abs_semitone

    if alter not in _ALTER_TO_LILYPOND_SUFFIX:
        return None  # interval needs a triple-sharp/flat or stranger -- not a real instrument transposition

    def _octave_marks(octave: int) -> str:
        base = _LILYPOND_OCTAVE_BASE
        if octave < base:
            return ',' * (base - octave)
        elif octave > base:
            return "'" * (octave - base)
        return ''

    concert_pitch = f"{_STEP_TO_LILYPOND[new_letter]}{_ALTER_TO_LILYPOND_SUFFIX[alter]}{_octave_marks(new_octave)}"
    return ("c'", concert_pitch)
