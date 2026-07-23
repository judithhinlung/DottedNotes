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

def test_musicxml_accidental_display_status_suppresses_spurious_naturals():
    # BANA-adjacent bug: music21's engraving pass attaches a non-None
    # `pitch.accidental` to almost every note in a keyed piece as internal
    # pitch-spelling bookkeeping, even when nothing should be printed.
    # `displayStatus == False` is music21's own signal that the accidental
    # is present but not meant to be shown -- only an explicit `<accidental>`
    # tag (or a real, need-to-show case) gets `True`/`None`. Parsed via
    # `music21.converter.parse` (not hand-built Accidental objects) since
    # it's converter.parse's own engraving pass that sets displayStatus.
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 3.1 Partwise//EN" "http://www.musicxml.org/dtds/partwise.dtd">
<score-partwise version="3.1">
  <part-list>
    <score-part id="P1"><part-name>Test</part-name></score-part>
  </part-list>
  <part id="P1">
    <measure number="1">
      <attributes>
        <divisions>1</divisions>
        <key><fifths>2</fifths></key>
        <time><beats>3</beats><beat-type>4</beat-type></time>
        <clef><sign>G</sign><line>2</line></clef>
      </attributes>
      <note>
        <pitch><step>F</step><alter>0</alter><octave>5</octave></pitch>
        <duration>1</duration><type>quarter</type>
        <accidental>natural</accidental>
      </note>
      <note>
        <pitch><step>F</step><alter>1</alter><octave>5</octave></pitch>
        <duration>1</duration><type>quarter</type>
      </note>
      <note>
        <pitch><step>G</step><alter>0</alter><octave>5</octave></pitch>
        <duration>1</duration><type>quarter</type>
      </note>
    </measure>
  </part>
</score-partwise>
"""
    m21_score = music21.converter.parse(xml, format="musicxml")
    score = MusicXMLTranslator().translate(m21_score)

    notes = score.staves[0].measures[0].notes
    assert len(notes) == 3

    explicit_natural, implied_by_key, fully_diatonic = notes
    assert explicit_natural.accidental is not None
    assert explicit_natural.accidental.type == AccidentalType.NATURAL
    assert implied_by_key.accidental is None
    assert fully_diatonic.accidental is None


def test_musicxml_overlapping_slurs_get_consistent_plain_vs_bracket_roles():
    # Regression test (found via gerhard_roberto_capriccio2_for_flute.xml):
    # two overlapping slurs -- slurA spanning n1-n3, slurB spanning n2-n4
    # (opening while slurA is still open) -- must resolve to the SAME
    # plain/bracket role (BANA 13.3) at both their start and end notes.
    # `getSpannerSites(Slur)`'s per-note list position isn't a stable
    # identifier for a given slur across different notes, so deciding
    # plain-vs-bracket independently at each note (the previous approach)
    # could assign a slur one role at its start and the other at its end,
    # producing mismatched LilyPond slur signs ("already have slur"/
    # "cannot end slur"). Here slurA must stay "primary" (opens when
    # nothing else is open) and slurB must be "bracket" throughout (opens
    # while slurA is still open), consistently at both ends.
    n1 = music21.note.Note('C4', type='quarter')
    n2 = music21.note.Note('D4', type='quarter')
    n3 = music21.note.Note('E4', type='quarter')
    n4 = music21.note.Note('F4', type='quarter')
    slur_a = music21.spanner.Slur(n1, n3)
    slur_b = music21.spanner.Slur(n2, n4)

    m = music21.stream.Measure(number=1)
    for n in (n1, n2, n3, n4):
        m.append(n)
    m.insert(0, slur_a)
    m.insert(0, slur_b)

    from dottednotes.models.duration import Duration as ModelDuration
    translator = MusicXMLTranslator()
    model_duration = ModelDuration(value=4)
    notes = [translator.translate_note_obj(n, model_duration) for n in (n1, n2, n3, n4)]
    note1, note2, note3, note4 = notes

    assert (note1.slur_start, note1.slur_bracket_open) == (True, False)
    assert (note3.slur_end, note3.slur_bracket_close) == (True, False)
    assert (note2.slur_bracket_open, note2.slur_start) == (True, False)
    assert (note4.slur_bracket_close, note4.slur_end) == (True, False)


def test_musicxml_tied_continuation_note_keeps_accidental_differing_from_key():
    # Regression test (found via a real OMR-sourced solo flute piece,
    # gerhard_roberto_capriccio2_for_flute.xml): a tied-continuation note is
    # not visually re-printed with its accidental (music21 marks it
    # displayStatus=False, same signal as a key-signature-implied
    # accidental), but it still sounds the altered pitch and MUST keep its
    # Accidental -- dropping it previously produced a wrong LilyPond pitch
    # letter ("b" instead of "bes"), breaking the tie (the two notes no
    # longer had matching pitches). Key is C major (no sharps/flats), so
    # B-flat is a real deviation from the key here, unlike the
    # implied-by-key case above.
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 3.1 Partwise//EN" "http://www.musicxml.org/dtds/partwise.dtd">
<score-partwise version="3.1">
  <part-list>
    <score-part id="P1"><part-name>Test</part-name></score-part>
  </part-list>
  <part id="P1">
    <measure number="1">
      <attributes>
        <divisions>1</divisions>
        <key><fifths>0</fifths></key>
        <time><beats>4</beats><beat-type>4</beat-type></time>
        <clef><sign>G</sign><line>2</line></clef>
      </attributes>
      <note>
        <pitch><step>B</step><alter>-1</alter><octave>4</octave></pitch>
        <duration>2</duration><type>half</type>
        <tie type="start"/>
        <notations><tied type="start"/></notations>
      </note>
      <note>
        <pitch><step>B</step><alter>-1</alter><octave>4</octave></pitch>
        <duration>2</duration><type>half</type>
        <tie type="stop"/>
        <notations><tied type="stop"/></notations>
      </note>
    </measure>
  </part>
</score-partwise>
"""
    m21_score = music21.converter.parse(xml, format="musicxml")
    score = MusicXMLTranslator().translate(m21_score)

    first, second = score.staves[0].measures[0].notes
    assert first.accidental is not None
    assert first.accidental.type == AccidentalType.FLAT
    assert second.accidental is not None
    assert second.accidental.type == AccidentalType.FLAT
    assert first.note_name == second.note_name == "B"


def test_musicxml_duration_diverging_from_type_finds_exact_dotted_match():
    # Regression test (found via gerhard_roberto_capriccio2_for_flute.xml,
    # measure 75): a tie-continuation note whose <duration> implies a
    # dotted value (3 beats) but whose <type> carries no <dot> tag (a
    # legitimate MusicXML divergence between the printed type and the
    # actual performed length) previously fell back to a nearest-power-of-
    # 2 approximation that always reset dots to 0, silently losing a full
    # beat (interpreted as a plain, undotted half note = 2 beats instead
    # of the true dotted half = 3 beats). The fallback must search for an
    # EXACT (value, dots) match against the real duration before resorting
    # to that lossy approximation.
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 3.1 Partwise//EN" "http://www.musicxml.org/dtds/partwise.dtd">
<score-partwise version="3.1">
  <part-list>
    <score-part id="P1"><part-name>Test</part-name></score-part>
  </part-list>
  <part id="P1">
    <measure number="1">
      <attributes>
        <divisions>2</divisions>
        <key><fifths>0</fifths></key>
        <time><beats>3</beats><beat-type>4</beat-type></time>
        <clef><sign>G</sign><line>2</line></clef>
      </attributes>
      <note>
        <pitch><step>C</step><alter>1</alter><octave>6</octave></pitch>
        <duration>6</duration><type>half</type>
        <tie type="stop"/>
        <tie type="start"/>
        <notations>
          <tied type="stop"/>
          <tied type="start"/>
        </notations>
      </note>
    </measure>
  </part>
</score-partwise>
"""
    m21_score = music21.converter.parse(xml, format="musicxml")
    score = MusicXMLTranslator().translate(m21_score)

    note = score.staves[0].measures[0].notes[0]
    assert note.duration.value == 2
    assert note.duration.dots == 1
    assert score.staves[0].measures[0].total_ticks() == round(3 * 24)  # 3 beats, TICKS_PER_QUARTER=24


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


def test_musicxml_augmented_seventh_chord_kind():
    # Regression test (found via the MusicXML Test Suite's own
    # 71f-AllChordTypes.xml): 'augmented-seventh' is just the combination
    # of two primitives already mapped separately elsewhere in
    # _CHORD_KIND_TO_MODEL_FIELDS (is_augmented + a plain 7th extension --
    # BANA Table 23's "Plus" sign plus its "Italic 7" sign), not a new BANA
    # sign of its own.
    m21_score = music21.stream.Score()
    part = music21.stream.Part()
    measure = music21.stream.Measure(number=1)
    measure.insert(0.0, music21.harmony.ChordSymbol('C7+'))
    measure.insert(0.0, music21.note.Note('C4', quarterLength=4))
    part.append(measure)
    m21_score.append(part)

    score = MusicXMLTranslator().translate(m21_score)
    chord = score.chord_names.entries[0][1]
    assert chord.root == 'C'
    assert chord.is_augmented is True
    assert chord.extensions == [(7, None)]


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


def test_load_musicxml_wraps_internal_translate_errors_cleanly():
    # Regression test (found via the MusicXML Test Suite's own
    # 33e-Spanners-OctaveShifts-InvalidSize.xml): a malformed
    # <octave-shift size="..."> (non-numeric) makes music21 raise a raw
    # SpannerException deep inside MusicXMLTranslator.translate(), not
    # during the initial music21.converter.parse() call -- load_musicxml()
    # previously only wrapped the latter, so this reached the caller as an
    # unhandled traceback instead of a plain-text DottedNotesError.
    from dottednotes.exceptions import DottedNotesError

    xml = _measure_with_octave_shift(5, 'down').replace('size="8"', 'size="a"')
    with pytest.raises(DottedNotesError):
        load_musicxml(xml)


def test_load_musicxml_does_not_double_wrap_existing_dottednoteserror():
    # A DottedNotesError already raised inside translate() (e.g. an
    # unrecognized chord symbol kind) must reach the caller with its own
    # specific message intact, not re-wrapped inside a generic
    # "Could not import MusicXML: ..." message.
    from dottednotes.exceptions import DottedNotesError

    xml = """<?xml version="1.0" encoding="UTF-8"?>
<score-partwise version="3.1">
  <part-list><score-part id="P1"><part-name>Test</part-name></score-part></part-list>
  <part id="P1">
    <measure number="1">
      <attributes><divisions>1</divisions></attributes>
      <harmony><root><root-step>C</root-step></root><kind>power</kind></harmony>
      <note><pitch><step>C</step><octave>4</octave></pitch><duration>4</duration><type>whole</type></note>
    </measure>
  </part>
</score-partwise>
"""
    with pytest.raises(DottedNotesError, match="Unrecognized MusicXML chord kind"):
        load_musicxml(xml)


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


def test_musicxml_ottava_preserves_accidental_spelling():
    # Regression test for S10b-8: a flatted note under an 8va bracket must
    # keep its letter name and accidental (Ab5 -> Ab6), not get respelled
    # enharmonically (G#6). The bug was in shifting via
    # `Pitch.transpose(<semitones>)`, which builds a generic chromatic
    # interval and can pick a different spelling than the original;
    # shifting `Pitch.octave` directly (the fix) cannot. Found via a real
    # chord in a real Debussy "Mandoline" MusicXML sample (musicxml.com's
    # example set, measure 10), where an Ab5/C6/Ab6 chord under an 8va
    # bracket imported as G#7/C7/G#6 before this fix.
    xml = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 3.1 Partwise//EN" "http://www.musicxml.org/dtds/partwise.dtd">
<score-partwise version="3.1">
  <part-list><score-part id="P1"><part-name>Piano</part-name></score-part></part-list>
  <part id="P1">
    <measure number="1">
      <attributes><divisions>1</divisions><time><beats>4</beats><beat-type>4</beat-type></time><clef><sign>G</sign><line>2</line></clef></attributes>
      <direction placement="above"><direction-type><octave-shift type="down" size="8" number="1"/></direction-type></direction>
      <note><pitch><step>A</step><alter>-1</alter><octave>5</octave></pitch><duration>4</duration><type>whole</type><accidental>flat</accidental></note>
      <direction><direction-type><octave-shift type="stop" size="8" number="1"/></direction-type></direction>
    </measure>
  </part>
</score-partwise>
'''
    m21_score = music21.converter.parse(xml, format='musicxml')
    score = MusicXMLTranslator().translate(m21_score)
    note = score.staves[0].measures[0].notes[0]
    assert note.note_name == 'A'
    assert note.accidental.type == AccidentalType.FLAT
    assert note.octave == 6


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

def test_musicxml_volta_ending_numbers_import():
    m21_score = music21.stream.Score()
    part = music21.stream.Part()

    m1 = music21.stream.Measure(number=1)
    m1.append(music21.note.Note('C4', quarterLength=4))
    m2 = music21.stream.Measure(number=2)
    m2.append(music21.note.Note('D4', quarterLength=4))
    m3 = music21.stream.Measure(number=3)
    m3.append(music21.note.Note('E4', quarterLength=4))
    part.append(m1)
    part.append(m2)
    part.append(m3)

    rb1 = music21.spanner.RepeatBracket(m1, number='1')
    rb2 = music21.spanner.RepeatBracket(m2, number='2')
    part.insert(0, rb1)
    part.insert(0, rb2)
    m21_score.append(part)

    score = MusicXMLTranslator().translate(m21_score)
    measures = score.staves[0].measures
    assert measures[0].ending_numbers == [1]
    assert measures[1].ending_numbers == [2]
    assert measures[2].ending_numbers is None


def test_musicxml_combined_volta_ending_numbers_import():
    m21_score = music21.stream.Score()
    part = music21.stream.Part()

    m1 = music21.stream.Measure(number=1)
    m1.append(music21.note.Note('C4', quarterLength=4))
    part.append(m1)

    rb = music21.spanner.RepeatBracket(m1, number='1,2')
    part.insert(0, rb)
    m21_score.append(part)

    score = MusicXMLTranslator().translate(m21_score)
    assert score.staves[0].measures[0].ending_numbers == [1, 2]

def test_musicxml_forward_repeat_attaches_to_previous_measure():
    # music21/MusicXML mark a forward repeat on the FIRST measure of the
    # repeated section (leftBarline) -- but this codebase's tested
    # convention (braille_parser.py, test_forward_repeat_sets_bar_line_type)
    # attaches bar_line_type='forward_repeat' to the LAST measure BEFORE
    # the repeated section instead. Found and fixed while implementing
    # volta LilyPond output, which depends on correctly locating where a
    # repeated section starts.
    m21_score = music21.stream.Score()
    part = music21.stream.Part()
    m1 = music21.stream.Measure(number=1)
    m1.append(music21.note.Note('C4', quarterLength=4))
    m2 = music21.stream.Measure(number=2)
    m2.append(music21.note.Note('D4', quarterLength=4))
    m2.leftBarline = music21.bar.Repeat(direction='start')
    m3 = music21.stream.Measure(number=3)
    m3.append(music21.note.Note('E4', quarterLength=4))
    part.append(m1)
    part.append(m2)
    part.append(m3)
    m21_score.append(part)

    score = MusicXMLTranslator().translate(m21_score)
    measures = score.staves[0].measures
    assert measures[0].bar_line_type == 'forward_repeat'
    assert measures[1].bar_line_type == 'measure_separator'
    assert measures[2].bar_line_type == 'measure_separator'


def test_musicxml_forward_repeat_at_first_measure_has_no_preceding_marker():
    m21_score = music21.stream.Score()
    part = music21.stream.Part()
    m1 = music21.stream.Measure(number=1)
    m1.append(music21.note.Note('C4', quarterLength=4))
    m1.leftBarline = music21.bar.Repeat(direction='start')
    part.append(m1)
    m21_score.append(part)

    score = MusicXMLTranslator().translate(m21_score)
    # No preceding measure to attach the sign to -- shouldn't error, and
    # the (only) measure keeps its default bar_line_type.
    assert score.staves[0].measures[0].bar_line_type == 'measure_separator'


def test_repeat_bracket_numbers_uses_number_range_when_present():
    from dottednotes.parser.musicxml_parser import _repeat_bracket_numbers
    rb = music21.spanner.RepeatBracket(number='1,2')
    assert _repeat_bracket_numbers(rb) == [1, 2]


def test_repeat_bracket_numbers_falls_back_when_number_range_missing():
    # Some music21 versions don't have the `numberRange` attribute at all
    # (confirmed on CI: AttributeError even though pyproject.toml only
    # pins music21>=8.3.0 with no upper bound) -- _repeat_bracket_numbers()
    # must fall back to parsing `.number` directly rather than assuming
    # numberRange always exists.
    from dottednotes.parser.musicxml_parser import _repeat_bracket_numbers

    class FakeOldRepeatBracket:
        def __init__(self, number):
            self.number = number

    assert _repeat_bracket_numbers(FakeOldRepeatBracket('1')) == [1]
    assert _repeat_bracket_numbers(FakeOldRepeatBracket('1, 2')) == [1, 2]
    assert _repeat_bracket_numbers(FakeOldRepeatBracket('1-3')) == [1, 2, 3]
    assert _repeat_bracket_numbers(FakeOldRepeatBracket('1, 2, 3, 7')) == [1, 2, 3, 7]
