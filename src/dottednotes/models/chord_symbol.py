from __future__ import annotations

from dataclasses import dataclass, field

from .accidental import ACCIDENTAL_TO_LILYPOND_SUFFIX, AccidentalType
from .note import NOTE_NAME_TO_LILYPOND

_STR_TO_ACCIDENTAL_TYPE = {
    'sharp': AccidentalType.SHARP,
    'flat': AccidentalType.FLAT,
    'natural': AccidentalType.NATURAL,
}


def _root_to_lilypond(letter: str, accidental: str | None) -> str:
    suffix = ACCIDENTAL_TO_LILYPOND_SUFFIX[_STR_TO_ACCIDENTAL_TYPE[accidental]] if accidental else ''
    return NOTE_NAME_TO_LILYPOND[letter] + suffix


@dataclass
class ChordSymbol:
    """A BANA Sec. 23 (Table 23) lead-sheet chord symbol, e.g. "Dm", "F#dim7",
    "B♭ø7", "G7/B". `root` and `accidental` are None only for `no_chord`/`tacet`.

    `extensions` is the ordered list of (scale degree, alteration) pairs read
    from the braille exactly as printed -- e.g. "Gmaj7+9" is [(7, None), (9, '+')].
    The first entry with no alteration is consumed as the chord's primary
    extension digit (the "7" in "Dmaj7"); any remaining entries become
    additional altered-degree additions in `to_lilypond()`.
    """
    root: str | None = None
    accidental: str | None = None          # 'sharp' | 'flat' | 'natural' | None
    is_minor: bool = False                 # spelled "m"/"min"
    is_diminished: bool = False            # circle sign or spelled "dim"
    is_half_diminished: bool = False       # circle+bisect sign (ø)
    is_augmented: bool = False             # standalone plus, or spelled "aug"
    is_major7_symbol: bool = False         # triangle sign alone (△ = maj7)
    has_explicit_maj: bool = False         # spelled "maj" word
    suspended: int | None = None           # 2 or 4, from "sus2"/"sus4"/"sus" (defaults to 4)
    extensions: list[tuple[int, str | None]] = field(default_factory=list)
    bass_note: tuple[str, str | None] | None = None   # (root letter, accidental)
    no_chord: bool = False
    tacet: bool = False

    def to_lilypond(self, duration: str = '') -> str:
        """Return a \\chordmode entry, e.g. 'd4:m', 'fis4:dim7', 'g4:7/b'.

        `duration` (e.g. '4', '8.') is spliced in right after the root pitch
        and before the ':modifiers', matching LilyPond's own chordmode
        syntax -- callers (ChordNamesTrack) supply it to align with the
        melody's rhythm.
        """
        if self.no_chord or self.tacet:
            return f's{duration}'

        root_ly = _root_to_lilypond(self.root, self.accidental) + duration
        exts = list(self.extensions)
        primary = ''

        def _pop_plain_degree(default: int) -> int:
            if exts and exts[0][1] is None:
                return exts.pop(0)[0]
            return default

        if self.is_half_diminished:
            primary = 'm7.5-'
            if exts and exts[0] == (7, None):
                exts.pop(0)
        elif self.is_diminished:
            degree = _pop_plain_degree(0)
            primary = f'dim{degree}' if degree else 'dim'
        elif self.is_augmented:
            degree = _pop_plain_degree(0)
            primary = f'aug{degree}' if degree else 'aug'
        elif self.is_minor:
            degree = _pop_plain_degree(0)
            primary = f'm{degree}' if degree else 'm'
        elif self.has_explicit_maj or self.is_major7_symbol:
            primary = f'maj{_pop_plain_degree(7)}'
        elif exts and exts[0][1] is None:
            primary = str(exts.pop(0)[0])

        extra_mods = []
        if self.suspended is not None:
            extra_mods.append(f'sus{self.suspended}')
        for degree, alteration in exts:
            extra_mods.append(f'{degree}{"+" if alteration == "+" else "-"}')

        all_mods = ([primary] if primary else []) + extra_mods
        result = root_ly
        if all_mods:
            result += ':' + '.'.join(all_mods)
        if self.bass_note is not None:
            bass_letter, bass_accidental = self.bass_note
            result += '/' + _root_to_lilypond(bass_letter, bass_accidental)
        return result
