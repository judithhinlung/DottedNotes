from __future__ import annotations

import os
import music21

from dottednotes.exceptions import DottedNotesError
from dottednotes.models import (
    Score, Staff, Measure, Note, Rest, Chord, Duration,
    Accidental, AccidentalType, Dynamic, DynamicLevel,
    Articulation, ArticulationType, Ornament, OrnamentType,
    GraceNote, Clef, ClefType, KeySignature, TimeSignature,
    TextMarking, TextMarkingType, Tuplet, InAccord,
    ChordSymbol, ChordNamesTrack, Fermata, FermataShape,
    BreathMark, BreathMarkVariant,
)
from dottednotes.models.fingering import Fingering
from dottednotes.models.duration import TICKS_PER_QUARTER
from dottednotes.models.transposition import transposition_from_interval

def load_musicxml(source: str) -> Score:
    """Parse a MusicXML file path or string using music21 and return a DottedNotes Score."""
    if isinstance(source, str) and not source.strip().startswith("<") and not os.path.exists(source):
        raise DottedNotesError(f"File not found: '{source}'")
    try:
        m21_score = music21.converter.parse(source)
    except Exception as e:
        raise DottedNotesError(f"Could not parse MusicXML: {e}")
    return MusicXMLTranslator().translate(m21_score)


M21_DURATION_MAP = {
    'breve': 0,
    'whole': 1,
    'half': 2,
    'quarter': 4,
    'eighth': 8,
    '16th': 16,
    '32nd': 32,
    '64th': 64,
}

M21_ARTICULATION_MAP = {
    music21.articulations.Staccato: ArticulationType.STACCATO,
    music21.articulations.Staccatissimo: ArticulationType.STACCATISSIMO,
    music21.articulations.Tenuto: ArticulationType.TENUTO,
    music21.articulations.Accent: ArticulationType.ACCENT,
    music21.articulations.StrongAccent: ArticulationType.EXPRESSIVE_ACCENT,
    music21.articulations.DownBow: ArticulationType.DOWN_BOW,
    music21.articulations.UpBow: ArticulationType.UP_BOW,
    music21.articulations.Stopped: ArticulationType.STOPPED,
    music21.articulations.OpenString: ArticulationType.OPEN,
}

# music21.expressions.Fermata.shape values (confirmed against its source:
# only 'normal'/'angled'/'square' are modeled) -> BANA Table 22(B) variant
# (S10b-4). 'angled' -> TENT and 'square' -> SQUARED per the same
# Henze-fermata cross-reference documented in models/fermata.py.
_M21_FERMATA_SHAPE_TO_MODEL = {
    'normal': FermataShape.NORMAL,
    'angled': FermataShape.TENT,
    'square': FermataShape.SQUARED,
}


class MusicXMLTranslator:
    def translate(self, m21_score: music21.stream.Score) -> Score:
        score = Score()
        
        # Metadata
        if m21_score.metadata:
            score.title = m21_score.metadata.title or m21_score.metadata.movementName or ""
            score.composer = m21_score.metadata.composer or ""
            score.copyright = m21_score.metadata.copyright or ""
            
        parts = list(m21_score.parts)
        for part in parts:
            staff, chord_track_entries = self.translate_part(part)
            score.add_staff(staff)
            # Lead-sheet chord symbols (BANA Sec. 23/27, S10b-3) are only
            # supported for a single melody staff, matching
            # lead_sheet_parser.py's identical restriction on the BRF side --
            # a chord-symbol line has no defined alignment against more than
            # one staff.
            if len(parts) == 1 and chord_track_entries:
                score.chord_names = ChordNamesTrack(entries=chord_track_entries)

        return score

    def translate_part(self, part: music21.stream.Part) -> tuple[Staff, list]:
        # Determine staff name
        name = str(part.partName) if hasattr(part, 'partName') and part.partName else str(part.id)
        if not name:
            name = "Staff"
        lower_id = str(part.id).lower()
        lower_name = name.lower()
        
        if "piano" in lower_name or "harp" in lower_name:
            base = "Piano" if "piano" in lower_name else "Harp"
            if "staff1" in lower_id or "staff 1" in lower_id:
                name = f"{base} right hand"
            elif "staff2" in lower_id or "staff 2" in lower_id:
                name = f"{base} left hand"

        staff = Staff(name=name)

        # Prefer music21's own structured transposition data over matching
        # `staff.name` against a fixed instrument-name table (S10b-2): real
        # MusicXML part names vary too much ("Bb Clarinet", "Horn in F 1")
        # to reliably match get_transposition()'s "<instrument> in <key>"
        # pattern, but music21 exposes the actual <transpose> interval from
        # the file directly, for any instrument, not just a hardcoded few.
        instrument = part.getInstrument(returnDefault=False)
        if instrument is not None and instrument.transposition is not None:
            interval = instrument.transposition
            staff.resolved_transposition = transposition_from_interval(
                interval.diatonic.generic.staffDistance,
                interval.chromatic.semitones,
            )

        current_clef = "treble"
        current_key = 0
        current_time = (4, 4)
        
        # Collect lyrics by verse number
        verses_data: dict[int, list[str]] = {}

        # Lead-sheet chord-symbol alignment (BANA Sec. 23/27, S10b-3),
        # accumulated across all of this part's measures in melody order.
        chord_track_entries: list = []

        for m21_measure in part.getElementsByClass(music21.stream.Measure):
            measure, measure_chord_entries = self.translate_measure(m21_measure, current_clef, current_key, current_time)
            chord_track_entries.extend(measure_chord_entries)

            # Carry over active clef/key/time signatures
            current_clef = measure.clef
            current_key = measure.key_signature
            current_time = measure.time_signature
            
            # Populate staff-level signature models at the first measure
            if len(staff.measures) == 0:
                # Key signature
                staff.key_signature = KeySignature(dots=frozenset(), category=None, raw_brl="", sharps_or_flats=current_key)
                # Time signature
                staff.time_signature = TimeSignature(dots=frozenset(), category=None, raw_brl="", numerator=current_time[0], denominator=current_time[1])
                # Clef
                clefs = list(m21_measure.getElementsByClass(music21.clef.Clef))
                if clefs:
                    staff.clef = self.map_clef_model(clefs[0])
                else:
                    # heuristic or default
                    ct = ClefType.TREBLE if current_clef == "treble" else ClefType.BASS
                    if current_clef == "alto": ct = ClefType.ALTO
                    elif current_clef == "tenor": ct = ClefType.TENOR
                    staff.clef = Clef(dots=frozenset(), category=None, raw_brl="", clef_type=ct)
            
            staff.add_measure(measure)
            
            # Collect lyrics from notes/chords in this measure
            for note in m21_measure.notes:
                m21_lyrics = note.lyrics
                if not m21_lyrics and isinstance(note, music21.chord.Chord):
                    m21_lyrics = note.notes[0].lyrics
                for lyric in m21_lyrics:
                    v_num = lyric.number if lyric.number is not None else 1
                    if v_num not in verses_data:
                        verses_data[v_num] = []
                    text = lyric.text or ""
                    if lyric.syllabic in ('begin', 'middle'):
                        text = text + " --"
                    verses_data[v_num].append(text)
                    
        # Populate lyrics on staff
        if verses_data:
            sorted_v_nums = sorted(verses_data.keys())
            staff.verses = [verses_data[n] for n in sorted_v_nums]
            staff.lyrics = staff.verses[0]
            if len(sorted_v_nums) > 1:
                staff.verse_prefixes = [f"{n}." for n in sorted_v_nums]
            else:
                staff.verse_prefixes = [None] * len(sorted_v_nums)

        return staff, chord_track_entries

    def map_clef_model(self, m21_clef) -> Clef:
        if isinstance(m21_clef, music21.clef.TrebleClef):
            ct = ClefType.TREBLE
        elif isinstance(m21_clef, music21.clef.BassClef):
            ct = ClefType.BASS
        elif isinstance(m21_clef, music21.clef.AltoClef):
            ct = ClefType.ALTO
        elif isinstance(m21_clef, music21.clef.TenorClef):
            ct = ClefType.TENOR
        else:
            ct = ClefType.TREBLE
        return Clef(dots=frozenset(), category=None, raw_brl="", clef_type=ct)

    def translate_measure(self, m21_measure: music21.stream.Measure, prev_clef: str, prev_key: int, prev_time: tuple[int, int]) -> tuple[Measure, list]:
        # Determine signatures for this measure
        clef_name = prev_clef
        clefs = list(m21_measure.getElementsByClass(music21.clef.Clef))
        if clefs:
            if isinstance(clefs[0], music21.clef.TrebleClef):
                clef_name = "treble"
            elif isinstance(clefs[0], music21.clef.BassClef):
                clef_name = "bass"
            elif isinstance(clefs[0], music21.clef.AltoClef):
                clef_name = "alto"
            elif isinstance(clefs[0], music21.clef.TenorClef):
                clef_name = "tenor"
                
        key_val = prev_key
        keys = list(m21_measure.getElementsByClass(music21.key.KeySignature))
        if keys:
            key_val = keys[0].sharps
            
        time_val = prev_time
        times = list(m21_measure.getElementsByClass(music21.meter.TimeSignature))
        if times:
            time_val = (times[0].numerator, times[0].denominator)
            
        measure = Measure(
            number=m21_measure.number,
            clef=clef_name,
            key_signature=key_val,
            time_signature=time_val
        )
        
        # Determine bar line type
        bar_line = 'measure_separator'
        if m21_measure.rightBarline:
            rb = m21_measure.rightBarline
            if isinstance(rb, music21.bar.Repeat) and rb.direction == 'end':
                bar_line = 'end_repeat'
            elif rb.type == 'final':
                bar_line = 'final_double_bar'
            elif rb.type == 'double':
                bar_line = 'section_double_bar'
        if m21_measure.leftBarline:
            lb = m21_measure.leftBarline
            if isinstance(lb, music21.bar.Repeat) and lb.direction == 'start':
                bar_line = 'forward_repeat'
        measure.bar_line_type = bar_line

        # First/second (or later) endings (BANA Chapter 17, Par. 17.1.1,
        # S10b-5). Confirmed against music21 10.5.0: a measure spanned by a
        # RepeatBracket exposes it via getSpannerSites, and
        # RepeatBracket.numberRange already gives the combined/ranged
        # ending numbers as a plain list (e.g. [1, 2] for a "1,2" bracket).
        repeat_brackets = m21_measure.getSpannerSites(music21.spanner.RepeatBracket)
        if repeat_brackets:
            measure.ending_numbers = list(repeat_brackets[0].numberRange)


        # Text markings & Metronome marks
        for t in m21_measure.getElementsByClass(music21.expressions.TextExpression):
            text_val = t.content or ""
            is_tempo = text_val.lower().strip() in TEMPO_TERMS
            tm_type = TextMarkingType.TEMPO if is_tempo else TextMarkingType.EXPRESSION
            measure.text_markings.append(TextMarking(text=text_val, type=tm_type))
            
        for m in m21_measure.getElementsByClass(music21.tempo.MetronomeMark):
            text_val = m.text or f"{m.number}"
            measure.text_markings.append(TextMarking(text=text_val, type=TextMarkingType.TEMPO))
            
        # Collect dynamics in the measure
        dynamic_offsets: dict[float, Dynamic] = {}
        for d in m21_measure.getElementsByClass(music21.dynamics.Dynamic):
            val = (d.value or "").lower()
            lvl = None
            if val == 'ppp': lvl = DynamicLevel.PPP
            elif val == 'pp': lvl = DynamicLevel.PP
            elif val == 'p': lvl = DynamicLevel.P
            elif val == 'mp': lvl = DynamicLevel.MP
            elif val == 'mf': lvl = DynamicLevel.MF
            elif val == 'f': lvl = DynamicLevel.F
            elif val == 'ff': lvl = DynamicLevel.FF
            elif val == 'fff': lvl = DynamicLevel.FFF
            elif val == 'sf': lvl = DynamicLevel.SF
            elif val == 'sfz': lvl = DynamicLevel.SFZ
            elif val == 'fp': lvl = DynamicLevel.FP
            if lvl is not None:
                dynamic_offsets[d.offset] = Dynamic(level=lvl)
                
        # Parse notes and rests. A measure whose content lives in nested
        # music21 Voice streams (MusicXML's <voice> numbering -- the normal
        # way a single staff carries two independent rhythmic lines, e.g.
        # piano writing) is NOT reached by `m21_measure.notesAndRests`: that
        # call does not descend into Voice sub-streams and would silently
        # return an empty measure (confirmed against music21 10.5.0). Each
        # voice is translated separately and wrapped in an InAccord (BANA
        # Chapter 11) instead (S10b-1).
        voices = list(m21_measure.voices)
        chord_track_entries: list = []
        if voices:
            voice_items = [
                self._translate_note_stream(voice.notesAndRests, clef_name, dynamic_offsets)
                for voice in voices
            ]
            ordered = self._order_voices_by_bana_convention(voice_items, clef_name)
            measure.add_note(InAccord(parts=ordered, in_accord_type='full_measure'))
            # Lead-sheet chord symbols (BANA 27.1) are only defined for a
            # single melody line, matching lead_sheet_parser.py's identical
            # restriction on the BRF side -- a multi-voice measure has no
            # single line to align chord symbols against, so any chord
            # symbols here are silently not collected.
        else:
            stream_elements = list(m21_measure.notesAndRests)
            for item in self._translate_note_stream(stream_elements, clef_name, dynamic_offsets):
                measure.add_note(item)
            chord_symbols = list(m21_measure.getElementsByClass(music21.harmony.ChordSymbol))
            if chord_symbols:
                chord_track_entries = self._align_chord_symbols(stream_elements, chord_symbols)

        return measure, chord_track_entries

    def _align_chord_symbols(self, elements, m21_chord_symbols) -> list:
        """Align music21 harmony.ChordSymbol elements to the melody notes/
        rests in `elements` by offset (S10b-3), mirroring lead_sheet_parser.py's
        column-alignment for the BRF side: BANA 27.1 places a chord symbol's
        initial cell "below the first sign of the note...with which it
        coincides," so each chord symbol attaches to the melody item at or
        immediately after its own offset. Returns one (Duration, ChordSymbol
        | None) entry per melody note/rest -- Chord items are excluded, since
        BANA lead sheets pair chord symbols with a single melody line, the
        same restriction lead_sheet_parser.py applies on the BRF side.
        """
        melody = [
            el for el in elements
            if isinstance(el, (music21.note.Note, music21.note.Rest)) and not el.duration.isGrace
        ]
        if not melody:
            return []

        chord_for_index: dict[int, ChordSymbol] = {}
        for cs in sorted(m21_chord_symbols, key=lambda c: c.offset):
            candidates = [i for i, el in enumerate(melody) if el.offset <= cs.offset]
            if not candidates:
                continue
            chord_for_index[max(candidates)] = self._translate_chord_symbol(cs)

        return [
            (self.map_duration(el.duration), chord_for_index.get(i))
            for i, el in enumerate(melody)
        ]

    _CHORD_KIND_TO_MODEL_FIELDS: dict[str, dict] = {
        'major': {},
        'minor': {'is_minor': True},
        'augmented': {'is_augmented': True},
        'diminished': {'is_diminished': True},
        'diminished-seventh': {'is_diminished': True, 'extensions': [(7, None)]},
        'half-diminished-seventh': {'is_half_diminished': True},
        'dominant-seventh': {'extensions': [(7, None)]},
        'dominant-ninth': {'extensions': [(9, None)]},
        'dominant-11th': {'extensions': [(11, None)]},
        'dominant-13th': {'extensions': [(13, None)]},
        'major-seventh': {'has_explicit_maj': True},
        'major-ninth': {'has_explicit_maj': True, 'extensions': [(9, None)]},
        'major-11th': {'has_explicit_maj': True, 'extensions': [(11, None)]},
        'major-13th': {'has_explicit_maj': True, 'extensions': [(13, None)]},
        'major-sixth': {'extensions': [(6, None)]},
        'minor-sixth': {'is_minor': True, 'extensions': [(6, None)]},
        'minor-seventh': {'is_minor': True, 'extensions': [(7, None)]},
        'minor-ninth': {'is_minor': True, 'extensions': [(9, None)]},
        'minor-11th': {'is_minor': True, 'extensions': [(11, None)]},
        'minor-13th': {'is_minor': True, 'extensions': [(13, None)]},
        'minor-major-seventh': {'is_minor': True, 'has_explicit_maj': True},
        'suspended-second': {'suspended': 2},
        'suspended-fourth': {'suspended': 4},
        'suspended-fourth-seventh': {'suspended': 4, 'extensions': [(7, None)]},
    }

    _M21_ACCIDENTAL_TO_MODEL = {'sharp': 'sharp', 'flat': 'flat', 'natural': 'natural'}

    def _translate_chord_symbol(self, cs) -> ChordSymbol:
        """Translate one music21 harmony.ChordSymbol into a DottedNotes
        ChordSymbol (BANA Sec. 23/27). `cs.chordKind` is MusicXML's own
        controlled-vocabulary chord-quality string (e.g. 'minor-seventh');
        `_CHORD_KIND_TO_MODEL_FIELDS` covers the common jazz/lead-sheet
        qualities. An unrecognized kind raises rather than guessing a chord
        quality that would then sound (or print) wrong -- matching
        chord_symbol_parser.py's own fail-fast behavior on an unrecognized
        braille chord-symbol cell, rather than silently defaulting to a
        plain major triad.
        """
        if cs.chordKind == 'none' or cs.root() is None:
            return ChordSymbol(no_chord=True)

        if cs.chordKind not in self._CHORD_KIND_TO_MODEL_FIELDS:
            raise DottedNotesError(
                f"Unrecognized MusicXML chord kind '{cs.chordKind}' (chord symbol "
                f"'{cs.figure}') -- not one of the lead-sheet chord qualities "
                "DottedNotes currently maps (BANA Sec. 23/27)."
            )

        root = cs.root()
        root_accidental = (
            self._M21_ACCIDENTAL_TO_MODEL.get(root.accidental.name) if root.accidental else None
        )

        fields = dict(self._CHORD_KIND_TO_MODEL_FIELDS[cs.chordKind])
        extensions = list(fields.pop('extensions', []))

        chord = ChordSymbol(root=root.step, accidental=root_accidental, extensions=extensions, **fields)

        bass = cs.bass()
        if bass is not None and bass is not root:
            bass_accidental = (
                self._M21_ACCIDENTAL_TO_MODEL.get(bass.accidental.name) if bass.accidental else None
            )
            chord.bass_note = (bass.step, bass_accidental)

        return chord

    def _order_voices_by_bana_convention(self, voice_items: list, clef_name: str) -> list:
        """Order InAccord voices per BANA Chapter 11: highest voice first for
        treble/alto clef, lowest voice first for bass/tenor clef. music21's
        own voice numbering doesn't reliably reflect pitch order (a "voice
        2" can sit above "voice 1" depending on how the source engraving
        software assigned voice numbers), so this derives order from each
        voice's actual average pitch instead of trusting the numbering."""
        def avg_pitch(items: list) -> float:
            pitches: list[int] = []

            def collect(item):
                if isinstance(item, Note):
                    pitches.append(item._midi_pitch())
                elif isinstance(item, Chord) and item.notes:
                    pitches.append(item.notes[0]._midi_pitch())
                elif isinstance(item, Tuplet):
                    for sub in item.items:
                        collect(sub)

            for item in items:
                collect(item)
            return sum(pitches) / len(pitches) if pitches else 0.0

        reverse = clef_name not in ("bass", "tenor")
        return sorted(voice_items, key=avg_pitch, reverse=reverse)

    def _ottava_semitone_shift(self, el) -> int:
        """Return the signed semitone shift from an active `music21.spanner.
        Ottava` (8va/8vb/15ma/15mb) bracket around `el`, or 0 if none (S10b-8).

        Confirmed against music21 10.5.0 by parsing hand-written MusicXML
        resembling real notation-software output (not just round-tripping
        through music21's own exporter, which gave a misleadingly-already-
        correct result): `music21.converter.parse()` leaves `Note.pitch` at
        the *printed* staff position under an `<octave-shift>` bracket, not
        the sounding pitch. BANA Par. 3.3 requires the opposite -- "the
        words '8va,' '15ma,' 'loco'... are represented by transcribing the
        pitches in the octave in which they are to be performed without
        noting the expressions" -- so the importer has to apply this shift
        itself rather than trusting music21's parsed pitch as-is.
        """
        for sp in el.getSpannerSites(music21.spanner.Ottava):
            return sp.interval().semitones
        return 0

    def _translate_note_stream(self, elements, clef_name: str, dynamic_offsets: dict) -> list:
        """Translate one flat sequence of music21 notes/rests/chords (a whole
        single-voice measure, or one voice of a multi-voice measure) into
        DottedNotes measure items, handling grace notes, chords, and triplet
        tuplet-grouping. Extracted from `translate_measure` (S10b-1) so it
        can run once per InAccord voice as well as for a single-voice
        measure."""
        items: list = []
        current_grace_notes: list[Note] = []
        current_grace_unslashed: list[bool] = []
        tuplet_group = []

        for el in elements:
            # music21.harmony.ChordSymbol is itself a music21.chord.Chord
            # subclass (confirmed against music21 10.5.0) and shows up in
            # `elements` right alongside real notes -- without this check it
            # falls into the `isinstance(el, music21.chord.Chord)` branch
            # below and imports as a real, sounding chord (e.g. a "Cmaj7"
            # lead-sheet symbol becomes a 4-note played chord competing with
            # the actual melody note at that beat) instead of the annotation
            # it is. Lead-sheet chord symbols are collected separately by
            # `_align_chord_symbols` (S10b-3); they carry no rhythmic weight
            # of their own here.
            if isinstance(el, music21.harmony.ChordSymbol):
                continue

            duration = self.map_duration(el.duration)
            ottava_shift = self._ottava_semitone_shift(el)

            if isinstance(el, music21.note.Note):
                note_obj = self.translate_note_obj(el, duration, ottava_shift)
                if el.duration.isGrace:
                    current_grace_notes.append(note_obj)
                    current_grace_unslashed.append(not getattr(el.duration, 'slash', True))
                    continue
                else:
                    if current_grace_notes:
                        note_obj.grace_note = GraceNote(
                            notes=current_grace_notes,
                            long_appoggiatura=any(current_grace_unslashed)
                        )
                        current_grace_notes = []
                        current_grace_unslashed = []
                    dn_item = note_obj
                    
            elif isinstance(el, music21.chord.Chord):
                chord_notes = [self.translate_note_obj(n, duration, ottava_shift) for n in el.notes]
                chord_notes.sort(key=lambda n: n._midi_pitch() if hasattr(n, '_midi_pitch') else 60, reverse=not (clef_name in ("bass", "tenor")))
                
                written_note = chord_notes[0]
                
                if el.offset in dynamic_offsets:
                    written_note.dynamics.append(dynamic_offsets[el.offset])
                    
                for sp in el.getSpannerSites(music21.dynamics.Crescendo):
                    if sp.isFirst(el):
                        written_note.dynamics.append(Dynamic(level=DynamicLevel.CRESCENDO_START))
                    if sp.isLast(el):
                        written_note.dynamics.append(Dynamic(level=DynamicLevel.CRESCENDO_END))
                for sp in el.getSpannerSites(music21.dynamics.Diminuendo):
                    if sp.isFirst(el):
                        written_note.dynamics.append(Dynamic(level=DynamicLevel.DECRESCENDO_START))
                    if sp.isLast(el):
                        written_note.dynamics.append(Dynamic(level=DynamicLevel.DECRESCENDO_END))
                        
                for other in chord_notes[1:]:
                    for dyn in other.dynamics:
                        if dyn not in written_note.dynamics:
                            written_note.dynamics.append(dyn)
                    for art in other.articulations:
                        if art not in written_note.articulations:
                            written_note.articulations.append(art)
                    for o in other.ornaments:
                        if o not in written_note.ornaments:
                            written_note.ornaments.append(o)
                    if other.tie: written_note.tie = True
                    if other.slur_start: written_note.slur_start = True
                    if other.slur_end: written_note.slur_end = True
                    if other.slur_bracket_open: written_note.slur_bracket_open = True
                    if other.slur_bracket_close: written_note.slur_bracket_close = True
                    
                    other.dynamics = []
                    other.articulations = []
                    other.ornaments = []
                    other.tie = False
                    other.slur_start = False
                    other.slur_end = False
                    other.slur_bracket_open = False
                    other.slur_bracket_close = False
                    
                if el.duration.isGrace:
                    current_grace_notes.extend(chord_notes)
                    current_grace_unslashed.extend([not getattr(el.duration, 'slash', True)] * len(chord_notes))
                    continue
                else:
                    if current_grace_notes:
                        written_note.grace_note = GraceNote(
                            notes=current_grace_notes,
                            long_appoggiatura=any(current_grace_unslashed)
                        )
                        current_grace_notes = []
                        current_grace_unslashed = []
                    dn_item = Chord(notes=chord_notes)
                    
            elif isinstance(el, music21.note.Rest):
                is_full = getattr(el, 'fullMeasure', False) is True
                dn_item = Rest(
                    dots=frozenset(),
                    category=None,
                    raw_brl="",
                    duration=duration,
                    is_full_measure=is_full,
                    multi_measure_count=1
                )
                current_grace_notes = []
                current_grace_unslashed = []
            else:
                continue
                
            if not el.duration.isGrace:
                target_note = dn_item.notes[0] if isinstance(dn_item, Chord) else dn_item
                if isinstance(target_note, Note):
                    if el.offset in dynamic_offsets:
                        target_note.dynamics.append(dynamic_offsets[el.offset])
                    for sp in el.getSpannerSites(music21.dynamics.Crescendo):
                        if sp.isFirst(el):
                            target_note.dynamics.append(Dynamic(level=DynamicLevel.CRESCENDO_START))
                        if sp.isLast(el):
                            target_note.dynamics.append(Dynamic(level=DynamicLevel.CRESCENDO_END))
                    for sp in el.getSpannerSites(music21.dynamics.Diminuendo):
                        if sp.isFirst(el):
                            target_note.dynamics.append(Dynamic(level=DynamicLevel.DECRESCENDO_START))
                        if sp.isLast(el):
                            target_note.dynamics.append(Dynamic(level=DynamicLevel.DECRESCENDO_END))
            
            if el.duration.tuplets:
                t = el.duration.tuplets[0]
                if t.numberNotesActual == 3 and t.numberNotesNormal == 2:
                    if t.type == 'start' and tuplet_group:
                        items.append(Tuplet(items=tuplet_group))
                        tuplet_group = []
                    tuplet_group.append(dn_item)
                    if t.type == 'stop':
                        items.append(Tuplet(items=tuplet_group))
                        tuplet_group = []
                else:
                    if tuplet_group:
                        items.append(Tuplet(items=tuplet_group))
                        tuplet_group = []
                    items.append(dn_item)
            else:
                if tuplet_group:
                    items.append(Tuplet(items=tuplet_group))
                    tuplet_group = []
                items.append(dn_item)

        if tuplet_group:
            items.append(Tuplet(items=tuplet_group))

        return items

    def map_duration(self, m21_duration) -> Duration:
        is_triplet = False
        if m21_duration.tuplets:
            t = m21_duration.tuplets[0]
            if t.numberNotesActual == 3 and t.numberNotesNormal == 2:
                is_triplet = True

        m21_type = m21_duration.type
        val = M21_DURATION_MAP.get(m21_type)
        dots = m21_duration.dots

        # MusicXML allows <type> and <duration> to diverge (e.g. a "whole rest"
        # used as a fermata-hold convention that doesn't actually span a whole
        # measure) -- if the declared type/dots don't reproduce the note's
        # actual quarterLength, trust quarterLength instead. Otherwise the
        # mismatched duration survives into export and desyncs the measure.
        actual_ticks = round(m21_duration.quarterLength * TICKS_PER_QUARTER)
        if val is None or Duration(value=val, dots=dots, is_triplet=is_triplet).duration_in_ticks() != actual_ticks:
            val = None
            ql = m21_duration.quarterLength
            if ql >= 8.0: val = 0
            elif ql >= 4.0: val = 1
            elif ql >= 2.0: val = 2
            elif ql >= 1.0: val = 4
            elif ql >= 0.5: val = 8
            elif ql >= 0.25: val = 16
            elif ql >= 0.125: val = 32
            else: val = 64
            dots = 0

        return Duration(value=val, dots=dots, is_triplet=is_triplet)

    def translate_note_obj(self, m21_note, duration: Duration, ottava_shift: int = 0) -> Note:
        pitch = m21_note.pitch.transpose(ottava_shift) if ottava_shift else m21_note.pitch
        note_name = pitch.step
        octave = pitch.octave
        if octave is None:
            octave = 4

        acc = None
        if pitch.accidental is not None:
            m21_acc = pitch.accidental
            acc_type = None
            name = m21_acc.name
            if name == 'sharp': acc_type = AccidentalType.SHARP
            elif name == 'flat': acc_type = AccidentalType.FLAT
            elif name == 'natural': acc_type = AccidentalType.NATURAL
            elif name == 'double-sharp': acc_type = AccidentalType.DOUBLE_SHARP
            elif name == 'double-flat': acc_type = AccidentalType.DOUBLE_FLAT
            else:
                alter = m21_acc.alter
                if alter == 1.0: acc_type = AccidentalType.SHARP
                elif alter == -1.0: acc_type = AccidentalType.FLAT
                elif alter == 0.0: acc_type = AccidentalType.NATURAL
                elif alter == 2.0: acc_type = AccidentalType.DOUBLE_SHARP
                elif alter == -2.0: acc_type = AccidentalType.DOUBLE_FLAT
            if acc_type is not None:
                acc = Accidental(dots=frozenset(), category=None, raw_brl="", type=acc_type)
                
        note = Note(
            dots=frozenset(),
            category=None,
            raw_brl="",
            note_name=note_name,
            octave=octave,
            duration=duration,
            accidental=acc
        )
        
        for art in m21_note.articulations:
            art_type = M21_ARTICULATION_MAP.get(type(art))
            if art_type is not None:
                note.articulations.append(Articulation(type=art_type))
            elif isinstance(art, music21.articulations.BreathMark):
                # BANA Table 22(B) sign (a), "Half breath" (Table 31) --
                # mapping confirmed with the developer, see
                # models/breath_mark.py (S10b-6).
                note.breath_mark = BreathMark(variant=BreathMarkVariant.HALF)
            elif isinstance(art, music21.articulations.Caesura):
                # BANA Table 22(B) sign (b), "Full breath" (Table 31).
                note.breath_mark = BreathMark(variant=BreathMarkVariant.FULL)

        for expr in m21_note.expressions:
            if isinstance(expr, music21.expressions.Trill):
                note.ornaments.append(Ornament(type=OrnamentType.TRILL))
            elif isinstance(expr, music21.expressions.Mordent):
                if expr.direction == 'up':
                    note.ornaments.append(Ornament(type=OrnamentType.UPPER_MORDENT))
                else:
                    note.ornaments.append(Ornament(type=OrnamentType.MORDENT))
            elif isinstance(expr, music21.expressions.InvertedMordent):
                note.ornaments.append(Ornament(type=OrnamentType.UPPER_MORDENT))
            elif isinstance(expr, music21.expressions.Turn):
                note.ornaments.append(Ornament(type=OrnamentType.TURN))
            elif isinstance(expr, music21.expressions.InvertedTurn):
                note.ornaments.append(Ornament(type=OrnamentType.INVERTED_TURN))
            elif isinstance(expr, music21.expressions.Fermata):
                # music21's Fermata.shape is 'normal'/'angled'/'square'
                # (confirmed against its source -- these are the only 3
                # values it models). BANA Table 22(B) doesn't distinguish
                # "over" vs. "under" the staff with a separate sign (unlike
                # music21's separate .type='upright'/'inverted'), so .type
                # is intentionally not consulted here (S10b-4).
                shape = _M21_FERMATA_SHAPE_TO_MODEL.get(expr.shape, FermataShape.NORMAL)
                note.fermata = Fermata(shape=shape)

        m21_fingerings = [art for art in m21_note.articulations if isinstance(art, music21.articulations.Fingering)]
        for m21_f in m21_fingerings:
            val_str = str(m21_f.fingerNumber)
            if '-' in val_str:
                parts = val_str.split('-')
                try:
                    finger = int(parts[0]) if parts[0] else None
                    change_to = int(parts[1]) if parts[1] else None
                    note.fingerings.append(Fingering(dots=frozenset(), category=None, raw_brl="", finger=finger, change_to=change_to))
                except ValueError:
                    pass
            elif '/' in val_str:
                parts = val_str.split('/')
                try:
                    finger = int(parts[0]) if parts[0] else None
                    alternative = int(parts[1]) if parts[1] else None
                    note.fingerings.append(Fingering(dots=frozenset(), category=None, raw_brl="", finger=finger, alternative=alternative))
                except ValueError:
                    pass
            else:
                try:
                    finger = int(val_str)
                    note.fingerings.append(Fingering(dots=frozenset(), category=None, raw_brl="", finger=finger))
                except ValueError:
                    pass
                    
        if m21_note.tie is not None:
            if m21_note.tie.type in ('start', 'continue'):
                note.tie = True
                
        slurs = m21_note.getSpannerSites(music21.spanner.Slur)
        for idx, slur in enumerate(slurs):
            if idx == 0:
                if slur.isFirst(m21_note):
                    note.slur_start = True
                if slur.isLast(m21_note):
                    note.slur_end = True
            else:
                if slur.isFirst(m21_note):
                    note.slur_bracket_open = True
                if slur.isLast(m21_note):
                    note.slur_bracket_close = True
                
        return note


TEMPO_TERMS = frozenset({
    'allegro', 'andante', 'adagio', 'presto', 'moderato',
    'largo', 'vivace', 'lento', 'prestissimo', 'allegretto',
    'andantino', 'grave', 'larghetto', 'allegro moderato',
    'poco allegro', 'con moto', 'a tempo', 'langsam', 'zart', 'ritard.'
})
