from __future__ import annotations

import os
import music21

from dottednotes.models import (
    Score, Staff, Measure, Note, Rest, Chord, Duration,
    Accidental, AccidentalType, Dynamic, DynamicLevel,
    Articulation, ArticulationType, Ornament, OrnamentType,
    GraceNote, Clef, ClefType, KeySignature, TimeSignature,
    TextMarking, TextMarkingType, InAccord, Tuplet,
    FermataShape, BreathMarkVariant,
)
from dottednotes.models.duration import TICKS_PER_QUARTER
from dottednotes.models.fingering import Fingering


def _item_quarter_length(item) -> float:
    """Quarter-note length of a Note/Chord/Rest, used to track offsets while
    building the music21 stream (an item's music21 .offset isn't reliable
    until after it's been inserted into a stream, so we track it ourselves)."""
    if isinstance(item, (Note, Chord, Rest)):
        return item.duration.duration_in_ticks() / TICKS_PER_QUARTER
    return 0.0


def export_musicxml(score: Score, output_path: str) -> None:
    """Export a DottedNotes Score model to a MusicXML file."""
    m21_score = MusicXMLRenderer().render(score)
    suffix = os.path.splitext(output_path)[1].lower()
    if suffix == '.mxl':
        m21_score.write('mxl', fp=output_path)
    else:
        m21_score.write('musicxml', fp=output_path)


DURATION_VAL_MAP = {
    0: 'breve',
    1: 'whole',
    2: 'half',
    4: 'quarter',
    8: 'eighth',
    16: '16th',
    32: '32nd',
    64: '64th',
}

ARTICULATION_TYPE_MAP = {
    ArticulationType.STACCATO: music21.articulations.Staccato,
    ArticulationType.STACCATISSIMO: music21.articulations.Staccatissimo,
    ArticulationType.TENUTO: music21.articulations.Tenuto,
    ArticulationType.ACCENT: music21.articulations.Accent,
    ArticulationType.EXPRESSIVE_ACCENT: music21.articulations.StrongAccent,
    ArticulationType.DOWN_BOW: music21.articulations.DownBow,
    ArticulationType.UP_BOW: music21.articulations.UpBow,
    ArticulationType.STOPPED: music21.articulations.Stopped,
    ArticulationType.OPEN: music21.articulations.OpenString,
}

# Reverse of musicxml_parser.py's _M21_FERMATA_SHAPE_TO_MODEL (S10c-4).
# BETWEEN_NOTES has no distinct MusicXML/music21 shape -- it's purely a
# braille positional convention (see models/fermata.py) -- so it round-trips
# to the same 'normal' shape as FermataShape.NORMAL.
FERMATA_SHAPE_TO_M21 = {
    FermataShape.NORMAL: 'normal',
    FermataShape.BETWEEN_NOTES: 'normal',
    FermataShape.SQUARED: 'square',
    FermataShape.TENT: 'angled',
}


class MusicXMLRenderer:
    def render(self, score: Score) -> music21.stream.Score:
        m21_score = music21.stream.Score()
        
        # Metadata
        m21_score.insert(0, music21.metadata.Metadata())
        m21_score.metadata.title = score.title
        m21_score.metadata.composer = score.composer
        m21_score.metadata.copyright = score.copyright
        
        for staff in score.staves:
            m21_part = self.render_staff(staff)
            m21_score.append(m21_part)
            
        return m21_score

    def render_staff(self, staff: Staff) -> music21.stream.Part:
        m21_part = music21.stream.Part()
        m21_part.id = staff.name
        m21_part.partName = staff.name
        
        # Tracking variables
        active_clef_name = None
        active_key_val = None
        active_time_val = None
        
        active_slurs: list[music21.spanner.Slur] = []
        active_phrasing: list[music21.spanner.Slur] = []
        slur_spanners: list[music21.spanner.Spanner] = []
        
        active_cresc: list[music21.dynamics.Crescendo] = []
        active_decresc: list[music21.dynamics.Diminuendo] = []
        dyn_spanners: list[music21.spanner.Spanner] = []
        
        active_ties: set[tuple[str, int]] = set()

        volta_spanners: list[music21.spanner.RepeatBracket] = []

        model_to_m21: dict[int, music21.base.Music21Object] = {}
        
        # Collect pitched items for lyrics alignment later
        pitched_items: list[Note | Chord] = []
        
        for measure_model in staff.measures:
            m21_measure = music21.stream.Measure(number=measure_model.number)
            measure_ql = measure_model.time_signature[0] * 4.0 / measure_model.time_signature[1]

            # Key signature
            if measure_model.key_signature != active_key_val:
                m21_key = music21.key.KeySignature(measure_model.key_signature)
                m21_measure.insert(0, m21_key)
                active_key_val = measure_model.key_signature
                
            # Time signature
            if measure_model.time_signature != active_time_val:
                ts_num, ts_den = measure_model.time_signature
                m21_ts = music21.meter.TimeSignature(f"{ts_num}/{ts_den}")
                m21_measure.insert(0, m21_ts)
                active_time_val = measure_model.time_signature
                
            # Clef
            if measure_model.clef != active_clef_name:
                if measure_model.clef == "treble":
                    m21_measure.insert(0, music21.clef.TrebleClef())
                elif measure_model.clef == "bass":
                    m21_measure.insert(0, music21.clef.BassClef())
                elif measure_model.clef == "alto":
                    m21_measure.insert(0, music21.clef.AltoClef())
                elif measure_model.clef == "tenor":
                    m21_measure.insert(0, music21.clef.TenorClef())
                active_clef_name = measure_model.clef
                
            # Barline type
            if measure_model.bar_line_type == 'final_double_bar':
                m21_measure.rightBarline = music21.bar.Barline('final')
            elif measure_model.bar_line_type == 'section_double_bar':
                m21_measure.rightBarline = music21.bar.Barline('double')
            elif measure_model.bar_line_type == 'end_repeat':
                m21_measure.rightBarline = music21.bar.Repeat(direction='end')
            elif measure_model.bar_line_type == 'forward_repeat':
                m21_measure.leftBarline = music21.bar.Repeat(direction='start')
                
            # Text markings
            for tm in measure_model.text_markings:
                if tm.type == TextMarkingType.TEMPO:
                    try:
                        # Try to parse numeric tempo if format matches
                        # e.g., "120" or "Quarter = 120"
                        if tm.text.isdigit():
                            mm = music21.tempo.MetronomeMark(number=int(tm.text))
                        else:
                            mm = music21.tempo.MetronomeMark(text=tm.text)
                        m21_measure.append(mm)
                    except Exception:
                        m21_measure.append(music21.expressions.TextExpression(tm.text))
                else:
                    m21_measure.append(music21.expressions.TextExpression(tm.text))
                    
            # Translate items
            # InAccord items map to voices in music21 measure
            has_in_accord = any(isinstance(x, InAccord) for x in measure_model.notes)
            
            if has_in_accord:
                # Get the InAccord item
                in_accord_item = next(x for x in measure_model.notes if isinstance(x, InAccord))
                # For each part in InAccord, create a voice
                for v_idx, part_list in enumerate(in_accord_item.parts):
                    m21_voice = music21.stream.Voice(id=f"V{v_idx + 1}")
                    voice_offset = 0.0
                    for item in part_list:
                        m21_item = self.render_item(
                            item, model_to_m21, pitched_items, active_ties,
                            active_slurs, active_phrasing, slur_spanners,
                            active_cresc, active_decresc, dyn_spanners, m21_measure,
                            voice_offset, m21_voice, measure_ql
                        )
                        if m21_item is not None:
                            m21_voice.append(m21_item)
                        voice_offset += _item_quarter_length(item)
                    m21_measure.append(m21_voice)
            else:
                current_offset = 0.0
                for item in measure_model.notes:
                    if isinstance(item, Tuplet):
                        # Map all items inside Tuplet
                        for sub_idx, sub_item in enumerate(item.items):
                            m21_item = self.render_item(
                                sub_item, model_to_m21, pitched_items, active_ties,
                                active_slurs, active_phrasing, slur_spanners,
                                active_cresc, active_decresc, dyn_spanners, m21_measure,
                                current_offset, m21_measure, measure_ql
                            )
                            if m21_item is not None:
                                t = music21.duration.Tuplet(3, 2)
                                if sub_idx == 0:
                                    t.type = 'start'
                                elif sub_idx == len(item.items) - 1:
                                    t.type = 'stop'
                                m21_item.duration.appendTuplet(t)
                                m21_measure.append(m21_item)
                            current_offset += _item_quarter_length(sub_item)
                    else:
                        m21_item = self.render_item(
                            item, model_to_m21, pitched_items, active_ties,
                            active_slurs, active_phrasing, slur_spanners,
                            active_cresc, active_decresc, dyn_spanners, m21_measure,
                            current_offset, m21_measure, measure_ql
                        )
                        if m21_item is not None:
                            m21_measure.append(m21_item)
                        current_offset += _item_quarter_length(item)
                            
            m21_part.append(m21_measure)

            # First/second endings (S10c-4). RepeatBracket's `number` takes
            # a comma-joined string for combined endings ("1,2") -- the
            # exact form confirmed to round-trip back to numberRange == the
            # matching list of ints during S10b-5's import-side investigation.
            if measure_model.ending_numbers:
                number_str = ','.join(str(n) for n in measure_model.ending_numbers)
                volta_spanners.append(music21.spanner.RepeatBracket(m21_measure, number=number_str))

        # Add collected spanners
        for sp in slur_spanners:
            m21_part.insert(0, sp)
        for sp in dyn_spanners:
            m21_part.insert(0, sp)
        for sp in volta_spanners:
            m21_part.insert(0, sp)
            
        # Attach lyrics
        if staff.verses:
            for v_idx, verse in enumerate(staff.verses):
                for s_idx, syllable in enumerate(verse):
                    if s_idx < len(pitched_items):
                        item = pitched_items[s_idx]
                        m21_obj = model_to_m21.get(id(item))
                        if m21_obj is not None:
                            text = syllable.strip()
                            if text.endswith('--'):
                                text = text[:-2].strip()
                                syllabic = 'begin'
                            elif text.endswith(' --'):
                                text = text[:-3].strip()
                                syllabic = 'begin'
                            elif ' --' in text:
                                text = text.replace(' --', '')
                                syllabic = 'begin'
                            else:
                                syllabic = 'single'
                            ly = music21.note.Lyric(text=text, number=v_idx + 1)
                            ly.syllabic = syllabic
                            m21_obj.lyrics.append(ly)
                            
        return m21_part

    def render_item(
        self, item, model_to_m21, pitched_items, active_ties,
        active_slurs, active_phrasing, slur_spanners,
        active_cresc, active_decresc, dyn_spanners, m21_measure,
        offset: float, container: music21.stream.Stream, measure_ql: float
    ) -> music21.base.Music21Object | None:
        if isinstance(item, Note):
            m21_note = self.render_note(item, active_ties)
            model_to_m21[id(item)] = m21_note
            pitched_items.append(item)

            # Map dynamics, slurs, grace notes, etc.
            self.apply_note_dynamics(item, m21_note, active_cresc, active_decresc, dyn_spanners, m21_measure, offset)
            self.apply_note_slurs(item, m21_note, active_slurs, active_phrasing, slur_spanners)
            self.apply_note_grace(item, m21_note, active_ties, container, offset)

            return m21_note

        elif isinstance(item, Chord):
            # Sort pitches: descending for treble/alto, ascending for bass/tenor
            m21_chord = self.render_chord(item, active_ties)
            model_to_m21[id(item)] = m21_chord
            pitched_items.append(item)

            # Apply dynamic/slur markings from the written note (item.notes[0])
            written_note = item.notes[0]
            self.apply_note_dynamics(written_note, m21_chord, active_cresc, active_decresc, dyn_spanners, m21_measure, offset)
            self.apply_note_slurs(written_note, m21_chord, active_slurs, active_phrasing, slur_spanners)
            self.apply_note_grace(written_note, m21_chord, active_ties, container, offset)

            return m21_chord
            
        elif isinstance(item, Rest):
            m21_rest = self.render_rest(item, measure_ql)
            return m21_rest
            
        return None

    def render_note(self, note: Note, active_ties: set[tuple[str, int]]) -> music21.note.Note:
        # Construct pitch string
        acc_str = ""
        if note.accidental is not None:
            acc_type = note.accidental.type
            if acc_type == AccidentalType.SHARP: acc_str = "#"
            elif acc_type == AccidentalType.FLAT: acc_str = "-"
            elif acc_type == AccidentalType.DOUBLE_SHARP: acc_str = "##"
            elif acc_type == AccidentalType.DOUBLE_FLAT: acc_str = "--"
            
        pitch_str = f"{note.note_name}{acc_str}{note.octave}"
        m21_note = music21.note.Note(pitch_str)
        
        # Set duration
        m21_note.duration.type = DURATION_VAL_MAP.get(note.duration.value, 'quarter')
        m21_note.duration.dots = note.duration.dots
        
        # Articulations
        for art in note.articulations:
            cls = ARTICULATION_TYPE_MAP.get(art.type)
            if cls is not None:
                m21_note.articulations.append(cls())
                
        # Ornaments / Expressions
        for o in note.ornaments:
            if o.type == OrnamentType.TRILL:
                m21_note.expressions.append(music21.expressions.Trill())
            elif o.type == OrnamentType.MORDENT:
                m21_note.expressions.append(music21.expressions.Mordent(direction='down'))
            elif o.type == OrnamentType.UPPER_MORDENT:
                m21_note.expressions.append(music21.expressions.InvertedMordent())
            elif o.type == OrnamentType.TURN:
                m21_note.expressions.append(music21.expressions.Turn())
            elif o.type == OrnamentType.INVERTED_TURN:
                m21_note.expressions.append(music21.expressions.InvertedTurn())
                
        # Fermata (S10c-4)
        if note.fermata is not None:
            m21_fermata = music21.expressions.Fermata()
            m21_fermata.shape = FERMATA_SHAPE_TO_M21[note.fermata.shape]
            m21_note.expressions.append(m21_fermata)

        # Breath/break mark (S10c-4)
        if note.breath_mark is not None:
            if note.breath_mark.variant == BreathMarkVariant.HALF:
                m21_note.articulations.append(music21.articulations.BreathMark())
            else:
                m21_note.articulations.append(music21.articulations.Caesura())

        # Fingerings
        for f in note.fingerings:
            val = ""
            if f.change_to is not None:
                val = f"{f.finger or ''}-{f.change_to}"
            elif f.alternative is not None:
                val = f"{f.finger or ''}/{f.alternative}"
            elif f.finger is not None:
                val = str(f.finger)
            if val:
                m21_note.articulations.append(music21.articulations.Fingering(val))
                
        # Tie
        key = (note.note_name, note.octave)
        if key in active_ties:
            m21_note.tie = music21.tie.Tie('stop')
            active_ties.remove(key)
            
        if note.tie:
            if m21_note.tie is not None:
                m21_note.tie = music21.tie.Tie('continue')
            else:
                m21_note.tie = music21.tie.Tie('start')
            active_ties.add(key)
            
        return m21_note

    def render_chord(self, chord: Chord, active_ties: set[tuple[str, int]]) -> music21.chord.Chord:
        m21_notes = [self.render_note(n, active_ties) for n in chord.notes]
        m21_chord = music21.chord.Chord(m21_notes)
        m21_chord.duration.type = DURATION_VAL_MAP.get(chord.duration.value, 'quarter')
        m21_chord.duration.dots = chord.duration.dots
        return m21_chord

    def render_rest(self, rest: Rest, measure_ql: float) -> music21.note.Rest:
        m21_rest = music21.note.Rest()
        if rest.is_full_measure:
            # A full-measure rest's nominal note value (e.g. "whole") is a display
            # convention -- BANA/LilyPond both size it to the actual measure length
            # regardless of time signature, so match that here rather than using
            # DURATION_VAL_MAP, or a rest in a non-4/4 measure ends up with the wrong
            # quarterLength and music21 pads the part with an extra spillover measure.
            m21_rest.duration.quarterLength = measure_ql
            m21_rest.fullMeasure = True
        else:
            m21_rest.duration.type = DURATION_VAL_MAP.get(rest.duration.value, 'quarter')
            m21_rest.duration.dots = rest.duration.dots
        return m21_rest

    def apply_note_dynamics(
        self, note_model: Note, m21_obj: music21.base.Music21Object,
        active_cresc: list[music21.dynamics.Crescendo],
        active_decresc: list[music21.dynamics.Diminuendo],
        dyn_spanners: list[music21.spanner.Spanner],
        m21_measure: music21.stream.Measure,
        offset: float
    ) -> None:
        for dyn in note_model.dynamics:
            if dyn.level in (DynamicLevel.CRESCENDO_START, DynamicLevel.CRESCENDO_END,
                             DynamicLevel.DECRESCENDO_START, DynamicLevel.DECRESCENDO_END):
                if dyn.level == DynamicLevel.CRESCENDO_START:
                    sp = music21.dynamics.Crescendo()
                    sp.addSpannedElements(m21_obj)
                    active_cresc.append(sp)
                    dyn_spanners.append(sp)
                elif dyn.level == DynamicLevel.CRESCENDO_END:
                    if active_cresc:
                        sp = active_cresc.pop()
                        sp.addSpannedElements(m21_obj)
                elif dyn.level == DynamicLevel.DECRESCENDO_START:
                    sp = music21.dynamics.Diminuendo()
                    sp.addSpannedElements(m21_obj)
                    active_decresc.append(sp)
                    dyn_spanners.append(sp)
                elif dyn.level == DynamicLevel.DECRESCENDO_END:
                    if active_decresc:
                        sp = active_decresc.pop()
                        sp.addSpannedElements(m21_obj)
            else:
                # Numeric/Text dynamic (e.g. p, f)
                val_str = dyn.to_lilypond().replace('\\', '')
                m21_dyn = music21.dynamics.Dynamic(val_str)
                m21_measure.insert(offset, m21_dyn)

    def apply_note_slurs(
        self, note_model: Note, m21_obj: music21.base.Music21Object,
        active_slurs: list[music21.spanner.Slur],
        active_phrasing: list[music21.spanner.Slur],
        slur_spanners: list[music21.spanner.Spanner]
    ) -> None:
        if note_model.slur_start:
            sp = music21.spanner.Slur()
            sp.addSpannedElements(m21_obj)
            active_slurs.append(sp)
            slur_spanners.append(sp)
        if note_model.slur_bracket_open:
            sp = music21.spanner.Slur()
            sp.addSpannedElements(m21_obj)
            active_phrasing.append(sp)
            slur_spanners.append(sp)
            
        if note_model.slur_end and active_slurs:
            sp = active_slurs.pop()
            sp.addSpannedElements(m21_obj)
        if note_model.slur_bracket_close and active_phrasing:
            sp = active_phrasing.pop()
            sp.addSpannedElements(m21_obj)

    def apply_note_grace(
        self, note_model: Note, m21_obj: music21.base.Music21Object,
        active_ties: set[tuple[str, int]], container: music21.stream.Stream,
        offset: float
    ) -> None:
        if note_model.grace_note is not None:
            # Grace notes have quarterLength 0, so inserting them into the same
            # container (measure/voice) at the main note's own offset, before the
            # main note itself is appended, places them immediately ahead of it.
            for gn in note_model.grace_note.notes:
                m21_gn = self.render_note(gn, active_ties)
                # Replacing .duration with a fresh GraceDuration() would drop the
                # note's written type/dots (defaulting to a bare "zero" duration),
                # so carry them over explicitly.
                orig_type = m21_gn.duration.type
                orig_dots = m21_gn.duration.dots
                m21_gn.duration = music21.duration.GraceDuration(type=orig_type)
                m21_gn.duration.dots = orig_dots
                m21_gn.duration.slash = not note_model.grace_note.long_appoggiatura
                container.insert(offset, m21_gn)
