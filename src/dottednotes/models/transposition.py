"""Transposing-instrument interval support (S5b-6, BANA Sec. 33.2 + LilyPond
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
concert pitch, i.e. \\transpose <written> <concert>.

get_transposition() below computes this interval generically from <Key>'s
pitch class (S5b-6 follow-up -- was originally a hardcoded per-instrument
table) instead of needing every "<instrument> in <Key>" combination added by
hand: the convention for a simply-named transposing instrument (no "alto"/
"bass"/octave qualifier) is the *smaller* of the two intervals, within an
octave, connecting written c' to <Key>'s pitch class -- e.g. B-flat is a
major 2nd below c' (2 semitones) or a minor 7th above (10 semitones), so the
major 2nd below is what's used. Verified to reproduce every instrument this
module used to hardcode (clarinet/trumpet in Bb/A/C) and extends for free to
any new key (e.g. "Trumpet in D" needs no new entry -- D resolves to a major
2nd up, cross-checked against Wikipedia's "Transposing instrument" article).

The documented exceptions are the families in _FORCED_DOWN_FAMILIES below:
real convention always treats them as transposing *down*, even on a key
where the nearest-interval rule above would pick *up* instead, because that
convention comes from the instrument's own history/register, not from the
key letter itself, so it can't be derived by the same formula:
  - Horn (F): 5 semitones up vs. 7 down -- horns use the further-but-
    conventional 7-down option, a historical convention from natural-horn
    crooks.
  - Alto saxophone (E-flat): 3 semitones up vs. 9 down -- an E-flat
    clarinet uses the nearer 3-up (minor 3rd) for the very same key letter,
    but alto sax is, by convention, always the farther 9-down (major 6th)
    option instead.
Both exceptions above still transpose by *less* than an octave, so the
plain mod-12 "forced down" override is sufficient for them. This module
does NOT attempt instruments transposing by *more* than an octave -- e.g.
tenor saxophone in B-flat (a major 9th down: an octave lower than soprano
saxophone/clarinet's plain major 2nd down for the same key), baritone
saxophone in E-flat (an octave *and* a major 6th down, one octave lower
than alto sax's major 6th for the same key), or bass clarinet in B-flat (a
major 9th down, not the plain major 2nd a soprano/Bb clarinet uses). Those
will silently fall through to the nearest-interval default instead of
raising, which is wrong for those instruments specifically (right pitch
class, wrong octave) -- add a dedicated interval override if/when they come
up (not a `_FORCED_DOWN_FAMILIES` entry -- that mechanism only flips
direction within an octave, it doesn't shift by a full extra octave).
"""

from __future__ import annotations

import re

_KEY_PATTERN = re.compile(r'^(.*?)\s+in\s+(.+)$', re.IGNORECASE)

_STEP_ORDER = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
_STEP_SEMITONES = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}

# See module docstring: instrument families whose real convention is always
# "down", overriding the nearest-interval default for whichever of their
# keys that default would otherwise get wrong (F for horn, E-flat for alto
# saxophone). Both common full names and their usual abbreviations are
# listed so either spelling resolves the same way.
_FORCED_DOWN_FAMILIES: frozenset[str] = frozenset({
    'horn', 'english horn',
    'alto saxophone', 'alto sax',
})


def _parse_key_pitch_class(raw_key: str) -> tuple[str, int] | None:
    """Parse a transposition key like "B-flat", "Bb", "F#", "D natural",
    plain "D" into (letter, accidental_semitones), e.g. ("B", -1), ("F", 1),
    ("D", 0). Returns None if `raw_key` isn't a recognized single-letter,
    single-accidental pitch name (callers then treat the whole instrument
    name as not a recognized transposing instrument, same as today)."""
    normalized = raw_key.strip()
    if not normalized:
        return None
    letter = normalized[0].upper()
    if letter not in _STEP_SEMITONES:
        return None
    rest = normalized[1:].strip().lower().lstrip('-').strip()
    if rest in ('', 'natural', 'nat'):
        return letter, 0
    if rest in ('b', 'flat', '♭'):
        return letter, -1
    if rest in ('#', 'sharp', '♯'):
        return letter, 1
    return None


def get_transposition(instrument_name: str) -> tuple[str, str] | None:
    """Return (written_pitch, concert_pitch) LilyPond absolute pitches for
    `instrument_name` (e.g. "Horn in F", "Clarinet in B-flat", "Trumpet in
    D"), or None if it isn't a recognized "<instrument> in <key>" name.

    written_pitch == concert_pitch for a named non-transposing key (e.g.
    "Trumpet in C") -- callers should treat that the same as None, i.e. no
    \\transpose is needed.

    The interval comes from <key>'s pitch class (see module docstring for
    the nearest-interval rule and its one documented exception), not a
    hardcoded per-instrument table -- any "<instrument> in <key>" name
    works. This is what the BRF/ensemble path uses (BANA's instrument-list
    header preserves the instrument's key as text -- see CLAUDE.md Key
    Design Decision #4). `transposition_from_interval()` below is the
    alternative used by the MusicXML import path (S10b-2), which resolves
    the interval from the source file's own structured transposition data
    instead of a name match.
    """
    match = _KEY_PATTERN.match(instrument_name.strip())
    if match is None:
        return None
    base = match.group(1).strip().lower()
    parsed = _parse_key_pitch_class(match.group(2))
    if parsed is None:
        return None
    letter, accidental = parsed

    key_semitone = (_STEP_SEMITONES[letter] + accidental) % 12
    if key_semitone == 0:
        return ("c'", "c'")  # same pitch class as written c' -- non-transposing

    letter_idx = _STEP_ORDER.index(letter)
    up_chromatic, up_diatonic = key_semitone, letter_idx
    down_chromatic, down_diatonic = 12 - key_semitone, letter_idx - 7

    # Ties (a tritone key, exactly 6 semitones either way -- no standard
    # orchestral instrument transposes by one) favor down, arbitrarily but
    # consistently.
    use_down = base in _FORCED_DOWN_FAMILIES or down_chromatic <= up_chromatic

    if use_down:
        diatonic_steps, chromatic_semitones = down_diatonic, -down_chromatic
    else:
        diatonic_steps, chromatic_semitones = up_diatonic, up_chromatic

    return transposition_from_interval(diatonic_steps, chromatic_semitones)


# Matches models/note.py's _LILYPOND_OCTAVE_BASE (duplicated rather than
# imported to keep this module free of intra-package dependencies).
_LILYPOND_OCTAVE_BASE = 3

# _STEP_ORDER/_STEP_SEMITONES are defined above, shared with get_transposition().
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
