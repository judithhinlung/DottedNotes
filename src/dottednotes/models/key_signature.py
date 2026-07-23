from dataclasses import dataclass

from dottednotes.bana_symbols import SymbolCategory, LITERARY_DIGITS
from dottednotes.models.base import BrailleSymbol

# Maps sharps_or_flats count → (lilypond_note, mode_string)
# Positive values = sharps, negative values = flats, 0 = C major / A minor.
# Note names use LilyPond conventions: sharps add 'is', flats add 'es'.
# Covers the standard range (test_key_to_lilypond_covers_all_standard_keys
# checks this dict is exactly -7..7); anything beyond that falls back to
# _tonic_letter_and_accidental()'s general derivation instead (S10d-8).
KEY_TO_LILYPOND: dict[int, tuple[str, str]] = {
     7: ('cis', 'major'),
     6: ('fis', 'major'),
     5: ('b',   'major'),
     4: ('e',   'major'),
     3: ('a',   'major'),
     2: ('d',   'major'),
     1: ('g',   'major'),
     0: ('c',   'major'),
    -1: ('f',   'major'),
    -2: ('bes', 'major'),
    -3: ('ees', 'major'),
    -4: ('aes', 'major'),
    -5: ('des', 'major'),
    -6: ('ges', 'major'),
    -7: ('ces', 'major'),
}


_KEY_TO_BRL = {
    1: '⠩',
    2: '⠩⠩',
    3: '⠩⠩⠩',
    4: '⠼⠙⠩',
    5: '⠼⠑⠩',
    6: '⠼⠋⠩',
    7: '⠼⠛⠩',
    -1: '⠣',
    -2: '⠣⠣',
    -3: '⠣⠣⠣',
    -4: '⠼⠙⠣',
    -5: '⠼⠑⠣',
    -6: '⠼⠋⠣',
    -7: '⠼⠛⠣',
}

# Tonic letter/accidental derivation for |sharps_or_flats| > 7 (S10d-8), via
# circle-of-fifths semitone arithmetic rather than a table -- BANA Par. 6.5
# states the numeral-prefixed form for "four or more accidentals" with no
# upper limit, so the model should not impose one either. Verified by
# reproducing KEY_TO_LILYPOND's own -7..7 entries exactly before relying on
# it for the extension past +/-7 (e.g. +8 = G# major, needing F## -- gis;
# -8 = Fb major, needing Cb again as one of its 8 flats -- fes).
_NATURAL_SEMITONE = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
_SHARP_LETTER_CYCLE = "CGDAEBF"  # tonic letters for +1, +2, +3, ... sharps
_FLAT_LETTER_CYCLE = "CFBEADG"   # tonic letters for -1, -2, -3, ... flats
_ACCIDENTAL_SUFFIX = {-2: 'eses', -1: 'es', 0: '', 1: 'is', 2: 'isis'}


def _tonic_letter_and_accidental(sharps_or_flats: int) -> tuple[str, int]:
    if sharps_or_flats > 0:
        n = sharps_or_flats
        letter = _SHARP_LETTER_CYCLE[n % 7]
        target = (7 * n) % 12
    else:
        n = -sharps_or_flats
        letter = _FLAT_LETTER_CYCLE[n % 7]
        target = (5 * n) % 12
    raw = target - _NATURAL_SEMITONE[letter]
    accidental = ((raw + 6) % 12) - 6
    return (letter, accidental)


def _numeral_prefixed_braille(count: int, sign_cell: str) -> str:
    """BANA Par. 6.5: four or more accidentals are brailled as the numeral
    sign, the count spelled with the same LITERARY_DIGITS letter alphabet
    BANA measure numbers use (bana_symbols.py, inverted here), then a
    single flat or sharp sign."""
    digit_to_cell = {v: k for k, v in LITERARY_DIGITS.items()}
    digits = "".join(digit_to_cell[int(d)] for d in str(count))
    return '⠼' + digits + sign_cell


@dataclass
class KeySignature(BrailleSymbol):
    """A key signature.

    sharps_or_flats > 0 = that many sharps (G major = 1, D major = 2, …)
    sharps_or_flats < 0 = that many flats  (F major = –1, Bb major = –2, …)
    sharps_or_flats = 0 = C major / A minor (no accidentals)

    BANA Par. 6.5 has no upper limit on accidental count (the numeral-
    prefixed form is used for "four or more" with no cap stated), so
    sharps_or_flats is unbounded past +/-7 too (S10d-8) -- values within
    +/-7 use the standard KEY_TO_LILYPOND/_KEY_TO_BRL tables; anything
    beyond that is derived from circle-of-fifths arithmetic instead (see
    _tonic_letter_and_accidental).

    Minor keys are not yet distinguished from their relative majors;
    the same braille cell covers both.  Minor-mode support is deferred
    to a later sprint.
    """
    sharps_or_flats: int

    def to_lilypond(self) -> str:
        """Return a LilyPond key directive, e.g. '\\key g \\major'."""
        if self.sharps_or_flats in KEY_TO_LILYPOND:
            note, mode = KEY_TO_LILYPOND[self.sharps_or_flats]
            return f'\\key {note} \\{mode}'
        letter, accidental = _tonic_letter_and_accidental(self.sharps_or_flats)
        note = letter.lower() + _ACCIDENTAL_SUFFIX[accidental]
        return f'\\key {note} \\major'

    def to_braille(self) -> str:
        if self.sharps_or_flats in _KEY_TO_BRL:
            return _KEY_TO_BRL[self.sharps_or_flats]
        if self.sharps_or_flats == 0:
            return ''
        sign_cell = '⠩' if self.sharps_or_flats > 0 else '⠣'
        return _numeral_prefixed_braille(abs(self.sharps_or_flats), sign_cell)
