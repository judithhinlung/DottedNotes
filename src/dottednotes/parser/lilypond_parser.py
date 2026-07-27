import re
from typing import Optional, Union
from dottednotes.models.score import Score
from dottednotes.models.orchestra_score import OrchestraScore
from dottednotes.models.staff import Staff
from dottednotes.models.measure import Measure
from dottednotes.models.note import Note, Rest
from dottednotes.models.chord import Chord
from dottednotes.models.in_accord import InAccord
from dottednotes.models.duration import Duration
from dottednotes.models.key_signature import KeySignature
from dottednotes.models.time_signature import TimeSignature
from dottednotes.models.clef import Clef, ClefType
from dottednotes.models.text_marking import TextMarking, TextMarkingType
from dottednotes.models.accidental import Accidental, AccidentalType
from dottednotes.models.dynamic import Dynamic, DynamicLevel
from dottednotes.models.articulation import Articulation, ArticulationType
from dottednotes.models.ornament import Ornament, OrnamentType, GraceNote
from dottednotes.models.tuplet import Tuplet

_ACCIDENTAL_MAP = {
    'is': AccidentalType.SHARP,
    'es': AccidentalType.FLAT,
    'isis': AccidentalType.DOUBLE_SHARP,
    'eses': AccidentalType.DOUBLE_FLAT,
}

_DYNAMIC_MAP = {
    'ppp': DynamicLevel.PPP,
    'pp': DynamicLevel.PP,
    'p': DynamicLevel.P,
    'mp': DynamicLevel.MP,
    'mf': DynamicLevel.MF,
    'f': DynamicLevel.F,
    'ff': DynamicLevel.FF,
    'fff': DynamicLevel.FFF,
    'sf': DynamicLevel.SF,
    'sfz': DynamicLevel.SFZ,
    'fp': DynamicLevel.FP,
    'cresc': DynamicLevel.CRESCENDO_START,
    'decresc': DynamicLevel.DECRESCENDO_START,
    'cr': DynamicLevel.CRESCENDO_START,
    'decr': DynamicLevel.DECRESCENDO_START,
}

_ARTICULATION_MAP = {
    '-.': ArticulationType.STACCATO,
    'staccato': ArticulationType.STACCATO,
    '-^': ArticulationType.ACCENT,
    'accent': ArticulationType.ACCENT,
    '-_': ArticulationType.TENUTO,
    'tenuto': ArticulationType.TENUTO,
    '-+': ArticulationType.STOPPED,
    'stopped': ArticulationType.STOPPED,
    'open': ArticulationType.OPEN,
}


def tokenize_lilypond(ly_text: str) -> list[str]:
    # Strip block comments %{ ... %}
    ly_text = re.sub(r'%\{.*?%\}', '', ly_text, flags=re.DOTALL)
    # Strip single line comments % ...
    ly_text = re.sub(r'%.*?\n', '\n', ly_text)

    # Tokenize
    token_re = re.compile(
        r'\\\(|\\\)|<<|>>|\\\\|'
        r'\-\.|\-\!|\-_|\-\-|\-\>|\-\^|\\<|\\>|\\!|\*|'
        r'[{}[\]<>|~()=]|'
        r'\\[a-zA-Z]+|'
        r'"(?:[^"\\]|\\.)*"|'
        r'[a-zA-Z_][a-zA-Z_-]*\'*\,*|'
        r'\.+|'
        r'[0-9]+/[0-9]+|'
        r'[0-9]+'
    )
    return token_re.findall(ly_text)


def parse_pitch_token(token: str) -> Optional[tuple[str, str, str]]:
    match = re.match(r'^([a-g])(is|es|isis|eses)?([\'\,,]*)$', token, re.IGNORECASE)
    if match:
        return match.group(1).upper(), match.group(2) or "", match.group(3)
    return None


def get_absolute_pitch(note_name: str, octave_marks: str, prev_note: tuple[str, int]) -> tuple[str, int]:
    DIATONIC = {'C': 0, 'D': 1, 'E': 2, 'F': 3, 'G': 4, 'A': 5, 'B': 6}
    prev_idx = DIATONIC[prev_note[0].upper()]
    curr_idx = DIATONIC[note_name.upper()]

    diff = (curr_idx - prev_idx) % 7
    if diff > 3:
        diff -= 7

    base_octave = prev_note[1] + (prev_idx + diff) // 7
    octave = base_octave + octave_marks.count("'") - octave_marks.count(",")
    return note_name.upper(), octave


def _skip_balanced_block(tokens: list[str], start_idx: int) -> int:
    """Return the index just past the closing brace of a `{...}` block that
    starts at tokens[start_idx]. Also balances `<<`/`>>` against `{`/`}`
    using one shared depth counter, since real generated LilyPond never
    interleaves them in a way that would make that ambiguous.

    If tokens[start_idx] is not '{', returns start_idx unchanged so the
    caller can decide how to handle a bare/braceless value.

    String tokens are already emitted as a single atomic token by
    tokenize_lilypond's `"(?:[^"\\]|\\.)*"` alternative, so a `{`/`}`
    character embedded in a string literal is never seen here as a
    separate token -- no string-aware skipping is needed.
    """
    i = start_idx
    if i >= len(tokens) or tokens[i] != '{':
        return start_idx
    depth = 1
    i += 1
    while i < len(tokens) and depth > 0:
        if tokens[i] in ('{', '<<'):
            depth += 1
        elif tokens[i] in ('}', '>>'):
            depth -= 1
        i += 1
    return i


class LilypondParser:
    def __init__(self):
        self.variables = {}
        self.score = None
        self._is_piano_staff = False

    def parse(self, ly_text: str) -> Score:
        tokens = tokenize_lilypond(ly_text)

        # Determine if it is an orchestra score
        # Simple check: if there are variable defs like fluteMusic = ... and violinMusic = ...
        # or if \score contains multiple \new Staff
        is_orchestra = False
        if 'StaffGroup' in ly_text or 'PianoStaff' in ly_text:
            is_orchestra = True
        # A PianoStaff (as opposed to a genuine multi-instrument StaffGroup)
        # is tagged OrchestraScore only so its two staves stay paired instead
        # of falling into the solo-score path (see braille_renderer.py's own
        # comment on this) -- it still needs to round-trip back through the
        # *piano* braille layout, not the ensemble one, which
        # BrailleRenderer.render() decides based on staff *names* looking
        # like a keyboard instrument. Real DottedNotes-generated PianoStaff
        # output has no per-staff instrumentName (see Score.to_lilypond()),
        # so _parse_score_block defaults unnamed staves here to "Piano right
        # hand"/"Piano left hand" instead of the generic "Melody" fallback.
        self._is_piano_staff = 'PianoStaff' in ly_text and 'StaffGroup' not in ly_text

        self.score = OrchestraScore() if is_orchestra else Score()
        self.variables = {}

        self._parse_top_level(tokens)

        if not self.score.staves:
            relative_indices = [idx for idx, t in enumerate(tokens) if t == '\\relative']
            if relative_indices:
                r_idx = relative_indices[0]
                brace_count = 0
                music_tokens = []
                for t in tokens[r_idx:]:
                    if t == '{':
                        brace_count += 1
                    elif t == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            music_tokens.append(t)
                            break
                    music_tokens.append(t)
                staff = self._parse_music_tokens(music_tokens)
                self.score.add_staff(staff)
            else:
                # Clean tokens of version/header blocks
                clean = [t for t in tokens if t not in ('\\version', '\\header')]
                staff = self._parse_music_tokens(clean)
                self.score.add_staff(staff)

        return self.score

    def _parse_top_level(self, tokens: list[str]) -> None:
        i = 0
        while i < len(tokens):
            t = tokens[i]
            if t == '\\header':
                i = self._parse_header(tokens, i + 1)
            elif t in ('\\paper', '\\layout', '\\midi'):
                i = _skip_balanced_block(tokens, i + 1)
            elif i + 1 < len(tokens) and tokens[i+1] == '=':
                var_name = tokens[i]
                i = self._parse_variable_def(tokens, i + 2, var_name)
            elif t == '\\score':
                i = self._parse_score_block(tokens, i + 1)
            else:
                i += 1

    def _parse_header(self, tokens: list[str], start_idx: int) -> int:
        i = start_idx
        if i < len(tokens) and tokens[i] == '{':
            i += 1
        
        brace_count = 1
        while i < len(tokens) and brace_count > 0:
            t = tokens[i]
            if t == '{':
                brace_count += 1
                i += 1
            elif t == '}':
                brace_count -= 1
                i += 1
            elif i + 2 < len(tokens) and tokens[i+1] == '=':
                key = tokens[i]
                val = tokens[i+2].strip('"')
                if key == 'title':
                    self.score.title = val
                elif key == 'composer':
                    self.score.composer = val
                elif key == 'copyright':
                    self.score.copyright = val
                elif key == 'tagline':
                    self.score.tagline = val
                i += 3
            else:
                i += 1
        return i

    def _parse_variable_def(self, tokens: list[str], start_idx: int, var_name: str) -> int:
        i = start_idx
        while i < len(tokens) and tokens[i] != '{':
            i += 1
        end_idx = _skip_balanced_block(tokens, i)
        self.variables[var_name] = tokens[start_idx:end_idx]
        return end_idx

    def _parse_score_block(self, tokens: list[str], start_idx: int) -> int:
        i = start_idx
        if i < len(tokens) and tokens[i] == '{':
            i += 1
        
        brace_count = 1
        score_tokens = []
        while i < len(tokens) and brace_count > 0:
            t = tokens[i]
            if t == '{':
                brace_count += 1
            elif t == '}':
                brace_count -= 1
                if brace_count == 0:
                    i += 1
                    break
            score_tokens.append(t)
            i += 1

        # Now parse the contents of the score block
        # Look for \new Staff, or if none, look for inline relative block
        new_staff_indices = [idx for idx, t in enumerate(score_tokens) if t == '\\new' and idx + 1 < len(score_tokens) and score_tokens[idx+1] == 'Staff']
        
        if new_staff_indices:
            # Multi-staff
            for s_idx, idx in enumerate(new_staff_indices):
                # The tokens for this staff block go from idx until the next \new Staff or end
                end_idx = new_staff_indices[s_idx + 1] if s_idx + 1 < len(new_staff_indices) else len(score_tokens)
                staff_tokens = score_tokens[idx:end_idx]
                
                # Find instrumentName
                staff_name = None
                for j in range(len(staff_tokens)):
                    if staff_tokens[j] == 'instrumentName' and j + 2 < len(staff_tokens) and staff_tokens[j+1] == '=':
                        staff_name = staff_tokens[j+2].strip('"')
                        break
                    elif staff_tokens[j] == '\\set' and j + 3 < len(staff_tokens) and staff_tokens[j+1] == 'Staff.instrumentName' and staff_tokens[j+2] == '=':
                        staff_name = staff_tokens[j+3].strip('"')
                        break

                if staff_name is None and self._is_piano_staff:
                    # Real DottedNotes PianoStaff output has no
                    # instrumentName (see comment on _is_piano_staff) -- BANA
                    # convention writes the right hand first/above, left
                    # hand second/below, matching \new Staff = "upper" then
                    # "lower" here. These specific names (not just "Piano")
                    # are what BrailleRenderer.render()'s is_piano detection
                    # (get_instrument_family) recognizes via "hand".
                    staff_name = "Piano right hand" if s_idx == 0 else "Piano left hand"


                # Look for a variable reference
                music_tokens = []
                for st in staff_tokens:
                    if st.startswith('\\') and st[1:] in self.variables:
                        music_tokens = self.variables[st[1:]]
                        break
                        
                # If no variable reference, we extract the inline block (e.g. within braces)
                if not music_tokens:
                    if '\\relative' in staff_tokens:
                        r_idx = staff_tokens.index('\\relative')
                        music_tokens = staff_tokens[r_idx:]
                    else:
                        brace_indices = [k for k, t in enumerate(staff_tokens) if t == '{']
                        if len(brace_indices) >= 2:
                            music_tokens = staff_tokens[brace_indices[1]:]
                        elif len(brace_indices) == 1:
                            music_tokens = staff_tokens[brace_indices[0]:]
                        else:
                            music_tokens = staff_tokens
                            
                staff = self._parse_music_tokens(music_tokens, staff_name=staff_name)
                self.score.add_staff(staff)
        else:
            # Single staff
            staff = self._parse_music_tokens(score_tokens)
            self.score.add_staff(staff)

        return i

    def _parse_music_tokens(self, tokens: list[str], staff_name: Optional[str] = None) -> Staff:
        staff = Staff(name=staff_name or "Melody")
        
        i = 0
        is_relative = False
        relative_base = ('C', 4)  # default C4
        current_duration = Duration(value=4, dots=0)
        
        measure_number = 1
        current_measure = Measure(number=1)
        
        # Parse list of tokens
        while i < len(tokens):
            t = tokens[i]
            
            if t == '\\relative':
                is_relative = True
                # Next token is the reference pitch, e.g. c'
                if i + 1 < len(tokens):
                    ref_pitch = tokens[i+1]
                    pitch_info = parse_pitch_token(ref_pitch)
                    if pitch_info:
                        name, acc, oct_marks = pitch_info
                        octave = 3 + oct_marks.count("'") - oct_marks.count(",")
                        relative_base = (name, octave)
                    i += 2
                else:
                    i += 1
                continue
                
            elif t == '\\time':
                if i + 1 < len(tokens):
                    ts_str = tokens[i+1]
                    match = re.match(r'^([0-9]+)/([0-9]+)$', ts_str)
                    if match:
                        num, den = int(match.group(1)), int(match.group(2))
                        staff.time_signature = TimeSignature(
                            dots=frozenset(), category=None, raw_brl="", numerator=num, denominator=den
                        )
                        current_measure.time_signature = (num, den)
                    i += 2
                else:
                    i += 1
                continue
                
            elif t == '\\key':
                if i + 2 < len(tokens):
                    key_note = tokens[i+1]
                    key_mode_token = tokens[i+2].lower()
                    mode = "minor" if key_mode_token == "\\minor" else "major"
                    
                    key_map_major = {
                        'c': 0,
                        'g': 1, 'd': 2, 'a': 3, 'e': 4, 'b': 5, 'fis': 6, 'cis': 7,
                        'f': -1, 'bes': -2, 'ees': -3, 'aes': -4, 'des': -5, 'ges': -6, 'ces': -7
                    }
                    key_map_minor = {
                        'a': 0,
                        'e': 1, 'b': 2, 'fis': 3, 'cis': 4, 'gis': 5, 'dis': 6, 'ais': 7,
                        'd': -1, 'g': -2, 'c': -3, 'f': -4, 'bes': -5, 'ees': -6, 'aes': -7
                    }
                    
                    if mode == "minor":
                        sharps_or_flats = key_map_minor.get(key_note.lower(), 0)
                    else:
                        sharps_or_flats = key_map_major.get(key_note.lower(), 0)
                        
                    staff.key_signature = KeySignature(dots=frozenset(), category=None, raw_brl="", sharps_or_flats=sharps_or_flats, mode=mode)
                    current_measure.key_signature = sharps_or_flats
                    i += 3
                else:
                    i += 1
                continue
                
            elif t == '\\clef':
                if i + 1 < len(tokens):
                    clef_name = tokens[i+1].upper()
                    clef_type = ClefType.TREBLE
                    if clef_name == 'BASS':
                        clef_type = ClefType.BASS
                    elif clef_name == 'ALTO':
                        clef_type = ClefType.ALTO
                    elif clef_name == 'TENOR':
                        clef_type = ClefType.TENOR
                    staff.clef = Clef(dots=frozenset(), category=None, raw_brl="", clef_type=clef_type)
                    current_measure.clef = clef_name.lower()
                    i += 2
                else:
                    i += 1
                continue
                
            elif t == '\\tempo':
                if i + 1 < len(tokens):
                    tempo_text = tokens[i+1].strip('"')
                    staff.tempo = TextMarking(text=tempo_text, type=TextMarkingType.TEMPO)
                    i += 2
                else:
                    i += 1
                continue

            elif t == '\\addlyrics':
                # Parse lyrics block
                if i + 1 < len(tokens) and tokens[i+1] == '{':
                    i += 2
                    lyric_words = []
                    while i < len(tokens) and tokens[i] != '}':
                        w = tokens[i]
                        # Clean word
                        w_clean = w.replace('--', '').replace('_', '').strip()
                        if w_clean:
                            lyric_words.append(w_clean)
                        i += 1
                    staff.lyrics.extend(lyric_words)
                    i += 1
                else:
                    i += 1
                continue
                
            elif t == '|':
                # Measure boundary
                if current_measure.notes:
                    staff.add_measure(current_measure)
                    current_measure = Measure(number=measure_number + 1, key_signature=current_measure.key_signature, time_signature=current_measure.time_signature, clef=current_measure.clef)
                    measure_number += 1
                i += 1
                continue
                
            elif t == '\\bar':
                if i + 1 < len(tokens):
                    bar_type = tokens[i+1].strip('"')
                    bana_bar_type = {
                        '|': 'measure_separator',
                        '|.': 'final_double_bar',
                        '||': 'section_double_bar',
                        '.|:': 'forward_repeat',
                        ':|.': 'end_repeat',
                    }.get(bar_type, 'measure_separator')
                    current_measure.bar_line_type = bana_bar_type
                    i += 2
                else:
                    i += 1
                continue

            elif t == '<<':
                # In-accord: two or more independent voices sharing one
                # measure, separated by a bare '\\' (BANA Ch. 11 InAccord).
                # LilyPond's \relative pitch tracking treats '<<', '\\', and
                # '>>' as complete no-ops: it is a purely sequential/textual
                # chain through the token stream, blind to the << \\ >>
                # structure. So voice 2 continues from voice 1's LAST note
                # (not from the pitch before '<<', and not from voice 1's
                # FIRST note), voice 3 continues from voice 2's last note,
                # and whatever follows the closing '>>' continues from the
                # LAST voice's last note (not voice 0's). Verified against
                # the real `lilypond` binary's `\displayLilyMusic` output --
                # see the commit introducing this comment for the disambiguating
                # test cases (the "reset per voice, resume from voice 0" model
                # implemented here previously was self-consistent but did not
                # match real LilyPond, and caused runaway octave drift on real
                # multi-measure in-accord passages).
                depth = 1
                j = i + 1
                group_tokens: list[str] = []
                while j < len(tokens) and depth > 0:
                    if tokens[j] == '<<':
                        depth += 1
                    elif tokens[j] == '>>':
                        depth -= 1
                        if depth == 0:
                            break
                    group_tokens.append(tokens[j])
                    j += 1
                i = j + 1  # past the matching '>>'

                # Split on top-level '\\' only (not inside a voice's own
                # '{ }'), matching how InAccord.to_relative_lilypond() joins
                # voices with ' \\\\ '.
                voices_tokens: list[list[str]] = [[]]
                brace_depth = 0
                for gt in group_tokens:
                    if gt == '{':
                        brace_depth += 1
                        voices_tokens[-1].append(gt)
                    elif gt == '}':
                        brace_depth -= 1
                        voices_tokens[-1].append(gt)
                    elif gt == '\\\\' and brace_depth == 0:
                        voices_tokens.append([])
                    else:
                        voices_tokens[-1].append(gt)

                parts: list[list] = []
                for voice_tokens in voices_tokens:
                    voice_items: list = []
                    vi = 0
                    while vi < len(voice_tokens):
                        if voice_tokens[vi] in ('{', '}'):
                            vi += 1
                            continue
                        item, vi, relative_base, current_duration = self._parse_one_music_item(
                            voice_tokens, vi, is_relative, relative_base,
                            current_duration, current_measure.clef
                        )
                        if item is not None:
                            voice_items.append(item)
                    parts.append(voice_items)

                if any(parts):
                    current_measure.add_note(InAccord(parts=parts, in_accord_type='full_measure'))
                continue

            # Check if note or rest
            elif (
                t.startswith('r') or t.startswith('R') or t == '<'
                or t in ('\\grace', '\\appoggiatura') or parse_pitch_token(t)
            ):
                item, i, relative_base, current_duration = self._parse_one_music_item(
                    tokens, i, is_relative, relative_base, current_duration,
                    current_measure.clef
                )
                if isinstance(item, Rest) and item.multi_measure_count > 1:
                    # R1*N (Staff.to_lilypond()'s own compression of N
                    # consecutive whole-measure-rest Measures into one
                    # compact token, see staff.py) must expand back into N
                    # real Measure objects here, or every later measure
                    # number in this staff drifts by N-1.
                    count = item.multi_measure_count
                    for k in range(count):
                        rest_measure = Measure(
                            number=measure_number + k,
                            key_signature=current_measure.key_signature,
                            time_signature=current_measure.time_signature,
                            clef=current_measure.clef,
                        )
                        rest_measure.add_note(Rest(
                            dots=item.dots,
                            category=item.category,
                            raw_brl=item.raw_brl,
                            duration=item.duration,
                            is_full_measure=True,
                            multi_measure_count=1,
                        ))
                        staff.add_measure(rest_measure)
                    measure_number += count
                    current_measure = Measure(
                        number=measure_number,
                        key_signature=current_measure.key_signature,
                        time_signature=current_measure.time_signature,
                        clef=current_measure.clef,
                    )
                elif item is not None:
                    current_measure.add_note(item)
                continue

            else:
                i += 1

        # Add remaining measure
        if current_measure.notes:
            staff.add_measure(current_measure)

        if staff.time_signature is None:
            staff.time_signature = TimeSignature(
                dots=frozenset(), category=None, raw_brl="", numerator=4, denominator=4
            )
            for m in staff.measures:
                m.time_signature = (4, 4)
            
        return staff

    def _parse_one_music_item(
        self,
        tokens: list[str],
        i: int,
        is_relative: bool,
        relative_base: tuple[str, int],
        current_duration: Duration,
        clef: Optional[str],
    ) -> tuple[Optional[object], int, tuple[str, int], Duration]:
        """Parse one rest, chord, or note (with its trailing duration and
        decorations) starting at tokens[i].

        Shared between _parse_music_tokens' main per-staff loop and each
        independent voice inside a <<{...}\\{...}>> in-accord group, so both
        read notes/rests/chords identically -- only the relative_base/
        current_duration state threaded through differs per caller.

        Returns (item_or_None, new_i, new_relative_base, new_current_duration).
        item is None if tokens[i] wasn't a rest/chord/note token, in which
        case new_i == i + 1 and the other values are unchanged.
        """
        t = tokens[i]

        if t in ('\\grace', '\\appoggiatura'):
            # One or more grace notes prefixed to the following main note
            # (Note.to_relative_lilypond()'s own documented contract: grace
            # notes chain into the relative-pitch reference exactly like
            # ordinary notes -- the grace note(s) are relative to whatever
            # came before them, and the main note that follows is relative
            # to the last grace note). So the grace notes are parsed with
            # this same helper, threading relative_base/current_duration
            # through normally, then the very next item is parsed the same
            # way and the resulting GraceNote is attached to it.
            long_appoggiatura = (t == '\\appoggiatura')
            j = i + 1
            grace_notes: list[Note] = []
            if j < len(tokens) and tokens[j] == '{':
                j += 1
                while j < len(tokens) and tokens[j] != '}':
                    g_item, j, relative_base, current_duration = self._parse_one_music_item(
                        tokens, j, is_relative, relative_base, current_duration, clef
                    )
                    if isinstance(g_item, Note):
                        grace_notes.append(g_item)
                if j < len(tokens) and tokens[j] == '}':
                    j += 1
            i = j

            if i >= len(tokens):
                return None, i, relative_base, current_duration

            item, i, relative_base, current_duration = self._parse_one_music_item(
                tokens, i, is_relative, relative_base, current_duration, clef
            )
            if grace_notes and item is not None:
                grace_obj = GraceNote(notes=grace_notes, long_appoggiatura=long_appoggiatura)
                if isinstance(item, Note):
                    item.grace_note = grace_obj
                elif isinstance(item, Chord) and item.notes:
                    item.notes[0].grace_note = grace_obj
            return item, i, relative_base, current_duration

        elif t.startswith('r') or t.startswith('R'):
            # Rest
            is_full = t.startswith('R')
            dur_val = None
            dur_dots = 0
            multi_measure_count = 1
            j = i + 1
            if j < len(tokens) and tokens[j].isdigit():
                dur_val = int(tokens[j])
                j += 1
                # count dots
                while j < len(tokens) and tokens[j] == '.':
                    dur_dots += 1
                    j += 1
                # multi-measure rest count, e.g. R1*8
                if j < len(tokens) and tokens[j] == '*' and j + 1 < len(tokens) and tokens[j + 1].isdigit():
                    multi_measure_count = int(tokens[j + 1])
                    j += 2
                current_duration = Duration(value=dur_val, dots=dur_dots)
                i = j
            else:
                i += 1

            rest_obj = Rest(
                dots=frozenset(),
                category=None,
                raw_brl="",
                duration=current_duration,
                is_full_measure=is_full,
                multi_measure_count=multi_measure_count
            )
            return rest_obj, i, relative_base, current_duration

        elif t == '<':
            # Chord start
            chord_pitches = []
            j = i + 1
            while j < len(tokens) and tokens[j] != '>':
                chord_pitches.append(tokens[j])
                j += 1

            i = j + 1
            # Parse duration of chord
            if i < len(tokens) and tokens[i].isdigit():
                dur_val = int(tokens[i])
                i += 1
                dur_dots = 0
                while i < len(tokens) and tokens[i] == '.':
                    dur_dots += 1
                    i += 1
                current_duration = Duration(value=dur_val, dots=dur_dots)

            # Parse notes inside chord
            chord_notes = []
            curr_ref = relative_base
            for pitch_tok in chord_pitches:
                pitch_info = parse_pitch_token(pitch_tok)
                if pitch_info:
                    name, acc, oct_marks = pitch_info
                    # Relative logic:
                    # 1st note is relative to relative_base
                    # Subsequent notes are relative to preceding chord note!
                    if is_relative:
                        name, octave = get_absolute_pitch(name, oct_marks, curr_ref)
                    else:
                        octave = 4 + oct_marks.count("'") - oct_marks.count(",")

                    acc_obj = None
                    if acc:
                        acc_obj = Accidental(dots=frozenset(), category=None, raw_brl="", type=_ACCIDENTAL_MAP[acc])

                    n_obj = Note(
                        dots=frozenset(),
                        category=None,
                        raw_brl="",
                        note_name=name,
                        octave=octave,
                        duration=current_duration,
                        accidental=acc_obj
                    )
                    chord_notes.append(n_obj)
                    curr_ref = (name, octave)

            if not chord_notes:
                return None, i, relative_base, current_duration

            # Preserve LilyPond's own \relative pitch-chain rule, which
            # references the note literally *written first in the
            # source* -- independent of the BANA written-note sort below.
            lilypond_first_note = chord_notes[0]

            # BANA written-note ordering (see Chord's docstring): treble/
            # alto clef writes the highest note first; bass/tenor writes
            # the lowest note first. clef defaults to "treble".
            if clef in ('bass', 'tenor'):
                chord_notes = sorted(chord_notes, key=lambda n: n._midi_pitch())
            else:
                chord_notes = sorted(chord_notes, key=lambda n: n._midi_pitch(), reverse=True)

            chord_obj = Chord(notes=chord_notes)
            # Update relative reference to the note as literally written
            # in the source (not the BANA-sorted written note).
            relative_base = (lilypond_first_note.note_name, lilypond_first_note.octave)

            # Parse dynamic or slur decoration after chord; attach to
            # the same Note object that is now Chord.notes[0], since
            # Chord.to_lilypond() reads chord-level decorations from
            # notes[0].
            self._parse_note_decorations(tokens, i, chord_notes[0])
            return chord_obj, i, relative_base, current_duration

        else:
            # Regular note pitch
            pitch_info = parse_pitch_token(t)
            if pitch_info:
                name, acc, oct_marks = pitch_info

                if is_relative:
                    name, octave = get_absolute_pitch(name, oct_marks, relative_base)
                else:
                    octave = 4 + oct_marks.count("'") - oct_marks.count(",")

                # Parse duration following it
                j = i + 1
                if j < len(tokens) and tokens[j].isdigit():
                    dur_val = int(tokens[j])
                    j += 1
                    dur_dots = 0
                    while j < len(tokens) and tokens[j] == '.':
                        dur_dots += 1
                        j += 1
                    current_duration = Duration(value=dur_val, dots=dur_dots)
                    i = j
                else:
                    i += 1

                acc_obj = None
                if acc:
                    acc_obj = Accidental(dots=frozenset(), category=None, raw_brl="", type=_ACCIDENTAL_MAP[acc])

                n_obj = Note(
                    dots=frozenset(),
                    category=None,
                    raw_brl="",
                    note_name=name,
                    octave=octave,
                    duration=current_duration,
                    accidental=acc_obj
                )

                # Update relative reference
                relative_base = (name, octave)

                # Parse decorations following note/duration
                i = self._parse_note_decorations(tokens, i, n_obj)
                return n_obj, i, relative_base, current_duration
            else:
                return None, i + 1, relative_base, current_duration

    def _parse_note_decorations(self, tokens: list[str], start_idx: int, note: Note) -> int:
        i = start_idx
        while i < len(tokens):
            t = tokens[i]
            if t == '~':
                note.tie = True
                i += 1
            elif t == '(':
                note.slur_start = True
                i += 1
            elif t == ')':
                note.slur_end = True
                i += 1
            elif t == '\\(':
                note.slur_bracket_open = True
                i += 1
            elif t == '\\)':
                note.slur_bracket_close = True
                i += 1
            elif t.startswith('\\') and t[1:] in _DYNAMIC_MAP:
                note.dynamics.append(Dynamic(level=_DYNAMIC_MAP[t[1:]]))
                i += 1
            elif t.startswith('\\') and t[1:] in _ARTICULATION_MAP:
                note.articulations.append(Articulation(type=_ARTICULATION_MAP[t[1:]]))
                i += 1
            elif t in _ARTICULATION_MAP: # e.g. -. or ->
                note.articulations.append(Articulation(type=_ARTICULATION_MAP[t]))
                i += 1
            elif t == '\\sustainOn':
                note.pedal_sustain = "on"
                i += 1
            elif t == '\\sustainOff':
                note.pedal_sustain = "off"
                i += 1
            elif t.startswith('\\') and t[1:] == 'trill':
                note.ornaments.append(Ornament(type=OrnamentType.TRILL))
                i += 1
            elif t == '\\startTrillSpan':
                note.ornaments.append(Ornament(type=OrnamentType.TRILL_SPAN_START))
                i += 1
            elif t == '\\stopTrillSpan':
                note.ornaments.append(Ornament(type=OrnamentType.TRILL_SPAN_END))
                i += 1
            elif t == '\\mordent':
                note.ornaments.append(Ornament(type=OrnamentType.MORDENT))
                i += 1
            elif t == '\\prall':
                note.ornaments.append(Ornament(type=OrnamentType.UPPER_MORDENT))
                i += 1
            elif t == '\\turn':
                note.ornaments.append(Ornament(type=OrnamentType.TURN))
                i += 1
            elif t == '\\reverseturn':
                note.ornaments.append(Ornament(type=OrnamentType.INVERTED_TURN))
                i += 1
            elif t == '\\glissando':
                note.ornaments.append(Ornament(type=OrnamentType.GLISSANDO))
                i += 1
            else:
                break
        return i
