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
    """
    match = _KEY_PATTERN.match(instrument_name.strip())
    if match is None:
        return None
    base = match.group(1).strip().lower()
    key = _canonical_key(match.group(2))
    return _TRANSPOSITIONS.get((base, key))
