import pytest
import music21

from dottednotes.parser.musicxml_parser import load_musicxml, MusicXMLTranslator
from dottednotes.models import (
    AccidentalType, ArticulationType, OrnamentType, DynamicLevel, ClefType
)
from dottednotes.models.in_accord import InAccord

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

def test_musicxml_multi_voice_single_staff_imports_as_in_accord():
    m21_score = music21.stream.Score()
    part = music21.stream.Part()
    measure = music21.stream.Measure(number=1)
    measure.insert(0, music21.clef.TrebleClef())

    # Voice id '1' deliberately holds the LOWER pitch material and voice id
    # '2' the HIGHER -- this checks that voice ordering is derived from
    # actual pitch content, not from music21's voice numbering (S10b-1).
    low_voice = music21.stream.Voice()
    low_voice.id = '1'
    low_voice.append(music21.note.Note('C4', quarterLength=2))

    high_voice = music21.stream.Voice()
    high_voice.id = '2'
    high_voice.append(music21.note.Note('G4', quarterLength=1))
    high_voice.append(music21.note.Note('A4', quarterLength=1))

    measure.insert(0, low_voice)
    measure.insert(0, high_voice)

    part.append(measure)
    m21_score.append(part)

    score = MusicXMLTranslator().translate(m21_score)
    m = score.staves[0].measures[0]

    assert len(m.notes) == 1
    in_accord = m.notes[0]
    assert isinstance(in_accord, InAccord)
    assert len(in_accord.parts) == 2

    # Treble clef -> highest voice first (BANA Chapter 11), regardless of
    # which music21 voice id the higher pitches happened to be stored under.
    top_voice, bottom_voice = in_accord.parts
    assert [n.note_name for n in top_voice] == ['G', 'A']
    assert [n.note_name for n in bottom_voice] == ['C']

def test_musicxml_transposing_instrument_resolved_from_structured_data():
    # Real-world part names for transposing instruments vary a lot ("Bb
    # Clarinet", "Clarinet in Bb 1", etc.) and won't reliably match
    # get_transposition()'s "<instrument> in <key>" string pattern -- so the
    # importer should resolve the \transpose wrapping from music21's own
    # structured <transpose> data instead (S10b-2), independent of the part
    # name string.
    m21_score = music21.stream.Score()
    part = music21.stream.Part()
    inst = music21.instrument.Clarinet()
    inst.partName = "Bb Clarinet"
    inst.transposition = music21.interval.Interval('M-2')
    part.insert(0, inst)
    measure = music21.stream.Measure(number=1)
    measure.append(music21.note.Note('D5', quarterLength=4))
    part.append(measure)
    m21_score.append(part)

    score = MusicXMLTranslator().translate(m21_score)
    staff = score.staves[0]

    assert staff.resolved_transposition == ("c'", "bes")

def test_musicxml_non_transposing_instrument_has_no_resolved_transposition():
    m21_score = music21.stream.Score()
    part = music21.stream.Part()
    inst = music21.instrument.Flute()
    part.insert(0, inst)
    measure = music21.stream.Measure(number=1)
    measure.append(music21.note.Note('D5', quarterLength=4))
    part.append(measure)
    m21_score.append(part)

    score = MusicXMLTranslator().translate(m21_score)
    staff = score.staves[0]

    assert staff.resolved_transposition is None

def test_musicxml_chord_symbol_does_not_import_as_played_chord():
    # music21.harmony.ChordSymbol is itself a music21.chord.Chord subclass,
    # so without an explicit exclusion it used to fall into the generic
    # Chord-translation branch and import as a real 4-note sounding chord
    # competing with the actual melody note at that beat (S10b-3).
    m21_score = music21.stream.Score()
    part = music21.stream.Part()
    measure = music21.stream.Measure(number=1)
    measure.insert(0, music21.harmony.ChordSymbol('Cmaj7'))
    measure.insert(0, music21.note.Note('C4', quarterLength=4))
    part.append(measure)
    m21_score.append(part)

    score = MusicXMLTranslator().translate(m21_score)
    m = score.staves[0].measures[0]

    assert len(m.notes) == 1
    assert m.notes[0].note_name == 'C'
    assert m.notes[0].octave == 4


def test_musicxml_lead_sheet_chord_symbols_import_and_align():
    m21_score = music21.stream.Score()
    part = music21.stream.Part()
    measure = music21.stream.Measure(number=1)
    measure.insert(0, music21.clef.TrebleClef())
    measure.insert(0.0, music21.harmony.ChordSymbol('Cmaj7'))
    measure.insert(0.0, music21.note.Note('C4', quarterLength=2))
    measure.insert(2.0, music21.harmony.ChordSymbol('Dm7'))
    measure.insert(2.0, music21.note.Note('D4', quarterLength=2))
    part.append(measure)
    m21_score.append(part)

    score = MusicXMLTranslator().translate(m21_score)

    assert score.chord_names is not None
    entries = score.chord_names.entries
    assert len(entries) == 2
    assert entries[0][1].root == 'C'
    assert entries[0][1].has_explicit_maj is True
    assert entries[1][1].root == 'D'
    assert entries[1][1].is_minor is True
    assert entries[1][1].extensions == [(7, None)]

    ly = score.chord_names.to_lilypond()
    assert 'c2:maj7' in ly
    assert 'd2:m7' in ly


def test_musicxml_chord_symbol_with_slash_bass():
    m21_score = music21.stream.Score()
    part = music21.stream.Part()
    measure = music21.stream.Measure(number=1)
    measure.insert(0.0, music21.harmony.ChordSymbol('G7/B'))
    measure.insert(0.0, music21.note.Note('G4', quarterLength=4))
    part.append(measure)
    m21_score.append(part)

    score = MusicXMLTranslator().translate(m21_score)
    chord = score.chord_names.entries[0][1]
    assert chord.root == 'G'
    assert chord.extensions == [(7, None)]
    assert chord.bass_note == ('B', None)


def test_musicxml_unrecognized_chord_kind_raises():
    from dottednotes.exceptions import DottedNotesError

    m21_score = music21.stream.Score()
    part = music21.stream.Part()
    measure = music21.stream.Measure(number=1)
    measure.insert(0.0, music21.harmony.ChordSymbol('Cpower'))
    measure.insert(0.0, music21.note.Note('C4', quarterLength=4))
    part.append(measure)
    m21_score.append(part)

    with pytest.raises(DottedNotesError):
        MusicXMLTranslator().translate(m21_score)

def _measure_with_octave_shift(pitch_octave: int, shift_type: str) -> str:
    """A minimal single-note, single-measure MusicXML document with an
    <octave-shift> bracket around the note, matching what real notation
    software emits. `shift_type` is the MusicXML type attribute -- "down"
    is the real-world encoding for a bracket meaning "sounds an octave
    HIGHER than written" (confirmed by round-tripping music21's own
    Ottava(type='8va') through its exporter during S10b-8's investigation);
    "up" means "sounds an octave LOWER than written".
    """
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 3.1 Partwise//EN" "http://www.musicxml.org/dtds/partwise.dtd">
<score-partwise version="3.1">
  <part-list><score-part id="P1"><part-name>Piano</part-name></score-part></part-list>
  <part id="P1">
    <measure number="1">
      <attributes><divisions>1</divisions><time><beats>4</beats><beat-type>4</beat-type></time><clef><sign>G</sign><line>2</line></clef></attributes>
      <direction placement="above"><direction-type><octave-shift type="{shift_type}" size="8" number="1"/></direction-type></direction>
      <note><pitch><step>C</step><octave>{pitch_octave}</octave></pitch><duration>4</duration><type>whole</type></note>
      <direction><direction-type><octave-shift type="stop" size="8" number="1"/></direction-type></direction>
    </measure>
  </part>
</score-partwise>
'''


def test_musicxml_ottava_up_imports_at_sounding_octave():
    # Printed C5 under an "8va" (sounds higher) bracket must import at the
    # true sounding octave, C6, per BANA Par. 3.3 -- braille has no
    # equivalent of an 8va bracket; it just writes the octave actually
    # performed (S10b-8).
    m21_score = music21.converter.parse(_measure_with_octave_shift(5, 'down'), format='musicxml')
    score = MusicXMLTranslator().translate(m21_score)
    note = score.staves[0].measures[0].notes[0]
    assert note.note_name == 'C'
    assert note.octave == 6


def test_musicxml_ottava_down_imports_at_sounding_octave():
    # Printed C5 under an "8vb" (sounds lower) bracket must import at C4.
    m21_score = music21.converter.parse(_measure_with_octave_shift(5, 'up'), format='musicxml')
    score = MusicXMLTranslator().translate(m21_score)
    note = score.staves[0].measures[0].notes[0]
    assert note.note_name == 'C'
    assert note.octave == 4


def test_musicxml_note_without_ottava_is_unaffected():
    m21_score = music21.stream.Score()
    part = music21.stream.Part()
    measure = music21.stream.Measure(number=1)
    measure.append(music21.note.Note('C5', quarterLength=4))
    part.append(measure)
    m21_score.append(part)

    score = MusicXMLTranslator().translate(m21_score)
    note = score.staves[0].measures[0].notes[0]
    assert note.octave == 5

def test_musicxml_fermata_over_note_imports():
    from dottednotes.models import FermataShape

    m21_score = music21.stream.Score()
    part = music21.stream.Part()
    measure = music21.stream.Measure(number=1)
    n = music21.note.Note('C4', quarterLength=4)
    n.expressions.append(music21.expressions.Fermata())
    measure.append(n)
    part.append(measure)
    m21_score.append(part)

    score = MusicXMLTranslator().translate(m21_score)
    note = score.staves[0].measures[0].notes[0]
    assert note.fermata is not None
    assert note.fermata.shape == FermataShape.NORMAL


def test_musicxml_fermata_shape_variants_import():
    from dottednotes.models import FermataShape

    for m21_shape, expected in [('square', FermataShape.SQUARED), ('angled', FermataShape.TENT)]:
        m21_score = music21.stream.Score()
        part = music21.stream.Part()
        measure = music21.stream.Measure(number=1)
        n = music21.note.Note('C4', quarterLength=4)
        fermata = music21.expressions.Fermata()
        fermata.shape = m21_shape
        n.expressions.append(fermata)
        measure.append(n)
        part.append(measure)
        m21_score.append(part)

        score = MusicXMLTranslator().translate(m21_score)
        note = score.staves[0].measures[0].notes[0]
        assert note.fermata.shape == expected


def test_musicxml_note_without_fermata_has_none():
    m21_score = music21.stream.Score()
    part = music21.stream.Part()
    measure = music21.stream.Measure(number=1)
    measure.append(music21.note.Note('C4', quarterLength=4))
    part.append(measure)
    m21_score.append(part)

    score = MusicXMLTranslator().translate(m21_score)
    assert score.staves[0].measures[0].notes[0].fermata is None

def test_musicxml_breath_mark_imports_as_half_breath():
    from dottednotes.models import BreathMarkVariant

    m21_score = music21.stream.Score()
    part = music21.stream.Part()
    measure = music21.stream.Measure(number=1)
    n = music21.note.Note('C4', quarterLength=4)
    n.articulations.append(music21.articulations.BreathMark())
    measure.append(n)
    part.append(measure)
    m21_score.append(part)

    score = MusicXMLTranslator().translate(m21_score)
    note = score.staves[0].measures[0].notes[0]
    assert note.breath_mark is not None
    assert note.breath_mark.variant == BreathMarkVariant.HALF


def test_musicxml_caesura_imports_as_full_breath():
    from dottednotes.models import BreathMarkVariant

    m21_score = music21.stream.Score()
    part = music21.stream.Part()
    measure = music21.stream.Measure(number=1)
    n = music21.note.Note('C4', quarterLength=4)
    n.articulations.append(music21.articulations.Caesura())
    measure.append(n)
    part.append(measure)
    m21_score.append(part)

    score = MusicXMLTranslator().translate(m21_score)
    note = score.staves[0].measures[0].notes[0]
    assert note.breath_mark is not None
    assert note.breath_mark.variant == BreathMarkVariant.FULL


def test_musicxml_note_without_breath_mark_has_none():
    m21_score = music21.stream.Score()
    part = music21.stream.Part()
    measure = music21.stream.Measure(number=1)
    measure.append(music21.note.Note('C4', quarterLength=4))
    part.append(measure)
    m21_score.append(part)

    score = MusicXMLTranslator().translate(m21_score)
    assert score.staves[0].measures[0].notes[0].breath_mark is None
