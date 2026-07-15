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
    def __init__(self, column_limit: int = 40):
        self.column_limit = column_limit

    def validate(self, score: Score, raw_brl_text: Optional[str] = None) -> ValidationResult:
        corrections: list[Correction] = []

        # Rule S9b-4: Line Length (BF 2016 Section 1)
        if raw_brl_text:
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
            voices = self._get_staff_voices(staff)
            for voice in voices:
                corrections.extend(self._validate_octave_marks(voice))
                corrections.extend(self._validate_articulation_shorthand(voice))
                corrections.extend(self._validate_sign_order(voice))

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
                elif diff >= 5:
                    # 6th or greater: octave mark must be present
                    if not has_mark:
                        corrections.append(Correction(
                            line_number=line_num,
                            measure_number=m_num,
                            message=f"Missing octave mark on note '{curr_note.note_name}' (interval of 6th or greater).",
                            severity="warning",
                            rule_id="S9b-3"
                        ))
                elif diff in (3, 4):
                    # 4th or 5th: mark only if crossing octaves
                    crosses = (curr_note.octave != last_note.octave)
                    if crosses and not has_mark:
                        corrections.append(Correction(
                            line_number=line_num,
                            measure_number=m_num,
                            message=f"Missing octave mark on note '{curr_note.note_name}' (interval of 4th/5th crossing octaves).",
                            severity="warning",
                            rule_id="S9b-3"
                        ))
                    elif not crosses and has_mark:
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
