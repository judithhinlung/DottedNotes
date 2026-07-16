from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from typing import Optional, Any
from dottednotes.bana_symbols import SymbolCategory
from dottednotes.models.score import Score
from dottednotes.models.staff import Staff
from dottednotes.models.measure import Measure
from dottednotes.models.note import Note, Rest
from dottednotes.models.chord import Chord
from dottednotes.models.in_accord import InAccord
from dottednotes.models.tremolo import RepeatedTremolo
from dottednotes.models.tuplet import Tuplet
from dottednotes.models.accidental import AccidentalType


@dataclass
class Rule:
    rule_id: str
    name: str
    description: str
    citation: str
    default_severity: str = "warning"


RULE_REGISTRY: dict[str, Rule] = {
    "S9b-2": Rule(
        rule_id="S9b-2",
        name="Articulation Carry Shorthand",
        description="To save space, runs of 4 or more notes with the same articulation should use shorthand carry.",
        citation="MBC 2015 Part I, Section 14.1"
    ),
    "S9b-3": Rule(
        rule_id="S9b-3",
        name="Octave Register Tracking",
        description="Octave mark register tracking requires octave indicators at reset points and large intervals.",
        citation="MBC 2015 Part I, Section 3"
    ),
    "S9b-4": Rule(
        rule_id="S9b-4",
        name="Line Length Limit",
        description="A line of braille music must not exceed the standard column limit (default 40 cells).",
        citation="MBC 2015 Part I, Section 1.2"
    ),
    "S9b-sign-order": Rule(
        rule_id="S9b-sign-order",
        name="BANA Sign Ordering",
        description="Pre-note and post-note modifier signs must follow a strict sequential ordering around the note cell.",
        citation="MBC 2015 Appendix A, Section A.1"
    ),
    "S9c-beat-count": Rule(
        rule_id="S9c-beat-count",
        name="Measure Beat-Count Validation",
        description="The sum of note, rest, and chord durations within a measure must equal the expected beats defined by the time signature.",
        citation="MBC 2015 Part I, Section 2.1"
    ),
    "S9c-slur-matching": Rule(
        rule_id="S9c-slur-matching",
        name="Slur & Tie Matching",
        description="All opened slurs, ties, and slur brackets must be resolved and closed.",
        citation="MBC 2015 Part I, Section 13"
    ),
    "S9c-redundant-accidental": Rule(
        rule_id="S9c-redundant-accidental",
        name="Redundant Accidental Check",
        description="Explicit accidentals in braille should not be written if they match the key signature or active accidental state.",
        citation="MBC 2015 Part I, Section 5.1"
    ),
    "S9c-measure-repeat": Rule(
        rule_id="S9c-measure-repeat",
        name="Measure Repeat Shorthand Recommendation",
        description="Suggest using the measure repeat sign when two or more consecutive measures are musically identical.",
        citation="MBC 2015 Part I, Section 18.1"
    ),
}

VALIDATION_PROFILES: dict[str, list[str]] = {
    "standard": ["S9b-2", "S9b-3", "S9b-4", "S9b-sign-order", "S9c-beat-count", "S9c-slur-matching"],
    "strict": ["S9b-2", "S9b-3", "S9b-4", "S9b-sign-order", "S9c-beat-count", "S9c-slur-matching", "S9c-redundant-accidental", "S9c-measure-repeat"],
}


@dataclass
class Correction:
    line_number: int
    measure_number: int
    message: str
    severity: str
    rule_id: str
    proposed_fix: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ValidationResult:
    corrections: list[Correction]

    def to_json(self) -> str:
        return json.dumps([c.to_dict() for c in self.corrections], indent=2)


class BANAValidator:
    def __init__(self, column_limit: int = 40, profile: str = "standard", enabled_rules: Optional[list[str]] = None):
        self.column_limit = column_limit
        self.profile = profile
        if enabled_rules is not None:
            self.enabled_rules = set(enabled_rules)
        else:
            self.enabled_rules = set(VALIDATION_PROFILES.get(profile, VALIDATION_PROFILES["standard"]))

    def validate(self, score: Score, raw_brl_text: Optional[str] = None) -> ValidationResult:
        corrections: list[Correction] = []

        # Rule S9b-4: Line Length (BF 2016 Section 1)
        if "S9b-4" in self.enabled_rules and raw_brl_text:
            lines = raw_brl_text.splitlines()
            for idx, line in enumerate(lines):
                # We strip trailing whitespaces/newlines for column check
                stripped_line = line.rstrip('\r\n')
                if len(stripped_line) > self.column_limit:
                    # Look for spaces to propose a break
                    proposed = None
                    if ' ' in stripped_line:
                        parts = stripped_line.split(' ')
                        # Propose breaking at the last space within limit
                        break_pos = -1
                        accum = 0
                        for part in parts:
                            if accum + len(part) + (1 if accum > 0 else 0) <= self.column_limit:
                                accum += len(part) + (1 if accum > 0 else 0)
                            else:
                                break
                        if accum > 0:
                            proposed = f"Break line at column {accum}"

                    corrections.append(Correction(
                        line_number=idx + 1,
                        measure_number=0,
                        message=f"Line exceeds BANA column limit of {self.column_limit} cells (has {len(stripped_line)} cells).",
                        severity="warning",
                        rule_id="S9b-4",
                        proposed_fix=proposed
                    ))

        # Build melodic voices for each staff to validate octave marks and articulation carry
        for staff in score.staves:
            # Rule S9c-beat-count
            if "S9c-beat-count" in self.enabled_rules:
                corrections.extend(self._validate_beat_count(staff))

            # Rule S9c-measure-repeat
            if "S9c-measure-repeat" in self.enabled_rules:
                corrections.extend(self._validate_measure_repeats(staff))

            voices = self._get_staff_voices(staff)
            for voice in voices:
                if "S9b-3" in self.enabled_rules:
                    corrections.extend(self._validate_octave_marks(voice))
                if "S9b-2" in self.enabled_rules:
                    corrections.extend(self._validate_articulation_shorthand(voice))
                if "S9b-sign-order" in self.enabled_rules:
                    corrections.extend(self._validate_sign_order(voice))
                if "S9c-slur-matching" in self.enabled_rules:
                    corrections.extend(self._validate_slur_matching(voice))
                if "S9c-redundant-accidental" in self.enabled_rules:
                    corrections.extend(self._validate_redundant_accidentals(voice, staff))

        # Deduplicate corrections based on unique attributes
        seen = set()
        deduped = []
        for c in corrections:
            key = (c.line_number, c.measure_number, c.message, c.rule_id)
            if key not in seen:
                seen.add(key)
                deduped.append(c)

        # Sort corrections: line number first, then rule ID
        deduped.sort(key=lambda x: (x.line_number, x.rule_id))

        return ValidationResult(corrections=deduped)

    def _get_staff_voices(self, staff: Staff) -> list[list[tuple[Any, int]]]:
        # Find max number of parallel parts (InAccord) in any measure
        max_parts = 1
        for m in staff.measures:
            for item in m.notes:
                if isinstance(item, InAccord):
                    max_parts = max(max_parts, len(item.parts))

        voices: list[list[tuple[Any, int]]] = [[] for _ in range(max_parts)]
        for m in staff.measures:
            # Check if there is an InAccord in this measure
            in_accord = None
            for item in m.notes:
                if isinstance(item, InAccord):
                    in_accord = item
                    break

            if in_accord:
                for i in range(max_parts):
                    part_idx = min(i, len(in_accord.parts) - 1)
                    part_notes = self._flatten_items(in_accord.parts[part_idx])
                    for note in part_notes:
                        voices[i].append((note, m.number))
            else:
                measure_notes = self._flatten_items(m.notes)
                for i in range(max_parts):
                    for note in measure_notes:
                        voices[i].append((note, m.number))

        return voices

    def _flatten_items(self, items: list) -> list[Any]:
        flat = []
        for item in items:
            if isinstance(item, (Note, Rest, Chord)):
                flat.append(item)
            elif isinstance(item, Tuplet):
                flat.extend(self._flatten_items(item.items))
        return flat

    def _validate_octave_marks(self, voice: list[tuple[Any, int]]) -> list[Correction]:
        corrections = []
        last_note: Optional[Note] = None
        last_measure_number: Optional[int] = None
        is_first_note_in_voice = True

        PITCH_CLASS_TO_DIATONIC = {'C': 0, 'D': 1, 'E': 2, 'F': 3, 'G': 4, 'A': 5, 'B': 6}

        for idx, (item, m_num) in enumerate(voice):
            if isinstance(item, Rest):
                continue

            curr_note = item.notes[0] if isinstance(item, Chord) else item
            line_num = curr_note.parsed_tokens[0].line if curr_note.parsed_tokens else 1

            has_mark = curr_note.has_octave_mark or any(t.category == SymbolCategory.OCTAVE_MARK for t in curr_note.parsed_tokens)

            # Determine if this is a BANA reset point where octave mark is ALWAYS required:
            is_reset = False
            reset_reason = ""

            if is_first_note_in_voice:
                is_reset = True
                reset_reason = "first note of piece"
            elif curr_note.after_numeric_indicator:
                is_reset = True
                reset_reason = "first note after numeric indicator"
            elif last_measure_number is not None and m_num != last_measure_number:
                # BANA resets octave tracking at every measure boundary, not
                # just line starts -- Note.to_braille() (the actual renderer)
                # already forces an octave mark whenever is_measure_start is
                # True, regardless of interval size. This mirrors that rule.
                is_reset = True
                reset_reason = "first note of a new measure"
            else:
                # Check for line start
                if last_note and curr_note.parsed_tokens and last_note.parsed_tokens:
                    curr_line = curr_note.parsed_tokens[0].line
                    prev_line = last_note.parsed_tokens[0].line
                    if curr_line != prev_line:
                        is_reset = True
                        reset_reason = "first note in new line"

            if is_reset:
                if not has_mark:
                    corrections.append(Correction(
                        line_number=line_num,
                        measure_number=m_num,
                        message=f"Missing octave mark on note '{curr_note.note_name}' ({reset_reason}).",
                        severity="warning",
                        rule_id="S9b-3"
                    ))
                is_first_note_in_voice = False
                last_note = curr_note
                last_measure_number = m_num
                continue

            # Standard interval rules relative to last note
            if last_note:
                curr_val = curr_note.octave * 7 + PITCH_CLASS_TO_DIATONIC[curr_note.note_name]
                prev_val = last_note.octave * 7 + PITCH_CLASS_TO_DIATONIC[last_note.note_name]
                diff = abs(curr_val - prev_val)

                # "Missing octave mark" checks for a 6th+ interval, or a
                # 4th/5th that crosses octaves, are NOT done here: the
                # parser itself (BrailleParser._resolve_unmarked_octave)
                # now resolves any unmarked note to the nearest octave per
                # this same rule (BANA Sec. 3.2.2), so curr_note.octave is
                # never actually a 6th+ away, and never crosses octaves on
                # an unmarked 4th/5th -- there is nothing left to flag from
                # the resolved pitches. Only redundant (unnecessary)
                # explicit marks are still detectable here, since the
                # parser trusts an explicit mark at face value rather than
                # second-guessing it.
                if diff <= 2:
                    # 2nd or 3rd: octave mark must not be present
                    if has_mark:
                        corrections.append(Correction(
                            line_number=line_num,
                            measure_number=m_num,
                            message=f"Redundant octave mark on note '{curr_note.note_name}' (interval of 2nd/3rd).",
                            severity="warning",
                            rule_id="S9b-3"
                        ))
                elif diff in (3, 4):
                    # 4th or 5th: redundant if marked but not crossing octaves
                    crosses = (curr_note.octave != last_note.octave)
                    if not crosses and has_mark:
                        corrections.append(Correction(
                            line_number=line_num,
                            measure_number=m_num,
                            message=f"Redundant octave mark on note '{curr_note.note_name}' (interval of 4th/5th not crossing octaves).",
                            severity="warning",
                            rule_id="S9b-3"
                        ))

            is_first_note_in_voice = False
            last_note = curr_note
            last_measure_number = m_num

        return corrections

    def _validate_articulation_shorthand(self, voice: list[tuple[Any, int]]) -> list[Correction]:
        corrections = []
        n_notes = len(voice)
        i = 0
        while i < n_notes:
            item, m_num = voice[i]
            if isinstance(item, Rest):
                i += 1
                continue

            curr_note = item.notes[0] if isinstance(item, Chord) else item
            if len(curr_note.articulations) == 1 and curr_note.articulations[0].explicit:
                art_type = curr_note.articulations[0].type
                # Scan ahead to find a run of consecutive notes with the same articulation type explicitly written
                run = [(curr_note, m_num)]
                j = i + 1
                while j < n_notes:
                    nxt_item, nxt_m = voice[j]
                    if isinstance(nxt_item, Rest):
                        break  # Rest breaks the run
                    nxt_note = nxt_item.notes[0] if isinstance(nxt_item, Chord) else nxt_item
                    if len(nxt_note.articulations) == 1 and nxt_note.articulations[0].type == art_type and nxt_note.articulations[0].explicit:
                        run.append((nxt_note, nxt_m))
                        j += 1
                    else:
                        break

                if len(run) >= 4:
                    first_note, first_m = run[0]
                    line_num = first_note.parsed_tokens[0].line if first_note.parsed_tokens else 1
                    corrections.append(Correction(
                        line_number=line_num,
                        measure_number=first_m,
                        message=f"Articulation shorthand missing for run of {len(run)} consecutive notes with {art_type.name} articulation.",
                        severity="warning",
                        rule_id="S9b-2",
                        proposed_fix="Use BANA articulation shorthand carry."
                    ))
                i = j
            else:
                i += 1

        return corrections

    def _validate_sign_order(self, voice: list[tuple[Any, int]]) -> list[Correction]:
        corrections = []
        for item, m_num in voice:
            if isinstance(item, Rest):
                continue
            curr_note = item.notes[0] if isinstance(item, Chord) else item
            if not curr_note.parsed_tokens:
                continue

            # Map tokens to category indices
            # Correct BANA order:
            # 0: pedal down
            # 1: slur bracket open
            # 2: dynamic
            # 3: articulation
            # 4: ornament
            # 5: accidental
            # 6: octave mark
            # 7: note cell
            # 8: interval
            # 9: tremolo
            # 10: fingering
            # 11: tie / slur
            # 12: pedal up
            mapped = []
            for t in curr_note.parsed_tokens:
                idx = -1
                if t.category == SymbolCategory.PEDAL:
                    if t.character in ('⠣⠉', '⠐⠣⠉', '⠠⠣⠉'):
                        idx = 0
                    elif t.character in ('⠡⠉', '⠐⠡⠉', '⠡⠣⠉'):
                        idx = 12
                elif t.category == SymbolCategory.SLUR:
                    if t.character == '⠰⠃':
                        idx = 1
                    else:
                        idx = 11
                elif t.category == SymbolCategory.DYNAMIC:
                    idx = 2
                elif t.category == SymbolCategory.ARTICULATION:
                    idx = 3
                elif t.category == SymbolCategory.ORNAMENT:
                    idx = 4
                elif t.category == SymbolCategory.ACCIDENTAL:
                    idx = 5
                elif t.category == SymbolCategory.OCTAVE_MARK:
                    idx = 6
                elif t.category == SymbolCategory.NOTE:
                    idx = 7
                elif t.category == SymbolCategory.INTERVAL:
                    idx = 8
                elif t.category == SymbolCategory.TREMOLO:
                    idx = 9
                elif t.category == SymbolCategory.FINGERING:
                    idx = 10

                if idx != -1:
                    mapped.append((t, idx))

            # Check if non-decreasing
            for idx_m in range(len(mapped) - 1):
                tok_a, order_a = mapped[idx_m]
                tok_b, order_b = mapped[idx_m + 1]
                if order_a > order_b:
                    corrections.append(Correction(
                        line_number=tok_a.line,
                        measure_number=m_num,
                        message=f"BANA sign order violation: {tok_a.character} ({tok_a.category.name}) should not precede {tok_b.character} ({tok_b.category.name}) around note '{curr_note.note_name}'.",
                        severity="warning",
                        rule_id="S9b-sign-order",
                        proposed_fix="Reorder signs in preceding/succeeding BANA order."
                    ))

        return corrections

    def _find_measure(self, staff: Staff, m_num: int) -> Optional[Measure]:
        for m in staff.measures:
            if m.number == m_num:
                return m
        return None

    def _validate_beat_count(self, staff: Staff) -> list[Correction]:
        from dottednotes.models.duration import TICKS_PER_QUARTER
        from dottednotes.models.tremolo import AlternatingTremolo
        corrections = []

        def _item_ticks(item) -> int:
            if isinstance(item, Tuplet):
                return sum(_item_ticks(sub) for sub in item.items)
            if isinstance(item, AlternatingTremolo):
                return item.items[0].duration.duration_in_ticks()
            return item.duration.duration_in_ticks()

        for measure in staff.measures:
            num, den = measure.time_signature
            expected_beats = num * (4 / den)
            expected_ticks = round(expected_beats * TICKS_PER_QUARTER)

            actual_ticks = 0
            for item in measure.notes:
                if isinstance(item, InAccord):
                    if item.parts:
                        actual_ticks += max(
                            sum(_item_ticks(n) for n in part)
                            for part in item.parts
                        )
                else:
                    actual_ticks += _item_ticks(item)

            if actual_ticks != expected_ticks:
                line_num = measure.line if measure.line > 0 else 1
                for item in measure.notes:
                    note = item.notes[0] if isinstance(item, Chord) else item
                    if isinstance(note, Note) and note.parsed_tokens:
                        line_num = note.parsed_tokens[0].line
                        break

                corrections.append(Correction(
                    line_number=line_num,
                    measure_number=measure.number,
                    message=f"Measure {measure.number}: expected {expected_beats} beats but counted {actual_ticks / TICKS_PER_QUARTER}. Check for notation ambiguity or missing/extra notes.",
                    severity="warning",
                    rule_id="S9c-beat-count"
                ))

        return corrections

    def _validate_measure_repeats(self, staff: Staff) -> list[Correction]:
        corrections = []
        n_measures = len(staff.measures)
        for i in range(1, n_measures):
            m_prev = staff.measures[i - 1]
            m_curr = staff.measures[i]
            if m_curr.musical_equals(m_prev):
                line_num = m_curr.line if m_curr.line > 0 else 1
                for item in m_curr.notes:
                    note = item.notes[0] if isinstance(item, Chord) else item
                    if isinstance(note, Note) and note.parsed_tokens:
                        line_num = note.parsed_tokens[0].line
                        break
                corrections.append(Correction(
                    line_number=line_num,
                    measure_number=m_curr.number,
                    message=f"Measure {m_curr.number} is identical to measure {m_prev.number}. Consider using a measure repeat sign.",
                    severity="warning",
                    rule_id="S9c-measure-repeat"
                ))
        return corrections

    def _validate_slur_matching(self, voice: list[tuple[Any, int]]) -> list[Correction]:
        corrections = []
        open_slur_starts = []
        open_brackets = []

        for item, m_num in voice:
            if isinstance(item, Rest):
                continue

            curr_note = item.notes[0] if isinstance(item, Chord) else item
            line_num = curr_note.parsed_tokens[0].line if curr_note.parsed_tokens else 1

            if curr_note.slur_start:
                open_slur_starts.append((m_num, line_num))

            if curr_note.slur_end:
                if open_slur_starts:
                    open_slur_starts.pop()
                else:
                    corrections.append(Correction(
                        line_number=line_num,
                        measure_number=m_num,
                        message="Slur end without preceding slur start.",
                        severity="warning",
                        rule_id="S9c-slur-matching"
                    ))

            if curr_note.slur_bracket_open:
                open_brackets.append((m_num, line_num))

            if curr_note.slur_bracket_close:
                if open_brackets:
                    open_brackets.pop()
                else:
                    corrections.append(Correction(
                        line_number=line_num,
                        measure_number=m_num,
                        message="Slur bracket close without preceding bracket open.",
                        severity="warning",
                        rule_id="S9c-slur-matching"
                    ))

        for m_start, l_start in open_slur_starts:
            corrections.append(Correction(
                line_number=l_start,
                measure_number=m_start,
                message=f"Unclosed slur starting at measure {m_start}.",
                severity="warning",
                rule_id="S9c-slur-matching"
            ))

        for m_start, l_start in open_brackets:
            corrections.append(Correction(
                line_number=l_start,
                measure_number=m_start,
                message=f"Unclosed slur bracket starting at measure {m_start}.",
                severity="warning",
                rule_id="S9c-slur-matching"
            ))

        return corrections

    def _validate_redundant_accidentals(self, voice: list[tuple[Any, int]], staff: Staff) -> list[Correction]:
        def get_key_sig_accidental(key_sig: int, note_name: str) -> AccidentalType:
            if key_sig > 0:
                sharps = ['F', 'C', 'G', 'D', 'A', 'E', 'B'][:key_sig]
                if note_name in sharps:
                    return AccidentalType.SHARP
            elif key_sig < 0:
                flats = ['B', 'E', 'A', 'D', 'G', 'C', 'F'][:abs(key_sig)]
                if note_name in flats:
                    return AccidentalType.FLAT
            return AccidentalType.NATURAL

        corrections = []
        last_measure = None
        active_accidentals = {}

        for item, m_num in voice:
            if isinstance(item, Rest):
                continue

            if m_num != last_measure:
                active_accidentals = {}
                last_measure = m_num

            measure_obj = self._find_measure(staff, m_num)
            key_sig = 0
            if measure_obj and measure_obj.key_signature != 0:
                key_sig = measure_obj.key_signature
            elif staff.key_signature:
                key_sig = staff.key_signature.sharps_or_flats

            notes_in_item = item.notes if isinstance(item, Chord) else [item]

            for note in notes_in_item:
                note_name = note.note_name
                octave = note.octave
                has_acc = note.accidental is not None

                curr_state = active_accidentals.get((note_name, octave), get_key_sig_accidental(key_sig, note_name))

                if has_acc:
                    acc_type = note.accidental.type
                    if acc_type == curr_state:
                        line_num = note.parsed_tokens[0].line if note.parsed_tokens else 1
                        corrections.append(Correction(
                            line_number=line_num,
                            measure_number=m_num,
                            message=f"Redundant accidental on note '{note_name}' (matches key signature or active accidental).",
                            severity="warning",
                            rule_id="S9c-redundant-accidental"
                        ))
                    active_accidentals[(note_name, octave)] = acc_type
        return corrections
