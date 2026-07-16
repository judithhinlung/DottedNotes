import pytest
import music21

from dottednotes.parser.musicxml_parser import load_musicxml, MusicXMLTranslator
from dottednotes.models import (
    AccidentalType, ArticulationType, OrnamentType, DynamicLevel, ClefType
)

def test_musicxml_pitch_and_octave_translation():
    # Construct a music21 score in memory
    m21_score = music21.stream.Score()
    part = music21.stream.Part()
    measure = music21.stream.Measure(number=1)
    
    measure.insert(0, music21.clef.TrebleClef())
    measure.insert(0, music21.meter.TimeSignature('4/4'))
    
    # Add a note with sharp
    n1 = music21.note.Note('C#4')
    n1.duration.type = 'quarter'
    measure.append(n1)
    
    # Add a note with double flat
    n2 = music21.note.Note('B--5')
    n2.duration.type = 'eighth'
    measure.append(n2)
    
    part.append(measure)
    m21_score.append(part)
    
    # Translate
    score = MusicXMLTranslator().translate(m21_score)
    
    assert len(score.staves) == 1
    staff = score.staves[0]
    assert len(staff.measures) == 1
    m = staff.measures[0]
    
    assert len(m.notes) == 2
    
    # Check note 1
    note1 = m.notes[0]
    assert note1.note_name == 'C'
    assert note1.octave == 4
    assert note1.accidental is not None
    assert note1.accidental.type == AccidentalType.SHARP
    assert note1.duration.value == 4
    
    # Check note 2
    note2 = m.notes[1]
    assert note2.note_name == 'B'
    assert note2.octave == 5
    assert note2.accidental is not None
    assert note2.accidental.type == AccidentalType.DOUBLE_FLAT
    assert note2.duration.value == 8

def test_musicxml_tuplet_grouping():
    # Construct a music21 triplet measure: 3 eighth notes in a 3:2 tuplet
    m21_score = music21.stream.Score()
    part = music21.stream.Part()
    measure = music21.stream.Measure(number=1)
    
    # Create 3 triplet eighth notes
    notes = [music21.note.Note('C4'), music21.note.Note('D4'), music21.note.Note('E4')]
    t = music21.duration.Tuplet(3, 2)
    t.setDurationType('eighth')
    
    for i, n in enumerate(notes):
        n.duration.type = 'eighth'
        # Set start, normal, stop types
        ti = music21.duration.Tuplet(3, 2)
        if i == 0:
            ti.type = 'start'
        elif i == 2:
            ti.type = 'stop'
        n.duration.appendTuplet(ti)
        measure.append(n)
        
    part.append(measure)
    m21_score.append(part)
    
    score = MusicXMLTranslator().translate(m21_score)
    m = score.staves[0].measures[0]
    
    # Check that it got grouped into a Tuplet model
    assert len(m.notes) == 1
    tuplet = m.notes[0]
    from dottednotes.models.tuplet import Tuplet
    assert isinstance(tuplet, Tuplet)
    assert len(tuplet.items) == 3
    assert all(n.duration.is_triplet for n in tuplet.items)

def test_musicxml_dynamics_and_articulations():
    m21_score = music21.stream.Score()
    part = music21.stream.Part()
    measure = music21.stream.Measure(number=1)
    
    n = music21.note.Note('G4')
    n.duration.type = 'quarter'
    
    # Add articulations
    n.articulations.append(music21.articulations.Staccato())
    n.articulations.append(music21.articulations.Accent())
    
    # Add expressions
    n.expressions.append(music21.expressions.Trill())
    
    measure.append(n)
    
    # Add dynamic at offset 0.0
    dyn = music21.dynamics.Dynamic('ff')
    measure.insert(0.0, dyn)
    
    part.append(measure)
    m21_score.append(part)
    
    score = MusicXMLTranslator().translate(m21_score)
    note_model = score.staves[0].measures[0].notes[0]
    
    # Check articulations
    assert len(note_model.articulations) == 2
    assert note_model.articulations[0].type == ArticulationType.STACCATO
    assert note_model.articulations[1].type == ArticulationType.ACCENT
    
    # Check ornaments
    assert len(note_model.ornaments) == 1
    assert note_model.ornaments[0].type == OrnamentType.TRILL
    
    # Check dynamics
    assert len(note_model.dynamics) == 1
    assert note_model.dynamics[0].level == DynamicLevel.FF

def test_musicxml_lyrics_translation():
    m21_score = music21.stream.Score()
    part = music21.stream.Part()
    measure = music21.stream.Measure(number=1)
    
    n1 = music21.note.Note('C4')
    n1.lyrics.append(music21.note.Lyric(text='He', number=1, syllabic='begin'))
    n1.lyrics.append(music21.note.Lyric(text='A', number=2, syllabic='single'))
    measure.append(n1)
    
    n2 = music21.note.Note('D4')
    n2.lyrics.append(music21.note.Lyric(text='lo', number=1, syllabic='end'))
    n2.lyrics.append(music21.note.Lyric(text='B', number=2, syllabic='single'))
    measure.append(n2)
    
    part.append(measure)
    m21_score.append(part)
    
    score = MusicXMLTranslator().translate(m21_score)
    staff = score.staves[0]
    
    # Verify lyrics verses mapping
    assert len(staff.verses) == 2
    assert staff.verses[0] == ['He --', 'lo']
    assert staff.verses[1] == ['A', 'B']
    assert staff.lyrics == ['He --', 'lo']
    assert staff.verse_prefixes == ['1.', '2.']
