import pytest
from dottednotes.parser.tokenizer import BrailleTokenizer
from dottednotes.parser.braille_parser import BrailleParser
from dottednotes.models.note import Note, Rest

def test_compact_breve_notes():
    # ⠼⠙⠆ = 4/2 time signature (measure is 8 beats / 192 ticks)
    # ⠐ = octave 4 mark
    # ⠽⠅ = C breve note
    # ⠵⠅ = D breve note
    # ⠯⠅ = E breve note
    # ⠿⠅ = F breve note
    # ⠷⠅ = G breve note
    # ⠮⠅ = A breve note
    # ⠾⠅ = B breve note
    brf = "⠼⠙⠆⠐⠽⠅⠀⠐⠵⠅⠀⠐⠯⠅⠀⠐⠿⠅⠀⠐⠷⠅⠀⠐⠮⠅⠀⠐⠾⠅"
    tokens = BrailleTokenizer().tokenize(brf)
    score = BrailleParser(tokens=tokens).parse()
    
    # Check notes and their LilyPond formatting
    measures = score.staves[0].measures
    assert len(measures) == 7
    
    assert measures[0].notes[0].to_lilypond() == "c'\\breve"
    assert measures[1].notes[0].to_lilypond() == "d'\\breve"
    assert measures[2].notes[0].to_lilypond() == "e'\\breve"
    assert measures[3].notes[0].to_lilypond() == "f'\\breve"
    assert measures[4].notes[0].to_lilypond() == "g'\\breve"
    assert measures[5].notes[0].to_lilypond() == "a'\\breve"
    assert measures[6].notes[0].to_lilypond() == "b'\\breve"

def test_compact_breve_rest():
    # ⠼⠙⠆ = 4/2 time signature
    # ⠍⠅ = breve rest
    brf = "⠼⠙⠆⠍⠅"
    tokens = BrailleTokenizer().tokenize(brf)
    score = BrailleParser(tokens=tokens).parse()
    measures = score.staves[0].measures
    assert len(measures) == 1
    assert measures[0].notes[0].to_lilypond() == "R\\breve"

def test_longer_form_breve_notes():
    # ⠼⠙⠆ = 4/2 time signature
    # ⠐⠽⠘⠉⠽ = C breve note longer form (y^cy)
    # ⠐⠵⠘⠉⠵ = D breve note longer form (z^cz)
    brf = "⠼⠙⠆⠐⠽⠘⠉⠽⠀⠐⠵⠘⠉⠵"
    tokens = BrailleTokenizer().tokenize(brf)
    score = BrailleParser(tokens=tokens).parse()
    measures = score.staves[0].measures
    assert len(measures) == 2
    assert measures[0].notes[0].to_lilypond() == "c'\\breve"
    assert measures[1].notes[0].to_lilypond() == "d'\\breve"

def test_longer_form_breve_rest():
    # ⠼⠙⠆ = 4/2 time signature
    # ⠍⠘⠉⠍ = breve rest longer form (m^cm)
    brf = "⠼⠙⠆⠍⠘⠉⠍"
    tokens = BrailleTokenizer().tokenize(brf)
    score = BrailleParser(tokens=tokens).parse()
    measures = score.staves[0].measures
    assert len(measures) == 1
    assert measures[0].notes[0].to_lilypond() == "R\\breve"

def test_breve_beat_count_warning():
    # In 4/2 time signature (8.0 beats / 192 ticks)
    # ⠐⠽⠅⠐⠵⠅ = two compact breve notes (16 beats / 384 ticks) in one measure
    # This should trigger a beat validation warning since 16.0 != 8.0.
    brf = "⠼⠙⠆⠐⠽⠅⠐⠵⠅"
    tokens = BrailleTokenizer().tokenize(brf)
    with pytest.warns(UserWarning, match="expected 8.0 beats but counted 16.0"):
        BrailleParser(tokens=tokens).parse()
