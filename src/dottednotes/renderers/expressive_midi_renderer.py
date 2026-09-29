from __future__ import annotations

import math
import os
import re
from dataclasses import dataclass, field
from typing import Optional, Any

import music21.midi as m21midi

from dottednotes.models import (
    Score, Staff, Measure, Note, Rest, Chord, Duration,
    Accidental, AccidentalType, Dynamic, DynamicLevel,
    Articulation, ArticulationType, Ornament, OrnamentType,
    KeySignature, TimeSignature, TextMarking, TextMarkingType,
    InAccord, Tuplet,
)
from dottednotes.models.instrument import (
    get_midi_instrument_name,
    get_midi_program_number,
    is_unpitched_percussion,
    canonical_percussion_name,
)

# Standard DAW PPQ (ticks per quarter note)
MIDI_PPQ = 480

# DottedNotes internal TICKS_PER_QUARTER = 24. Scale factor to MIDI ticks:
TICKS_TO_MIDI = MIDI_PPQ // 24  # 20

# ---------------------------------------------------------------------------
# Universal Controller Mapping & Rule-Based Performance Baselines
# ---------------------------------------------------------------------------

DYNAMIC_TO_CC11: dict[DynamicLevel, int] = {
    DynamicLevel.PPP: 24,
    DynamicLevel.PP: 38,
    DynamicLevel.P: 52,
    DynamicLevel.MP: 68,
    DynamicLevel.MF: 84,
    DynamicLevel.F: 100,
    DynamicLevel.FF: 114,
    DynamicLevel.FFF: 127,
    DynamicLevel.SF: 112,
    DynamicLevel.SFZ: 112,
    DynamicLevel.FP: 104,
}

DYNAMIC_TO_BASE_VELOCITY: dict[DynamicLevel, int] = {
    DynamicLevel.PPP: 30,
    DynamicLevel.PP: 44,
    DynamicLevel.P: 58,
    DynamicLevel.MP: 72,
    DynamicLevel.MF: 84,
    DynamicLevel.F: 98,
    DynamicLevel.FF: 112,
    DynamicLevel.FFF: 126,
    DynamicLevel.SF: 120,
    DynamicLevel.SFZ: 120,
    DynamicLevel.FP: 104,
}

DEFAULT_CC11 = 84
DEFAULT_VELOCITY = 84

# General MIDI Percussion Key Map overrides (Channel 10). Covers every name
# in models/instrument.py's canonical unpitched-percussion set, including
# the plain/base names ('Snare drum', 'Bass drum', 'Triangle', 'Hi-hat',
# 'Cymbals') that renderers/musicxml_renderer.py's own copy of this table
# leaves out because it gets them for free from music21's instrument-class
# constructor defaults -- this module has no such fallback, so they must be
# listed explicitly or they'd fall through to the generic snare default below.
_PERC_MAP_PITCH_OVERRIDES: dict[str, int] = {
    'Snare drum': 38,
    'Bass drum': 35,
    'Triangle': 81,
    'Hi-hat': 44,
    'Cymbals': 49,
    'Ride cymbal': 51,
    'Mounted tom': 50,
    'Acoustic bass drum': 35,
    'Acoustic snare drum': 38,
    'Electric snare drum': 40,
    'Low floor tom': 41,
    'High floor tom': 43,
    'Low tom': 45,
    'High tom': 50,
    'Low-mid tom': 47,
    'High-mid tom': 48,
    'Closed hi-hat': 42,
    'Open hi-hat': 46,
    'Half-open hi-hat': 46,
    'Pedal hi-hat': 44,
    'Crash cymbal': 49,
    'Crash cymbal 1': 49,
    'Crash cymbal 2': 57,
    'Ride cymbal 1': 51,
    'Ride cymbal 2': 59,
    'Chinese cymbal': 52,
    'Splash cymbal': 55,
    'Ride bell': 53,
    'Cowbell': 56,
    'High bongo': 60,
    'Open high bongo': 60,
    'Muted high bongo': 60,
    'Low bongo': 61,
    'Open low bongo': 61,
    'Muted low bongo': 61,
    'High conga': 62,
    'Open high conga': 63,
    'Muted high conga': 62,
    'Low conga': 64,
    'Open low conga': 64,
    'Muted low conga': 64,
    'High timbale': 65,
    'Low timbale': 66,
    'High agogo': 67,
    'Low agogo': 68,
    'Guiro': 73,
    'Short guiro': 73,
    'Long guiro': 74,
    'Cabasa': 69,
    'Maracas': 70,
    'Claves': 75,
    'Open cuica': 79,
    'Muted cuica': 78,
    'Side stick': 37,
    'High side stick': 37,
    'Low side stick': 37,
    'Short whistle': 71,
    'Long whistle': 72,
    'Hand clap': 39,
    'Tambourine': 54,
    'Vibraslap': 58,
    'Tam-tam': 49,
    'High wood block': 76,
    'Low wood block': 77,
    'Open triangle': 81,
    'Muted triangle': 80,
}


def parse_tempo_bpm(text: str) -> int:
    """Extract or infer integer BPM from a tempo marking string."""
    digits = re.findall(r'\d+', text)
    if digits:
        val = int(digits[0])
        if 20 <= val <= 300:
            return val
    lower = text.lower()
    word_map = {
        'largo': 50,
        'adagio': 65,
        'andante': 88,
        'moderato': 108,
        'allegretto': 116,
        'allegro': 132,
        'vivace': 144,
        'presto': 168,
        'prestissimo': 200,
    }
    for word, bpm in word_map.items():
        if word in lower:
            return bpm
    return 120


@dataclass
class _TimedItem:
    item: Any  # Note, Chord, or Rest
    start_tick: int
    duration_ticks: int
    measure_number: int
    is_rest: bool = False
    pitches: list[int] = field(default_factory=list)
    dynamics: list[Dynamic] = field(default_factory=list)
    articulations: list[Articulation] = field(default_factory=list)
    slur_start: bool = False
    slur_end: bool = False
    tie: bool = False


@dataclass
class _HairpinSegment:
    start_tick: int
    end_tick: int
    start_val: int
    end_val: int
    is_crescendo: bool


class ExpressiveMidiRenderer:
    """Renders a DottedNotes Score model into a Standard MIDI File (Type 1)
    with rule-based expressive performance data:
    - CC11 (Expression) dynamic volume curves and hairpin interpolation
    - Velocity baseline scaling and articulation accents
    - Gate / duration scaling (50% staccato, 102% tenuto, 90% unslurred, 100% legato)
    - General MIDI instrument mapping with standard channel allocation
    """

    def render(self, score: Score) -> m21midi.MidiFile:
        mf = m21midi.MidiFile()
        mf.ticksPerQuarterNote = MIDI_PPQ

        tracks: list[m21midi.MidiTrack] = []

        # Track 0: Conductor Track (Tempo, Time Signature, Key Signature)
        conductor_track = self._render_conductor_track(score)
        tracks.append(conductor_track)

        # Tracks 1..N: Instrument Staves
        channel_index = 0
        for staff_idx, staff in enumerate(score.staves):
            is_perc = is_unpitched_percussion(staff.name)
            if is_perc:
                channel = 10
            else:
                # Cycle channels 1..16, skipping 10
                channel = (channel_index % 15) + 1
                if channel >= 10:
                    channel += 1
                channel_index += 1

            staff_track = self._render_staff_track(staff, staff_idx + 1, channel)
            tracks.append(staff_track)

        mf.tracks = tracks
        return mf

    def _render_conductor_track(self, score: Score) -> m21midi.MidiTrack:
        tr = m21midi.MidiTrack(0)
        events: list[tuple[int, int, m21midi.MidiEvent]] = []

        # Sequence / Track Name
        ev_name = m21midi.MidiEvent(tr)
        ev_name.type = m21midi.MetaEvents.SEQUENCE_TRACK_NAME
        title_text = score.title or "Conductor"
        ev_name.data = title_text.encode('utf-8', errors='replace')
        events.append((0, 0, ev_name))

        # Initial default tempo: 120 BPM
        current_bpm = 120
        init_tempo = m21midi.MidiEvent(tr)
        init_tempo.type = m21midi.MetaEvents.SET_TEMPO
        init_tempo.data = m21midi.putNumber(int(round(60_000_000 / current_bpm)), 3)
        events.append((0, 1, init_tempo))

        # Traverse measures to collect Time Signatures, Key Signatures, and Tempos
        ref_staff = score.staves[0] if score.staves else None
        if ref_staff:
            current_tick = 0
            active_ts: Optional[tuple[int, int]] = None
            active_ks: Optional[int] = None

            for m in ref_staff.measures:
                m_ts = m.time_signature
                m_ql = m_ts[0] * 4.0 / m_ts[1]
                m_ticks = int(round(m_ql * MIDI_PPQ))

                # Time Signature event
                if m_ts != active_ts:
                    ev_ts = m21midi.MidiEvent(tr)
                    ev_ts.type = m21midi.MetaEvents.TIME_SIGNATURE
                    num, den = m_ts
                    den_pow = int(math.log2(den)) if den > 0 and (den & (den - 1) == 0) else 2
                    ev_ts.data = bytes([num, den_pow, 24, 8])
                    events.append((current_tick, 2, ev_ts))
                    active_ts = m_ts

                # Key Signature event
                if m.key_signature != active_ks and m.key_signature is not None:
                    ev_ks = m21midi.MidiEvent(tr)
                    ev_ks.type = m21midi.MetaEvents.KEY_SIGNATURE
                    sf = m.key_signature & 0xff
                    mi = 1 if m.key_signature_mode == "minor" else 0
                    ev_ks.data = bytes([sf, mi])
                    events.append((current_tick, 3, ev_ks))
                    active_ks = m.key_signature

                # Tempo Markings
                for tm in m.text_markings:
                    if tm.type == TextMarkingType.TEMPO:
                        new_bpm = parse_tempo_bpm(tm.text)
                        if new_bpm != current_bpm:
                            ev_t = m21midi.MidiEvent(tr)
                            ev_t.type = m21midi.MetaEvents.SET_TEMPO
                            ev_t.data = m21midi.putNumber(int(round(60_000_000 / new_bpm)), 3)
                            events.append((current_tick, 4, ev_t))
                            current_bpm = new_bpm

                current_tick += m_ticks

        self._pack_events(tr, events)
        return tr

    def _render_staff_track(self, staff: Staff, track_idx: int, channel: int) -> m21midi.MidiTrack:
        tr = m21midi.MidiTrack(track_idx)
        events: list[tuple[int, int, m21midi.MidiEvent]] = []

        # Track Name
        ev_name = m21midi.MidiEvent(tr)
        ev_name.type = m21midi.MetaEvents.SEQUENCE_TRACK_NAME
        ev_name.data = staff.name.encode('utf-8', errors='replace')
        events.append((0, 0, ev_name))

        # Program Change
        is_perc = is_unpitched_percussion(staff.name)
        if not is_perc:
            midi_inst_name = staff.midi_instrument or get_midi_instrument_name(staff.name)
            program_num = get_midi_program_number(midi_inst_name) if midi_inst_name else 0
            if program_num is None:
                program_num = 0
            ev_pc = m21midi.MidiEvent(tr)
            ev_pc.type = m21midi.ChannelVoiceMessages.PROGRAM_CHANGE
            ev_pc.channel = channel
            ev_pc.data = program_num
            events.append((0, 1, ev_pc))

        # Collect timed items across measures
        timed_items = self._collect_timed_items(staff, is_perc)

        # Build dynamic timeline and hairpin segments
        hairpin_segments, note_dynamics = self._build_dynamic_timeline(timed_items)

        # Initial CC11 (Expression) controller event
        initial_cc11 = DEFAULT_CC11
        if timed_items:
            first_dyn = note_dynamics.get(0)
            if first_dyn in DYNAMIC_TO_CC11:
                initial_cc11 = DYNAMIC_TO_CC11[first_dyn]

        ev_init_cc = m21midi.MidiEvent(tr)
        ev_init_cc.type = m21midi.ChannelVoiceMessages.CONTROLLER_CHANGE
        ev_init_cc.channel = channel
        ev_init_cc.parameter1 = 11
        ev_init_cc.parameter2 = initial_cc11
        events.append((0, 2, ev_init_cc))

        # Emit CC11 curves for hairpins
        interpolated_ticks: set[int] = set()
        for hp in hairpin_segments:
            duration = hp.end_tick - hp.start_tick
            if duration <= 0:
                continue
            step = 40  # Sample every 40 ticks (~1/48th note)
            num_steps = max(1, duration // step)
            for s in range(num_steps + 1):
                t = min(hp.end_tick, hp.start_tick + s * step)
                if t in interpolated_ticks:
                    continue
                interpolated_ticks.add(t)
                frac = (t - hp.start_tick) / duration
                val = int(round(hp.start_val + frac * (hp.end_val - hp.start_val)))
                val = max(0, min(127, val))

                ev_cc = m21midi.MidiEvent(tr)
                ev_cc.type = m21midi.ChannelVoiceMessages.CONTROLLER_CHANGE
                ev_cc.channel = channel
                ev_cc.parameter1 = 11
                ev_cc.parameter2 = val
                events.append((t, 3, ev_cc))

        # Emit Note On / Note Off events with velocity & duration gate scaling
        active_slur = False
        sustaining_ties: dict[int, int] = {}  # pitch -> note_on tick

        for idx, item in enumerate(timed_items):
            if item.is_rest:
                continue

            # Slur tracking
            if item.slur_start:
                active_slur = True

            # Determine dynamic level & base velocity
            dyn_level = note_dynamics.get(idx, DynamicLevel.MF)
            base_vel = DYNAMIC_TO_BASE_VELOCITY.get(dyn_level, DEFAULT_VELOCITY)

            # Articulation velocity modifiers
            vel = base_vel
            art_types = {a.type for a in item.articulations}
            if ArticulationType.EXPRESSIVE_ACCENT in art_types:
                vel = min(127, base_vel + 28)
            elif ArticulationType.ACCENT in art_types:
                vel = min(127, base_vel + 18)
            elif ArticulationType.STACCATISSIMO in art_types:
                vel = min(127, base_vel + 8)
            elif ArticulationType.TENUTO in art_types:
                vel = min(127, base_vel + 4)

            # Sforzando / Forte-Piano checks
            for d in item.dynamics:
                if d.level in (DynamicLevel.SF, DynamicLevel.SFZ):
                    vel = 120
                elif d.level == DynamicLevel.FP:
                    vel = 104

            # Articulation gate / duration scaling
            dur = item.duration_ticks
            if ArticulationType.STACCATO in art_types:
                gate = max(20, int(round(dur * 0.50)))
            elif ArticulationType.STACCATISSIMO in art_types:
                gate = max(20, int(round(dur * 0.30)))
            elif ArticulationType.MEZZO_STACCATO in art_types:
                gate = max(20, int(round(dur * 0.75)))
            elif ArticulationType.TENUTO in art_types:
                gate = int(round(dur * 1.02))
            elif active_slur:
                gate = dur
            else:
                # Default unslurred natural detachment
                gate = max(20, int(round(dur * 0.90)))

            # Static dynamic change: emit discrete CC11 if not inside an active hairpin
            if item.dynamics:
                for d in item.dynamics:
                    if d.level in DYNAMIC_TO_CC11 and item.start_tick not in interpolated_ticks:
                        ev_dyn_cc = m21midi.MidiEvent(tr)
                        ev_dyn_cc.type = m21midi.ChannelVoiceMessages.CONTROLLER_CHANGE
                        ev_dyn_cc.channel = channel
                        ev_dyn_cc.parameter1 = 11
                        ev_dyn_cc.parameter2 = DYNAMIC_TO_CC11[d.level]
                        events.append((item.start_tick, 3, ev_dyn_cc))

            # Emit Note On / Off for each pitch
            for p in item.pitches:
                if p in sustaining_ties:
                    # Pitch is tied from a previous note: don't re-strike NOTE_ON
                    if not item.tie:
                        # Tie ends here: emit NOTE_OFF
                        ev_off = m21midi.MidiEvent(tr)
                        ev_off.type = m21midi.ChannelVoiceMessages.NOTE_OFF
                        ev_off.channel = channel
                        ev_off.pitch = p
                        ev_off.velocity = 0
                        events.append((item.start_tick + gate, 4, ev_off))
                        del sustaining_ties[p]
                else:
                    # New Note On
                    ev_on = m21midi.MidiEvent(tr)
                    ev_on.type = m21midi.ChannelVoiceMessages.NOTE_ON
                    ev_on.channel = channel
                    ev_on.pitch = p
                    ev_on.velocity = vel
                    events.append((item.start_tick, 5, ev_on))

                    if item.tie:
                        sustaining_ties[p] = item.start_tick
                    else:
                        ev_off = m21midi.MidiEvent(tr)
                        ev_off.type = m21midi.ChannelVoiceMessages.NOTE_OFF
                        ev_off.channel = channel
                        ev_off.pitch = p
                        ev_off.velocity = 0
                        events.append((item.start_tick + gate, 4, ev_off))

            if item.slur_end:
                active_slur = False

        self._pack_events(tr, events)
        return tr

    def _collect_timed_items(self, staff: Staff, is_perc: bool) -> list[_TimedItem]:
        timed_items: list[_TimedItem] = []
        current_tick = 0

        for m in staff.measures:
            m_ts = m.time_signature
            m_ql = m_ts[0] * 4.0 / m_ts[1]
            m_ticks = int(round(m_ql * MIDI_PPQ))

            # Note._midi_pitch()/_effective_accidental_type() need a real
            # KeySignature object (to call .accidental_by_step() on) --
            # Measure.key_signature is just the plain sharps/flats int, so
            # it must be wrapped the same way Measure.to_lilypond() does
            # before it can be handed to a Note.
            key_sig_obj = KeySignature(
                dots=frozenset(), category=None, raw_brl="",
                sharps_or_flats=m.key_signature,
            )

            has_in_accord = any(isinstance(x, InAccord) for x in m.notes)
            if has_in_accord:
                in_accord = next(x for x in m.notes if isinstance(x, InAccord))
                # Every voice in an in-accord starts together (BANA Ch. 11 --
                # mirrors InAccord.to_relative_lilypond's simultaneous
                # `<< {voice1} \\ {voice2} >>` rendering), so each part gets
                # its own m_offset run starting back at the measure start.
                for part_list in in_accord.parts:
                    m_offset = 0
                    for item in part_list:
                        dur_ticks = self._get_item_duration_ticks(item, m_ticks)
                        ti = self._make_timed_item(item, current_tick + m_offset, dur_ticks, m.number, key_sig_obj, is_perc, staff.name)
                        if ti:
                            timed_items.append(ti)
                        m_offset += dur_ticks
            else:
                m_offset = 0
                for item in m.notes:
                    if isinstance(item, Tuplet):
                        for sub_item in item.items:
                            dur_ticks = self._get_item_duration_ticks(sub_item, m_ticks)
                            ti = self._make_timed_item(sub_item, current_tick + m_offset, dur_ticks, m.number, key_sig_obj, is_perc, staff.name)
                            if ti:
                                timed_items.append(ti)
                            m_offset += dur_ticks
                    else:
                        dur_ticks = self._get_item_duration_ticks(item, m_ticks)
                        ti = self._make_timed_item(item, current_tick + m_offset, dur_ticks, m.number, key_sig_obj, is_perc, staff.name)
                        if ti:
                            timed_items.append(ti)
                        m_offset += dur_ticks

            current_tick += m_ticks

        return timed_items

    def _get_item_duration_ticks(self, item: Any, measure_ticks: int) -> int:
        if isinstance(item, Rest) and item.is_full_measure:
            return measure_ticks
        if hasattr(item, 'duration') and item.duration is not None:
            return item.duration.duration_in_ticks() * TICKS_TO_MIDI
        return 0

    def _make_timed_item(
        self, item: Any, start_tick: int, duration_ticks: int,
        measure_number: int, key_sig: Optional[KeySignature], is_perc: bool, staff_name: str
    ) -> Optional[_TimedItem]:
        if isinstance(item, Rest):
            return _TimedItem(
                item=item,
                start_tick=start_tick,
                duration_ticks=duration_ticks,
                measure_number=measure_number,
                is_rest=True,
            )
        elif isinstance(item, Note):
            pitch = self._resolve_note_pitch(item, key_sig, is_perc, staff_name)
            return _TimedItem(
                item=item,
                start_tick=start_tick,
                duration_ticks=duration_ticks,
                measure_number=measure_number,
                is_rest=False,
                pitches=[pitch],
                dynamics=list(item.dynamics),
                articulations=list(item.articulations),
                slur_start=item.slur_start or item.slur_bracket_open,
                slur_end=item.slur_end or item.slur_bracket_close,
                tie=item.tie,
            )
        elif isinstance(item, Chord):
            pitches = [self._resolve_note_pitch(n, key_sig, is_perc, staff_name) for n in item.notes]
            written_note = item.notes[0] if item.notes else None
            dynamics = list(written_note.dynamics) if written_note else []
            articulations = list(written_note.articulations) if written_note else []
            slur_start = (written_note.slur_start or written_note.slur_bracket_open) if written_note else False
            slur_end = (written_note.slur_end or written_note.slur_bracket_close) if written_note else False
            tie = written_note.tie if written_note else False
            return _TimedItem(
                item=item,
                start_tick=start_tick,
                duration_ticks=duration_ticks,
                measure_number=measure_number,
                is_rest=False,
                pitches=pitches,
                dynamics=dynamics,
                articulations=articulations,
                slur_start=slur_start,
                slur_end=slur_end,
                tie=tie,
            )
        return None

    def _resolve_note_pitch(self, note: Note, key_sig: Optional[KeySignature], is_perc: bool, staff_name: str) -> int:
        if is_perc:
            canonical = canonical_percussion_name(staff_name)
            if canonical in _PERC_MAP_PITCH_OVERRIDES:
                return _PERC_MAP_PITCH_OVERRIDES[canonical]
            return 38  # Default General MIDI snare
        return note._midi_pitch(key_sig)

    def _build_dynamic_timeline(
        self, timed_items: list[_TimedItem]
    ) -> tuple[list[_HairpinSegment], dict[int, DynamicLevel]]:
        """Compute the prevailing dynamic level at each item index, and detect
        all crescendo/decrescendo hairpin regions for continuous interpolation."""
        note_dynamics: dict[int, DynamicLevel] = {}
        hairpin_segments: list[_HairpinSegment] = []

        current_dyn = DynamicLevel.MF
        active_cresc_start: Optional[tuple[int, int, int]] = None  # (item_idx, start_tick, start_val)
        active_decresc_start: Optional[tuple[int, int, int]] = None

        for idx, item in enumerate(timed_items):
            # Check for new static dynamic
            for d in item.dynamics:
                if d.level in DYNAMIC_TO_BASE_VELOCITY:
                    current_dyn = d.level
                    # If a hairpin was running, this static dynamic closes it
                    if active_cresc_start:
                        s_idx, s_tick, s_val = active_cresc_start
                        e_val = DYNAMIC_TO_CC11.get(current_dyn, min(127, s_val + 24))
                        hairpin_segments.append(_HairpinSegment(s_tick, item.start_tick, s_val, e_val, True))
                        active_cresc_start = None
                    if active_decresc_start:
                        s_idx, s_tick, s_val = active_decresc_start
                        e_val = DYNAMIC_TO_CC11.get(current_dyn, max(24, s_val - 24))
                        hairpin_segments.append(_HairpinSegment(s_tick, item.start_tick, s_val, e_val, False))
                        active_decresc_start = None

            note_dynamics[idx] = current_dyn

            # Check for hairpin start/end
            for d in item.dynamics:
                if d.level == DynamicLevel.CRESCENDO_START:
                    active_cresc_start = (idx, item.start_tick, DYNAMIC_TO_CC11.get(current_dyn, DEFAULT_CC11))
                elif d.level == DynamicLevel.CRESCENDO_END and active_cresc_start:
                    s_idx, s_tick, s_val = active_cresc_start
                    e_val = DYNAMIC_TO_CC11.get(current_dyn, min(127, s_val + 24))
                    end_tick = item.start_tick + item.duration_ticks
                    hairpin_segments.append(_HairpinSegment(s_tick, end_tick, s_val, e_val, True))
                    active_cresc_start = None

                elif d.level == DynamicLevel.DECRESCENDO_START:
                    active_decresc_start = (idx, item.start_tick, DYNAMIC_TO_CC11.get(current_dyn, DEFAULT_CC11))
                elif d.level == DynamicLevel.DECRESCENDO_END and active_decresc_start:
                    s_idx, s_tick, s_val = active_decresc_start
                    e_val = DYNAMIC_TO_CC11.get(current_dyn, max(24, s_val - 24))
                    end_tick = item.start_tick + item.duration_ticks
                    hairpin_segments.append(_HairpinSegment(s_tick, end_tick, s_val, e_val, False))
                    active_decresc_start = None

        # Close any unclosed hairpins at the end of the score
        if timed_items:
            final_tick = timed_items[-1].start_tick + timed_items[-1].duration_ticks
            if active_cresc_start:
                s_idx, s_tick, s_val = active_cresc_start
                e_val = min(127, s_val + 24)
                hairpin_segments.append(_HairpinSegment(s_tick, final_tick, s_val, e_val, True))
            if active_decresc_start:
                s_idx, s_tick, s_val = active_decresc_start
                e_val = max(24, s_val - 24)
                hairpin_segments.append(_HairpinSegment(s_tick, final_tick, s_val, e_val, False))

        return hairpin_segments, note_dynamics

    def _pack_events(self, track: m21midi.MidiTrack, events: list[tuple[int, int, m21midi.MidiEvent]]) -> None:
        """Sort events by (tick, priority) and interleave with exact DeltaTime objects."""
        # Sort order: tick ASC, priority ASC
        # Priority order:
        # 0: Meta events / Track Name / Program Change
        # 1: Initial tempo / settings
        # 2: Time sig / Key sig
        # 3: Controller changes (CC11 Expression)
        # 4: Note Off
        # 5: Note On
        events.sort(key=lambda x: (x[0], x[1]))

        last_tick = 0
        for tick, _, ev in events:
            dt = m21midi.DeltaTime(track)
            dt.time = max(0, tick - last_tick)
            track.events.append(dt)
            track.events.append(ev)
            last_tick = tick

        # End of Track
        dt_eot = m21midi.DeltaTime(track)
        dt_eot.time = 0
        track.events.append(dt_eot)
        ev_eot = m21midi.MidiEvent(track)
        ev_eot.type = m21midi.MetaEvents.END_OF_TRACK
        ev_eot.data = b''
        track.events.append(ev_eot)


def export_expressive_midi(score: Score, output_path: str) -> None:
    """Export a DottedNotes Score model to an Expressive MIDI (DAW) file."""
    renderer = ExpressiveMidiRenderer()
    midi_file = renderer.render(score)
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    midi_file.open(output_path, 'wb')
    midi_file.write()
    midi_file.close()
