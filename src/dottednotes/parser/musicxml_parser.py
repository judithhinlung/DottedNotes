from __future__ import annotations

import os
import warnings
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
from dottednotes.models.duration import TICKS_PER_QUARTER, VALID_DURATIONS
from dottednotes.models.transposition import transposition_from_interval

def load_musicxml(source: str) -> Score:
    """Parse a MusicXML file path or string using music21 and return a DottedNotes Score."""
    if isinstance(source, str) and not source.strip().startswith("<") and not os.path.exists(source):
        raise DottedNotesError(f"File not found: '{source}'")
    try:
        m21_score = music21.converter.parse(source)
    except Exception as e:
        raise DottedNotesError(f"Could not parse MusicXML: {e}")
    try:
        return MusicXMLTranslator().translate(m21_score)
    except DottedNotesError:
        # Already a clean, specific, plain-text error (e.g. an
        # unrecognized chord symbol kind) -- let it through unchanged
        # rather than burying its message inside a generic one.
        raise
    except Exception as e:
        # Any other internal failure during translation (malformed
        # spanner data, an unexpected music21 shape, ...) must still
        # surface as a plain-text message, not a raw Python traceback --
        # this project's own "never a silent failure, never a raw
        # traceback" rule (see exceptions.py) applied to music21's own
        # parsing internals, not just this file's own code.
        raise DottedNotesError(f"Could not import MusicXML: {e}")


M21_DURATION_MAP = {
    'breve': 0,
    'whole': 1,
    'half': 2,
    'quarter': 4,
    'eighth': 8,
    '16th': 16,
    '32nd': 32,
    '64th': 64,
    '128th': 128,  # S10d-9 (BANA Par. 2.1: the eighth-note cell also
                   # represents this smaller value, like the other pairs)
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


def _repeat_bracket_numbers(rb: "music21.spanner.RepeatBracket") -> list[int]:
    """Return a RepeatBracket's ending number(s) as a list of ints (S10b-5).

    Prefers `.numberRange` (music21 10.5.0's own pre-parsed list, e.g.
    [1, 2] for a "1,2" bracket) when present, but that attribute isn't on
    every music21 version -- CI hit `AttributeError: 'RepeatBracket' object
    has no attribute 'numberRange'` on a version where it's missing, even
    though `pyproject.toml` only pins `music21>=8.3.0` with no upper bound.
    Falls back to parsing `.number` directly, which the class docstring
    (and this project's own empirical check) confirms is always normalized
    to a string like "1", "1, 2", or a hyphenated range like "1-3",
    regardless of music21 version.
    """
    number_range = getattr(rb, 'numberRange', None)
    if number_range:
        return list(number_range)

    numbers: list[int] = []
    for part in str(rb.number).split(','):
        part = part.strip()
        if not part:
            continue
        if '-' in part:
            start_str, _, end_str = part.partition('-')
            numbers.extend(range(int(start_str), int(end_str) + 1))
        else:
            numbers.append(int(part))
    return numbers


class MusicXMLTranslator:
    def __init__(self):
        # Tracks each Slur spanner's plain-vs-bracket role (BANA 13.3) by
        # object identity, and which slurs are currently open, across the
        # whole translate() call -- see translate_note_obj's slur handling
        # for why this can't be recomputed independently at each note.
        self._slur_roles: dict[int, str] = {}
        self._open_slur_ids: set[int] = set()

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

            # Forward repeat (BANA Par. 17.1's "double bar followed by
            # dots"). MusicXML/music21 mark a forward repeat on the FIRST
            # measure of the repeated section (leftBarline) -- but this
            # codebase's tested convention (braille_parser.py +
            # tests/test_parser.py::test_forward_repeat_sets_bar_line_type)
            # attaches bar_line_type='forward_repeat' to the LAST measure
            # BEFORE the repeated section instead (Measure.to_lilypond()
            # always renders the bar-line sign at *this* measure's right
            # edge, which BANA/print convention reads as "repeat starts at
            # the next measure"). Apply it one measure back so MusicXML
            # import matches the same, already-tested convention rather
            # than introducing a second, inconsistent one -- found while
            # implementing S10c-3's volta LilyPond output, which depends on
            # correctly locating where a repeated section starts.
            if (
                m21_measure.leftBarline
                and isinstance(m21_measure.leftBarline, music21.bar.Repeat)
                and m21_measure.leftBarline.direction == 'start'
                and staff.measures
                and staff.measures[-1].bar_line_type == 'measure_separator'
            ):
                # The "and ... == 'measure_separator'" guard avoids
                # clobbering a more specific marking the previous measure
                # already has from its own rightBarline (e.g. a combined
                # ":|.|:" end-and-forward-repeat barline) -- a rare case
                # this model has no combined bar_line_type for, so the
                # existing marking wins rather than being silently lost.
                staff.measures[-1].bar_line_type = 'forward_repeat'
            # (If staff.measures is empty, the repeat starts at the very
            # first measure of the piece -- there's no preceding measure to
            # attach a trailing sign to, matching how the braille
            # convention has no sign to write in that case either.)

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
            if keys[0].sharps is None:
                # A non-traditional/microtonal key signature (MusicXML's
                # <key-step>/<key-alter> pairs instead of <fifths>, S10d-7)
                # -- keys[0].sharps is None for this encoding, which used
                # to crash downstream int comparisons (`'<=' not supported
                # between instances of 'int' and 'NoneType'`). Measure's
                # own key_signature field is a plain int (used pervasively
                # for the ordinary sharps/flats case), with no slot for
                # this; fully wiring a non-traditional signature through
                # Measure/Staff display would mean changing that field's
                # type everywhere it's used, a larger, separate change.
                # BANAValidator.KeySignature.non_traditional_pitches/
                # _non_traditional_to_braille() (models/key_signature.py)
                # already implement the BANA Par. 6.5.1 braille
                # construction and are ready for that follow-up -- this
                # fix only prevents the crash, keeping key_val (and
                # therefore the visible key-signature marker) unchanged
                # from whatever it was before this measure. Any note whose
                # correct pitch actually depends on one of this signature's
                # alterations (rather than carrying its own explicit
                # MusicXML accidental) will import at its plain, unaltered
                # pitch -- flagged here rather than silently risked.
                where = f" in measure {m21_measure.number}"
                warnings.warn(
                    f"Non-traditional or microtonal key signature{where} is "
                    "not yet transcribed (BANA Par. 6.5.1's construction is "
                    "implemented in the model but not wired into staff/measure "
                    "display -- see S10d-7). The visible key-signature marker "
                    "is omitted; notes relying on it without their own explicit "
                    "MusicXML accidental may import at the wrong pitch.",
                    stacklevel=2,
                )
            else:
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
        # NOTE: a leftBarline repeat-start is deliberately NOT handled here --
        # see translate_part(), which retroactively attaches
        # bar_line_type='forward_repeat' to the *previous* measure instead
        # (bug found and fixed while implementing S10c-3's volta LilyPond
        # output; see that commit for the full explanation).
        measure.bar_line_type = bar_line

        # First/second (or later) endings (BANA Chapter 17, Par. 17.1.1,
        # S10b-5). A measure spanned by a RepeatBracket exposes it via
        # getSpannerSites; _repeat_bracket_numbers() below reads the ending
        # number(s) off it without depending on the `numberRange` attribute,
        # which isn't present on every music21 version (confirmed missing
        # on at least one CI-resolved version -- AttributeError there,
        # despite being present and correct in this project's dev
        # environment, music21 10.5.0).
        repeat_brackets = m21_measure.getSpannerSites(music21.spanner.RepeatBracket)
        if repeat_brackets:
            measure.ending_numbers = _repeat_bracket_numbers(repeat_brackets[0])


        # Text markings & Metronome marks
        for t in m21_measure.getElementsByClass(music21.expressions.TextExpression):
            text_val = t.content or ""
            is_tempo = text_val.lower().strip() in TEMPO_TERMS
            tm_type = TextMarkingType.TEMPO if is_tempo else TextMarkingType.EXPRESSION
            measure.text_markings.append(TextMarking(text=text_val, type=tm_type))
            
        for m in m21_measure.getElementsByClass(music21.tempo.MetronomeMark):
            # A bare <sound tempo="..."/> (playback-only, e.g. no visible
            # <metronome>/text in the print) surfaces in music21 as a
            # MetronomeMark with both .text and .number None -- only
            # .numberSounding (the MIDI-playback BPM) is set. Previously
            # `m.text or f"{m.number}"` still produced the literal string
            # "None" for this case (Python stringifying the None fallback),
            # transcribing a spurious tempo marking that was never actually
            # printed. Skip creating a marking at all when there is no
            # genuine printed text or number to show.
            if m.text:
                text_val = m.text
            elif m.number is not None:
                text_val = str(m.number)
            else:
                continue
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
                
        # A <direction>/<harmony> element sitting between the first note of
        # a chord and its <chord/>-tagged continuation notes (BANA has no
        # bearing here -- this is a pure MusicXML/music21 parsing quirk)
        # makes music21 fail to group the continuation notes into the
        # anchor's Chord object: each continuation surfaces as its own
        # separate single-note Chord at its own (wrong, sequentially
        # advanced) offset instead of stacking on the anchor's offset,
        # inflating the measure's resolved beat count (S10d-5). Repair this
        # before extracting notesAndRests, on both the plain-measure and
        # each Voice sub-stream, so _translate_note_stream never has to
        # know this happened.
        self._merge_interrupted_chord_continuations(m21_measure)

        # Parse notes and rests. A measure whose content lives in nested
        # music21 Voice streams (MusicXML's <voice> numbering -- the normal
        # way a single staff carries two independent rhythmic lines, e.g.
        # piano writing) is NOT reached by `m21_measure.notesAndRests`: that
        # call does not descend into Voice sub-streams and would silently
        # return an empty measure (confirmed against music21 10.5.0). Each
        # voice is translated separately and wrapped in an InAccord (BANA
        # Chapter 11) instead (S10b-1).
        voices = list(m21_measure.voices)
        for voice in voices:
            self._merge_interrupted_chord_continuations(voice)
        chord_track_entries: list = []
        if voices:
            if self._voices_span_measure_in_lockstep(voices):
                voice_items = [
                    self._translate_note_stream(voice.notesAndRests, clef_name, dynamic_offsets)
                    for voice in voices
                ]
                ordered = self._order_voices_by_bana_convention(voice_items, clef_name)
                measure.add_note(InAccord(parts=ordered, in_accord_type='full_measure'))
            else:
                # A <backup> that does not fully rewind to the measure start
                # (BANA Par. 11.1.2, S10d-6): voices do not all cover the
                # same time range, so a single full-measure in-accord would
                # misrepresent the rhythm (every voice appearing to start
                # together). Divide the measure into temporal sections
                # instead -- each section either a single voice's notes
                # (added directly) or a part-measure in-accord of the
                # voices actually overlapping in that section.
                for section_parts in self._split_voices_into_sections(voices, clef_name, dynamic_offsets):
                    if len(section_parts) == 1:
                        for item in section_parts[0]:
                            measure.add_note(item)
                    else:
                        ordered = self._order_voices_by_bana_convention(section_parts, clef_name)
                        measure.add_note(InAccord(parts=ordered, in_accord_type='part_measure'))
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

        self._validate_measure_beat_count(measure)
        return measure, chord_track_entries

    def _validate_measure_beat_count(self, measure: Measure) -> None:
        """Warn (plain text) if a measure's resolved note/rest duration
        doesn't match its time signature -- mirrors braille_parser.py's
        identical check on the BRF side (S5-8). MusicXML import had no
        equivalent signal before this: a genuinely short/long source
        measure (e.g. an OMR misread that only captured part of a
        measure) converted silently, with the discrepancy only surfacing
        much later as LilyPond bar-check failures possibly measures away
        from the real defect, with no indication of which measure was
        actually at fault.
        """
        num, den = measure.time_signature
        expected_ticks = round(num * (4 / den) * TICKS_PER_QUARTER)
        actual_ticks = measure.total_ticks()
        if actual_ticks != expected_ticks:
            warnings.warn(
                f"Measure {measure.number}: expected "
                f"{expected_ticks / TICKS_PER_QUARTER} beats but counted "
                f"{actual_ticks / TICKS_PER_QUARTER}. Check the source "
                "MusicXML for a missing/extra note or rest.",
                stacklevel=2,
            )

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
            (self.map_duration(el.duration, measure_number=el.measureNumber), chord_for_index.get(i))
            for i, el in enumerate(melody)
        ]

    _CHORD_KIND_TO_MODEL_FIELDS: dict[str, dict] = {
        'major': {},
        'minor': {'is_minor': True},
        'augmented': {'is_augmented': True},
        'augmented-seventh': {'is_augmented': True, 'extensions': [(7, None)]},
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

    def _voices_span_measure_in_lockstep(self, voices) -> bool:
        """True when every voice's notesAndRests covers the exact same
        [start, end) time range -- the normal case a plain full-measure
        in-accord (BANA 11.1.1) is for. A <backup> that does not fully
        rewind (S10d-6) breaks this: the affected voice starts later than
        the others, so its range differs and this returns False, routing
        the measure through `_split_voices_into_sections` instead."""
        ranges = set()
        for voice in voices:
            elements = list(voice.notesAndRests)
            if not elements:
                continue
            start = elements[0].offset
            end = elements[-1].offset + elements[-1].duration.quarterLength
            ranges.add((start, end))
        return len(ranges) <= 1

    def _split_voices_into_sections(self, voices, clef_name: str, dynamic_offsets: dict) -> list[list[list]]:
        """Partition a measure's voices into temporal sections per BANA
        11.1.2, for the case where they do not all cover the same time
        range (S10d-6). Returns a list of sections in time order, each
        section a list of "parts" -- one already-translated DN item list
        per voice active during that section (not yet BANA-ordered; the
        caller orders each section's parts itself).

        Only splits sections at existing note/rest boundaries (the offsets
        already present in the voices) -- a note that straddles a section
        boundary (e.g. a half note starting before an overlap begins and
        ending after it ends) is not split into tied fragments; this is a
        known limitation, not attempted here.
        """
        voice_data = []
        for voice in voices:
            elements = list(voice.notesAndRests)
            if not elements:
                voice_data.append((0.0, 0.0, []))
                continue
            start = elements[0].offset
            end = elements[-1].offset + elements[-1].duration.quarterLength
            voice_data.append((start, end, elements))

        breakpoints = sorted({t for start, end, _ in voice_data for t in (start, end)})

        raw_sections: list[tuple[list[int], float, float]] = []
        for t0, t1 in zip(breakpoints, breakpoints[1:]):
            active = [
                idx for idx, (start, end, elements) in enumerate(voice_data)
                if elements and start <= t0 and end >= t1
            ]
            if not active:
                continue
            if raw_sections and raw_sections[-1][0] == active:
                raw_sections[-1] = (active, raw_sections[-1][1], t1)
            else:
                raw_sections.append((active, t0, t1))

        result: list[list[list]] = []
        for active, t0, t1 in raw_sections:
            parts = []
            for idx in active:
                _, _, elements = voice_data[idx]
                sliced = [el for el in elements if t0 <= el.offset < t1]
                parts.append(self._translate_note_stream(sliced, clef_name, dynamic_offsets))
            result.append(parts)
        return result

    def _ottava_octave_shift(self, el) -> int:
        """Return the signed number of octaves to shift `el`'s pitch by, from
        an active `music21.spanner.Ottava` (8va/8vb/15ma/15mb) bracket around
        it, or 0 if none (S10b-8).

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

        Returns a plain octave count (not a semitone count fed to
        `Pitch.transpose()`): every Ottava interval is an exact multiple of
        a perfect octave, and `Pitch.transpose(<int semitones>)` builds a
        generic chromatic interval that can enharmonically respell the
        pitch (e.g. `Pitch("A-5").transpose(12)` gives `G#6`, not `A-6`).
        Shifting `Pitch.octave` directly instead preserves the letter name
        and accidental exactly as notated, which is what BANA 3.3 needs.
        Confirmed against a real Debussy "Mandoline" MusicXML sample (from
        musicxml.com's example set, measure 10): an Ab5/C6/Ab6 chord under
        an 8va bracket must import as Ab6/C7/Ab7, not G#6/C7/G#7.
        """
        for sp in el.getSpannerSites(music21.spanner.Ottava):
            return sp.interval().semitones // 12
        return 0

    def _merge_interrupted_chord_continuations(self, stream_obj) -> None:
        """Repair chord notes that a <direction>/<harmony> element (or any
        other non-note element) split away from their chord (S10d-5).

        Under normal parsing, every <chord/>-tagged continuation note gets
        folded into one music21.chord.Chord together with its anchor, so a
        single-note Chord object never appears in a measure's notesAndRests
        -- a real one-note "chord" is just a Note. Confirmed against the
        MusicXML Test Suite's own 21f-Chord-ElementInBetween.xml: an
        intervening <direction> makes music21 fail that grouping, so each
        continuation note surfaces as its own single-note Chord at its own
        (wrongly, sequentially advanced) offset instead of stacking on the
        anchor. A single-note Chord is therefore an unambiguous signal that
        this happened, regardless of what its (corrupted) offset says.

        Mutates `stream_obj` (a Measure or Voice) in place: removes each
        such orphaned continuation and the note/chord anchor it belongs
        with, then re-inserts one merged Chord at the anchor's original
        offset, so measureNumber/offset/getSpannerSites all resolve
        normally afterward (this only works by going through
        stream.remove()/insert() -- a freshly constructed, unattached
        Chord's measureNumber is not derivable at all).
        """
        elements = list(stream_obj.notesAndRests)
        groups: list[list] = []
        for el in elements:
            is_orphaned_continuation = (
                isinstance(el, music21.chord.Chord)
                and len(el.notes) == 1
                and not el.duration.isGrace
                and groups
                and not (len(groups[-1]) == 1 and isinstance(groups[-1][0], music21.note.Rest))
                and not groups[-1][-1].duration.isGrace
            )
            if is_orphaned_continuation:
                groups[-1].append(el)
            else:
                groups.append([el])

        for group in groups:
            if len(group) < 2:
                continue
            anchor = group[0]
            anchor_offset = anchor.offset
            all_notes = list(anchor.notes) if isinstance(anchor, music21.chord.Chord) else [anchor]
            for continuation in group[1:]:
                all_notes.extend(continuation.notes)
            for el in group:
                stream_obj.remove(el)
            merged = music21.chord.Chord(all_notes)
            stream_obj.insert(anchor_offset, merged)

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
        tuplet_group_ratio: tuple[int, int] = (3, 2)

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

            duration = self.map_duration(el.duration, measure_number=el.measureNumber)
            ottava_shift = self._ottava_octave_shift(el)

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
                # Any ratio is grouped (S10d-4, BANA 8.4/8.5) -- not just
                # 3-in-the-time-of-2. tuplet_group_ratio tracks the ratio
                # of whatever group is currently open, taken from its
                # first note, so Tuplet(...) below gets the group's real
                # ratio instead of always defaulting to (3, 2).
                if t.type == 'start' and tuplet_group:
                    items.append(Tuplet(items=tuplet_group, ratio=tuplet_group_ratio))
                    tuplet_group = []
                if not tuplet_group:
                    tuplet_group_ratio = (t.numberNotesActual, t.numberNotesNormal)
                tuplet_group.append(dn_item)
                if t.type == 'stop':
                    items.append(Tuplet(items=tuplet_group, ratio=tuplet_group_ratio))
                    tuplet_group = []
            else:
                if tuplet_group:
                    items.append(Tuplet(items=tuplet_group, ratio=tuplet_group_ratio))
                    tuplet_group = []
                items.append(dn_item)

        if tuplet_group:
            items.append(Tuplet(items=tuplet_group, ratio=tuplet_group_ratio))

        return items

    def map_duration(self, m21_duration, measure_number: "int | None" = None) -> Duration:
        # Any tuplet ratio is supported (S10d-4, BANA 8.4/8.5), not just
        # 3-in-the-time-of-2: is_triplet marks the classic BANA 8.4
        # single-cell case (exactly 3 notes, regardless of what value they
        # replace -- confirmed real fixture data never pairs actual==3 with
        # a normal other than 2, but Par. 8.4's own wording ties the sign
        # to the note count, not the ratio's denominator); tuplet_ratio
        # carries the exact (actual, normal) pair so duration_in_ticks()
        # can compute an exact scaled tick count for ANY ratio instead of
        # only recognizing 2/3.
        is_triplet = False
        tuplet_ratio = None
        if m21_duration.tuplets:
            t = m21_duration.tuplets[0]
            is_triplet = (t.numberNotesActual == 3)
            tuplet_ratio = (t.numberNotesActual, t.numberNotesNormal)

        m21_type = m21_duration.type
        val = M21_DURATION_MAP.get(m21_type)
        dots = m21_duration.dots

        # MusicXML allows <type>/<dots> and <duration> to diverge (e.g. a
        # "whole rest" used as a fermata-hold convention that doesn't
        # actually span a whole measure, or a note whose <duration> implies
        # a dotted value with no <dot> tag present) -- if the declared
        # type/dots don't reproduce the note's actual quarterLength, trust
        # quarterLength instead. Otherwise the mismatched duration survives
        # into export and desyncs the measure.
        actual_ticks = round(m21_duration.quarterLength * TICKS_PER_QUARTER)
        if val is None or Duration(value=val, dots=dots, is_triplet=is_triplet, tuplet_ratio=tuplet_ratio).duration_in_ticks() != actual_ticks:
            # Search for an exact (value, dots) match against the note's
            # true duration before falling back to an imprecise
            # nearest-power-of-2 guess -- the previous code always reset
            # dots to 0 here, so a genuinely dotted duration (e.g. exactly
            # 3 quarter-beats) silently lost its dot and came out a full
            # beat short, with no warning.
            match = None
            for candidate_val in sorted(VALID_DURATIONS, reverse=True):
                for candidate_dots in (0, 1, 2):
                    candidate = Duration(value=candidate_val, dots=candidate_dots, is_triplet=is_triplet, tuplet_ratio=tuplet_ratio)
                    if candidate.duration_in_ticks() == actual_ticks:
                        match = candidate
                        break
                if match is not None:
                    break
            if match is not None:
                return match

            if tuplet_ratio is not None:
                where = f" in measure {measure_number}" if measure_number is not None else ""
                warnings.warn(
                    f"Could not find an exact written value for tuplet ratio "
                    f"{tuplet_ratio[0]}:{tuplet_ratio[1]}{where}. Duration "
                    "approximated; the surrounding measure(s) may not add up "
                    "to the time signature.",
                    stacklevel=2,
                )

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

        return Duration(value=val, dots=dots, is_triplet=is_triplet, tuplet_ratio=tuplet_ratio)

    def translate_note_obj(self, m21_note, duration: Duration, ottava_shift: int = 0) -> Note:
        pitch = m21_note.pitch
        note_name = pitch.step
        octave = pitch.octave
        if octave is None:
            octave = 4
        octave += ottava_shift

        # Note.accidental must record the note's actual sounding pitch
        # alteration whenever it's a REAL deviation from the active key
        # signature -- never gated on music21's own `displayStatus`
        # bookkeeping, which also goes False for a tied-continuation note
        # (and other "implied, not restated" cases) that still sounds the
        # altered pitch. Dropping it in that case previously produced a
        # wrong LilyPond pitch letter (e.g. "b" instead of "bes"), silently
        # breaking ties whose pitch no longer matched.
        #
        # The correct suppression signal is instead "does this alteration
        # match what the active key signature already implies for this
        # pitch step" -- if so, LilyPond/braille apply the key signature
        # automatically and no note-level accidental should be recorded at
        # all (this is also what keeps a real orchestral score's accidental
        # count sane: music21 attaches internal pitch-spelling bookkeeping
        # to nearly every note in a keyed piece, not just genuinely altered
        # ones). Whether a genuinely-different, still-present accidental
        # is merely *redundant to restate* (e.g. already shown earlier in
        # the same measure) is a separate, already-implemented concern
        # (BANAValidator's S9c-redundant-accidental rule, surfaced via
        # --report), not something to pre-decide by omitting it here.
        acc = None
        m21_acc = None
        if pitch.accidental is not None:
            key_sig = m21_note.getContextByClass(music21.key.KeySignature)
            key_accidental = key_sig.accidentalByStep(pitch.step) if key_sig else None
            key_alter = key_accidental.alter if key_accidental else 0.0
            if pitch.accidental.alter != key_alter:
                m21_acc = pitch.accidental
        if m21_acc is not None:
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
                
        # A slur's plain-vs-bracket role (BANA 13.3: the first of two+
        # simultaneously overlapping slurs stays a plain slur, any
        # additional one(s) get bracket treatment) must be decided ONCE per
        # slur and remembered by object identity -- `getSpannerSites`
        # returns the same Slur object at both its start and end notes, but
        # its position in that per-note list isn't guaranteed consistent
        # between the two, so deciding "plain vs bracket" independently at
        # each note (the previous approach) could assign a slur one role at
        # its start and the other at its end, producing mismatched
        # LilyPond slur signs ("already have slur"/"cannot end slur").
        # Endings are resolved before openings on this note so a note that
        # simultaneously closes one phrase and opens the next isn't
        # mistaken for a real overlap.
        slurs = m21_note.getSpannerSites(music21.spanner.Slur)
        for slur in slurs:
            if slur.isLast(m21_note):
                role = self._slur_roles.get(id(slur), "primary")
                if role == "primary":
                    note.slur_end = True
                else:
                    note.slur_bracket_close = True
                self._open_slur_ids.discard(id(slur))
        for slur in slurs:
            if slur.isFirst(m21_note):
                role = "bracket" if self._open_slur_ids else "primary"
                self._slur_roles[id(slur)] = role
                self._open_slur_ids.add(id(slur))
                if role == "primary":
                    note.slur_start = True
                else:
                    note.slur_bracket_open = True

        return note


TEMPO_TERMS = frozenset({
    'allegro', 'andante', 'adagio', 'presto', 'moderato',
    'largo', 'vivace', 'lento', 'prestissimo', 'allegretto',
    'andantino', 'grave', 'larghetto', 'allegro moderato',
    'poco allegro', 'con moto', 'a tempo', 'langsam', 'zart', 'ritard.'
})
