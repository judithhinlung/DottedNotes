from dataclasses import dataclass, field
from typing import Optional

from dottednotes.bana_symbols import SymbolCategory, LITERARY_DIGITS, NOTE_CELLS
from dottednotes.models.base import BrailleSymbol
from dottednotes.models.note import _OCTAVE_TO_BRL
from dottednotes.exceptions import DottedNotesError

# Reverse lookup C/D/E/F/G/A/B -> a NOTE_CELLS cell that spells that letter,
# for a non-traditional key signature's "note(s)" component (S10d-7) --
# the whole/16th-note-shaped cell is used since a key signature has no
# duration of its own (reusing the existing NOTE_CELLS table, not a new
# one).
_LETTER_TO_NOTE_CELL = {v[0]: k for k, v in NOTE_CELLS.items() if v is not None and v[1] == 1}

# BANA Table 6 (Pars. 6.1-6.5.1) -- quarter/three-quarter step accidentals,
# ASCII "@%"/"@<"/"_%"/"_<" decoded via ASCII_TO_DOTS: '@' = dot 4 (⠈),
# '_' = dots 4,5,6 (⠸), '%' = sharp (⠩), '<' = flat (⠣).
_MICROTONE_ACCIDENTAL_BRL = {
    0.5: '⠈⠩',   # quarter-sharp / half-sharp
    -0.5: '⠈⠣',  # quarter-flat / half-flat
    1.5: '⠸⠩',   # three-quarter-sharp
    -1.5: '⠸⠣',  # three-quarter-flat
}

# Whole-tone accidentals for a non-traditional key signature's altered
# pitches (S10d-7) -- the same cells as models/accidental.py's Accidental
# class, duplicated here (not imported) to avoid constructing a throwaway
# Accidental/AccidentalType just to call to_braille() on it.
_WHOLE_TONE_ACCIDENTAL_BRL = {
    1.0: '⠩', -1.0: '⠣', 0.0: '⠡', 2.0: '⠩⠩', -2.0: '⠣⠣',
}

# BANA Table 1's Music Parenthesis sign (",'" in ASCII, confirmed both from
# the table itself and from a separate inline mention in Par. 21 -- "'>"
# would be wrong; decoded as ',' = dots 6 (⠠) then "'" = dot 3 (⠄)), used
# unchanged for both the opening and closing parenthesis (Par. 6.5.1:
# "music parenthesis, hand or clef sign, accidental, octave mark,
# note(s), closing music parenthesis").
_MUSIC_PARENTHESIS = '⠠⠄'

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

KEY_TO_LILYPOND_MINOR: dict[int, str] = {
     7: 'ais',
     6: 'dis',
     5: 'gis',
     4: 'cis',
     3: 'fis',
     2: 'b',
     1: 'e',
     0: 'a',
    -1: 'd',
    -2: 'g',
    -3: 'c',
    -4: 'f',
    -5: 'bes',
    -6: 'ees',
    -7: 'aes',
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


def _accidental_suffix(accidental: int) -> str:
    """LilyPond spells n sharps/flats by repeating 'is'/'es' n times (Notation
    Reference "Pitches" -- cisis is double sharp, ceses is double flat, and
    the pattern keeps extending the same way for triple+ accidentals). A
    fixed {-2: 'eses', ..., 2: 'isis'} table used to raise KeyError once
    |sharps_or_flats| got large enough that the circle-of-fifths derivation
    below needed a triple accidental -- computing the suffix instead of
    looking it up keeps this unbounded, matching BANA Par. 6.5's own "four
    or more accidentals, no upper limit" numeral-prefixed braille form."""
    if accidental > 0:
        return 'is' * accidental
    if accidental < 0:
        return 'es' * (-accidental)
    return ''


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


def _tonic_letter_and_accidental_minor(sharps_or_flats: int) -> tuple[str, int]:
    if sharps_or_flats > 0:
        n = sharps_or_flats
        letter = _SHARP_LETTER_CYCLE[(n + 3) % 7]
        target = ((7 * n) - 3) % 12
    else:
        n = -sharps_or_flats
        letter = _FLAT_LETTER_CYCLE[(n + 4) % 7]
        target = ((5 * n) - 3) % 12
    raw = target - _NATURAL_SEMITONE[letter]
    accidental = ((raw + 6) % 12) - 6
    return (letter, accidental)


def tonic_name(sharps_or_flats: int, mode: str = "major") -> str:
    """Return just the LilyPond tonic note name (e.g. 'g', 'aes', 'eis') for
    a key signature and mode, without the surrounding '\\key ... \\major'/
    '\\minor' directive text. Shared by KeySignature.to_lilypond() and by
    web.py's key-mode selection dialog (S10d-16), which needs the same
    major/minor tonic derivation to build its "F Major" / "D Minor" option
    labels without duplicating the table-lookup-then-derive logic."""
    if mode == "minor":
        if sharps_or_flats in KEY_TO_LILYPOND_MINOR:
            return KEY_TO_LILYPOND_MINOR[sharps_or_flats]
        letter, accidental = _tonic_letter_and_accidental_minor(sharps_or_flats)
    else:
        if sharps_or_flats in KEY_TO_LILYPOND:
            return KEY_TO_LILYPOND[sharps_or_flats][0]
        letter, accidental = _tonic_letter_and_accidental(sharps_or_flats)
    return letter.lower() + _accidental_suffix(accidental)


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

    A "non-traditional" or microtonal key signature (MusicXML's
    <key-step>/<key-alter> pairs instead of <fifths>, S10d-7) can't be
    expressed as a single sharps_or_flats count at all -- set
    non_traditional_pitches instead (leaving sharps_or_flats as None):
    a list of (step, alter, octave-or-None) tuples, one per altered pitch,
    in the order the source gave them, where alter is a float semitone
    offset (1.0=sharp, -1.0=flat, 2.0=double-sharp, -2.0=double-flat,
    0.0=natural, 0.5/-0.5=quarter-sharp/flat, 1.5/-1.5=three-quarter-
    sharp/flat -- BANA Table 6's quarter/three-quarter step accidentals)
    and octave is the pitch's octave when the source specifies one
    (None when the alteration applies to a pitch class regardless of
    octave). Exactly one of sharps_or_flats/non_traditional_pitches must
    be set.

    A braille key signature cell only states the number of sharps/flats,
    never major vs. relative minor (BANA Chapter 6 has no separate mode
    marking) -- `mode` ("major"/"minor", default "major") disambiguates
    that when known, e.g. from an explicit source (LilyPond/MusicXML) or
    a user's post-translation choice (S10d-16). Braille output
    (to_braille) is unaffected, since the cell is identical either way.
    """
    sharps_or_flats: Optional[int] = None
    non_traditional_pitches: Optional[list[tuple[str, float, Optional[int]]]] = None
    mode: str = "major"

    def __post_init__(self) -> None:
        has_standard = self.sharps_or_flats is not None
        has_non_traditional = self.non_traditional_pitches is not None
        if has_standard == has_non_traditional:
            raise ValueError(
                "KeySignature requires exactly one of sharps_or_flats or "
                "non_traditional_pitches to be set."
            )

    def to_lilypond(self) -> str:
        """Return a LilyPond key directive, e.g. '\\key g \\major'."""
        if self.non_traditional_pitches is not None:
            # BANA Par. 6.5.1's braille construction for this case is
            # implemented below (to_braille); LilyPond's own non-standard/
            # microtonal key-signature and note-naming syntax has not been
            # verified against the Notation Reference yet (S10d-7) -- raise
            # rather than guess at unconfirmed LilyPond syntax.
            raise DottedNotesError(
                "Cannot render a non-traditional or microtonal key "
                "signature to LilyPond yet: this needs BANA Par. 6.5.1's "
                "construction verified further, and LilyPond's own "
                "non-standard-key-signature syntax has not been confirmed "
                "against the Notation Reference. Braille output (to_braille) "
                "is supported for the whole-tone case."
            )
        directive_mode = "minor" if self.mode == "minor" else "major"
        note = tonic_name(self.sharps_or_flats, directive_mode)
        return f'\\key {note} \\{directive_mode}'

    def to_braille(self) -> str:
        if self.non_traditional_pitches is not None:
            return self._non_traditional_to_braille()
        if self.sharps_or_flats in _KEY_TO_BRL:
            return _KEY_TO_BRL[self.sharps_or_flats]
        if self.sharps_or_flats == 0:
            return ''
        sign_cell = '⠩' if self.sharps_or_flats > 0 else '⠣'
        return _numeral_prefixed_braille(abs(self.sharps_or_flats), sign_cell)

    def _non_traditional_to_braille(self) -> str:
        """BANA Par. 6.5.1: "music parenthesis, hand or clef sign,
        accidental, octave mark, note(s), closing music parenthesis."
        Confirmed from the manual: the music parenthesis sign (Table 1,
        ⠠⠄) wraps the construction; Example 6.5.1-1's clef component
        decodes to exactly this project's own ClefType.TREBLE cell
        (⠜⠌⠇), confirming that component. Deliberately NOT attempted here:
        which clef to use when the source doesn't specify one for this
        construction (always assumes treble, since neither worked example
        in the manual covers a non-treble case), and BANA's exact
        convention for chaining multiple altered pitches within one
        signature (Example 6.5.1-2, "Unusual combined key signatures",
        could not be confidently decoded cell-by-cell from the manual's
        text alone without its accompanying print image) -- each altered
        pitch here gets its own complete parenthesis-wrapped construction
        instead, a defensible but unverified reading. Flag to the
        developer before trusting this for real transcription.
        """
        parts = []
        clef_brl = '⠜⠌⠇'  # ClefType.TREBLE (models/clef.py) -- see docstring
        for step, alter, octave in self.non_traditional_pitches:
            accidental_brl = _MICROTONE_ACCIDENTAL_BRL.get(alter)
            if accidental_brl is None:
                accidental_brl = _WHOLE_TONE_ACCIDENTAL_BRL.get(alter, '')
            octave_brl = _OCTAVE_TO_BRL.get(octave, '') if octave is not None else ''
            note_brl = _LETTER_TO_NOTE_CELL.get(step, '')
            parts.append(_MUSIC_PARENTHESIS + clef_brl + accidental_brl + octave_brl + note_brl + _MUSIC_PARENTHESIS)
        return "".join(parts)

    def accidental_by_step(self, step: str) -> Optional["AccidentalType"]:
        """Return the AccidentalType implied by the key signature for this note step, or None."""
        if self.sharps_or_flats is not None:
            from .accidental import AccidentalType
            step = step.upper()
            sharp_order = ['F', 'C', 'G', 'D', 'A', 'E', 'B']
            flat_order = ['B', 'E', 'A', 'D', 'G', 'C', 'F']
            if self.sharps_or_flats > 0:
                if step in sharp_order[:self.sharps_or_flats]:
                    return AccidentalType.SHARP
            elif self.sharps_or_flats < 0:
                num_flats = -self.sharps_or_flats
                if step in flat_order[:num_flats]:
                    return AccidentalType.FLAT
        elif self.non_traditional_pitches is not None:
            from .accidental import AccidentalType
            step = step.upper()
            for s, alter, _oct in self.non_traditional_pitches:
                if s.upper() == step:
                    if alter == 1.0: return AccidentalType.SHARP
                    elif alter == -1.0: return AccidentalType.FLAT
                    elif alter == 0.0: return AccidentalType.NATURAL
                    elif alter == 2.0: return AccidentalType.DOUBLE_SHARP
                    elif alter == -2.0: return AccidentalType.DOUBLE_FLAT
        return None

