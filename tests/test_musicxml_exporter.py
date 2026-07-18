import pytest
import tempfile
import pathlib
import music21

from dottednotes.models import (
    Score, Staff, Measure, Note, Rest, Chord, Duration,
    Accidental, AccidentalType, Dynamic, DynamicLevel,
    Articulation, ArticulationType, Ornament, OrnamentType,
    Clef, ClefType, KeySignature, TimeSignature,
    Fermata, FermataShape, BreathMark, BreathMarkVariant,
)
from dottednotes.renderers.musicxml_renderer import MusicXMLRenderer, export_musicxml

def test_musicxml_export_notes_and_chords():
    score = Score(title="Export Test", composer="Test Composer", copyright="2026 Test")
    staff = Staff(name="Melody")
    
    # Measure 1
    m = Measure(number=1, clef="treble", key_signature=1, time_signature=(3, 4))
    
    # Note G4 with sharp, quarter
    dur_q = Duration(value=4, dots=0)
    acc_sharp = Accidental(dots=frozenset(), category=None, raw_brl="", type=AccidentalType.SHARP)
    n1 = Note(dots=frozenset(), category=None, raw_brl="", note_name='G', octave=4, duration=dur_q, accidental=acc_sharp)
    n1.articulations.append(Articulation(type=ArticulationType.STACCATO))
    n1.ornaments.append(Ornament(type=OrnamentType.TRILL))
    m.add_note(n1)
    
    # Chord E4 and G4, half note
    dur_h = Duration(value=2, dots=0)
    c_n1 = Note(dots=frozenset(), category=None, raw_brl="", note_name='G', octave=4, duration=dur_h)
    c_n2 = Note(dots=frozenset(), category=None, raw_brl="", note_name='E', octave=4, duration=dur_h)
    chord = Chord(notes=[c_n1, c_n2])
    m.add_note(chord)
    
    staff.add_measure(m)
    score.add_staff(staff)
    
    # Render
    m21_score = MusicXMLRenderer().render(score)
    
    # Verify metadata
    assert m21_score.metadata.title == "Export Test"
    assert m21_score.metadata.composer == "Test Composer"
    assert m21_score.metadata.copyright == "2026 Test"
    
    # Verify part and measure
    assert len(m21_score.parts) == 1
    part = m21_score.parts[0]
    assert len(part.getElementsByClass(music21.stream.Measure)) == 1
    m21_measure = part.getElementsByClass(music21.stream.Measure)[0]
    
    # Verify signatures
    assert len(m21_measure.getElementsByClass(music21.key.KeySignature)) == 1
    assert m21_measure.getElementsByClass(music21.key.KeySignature)[0].sharps == 1
    assert len(m21_measure.getElementsByClass(music21.meter.TimeSignature)) == 1
    assert m21_measure.getElementsByClass(music21.meter.TimeSignature)[0].ratioString == '3/4'
    assert len(m21_measure.getElementsByClass(music21.clef.Clef)) == 1
    
    # Verify elements
    elements = m21_measure.notesAndRests
    assert len(elements) == 2
    
    # Verify G#4
    note_el = elements[0]
    assert isinstance(note_el, music21.note.Note)
    assert note_el.pitch.step == 'G'
    assert note_el.pitch.octave == 4
    assert note_el.pitch.accidental.name == 'sharp'
    assert note_el.duration.type == 'quarter'
    assert len(note_el.articulations) == 1
    assert isinstance(note_el.articulations[0], music21.articulations.Staccato)
    assert len(note_el.expressions) == 1
    assert isinstance(note_el.expressions[0], music21.expressions.Trill)
    
    # Verify Chord
    chord_el = elements[1]
    assert isinstance(chord_el, music21.chord.Chord)
    assert chord_el.duration.type == 'half'
    assert len(chord_el.notes) == 2
    pitches = [p.nameWithOctave for p in chord_el.pitches]
    # Default order sorted descending or ascending depending on clef. Clef is treble, so descending (highest first)
    assert pitches == ['G4', 'E4']

def test_musicxml_export_lyrics():
    score = Score(title="Lyrics Export")
    staff = Staff(name="Voice")
    m = Measure(number=1)
    
    dur = Duration(value=4, dots=0)
    n1 = Note(dots=frozenset(), category=None, raw_brl="", note_name='C', octave=4, duration=dur)
    n2 = Note(dots=frozenset(), category=None, raw_brl="", note_name='D', octave=4, duration=dur)
    m.add_note(n1)
    m.add_note(n2)
    staff.add_measure(m)
    
    # Add lyrics
    staff.verses = [['Hel --', 'lo']]
    staff.lyrics = staff.verses[0]
    
    score.add_staff(staff)
    
    m21_score = MusicXMLRenderer().render(score)
    m21_measure = m21_score.parts[0].getElementsByClass(music21.stream.Measure)[0]
    notes = m21_measure.notes
    
    assert len(notes[0].lyrics) == 1
    assert notes[0].lyrics[0].text == 'Hel'
    assert notes[0].lyrics[0].syllabic == 'begin'
    
    assert len(notes[1].lyrics) == 1
    assert notes[1].lyrics[0].text == 'lo'
    assert notes[1].lyrics[0].syllabic == 'single'

def test_export_musicxml_to_file():
    score = Score(title="File Write Test")
    staff = Staff(name="Melody")
    m = Measure(number=1)
    dur = Duration(value=4)
    m.add_note(Note(dots=frozenset(), category=None, raw_brl="", note_name='E', octave=4, duration=dur))
    staff.add_measure(m)
    score.add_staff(staff)
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        out_path = pathlib.Path(tmp_dir) / "test.musicxml"
        export_musicxml(score, str(out_path))
        assert out_path.exists()
        # Ensure it contains XML markup
        content = out_path.read_text(encoding="utf-8")
        assert "<score-partwise" in content

def test_musicxml_export_fermata_and_breath_mark():
    score = Score()
    staff = Staff(name="Melody")
    m = Measure(number=1)
    dur = Duration(value=4)
    n = Note(
        dots=frozenset(), category=None, raw_brl="", note_name='C', octave=4, duration=dur,
        fermata=Fermata(shape=FermataShape.SQUARED),
        breath_mark=BreathMark(variant=BreathMarkVariant.FULL),
    )
    m.add_note(n)
    staff.add_measure(m)
    score.add_staff(staff)

    m21_score = MusicXMLRenderer().render(score)
    m21_note = m21_score.parts[0].getElementsByClass(music21.stream.Measure)[0].notes[0]

    fermatas = [e for e in m21_note.expressions if isinstance(e, music21.expressions.Fermata)]
    assert len(fermatas) == 1
    assert fermatas[0].shape == 'square'

    caesuras = [a for a in m21_note.articulations if isinstance(a, music21.articulations.Caesura)]
    assert len(caesuras) == 1

def test_musicxml_export_volta_ending():
    score = Score()
    staff = Staff(name="Melody")
    m1 = Measure(number=1, ending_numbers=[1])
    m1.add_note(Note(dots=frozenset(), category=None, raw_brl="", note_name='C', octave=4, duration=Duration(value=4)))
    m2 = Measure(number=2, ending_numbers=[2])
    m2.add_note(Note(dots=frozenset(), category=None, raw_brl="", note_name='D', octave=4, duration=Duration(value=4)))
    staff.add_measure(m1)
    staff.add_measure(m2)
    score.add_staff(staff)

    m21_score = MusicXMLRenderer().render(score)
    part = m21_score.parts[0]
    measures = part.getElementsByClass(music21.stream.Measure)

    brackets_1 = measures[0].getSpannerSites(music21.spanner.RepeatBracket)
    brackets_2 = measures[1].getSpannerSites(music21.spanner.RepeatBracket)
    assert len(brackets_1) == 1 and brackets_1[0].numberRange == [1]
    assert len(brackets_2) == 1 and brackets_2[0].numberRange == [2]

def test_musicxml_export_combined_volta_ending():
    score = Score()
    staff = Staff(name="Melody")
    m = Measure(number=1, ending_numbers=[1, 2])
    m.add_note(Note(dots=frozenset(), category=None, raw_brl="", note_name='C', octave=4, duration=Duration(value=4)))
    staff.add_measure(m)
    score.add_staff(staff)

    m21_score = MusicXMLRenderer().render(score)
    measure = m21_score.parts[0].getElementsByClass(music21.stream.Measure)[0]
    brackets = measure.getSpannerSites(music21.spanner.RepeatBracket)
    assert len(brackets) == 1
    assert brackets[0].numberRange == [1, 2]

def test_musicxml_export_forward_repeat_on_next_measure_leftbarline():
    # bar_line_type='forward_repeat' on measure N means "repeat starts at
    # measure N+1" (this codebase's tested convention) -- must export as
    # measure N+1's leftBarline, not measure N's, and NOT as measure N's
    # rightBarline either (confirmed empirically: a Repeat on rightBarline
    # gets reinterpreted as a backward/end repeat regardless of its
    # .direction attribute).
    score = Score()
    staff = Staff(name="Melody")
    m1 = Measure(number=1, bar_line_type='forward_repeat')
    m1.add_note(Note(dots=frozenset(), category=None, raw_brl="", note_name='C', octave=4, duration=Duration(value=4)))
    m2 = Measure(number=2)
    m2.add_note(Note(dots=frozenset(), category=None, raw_brl="", note_name='D', octave=4, duration=Duration(value=4)))
    staff.add_measure(m1)
    staff.add_measure(m2)
    score.add_staff(staff)

    m21_score = MusicXMLRenderer().render(score)
    measures = m21_score.parts[0].getElementsByClass(music21.stream.Measure)
    assert measures[0].rightBarline is None
    assert measures[0].leftBarline is None
    assert isinstance(measures[1].leftBarline, music21.bar.Repeat)
    assert measures[1].leftBarline.direction == 'start'
