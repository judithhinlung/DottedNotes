import pytest
from dottednotes.parser.braille_parser import BrailleParser
from dottednotes.parser.tokenizer import BrailleTokenizer
from dottednotes.validation.validator import BANAValidator, Correction
from dottednotes.models.score import Score
from dottednotes.models.staff import Staff
from dottednotes.models.measure import Measure
from dottednotes.models.note import Note
from dottednotes.models.duration import Duration


def parse_brf(brf_text: str) -> Score:
    tokens = BrailleTokenizer().tokenize(brf_text)
    return BrailleParser(tokens=tokens).parse()


def test_validation_octave_marks_first_note():
    # First note of piece lacks octave mark (⠹ is C4, duration 8, no octave mark before it)
    brf = "⠹"
    score = parse_brf(brf)
    validator = BANAValidator(enabled_rules=["S9b-3"])
    result = validator.validate(score)
    assert len(result.corrections) == 1
    assert result.corrections[0].rule_id == "S9b-3"
    assert "Missing octave mark" in result.corrections[0].message
    assert "first note of piece" in result.corrections[0].message


def test_validation_octave_marks_redundant_step():
    # C4 followed by D4 with octave mark (⠐⠹ ⠐⠱ -> C4 then D4 with redundant octave 4 mark)
    brf = "⠐⠹⠐⠱"
    score = parse_brf(brf)
    validator = BANAValidator()
    result = validator.validate(score)
    # The first note might warn about missing/expected mark, but let's look at the second note.
    # C4 has ⠐ (octave 4), so no missing warning.
    # D4 has ⠐ (octave 4), which is redundant because it's a second interval (diff = 1).
    redundant = [c for c in result.corrections if "Redundant octave mark" in c.message]
    assert len(redundant) == 1
    assert redundant[0].measure_number == 1


def test_validation_octave_marks_missing_leap():
    # C4 then B, unmarked (⠐⠹ ⠞). A literal same-octave reading would be a
    # 7th above (B4, diff=6) -- but BrailleParser._resolve_unmarked_octave
    # (BANA Sec. 3.2.2) resolves this to the nearest reading instead: B3, a
    # 2nd below C4 (diff=-1). Since the parser itself now guarantees an
    # unmarked note is never actually a 6th+ away, there's nothing left for
    # the validator to flag here -- see validator.py's _validate_octave_marks.
    brf = "⠐⠹⠞"
    score = parse_brf(brf)
    assert score.staves[0].measures[0].notes[1].octave == 3
    validator = BANAValidator()
    result = validator.validate(score)
    missing = [c for c in result.corrections if "Missing octave mark" in c.message]
    assert len(missing) == 0


def test_validation_octave_marks_reset_points():
    # Reset point: new line start. In this parser's grammar a bare newline in
    # the source always starts a new measure too (BANA lines always begin at
    # a measure boundary), so the more specific "new measure" reset -- which
    # subsumes "new line" -- is what actually fires here; see
    # test_validation_octave_marks_new_measure_same_line below for a case
    # that isolates a measure boundary from a line boundary.
    # ⠐⠹ (line 1)
    # ⠱ (line 2, lacks octave mark)
    brf = "⠐⠹\n⠱"
    score = parse_brf(brf)
    validator = BANAValidator()
    result = validator.validate(score, raw_brl_text=brf)
    missing_new_measure = [c for c in result.corrections if "new measure" in c.message]
    assert len(missing_new_measure) == 1

    # Reset point: after numeric indicator (measure number ⠃)
    brf = "⠁⠀⠐⠹\n⠃⠀⠱"  # Line 2 starts with measure number 2, D4 lacks octave mark
    score = parse_brf(brf)
    result = validator.validate(score, raw_brl_text=brf)
    missing_num = [c for c in result.corrections if "after numeric indicator" in c.message]
    assert len(missing_num) == 1


def test_validation_octave_marks_new_measure_same_line():
    # Two measures on ONE line (BRF measure separator '⠀'): the second
    # measure's first note (D4) is a 2nd away from the previous note (C4) --
    # the interval-only rule would call a mark here "not needed" -- but since
    # it's the first note of a new measure, BANA still requires one (matching
    # Note.to_braille()'s real is_measure_start-based reset).
    brf = "⠐⠹⠀⠱"
    score = parse_brf(brf)
    validator = BANAValidator()
    result = validator.validate(score, raw_brl_text=brf)
    missing_new_measure = [c for c in result.corrections if "first note of a new measure" in c.message]
    assert len(missing_new_measure) == 1
    redundant = [c for c in result.corrections if "Redundant" in c.message]
    assert len(redundant) == 0


def test_validation_articulation_shorthand():
    # 4 consecutive notes with staccato articulation explicitly written (⠦⠹ ⠦⠹ ⠦⠹ ⠦⠹)
    # Staccato is ⠦ (dots 3,5,6).
    brf = "⠦⠹⠦⠹⠦⠹⠦⠹"
    score = parse_brf(brf)
    validator = BANAValidator()
    result = validator.validate(score)
    missing_shorthand = [c for c in result.corrections if c.rule_id == "S9b-2"]
    assert len(missing_shorthand) == 1
    assert "Articulation shorthand missing" in missing_shorthand[0].message


def test_validation_sign_order_prefix():
    # Incorrect order: staccato (articulation) before dynamic
    # Correct order: dynamic -> articulation
    # Let's tokenize staccato (⠦) then dynamic f (⠜⠋⠄) then note C (⠹)
    brf = "⠦⠜⠋⠄⠹"
    score = parse_brf(brf)
    validator = BANAValidator()
    result = validator.validate(score)
    violations = [c for c in result.corrections if c.rule_id == "S9b-sign-order"]
    assert len(violations) == 1
    assert "should not precede" in violations[0].message


def test_validation_sign_order_suffix():
    # Suffix order: fingering (10) -> tie / slur (11) -> pedal up (12)
    # Incorrect order: pedal up (⠡⠉) before slur (⠉)
    brf = "⠐⠹⠡⠉⠉⠹"
    score = parse_brf(brf)
    validator = BANAValidator()
    result = validator.validate(score)
    violations = [c for c in result.corrections if c.rule_id == "S9b-sign-order"]
    assert len(violations) == 1


def test_validation_line_length():
    # Line exceeding 40 cells
    brf = "⠐⠹" * 25  # 50 cells
    score = parse_brf(brf)
    validator = BANAValidator(column_limit=40)
    result = validator.validate(score, raw_brl_text=brf)
    too_long = [c for c in result.corrections if c.rule_id == "S9b-4"]
    assert len(too_long) == 1
    assert "exceeds BANA column limit" in too_long[0].message


def test_validation_to_json():
    brf = "⠹"
    score = parse_brf(brf)
    validator = BANAValidator()
    result = validator.validate(score)
    json_str = result.to_json()
    assert isinstance(json_str, str)
    assert "S9b-3" in json_str


def test_rule_registry_and_profiles():
    validator_std = BANAValidator(profile="standard")
    assert "S9c-beat-count" in validator_std.enabled_rules
    assert "S9c-redundant-accidental" not in validator_std.enabled_rules

    validator_strict = BANAValidator(profile="strict")
    assert "S9c-redundant-accidental" in validator_strict.enabled_rules
    assert "S9c-measure-repeat" in validator_strict.enabled_rules

    validator_custom = BANAValidator(enabled_rules=["S9b-4"])
    assert validator_custom.enabled_rules == {"S9b-4"}


def test_validation_beat_count():
    # expected 4 beats, but only has 1 beat (quarter note C4)
    brf = "⠼⠙⠲⠐⠹"
    score = parse_brf(brf)
    validator = BANAValidator()
    result = validator.validate(score)
    beat_errs = [c for c in result.corrections if c.rule_id == "S9c-beat-count"]
    assert len(beat_errs) == 1
    assert "expected 4.0 beats but counted 1.0" in beat_errs[0].message


def test_validation_slur_matching():
    # 1. Unclosed slur bracket open: ⠰⠃⠐⠹⠱
    brf = "⠰⠃⠐⠹⠱"
    score = parse_brf(brf)
    validator = BANAValidator()
    result = validator.validate(score)
    slur_errs = [c for c in result.corrections if c.rule_id == "S9c-slur-matching"]
    assert len(slur_errs) == 1
    assert "Unclosed slur bracket starting at measure 1" in slur_errs[0].message

    # 2. Slur bracket close without open: ⠐⠹⠘⠆
    brf = "⠐⠹⠘⠆"
    score = parse_brf(brf)
    result = validator.validate(score)
    slur_errs = [c for c in result.corrections if c.rule_id == "S9c-slur-matching"]
    assert len(slur_errs) == 1
    assert "Slur bracket close without preceding bracket open" in slur_errs[0].message


def test_validation_redundant_accidental():
    # Key signature G major (1 sharp: F sharp is ⠩).
    # Writing F sharp with explicit sharp accidental: ⠩\n⠐⠩⠻ (accidental ⠩ before F note ⠻)
    brf = "⠩\n⠐⠩⠻"
    score = parse_brf(brf)

    validator = BANAValidator(profile="strict")
    result = validator.validate(score)
    red_accs = [c for c in result.corrections if c.rule_id == "S9c-redundant-accidental"]
    assert len(red_accs) == 1
    assert "Redundant accidental on note 'F'" in red_accs[0].message


def test_validation_measure_repeat():
    # Two identical measures: ⠐⠹⠀⠐⠹
    brf = "⠐⠹⠀⠐⠹"
    score = parse_brf(brf)
    validator = BANAValidator(profile="strict")
    result = validator.validate(score)
    repeats = [c for c in result.corrections if c.rule_id == "S9c-measure-repeat"]
    assert len(repeats) == 1
    assert "Measure 2 is identical to measure 1" in repeats[0].message

