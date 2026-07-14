import pytest
from dottednotes.parser.tokenizer import BrailleTokenizer
from dottednotes.parser.braille_parser import BrailleParser
from dottednotes.models.note import Note, Rest
from dottednotes.models.chord import Chord

def test_sustain_pedal_notes():
    # ⠣⠉ = pedal down
    # ⠐⠹ = C4 (middle C, quarter note)
    # ⠐⠱ = D4 (quarter note)
    # ⠡⠉ = pedal up
    brf = "⠣⠉⠐⠹ ⠐⠱⠡⠉"
    tokens = BrailleTokenizer().tokenize(brf)
    score = BrailleParser(tokens=tokens).parse()
    
    notes = score.staves[0].measures[0].notes
    assert len(notes) == 2
    
    assert notes[0].pedal_sustain == "on"
    assert notes[1].pedal_sustain == "off"
    
    assert notes[0].to_lilypond() == "c'4\\sustainOn"
    assert notes[1].to_lilypond() == "d'4\\sustainOff"

def test_sustain_pedal_change():
    # ⠣⠉ = pedal down
    # ⠐⠹ = C4
    # ⠡⠣⠉ = pedal change
    # ⠐⠱ = D4
    # ⠡⠉ = pedal up
    brf = "⠣⠉⠐⠹⠡⠣⠉ ⠐⠱⠡⠉"
    tokens = BrailleTokenizer().tokenize(brf)
    score = BrailleParser(tokens=tokens).parse()
    
    notes = score.staves[0].measures[0].notes
    assert len(notes) == 2
    
    assert notes[0].pedal_sustain == "change"
    assert notes[1].pedal_sustain == "off"
    
    assert notes[0].to_lilypond() == "c'4\\sustainOff\\sustainOn"
    assert notes[1].to_lilypond() == "d'4\\sustainOff"

def test_sustain_pedal_chords():
    # ⠣⠉ = pedal down
    # ⠐⠹ = C4 (quarter note C)
    # ⠬ = interval 3rd (E4 / A3 depending on direction; default treble = descending -> A3)
    # ⠐⠱ = D4 (quarter note D)
    # ⠬ = interval 3rd (F4 / B3 depending on direction; default treble = descending -> B3)
    # ⠡⠉ = pedal up
    brf = "⠣⠉⠐⠹⠬ ⠐⠱⠬⠡⠉"
    tokens = BrailleTokenizer().tokenize(brf)
    score = BrailleParser(tokens=tokens).parse()
    
    chords = score.staves[0].measures[0].notes
    assert len(chords) == 2
    assert isinstance(chords[0], Chord)
    assert isinstance(chords[1], Chord)
    
    assert chords[0].notes[0].pedal_sustain == "on"
    assert chords[1].notes[0].pedal_sustain == "off"
    
    assert chords[0].to_lilypond() == "<c a>4\\sustainOn"
    assert chords[1].to_lilypond() == "<d b>4\\sustainOff"

def test_sustain_pedal_rests():
    # ⠣⠉ = pedal down
    # ⠍ = whole rest
    # ⠡⠉ = pedal up
    # Separated by measure separator to resolve to whole measure rests
    brf = "⠣⠉⠍⠀⠍⠡⠉"
    tokens = BrailleTokenizer().tokenize(brf)
    score = BrailleParser(tokens=tokens).parse()
    
    measures = score.staves[0].measures
    assert len(measures) == 2
    
    r1 = measures[0].notes[0]
    r2 = measures[1].notes[0]
    assert isinstance(r1, Rest)
    assert isinstance(r2, Rest)
    
    assert r1.pedal_sustain == "on"
    assert r2.pedal_sustain == "off"
    
    assert r1.to_lilypond() == "R1\\sustainOn"
    assert r2.to_lilypond() == "R1\\sustainOff"

def test_sustain_pedal_alternatives():
    # ⠐⠣⠉ = half pedal
    # ⠐⠹ = C4
    # ⠐⠡⠉ = pedal up immediately after strike
    # ⠠⠣⠉ = pedal down immediately after strike
    # ⠐⠱ = D4
    brf = "⠐⠣⠉⠐⠹⠐⠡⠉ ⠠⠣⠉⠐⠱"
    tokens = BrailleTokenizer().tokenize(brf)
    score = BrailleParser(tokens=tokens).parse()
    
    notes = score.staves[0].measures[0].notes
    assert len(notes) == 2
    
    assert notes[0].pedal_sustain == "on_off"
    assert notes[1].pedal_sustain == "on"
    
    assert notes[0].to_lilypond() == "c'4\\sustainOn\\sustainOff"
    assert notes[1].to_lilypond() == "d'4\\sustainOn"

def test_sustain_pedal_cross_measure():
    # Pedal up at start of measure 2 should attach to the last note of measure 1.
    # ⠣⠉ = pedal down
    # ⠐⠹ = C4
    # ⠀ = bar line
    # ⠡⠉ = pedal up
    # ⠐⠱ = D4
    brf = "⠣⠉⠐⠹⠀⠡⠉⠐⠱"
    tokens = BrailleTokenizer().tokenize(brf)
    score = BrailleParser(tokens=tokens).parse()
    
    measures = score.staves[0].measures
    assert len(measures) == 2
    
    m1_notes = measures[0].notes
    m2_notes = measures[1].notes
    
    assert m1_notes[0].pedal_sustain == "on_off"
    assert m2_notes[0].pedal_sustain is None
    
    assert m1_notes[0].to_lilypond() == "c'4\\sustainOn\\sustainOff"
    assert m2_notes[0].to_lilypond() == "d'4"
