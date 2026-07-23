"""Tests for BANA Par. 22.3.8 (Expressions That Contain Spaces): a "longer
expression" (two or more words and/or abbreviations) must be enclosed
between a PAIR of word signs, not just a leading one -- and when a measure
has more than one text marking, an intervening (blank-cell) space is needed
between adjacent markings whenever at least one of them is a longer
expression, while two adjacent single-word/abbreviation markings still get
no separator at all (Par. 22.3's general rule: "brailled without
interruption").
"""
from dottednotes.models.note import Note
from dottednotes.models.duration import Duration
from dottednotes.models.measure import Measure
from dottednotes.models.text_marking import TextMarking, TextMarkingType


def _note(name="C", octave=4, value=4):
    return Note(dots=frozenset(), category=None, raw_brl="", note_name=name, octave=octave, duration=Duration(value))


def test_single_word_expression_unchanged_one_leading_word_sign_only():
    tm = TextMarking(text="Dolce", type=TextMarkingType.EXPRESSION)
    assert tm.to_braille(inline=True) == '⠜⠙⠕⠇⠉⠑'
    assert tm.is_longer_expression() is False


def test_abbreviation_unchanged_one_leading_word_sign_only():
    tm = TextMarking(text="rit.", type=TextMarkingType.EXPRESSION)
    assert tm.to_braille(inline=True) == '⠜⠗⠊⠞'
    assert tm.is_longer_expression() is False


def test_longer_expression_gets_closing_word_sign():
    # BANA Par. 22.3.8: "enclosed between a pair of word signs" -- opening
    # AND closing, unlike a single word/abbreviation.
    tm = TextMarking(text="poco a poco", type=TextMarkingType.EXPRESSION)
    assert tm.is_longer_expression() is True
    brl = tm.to_braille(inline=True)
    assert brl.startswith('⠜')
    assert brl.endswith('⠜')
    # Internal word gaps are blank braille cells, not stripped.
    assert brl == '⠜⠏⠕⠉⠕⠀⠁⠀⠏⠕⠉⠕⠜'


def test_two_adjacent_single_word_markings_get_no_separator():
    # Par. 22.3's general rule: single words/abbreviations "may be brailled
    # without interruption, each being introduced by the word sign."
    m = Measure(number=1, notes=[_note()])
    m.text_markings = [
        TextMarking(text="Maestoso", type=TextMarkingType.EXPRESSION),
        TextMarking(text="Dolce", type=TextMarkingType.EXPRESSION),
    ]
    brl, _ = m.to_braille(is_measure_start=True)
    assert '⠜⠍⠁⠑⠎⠞⠕⠎⠕⠜⠙⠕⠇⠉⠑' in brl


def test_single_word_then_longer_expression_gets_intervening_space():
    m = Measure(number=1, notes=[_note()])
    m.text_markings = [
        TextMarking(text="Maestoso", type=TextMarkingType.EXPRESSION),
        TextMarking(text="poco a poco", type=TextMarkingType.EXPRESSION),
    ]
    brl, _ = m.to_braille(is_measure_start=True)
    assert '⠜⠍⠁⠑⠎⠞⠕⠎⠕⠀⠜⠏⠕⠉⠕⠀⠁⠀⠏⠕⠉⠕⠜' in brl


def test_two_longer_expressions_get_intervening_space():
    # Par. 22.3.8's own closing sentence: "Two or more unrelated longer
    # expressions should be enclosed in separate pairs of word signs with
    # an intervening space."
    m = Measure(number=1, notes=[_note()])
    m.text_markings = [
        TextMarking(text="poco a poco", type=TextMarkingType.EXPRESSION),
        TextMarking(text="molto legato", type=TextMarkingType.EXPRESSION),
    ]
    brl, _ = m.to_braille(is_measure_start=True)
    first_close = brl.index('⠜', 1)
    assert brl[first_close + 1] == '⠀'


def test_intervening_space_is_blank_braille_cell_not_ascii_space():
    # The separator must be U+2800 (blank braille cell), matching the rest
    # of the Unicode braille pipeline -- not a literal ASCII space, which
    # would break unicode_to_ascii_braille's offset-based conversion.
    m = Measure(number=1, notes=[_note()])
    m.text_markings = [
        TextMarking(text="Maestoso", type=TextMarkingType.EXPRESSION),
        TextMarking(text="poco a poco", type=TextMarkingType.EXPRESSION),
    ]
    brl, _ = m.to_braille(is_measure_start=True)
    assert ' ' not in brl
    assert '⠀' in brl
