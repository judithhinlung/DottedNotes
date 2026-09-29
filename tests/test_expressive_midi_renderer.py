import tempfile
import pathlib
import pytest
import music21.midi as m21midi

from dottednotes.models import (
    Score, Staff, Measure, Note, Rest, Chord, Duration,
    Dynamic, DynamicLevel, Articulation, ArticulationType,
    TextMarking, TextMarkingType, InAccord,
)
from dottednotes.renderers.expressive_midi_renderer import (
    ExpressiveMidiRenderer,
    export_expressive_midi,
    DYNAMIC_TO_CC11,
    DYNAMIC_TO_BASE_VELOCITY,
)


def _collect_track_events(track: m21midi.MidiTrack):
    """Utility to walk events in a MidiTrack and return (tick, event)."""
    cur_tick = 0
    result = []
    for ev in track.events:
        if isinstance(ev, m21midi.DeltaTime):
            cur_tick += ev.time
        else:
            result.append((cur_tick, ev))
    return result


def test_cc11_baseline_dynamics():
    score = Score(title="Dynamic Baseline Test")
    staff = Staff(name="Piano")
    m = Measure(number=1, time_signature=(4, 4))

    for idx, (d_level, note_name) in enumerate([
        (DynamicLevel.P, 'C'),
        (DynamicLevel.MP, 'D'),
        (DynamicLevel.MF, 'E'),
        (DynamicLevel.F, 'F'),
    ]):
        n = Note(dots=frozenset(), category=None, raw_brl="", note_name=note_name, octave=4, duration=Duration(value=4))
        n.dynamics.append(Dynamic(level=d_level))
        m.add_note(n)

    staff.add_measure(m)
    score.add_staff(staff)

    renderer = ExpressiveMidiRenderer()
    mf = renderer.render(score)
    events = _collect_track_events(mf.tracks[1])

    # Extract all CC11 events
    cc11_events = [(t, ev.parameter2) for t, ev in events if ev.type == m21midi.ChannelVoiceMessages.CONTROLLER_CHANGE and ev.parameter1 == 11]
    cc11_map = dict(cc11_events)

    assert cc11_map[0] == DYNAMIC_TO_CC11[DynamicLevel.P]      # 52
    assert cc11_map[480] == DYNAMIC_TO_CC11[DynamicLevel.MP]   # 68
    assert cc11_map[960] == DYNAMIC_TO_CC11[DynamicLevel.MF]   # 84
    assert cc11_map[1440] == DYNAMIC_TO_CC11[DynamicLevel.F]   # 100


def test_hairpin_crescendo_and_decrescendo_interpolation():
    score = Score(title="Hairpin Test")
    staff = Staff(name="Violin")
    m = Measure(number=1, time_signature=(4, 4))

    # Note 1: p with crescendo start
    n1 = Note(dots=frozenset(), category=None, raw_brl="", note_name='C', octave=4, duration=Duration(value=4))
    n1.dynamics.append(Dynamic(level=DynamicLevel.P))
    n1.dynamics.append(Dynamic(level=DynamicLevel.CRESCENDO_START))

    # Note 2, 3: intermediate notes
    n2 = Note(dots=frozenset(), category=None, raw_brl="", note_name='D', octave=4, duration=Duration(value=4))
    n3 = Note(dots=frozenset(), category=None, raw_brl="", note_name='E', octave=4, duration=Duration(value=4))

    # Note 4: f with crescendo end
    n4 = Note(dots=frozenset(), category=None, raw_brl="", note_name='F', octave=4, duration=Duration(value=4))
    n4.dynamics.append(Dynamic(level=DynamicLevel.F))
    n4.dynamics.append(Dynamic(level=DynamicLevel.CRESCENDO_END))

    m.notes = [n1, n2, n3, n4]
    staff.measures = [m]
    score.staves = [staff]

    renderer = ExpressiveMidiRenderer()
    mf = renderer.render(score)
    events = _collect_track_events(mf.tracks[1])

    cc11_events = [(t, ev.parameter2) for t, ev in events if ev.type == m21midi.ChannelVoiceMessages.CONTROLLER_CHANGE and ev.parameter1 == 11]

    # Verify start and end of crescendo
    assert cc11_events[0][1] == DYNAMIC_TO_CC11[DynamicLevel.P]    # 52
    last_cresc = [val for t, val in cc11_events if t == 1440]
    assert 100 in last_cresc

    # Verify interpolation is monotonically increasing
    cresc_values = [val for t, val in cc11_events if 0 <= t <= 1440]
    assert len(cresc_values) > 10
    for i in range(len(cresc_values) - 1):
        assert cresc_values[i] <= cresc_values[i + 1]


def test_velocity_articulation_scaling():
    score = Score(title="Velocity Articulation Test")
    staff = Staff(name="Trumpet")
    m = Measure(number=1, time_signature=(4, 4))

    # Note 1: plain mf (84)
    n1 = Note(dots=frozenset(), category=None, raw_brl="", note_name='C', octave=4, duration=Duration(value=4))
    n1.dynamics.append(Dynamic(level=DynamicLevel.MF))

    # Note 2: accent (+18 -> 102)
    n2 = Note(dots=frozenset(), category=None, raw_brl="", note_name='D', octave=4, duration=Duration(value=4))
    n2.articulations.append(Articulation(type=ArticulationType.ACCENT))

    # Note 3: expressive accent / marcato (+28 -> 112)
    n3 = Note(dots=frozenset(), category=None, raw_brl="", note_name='E', octave=4, duration=Duration(value=4))
    n3.articulations.append(Articulation(type=ArticulationType.EXPRESSIVE_ACCENT))

    # Note 4: sfz (120)
    n4 = Note(dots=frozenset(), category=None, raw_brl="", note_name='F', octave=4, duration=Duration(value=4))
    n4.dynamics.append(Dynamic(level=DynamicLevel.SFZ))

    m.notes = [n1, n2, n3, n4]
    staff.measures = [m]
    score.staves = [staff]

    renderer = ExpressiveMidiRenderer()
    mf = renderer.render(score)
    events = _collect_track_events(mf.tracks[1])

    note_on_vels = [ev.velocity for t, ev in events if ev.type == m21midi.ChannelVoiceMessages.NOTE_ON]
    assert note_on_vels[0] == 84   # Base mf
    assert note_on_vels[1] == 102  # Accent (+18)
    assert note_on_vels[2] == 112  # Marcato (+28)
    assert note_on_vels[3] == 120  # SFZ (120)


def test_gate_duration_scaling():
    score = Score(title="Gate Duration Test")
    staff = Staff(name="Clarinet")
    m = Measure(number=1, time_signature=(4, 4))

    # Note 1: Staccato (50% of 480 = 240 ticks)
    n1 = Note(dots=frozenset(), category=None, raw_brl="", note_name='C', octave=4, duration=Duration(value=4))
    n1.articulations.append(Articulation(type=ArticulationType.STACCATO))

    # Note 2: Tenuto (102% of 480 = 489 ticks)
    n2 = Note(dots=frozenset(), category=None, raw_brl="", note_name='D', octave=4, duration=Duration(value=4))
    n2.articulations.append(Articulation(type=ArticulationType.TENUTO))

    # Note 3: Default unslurred (90% of 480 = 432 ticks)
    n3 = Note(dots=frozenset(), category=None, raw_brl="", note_name='E', octave=4, duration=Duration(value=4))

    # Note 4: Inside slur (100% of 480 = 480 ticks)
    n4 = Note(dots=frozenset(), category=None, raw_brl="", note_name='F', octave=4, duration=Duration(value=4))
    n4.slur_start = True
    n4.slur_end = True

    m.notes = [n1, n2, n3, n4]
    staff.measures = [m]
    score.staves = [staff]

    renderer = ExpressiveMidiRenderer()
    mf = renderer.render(score)
    events = _collect_track_events(mf.tracks[1])

    note_offs = [t for t, ev in events if ev.type == m21midi.ChannelVoiceMessages.NOTE_OFF]
    assert note_offs[0] == 240        # 0 + 240 (50% staccato)
    assert note_offs[1] == 480 + int(round(480 * 1.02))  # 480 + 489 (102% tenuto)
    assert note_offs[2] == 960 + 432  # 960 + 432 (90% default)
    assert note_offs[3] == 1440 + 480 # 1440 + 480 (100% slur)


def test_tied_notes_duration():
    score = Score(title="Tie Test")
    staff = Staff(name="Cello")
    m = Measure(number=1, time_signature=(4, 4))

    # C4 tied to C4 across two quarter notes
    n1 = Note(dots=frozenset(), category=None, raw_brl="", note_name='C', octave=4, duration=Duration(value=4))
    n1.tie = True

    n2 = Note(dots=frozenset(), category=None, raw_brl="", note_name='C', octave=4, duration=Duration(value=4))
    n2.tie = False

    m.notes = [n1, n2]
    staff.measures = [m]
    score.staves = [staff]

    renderer = ExpressiveMidiRenderer()
    mf = renderer.render(score)
    events = _collect_track_events(mf.tracks[1])

    note_ons = [(t, ev.pitch) for t, ev in events if ev.type == m21midi.ChannelVoiceMessages.NOTE_ON]
    note_offs = [(t, ev.pitch) for t, ev in events if ev.type == m21midi.ChannelVoiceMessages.NOTE_OFF]

    # Only 1 NOTE_ON at tick 0
    assert len(note_ons) == 1
    assert note_ons[0][0] == 0

    # Only 1 NOTE_OFF at end of second note (480 + 432 = 912)
    assert len(note_offs) == 1
    assert note_offs[0][0] == 480 + int(480 * 0.90)


def test_chords_render_all_notes():
    score = Score(title="Chord Test")
    staff = Staff(name="Piano")
    m = Measure(number=1, time_signature=(4, 4))

    # C-major triad (C4, E4, G4)
    dur = Duration(value=4)
    c1 = Note(dots=frozenset(), category=None, raw_brl="", note_name='C', octave=4, duration=dur)
    c2 = Note(dots=frozenset(), category=None, raw_brl="", note_name='E', octave=4, duration=dur)
    c3 = Note(dots=frozenset(), category=None, raw_brl="", note_name='G', octave=4, duration=dur)
    chord = Chord(notes=[c1, c2, c3])
    m.add_note(chord)

    staff.add_measure(m)
    score.add_staff(staff)

    renderer = ExpressiveMidiRenderer()
    mf = renderer.render(score)
    events = _collect_track_events(mf.tracks[1])

    note_ons = [(t, ev.pitch) for t, ev in events if ev.type == m21midi.ChannelVoiceMessages.NOTE_ON]
    assert len(note_ons) == 3
    pitches = sorted([p for t, p in note_ons])
    assert pitches == [60, 64, 67]
    assert all(t == 0 for t, p in note_ons)


def test_multitrack_channel_and_programs():
    score = Score(title="Ensemble Test")
    flute_staff = Staff(name="Flute")
    violin_staff = Staff(name="Violin")
    snare_staff = Staff(name="Snare drum")

    m_f = Measure(number=1, time_signature=(4, 4))
    m_f.add_note(Note(dots=frozenset(), category=None, raw_brl="", note_name='G', octave=5, duration=Duration(value=1)))
    flute_staff.add_measure(m_f)

    m_v = Measure(number=1, time_signature=(4, 4))
    m_v.add_note(Note(dots=frozenset(), category=None, raw_brl="", note_name='E', octave=4, duration=Duration(value=1)))
    violin_staff.add_measure(m_v)

    m_s = Measure(number=1, time_signature=(4, 4))
    m_s.add_note(Note(dots=frozenset(), category=None, raw_brl="", note_name='C', octave=4, duration=Duration(value=1)))
    snare_staff.add_measure(m_s)

    score.staves = [flute_staff, violin_staff, snare_staff]

    renderer = ExpressiveMidiRenderer()
    mf = renderer.render(score)

    assert len(mf.tracks) == 4  # Conductor + 3 staves

    # Track 1: Flute -> channel 1, program 73
    flute_events = _collect_track_events(mf.tracks[1])
    pc_flute = [ev for t, ev in flute_events if ev.type == m21midi.ChannelVoiceMessages.PROGRAM_CHANGE]
    assert pc_flute[0].channel == 1
    assert pc_flute[0].data == 73  # GM Flute

    # Track 2: Violin -> channel 2, program 40
    violin_events = _collect_track_events(mf.tracks[2])
    pc_violin = [ev for t, ev in violin_events if ev.type == m21midi.ChannelVoiceMessages.PROGRAM_CHANGE]
    assert pc_violin[0].channel == 2
    assert pc_violin[0].data == 40  # GM Violin

    # Track 3: Snare Drum -> percussion channel 10
    snare_events = _collect_track_events(mf.tracks[3])
    snare_notes = [ev for t, ev in snare_events if ev.type == m21midi.ChannelVoiceMessages.NOTE_ON]
    assert snare_notes[0].channel == 10
    assert snare_notes[0].pitch == 38  # GM Snare Drum


def test_conductor_track_tempo_time_and_key_signatures():
    score = Score(title="Symphony No. 5")
    staff = Staff(name="Horn")
    m = Measure(number=1, time_signature=(3, 4), key_signature=3)
    m.text_markings.append(TextMarking(text="Allegro (132 BPM)", type=TextMarkingType.TEMPO))
    m.add_note(Note(dots=frozenset(), category=None, raw_brl="", note_name='C', octave=4, duration=Duration(value=2, dots=1)))
    staff.add_measure(m)
    score.add_staff(staff)

    renderer = ExpressiveMidiRenderer()
    mf = renderer.render(score)
    cond_events = _collect_track_events(mf.tracks[0])

    meta_types = [ev.type for t, ev in cond_events]
    assert m21midi.MetaEvents.SEQUENCE_TRACK_NAME in meta_types
    assert m21midi.MetaEvents.TIME_SIGNATURE in meta_types
    assert m21midi.MetaEvents.KEY_SIGNATURE in meta_types
    assert m21midi.MetaEvents.SET_TEMPO in meta_types


def test_export_expressive_midi_file(tmp_path):
    score = Score(title="Export File Test")
    staff = Staff(name="Oboe")
    m = Measure(number=1, time_signature=(4, 4))
    m.add_note(Note(dots=frozenset(), category=None, raw_brl="", note_name='A', octave=4, duration=Duration(value=4)))
    staff.add_measure(m)
    score.add_staff(staff)

    out_file = tmp_path / "test_piece_expressive.mid"
    export_expressive_midi(score, str(out_file))

    assert out_file.exists()
    assert out_file.stat().st_size > 0

    # Verify standard MIDI file header
    with open(out_file, 'rb') as f:
        header = f.read(4)
        assert header == b'MThd'


def test_key_signature_applies_accidentals_to_pitch():
    # A major (3 sharps): an unmarked "F" note must sound as F#4 (66), not
    # be forced to a fixed accidental-free pitch by a broken key-signature
    # lookup.
    score = Score(title="Key Signature Pitch Test")
    staff = Staff(name="Violin")
    m = Measure(number=1, time_signature=(4, 4), key_signature=3)
    m.add_note(Note(dots=frozenset(), category=None, raw_brl="", note_name='F', octave=4, duration=Duration(value=4)))
    staff.add_measure(m)
    score.add_staff(staff)

    renderer = ExpressiveMidiRenderer()
    mf = renderer.render(score)
    events = _collect_track_events(mf.tracks[1])

    note_ons = [ev.pitch for t, ev in events if ev.type == m21midi.ChannelVoiceMessages.NOTE_ON]
    assert note_ons == [66]  # F#4


def test_in_accord_renders_every_voice():
    score = Score(title="InAccord Voices Test")
    staff = Staff(name="Piano")
    m = Measure(number=1, time_signature=(4, 4))

    top_voice = [Note(dots=frozenset(), category=None, raw_brl="", note_name='C', octave=5, duration=Duration(value=1))]
    bottom_voice = [Note(dots=frozenset(), category=None, raw_brl="", note_name='C', octave=3, duration=Duration(value=1))]
    m.notes = [InAccord(parts=[top_voice, bottom_voice])]
    staff.measures = [m]
    score.staves = [staff]

    renderer = ExpressiveMidiRenderer()
    mf = renderer.render(score)
    events = _collect_track_events(mf.tracks[1])

    note_ons = [(t, ev.pitch) for t, ev in events if ev.type == m21midi.ChannelVoiceMessages.NOTE_ON]
    assert sorted(note_ons) == [(0, 48), (0, 72)]  # both voices sound, simultaneously


@pytest.mark.parametrize("staff_name,expected_pitch", [
    ("Snare drum", 38),
    ("Bass drum", 35),
    ("Triangle", 81),
    ("Hi-hat", 44),
    ("Cymbals", 49),
])
def test_percussion_base_names_map_to_correct_gm_pitch(staff_name, expected_pitch):
    score = Score(title="Percussion Base Name Test")
    staff = Staff(name=staff_name)
    m = Measure(number=1, time_signature=(4, 4))
    m.add_note(Note(dots=frozenset(), category=None, raw_brl="", note_name='C', octave=4, duration=Duration(value=4)))
    staff.add_measure(m)
    score.add_staff(staff)

    renderer = ExpressiveMidiRenderer()
    mf = renderer.render(score)
    events = _collect_track_events(mf.tracks[1])

    note_ons = [ev.pitch for t, ev in events if ev.type == m21midi.ChannelVoiceMessages.NOTE_ON]
    assert note_ons == [expected_pitch]
