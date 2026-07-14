"""Tests for S8b-5: BANA Sec. 23/27 (Table 23) lead-sheet chord symbols.

Every ASCII-braille chord symbol case here is taken directly from the BANA
Music Braille Code 2015 manual's Chart 23.1-1 "Representative Chord
Symbols" (p.169), not invented -- see bana_symbols.py's module comment for
the cell-by-cell derivation.
"""
import warnings

from dottednotes.exceptions import BrailleParseError
from dottednotes.models.chord_names import ChordNamesTrack
from dottednotes.models.chord_symbol import ChordSymbol
from dottednotes.models.duration import Duration
from dottednotes.parser.chord_symbol_parser import parse_chord_symbol_line
from dottednotes.parser.input_pipeline import ASCII_TO_DOTS
from dottednotes.parser.lead_sheet_parser import parse_lead_sheet


def u(ascii_str: str) -> str:
    """Convert an ASCII-braille string (BRF convention) to Unicode braille."""
    return ''.join(chr(0x2800 + ASCII_TO_DOTS.get(c.upper(), 0)) for c in ascii_str)


def _one(ascii_str: str) -> ChordSymbol:
    results = parse_chord_symbol_line(u(ascii_str))
    assert len(results) == 1, f"expected exactly one chord symbol in {ascii_str!r}, got {results}"
    return results[0][1]


# --- Chart 23.1-1 worked examples: parsing + to_lilypond() ---

def test_minor_triad():
    assert _one(',DM').to_lilypond('4') == 'd4:m'


def test_plain_major_triad_with_flat_root():
    assert _one(',E<').to_lilypond('4') == 'ees4'


def test_slash_bass_note():
    cs = _one(',D</,A<')
    assert cs.root == 'D' and cs.accidental == 'flat'
    assert cs.bass_note == ('A', 'flat')
    assert cs.to_lilypond('4') == 'des4/aes'


def test_major_seventh_spelled_out():
    assert _one(',DMAj#G').to_lilypond('4') == 'd4:maj7'


def test_added_sixth_with_bass():
    assert _one(',G#F/,D').to_lilypond('4') == 'g4:6/d'


def test_diminished_seventh_spelled_out():
    assert _one(',F%DIM#G').to_lilypond('4') == 'fis4:dim7'


def test_diminished_seventh_circle_sign():
    assert _one(',F%4#G').to_lilypond('4') == 'fis4:dim7'


def test_dominant_seventh():
    assert _one(',F%#G').to_lilypond('4') == 'fis4:7'


def test_dominant_seventh_suspended():
    assert _one(',C#GSUS').to_lilypond('4') == 'c4:7.sus4'


def test_minor_with_raised_seventh_in_parens():
    assert _one(',DM7%#G7').to_lilypond('4') == 'd4:m.7+'


def test_dominant_seventh_flat_nine():
    assert _one(',B#G-#I').to_lilypond('4') == 'b4:7.9-'


def test_major_seventh_sharp_nine():
    assert _one(',GMAJ#G+#I').to_lilypond('4') == 'g4:maj7.9+'


def test_augmented_triad_standalone_plus():
    assert _one(',B+').to_lilypond('4') == 'b4:aug'


def test_dominant_seventh_flat_nine_in_parens():
    assert _one(',B#G7-#I7').to_lilypond('4') == 'b4:7.9-'


def test_diminished_triad_circle_flat_root():
    assert _one(',B<4').to_lilypond('4') == 'bes4:dim'


def test_half_diminished_seventh():
    assert _one(",B<4'#G").to_lilypond('4') == 'bes4:m7.5-'


def test_major_seventh_triangle_sign():
    assert _one(',C0').to_lilypond('4') == 'c4:maj7'


def test_no_chord():
    cs = _one(',,nc')
    assert cs.no_chord is True
    assert cs.to_lilypond('4') == 's4'


def test_tacet():
    cs = _one(',tacet')
    assert cs.tacet is True
    assert cs.to_lilypond('4') == 's4'


def test_dominant_seventh_slash_bass_no_parens_text():
    assert _one(',G#g/,b').to_lilypond('4') == 'g4:7/b'


# --- Multiple chord symbols on one line ---

def test_multiple_chords_on_one_line_with_positions():
    line = u(',C') + u(' ') + u(',DM')
    results = parse_chord_symbol_line(line)
    assert [col for col, _ in results] == [0, 3]
    assert [cs.to_lilypond('4') for _, cs in results] == ['c4', 'd4:m']


# --- Rejections: never guess an unconfirmed BANA convention ---

def test_triangle_bisect_sign_is_rejected_not_guessed():
    try:
        parse_chord_symbol_line(u(",C0'"))
        assert False, "expected BrailleParseError"
    except BrailleParseError as e:
        assert "not confirmed" in str(e)


def test_standalone_minus_is_rejected_not_guessed():
    try:
        parse_chord_symbol_line(u(',B-'))
        assert False, "expected BrailleParseError"
    except BrailleParseError:
        pass


def test_unrecognized_quality_word_is_rejected():
    try:
        parse_chord_symbol_line(u(',BXYZ'))
        assert False, "expected BrailleParseError"
    except BrailleParseError:
        pass


# --- ChordNamesTrack ---

def test_chord_names_track_holds_over_repeated_chord():
    c_major = ChordSymbol(root='C')
    track = ChordNamesTrack(entries=[
        (Duration(value=4), c_major),
        (Duration(value=4), None),
        (Duration(value=4), None),
    ])
    ly = track.to_lilypond()
    assert '\\chordmode { c4 c4 c4 }' in ly
    assert '\\set chordChanges = ##t' in ly


def test_chord_names_track_raises_without_any_chord():
    track = ChordNamesTrack(entries=[(Duration(value=4), None)])
    try:
        track.to_lilypond()
        assert False, "expected ValueError"
    except ValueError:
        pass


# --- Full lead-sheet pipeline (S8b-5 DoD: "verify correct alignment") ---

def _lead_sheet_text() -> str:
    blank = u(' ')
    notes = {'C': '⠽', 'D': '⠵', 'E': '⠯', 'F': '⠿'}  # whole notes
    final_bar = '⠣⠅'
    music = notes['C'] + blank + notes['D'] + blank + notes['E'] + blank + notes['F'] + final_bar
    chords = u(',C') + u(',DM') + u(',EM') + u(',F')
    return music + '\n' + chords + '\n'


def test_lead_sheet_parses_without_beat_count_warnings():
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        score = parse_lead_sheet(_lead_sheet_text())
    assert score.chord_names is not None
    assert len(score.chord_names.entries) == 4


def test_lead_sheet_chord_alignment_matches_melody_order():
    score = parse_lead_sheet(_lead_sheet_text())
    rendered = [c.to_lilypond(d.to_lilypond()) for d, c in score.chord_names.entries]
    assert rendered == ['c1', 'd1:m', 'e1:m', 'f1']


def test_lead_sheet_to_lilypond_contains_chord_names_context():
    score = parse_lead_sheet(_lead_sheet_text())
    ly = score.to_lilypond()
    assert '\\new ChordNames' in ly
    assert '\\chordmode { c1 d1:m e1:m f1 }' in ly
    assert '\\new Staff' in ly


def test_lead_sheet_requires_even_number_of_lines():
    blank = u(' ')
    music = '⠽' + blank + '⠣⠅'
    try:
        parse_lead_sheet(music + '\n')
        assert False, "expected BrailleParseError"
    except BrailleParseError:
        pass


def test_lead_sheet_requires_chord_symbol_under_first_note():
    blank = u(' ')
    # Two segments (music/chords line pairs): the first segment's chord
    # line is entirely blank (no chord symbol at all for its note), so the
    # very first melody note ends up with nothing to hold over.
    music_line_1 = '⠽'
    chords_line_1 = blank
    music_line_2 = '⠵' + '⠣⠅'
    chords_line_2 = u(',DM')
    text = '\n'.join([music_line_1, chords_line_1, music_line_2, chords_line_2]) + '\n'
    try:
        parse_lead_sheet(text)
        assert False, "expected BrailleParseError"
    except BrailleParseError:
        pass
