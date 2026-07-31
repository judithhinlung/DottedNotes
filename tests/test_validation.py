import pytest
from dottednotes.parser.braille_parser import BrailleParser
from dottednotes.parser.tokenizer import BrailleTokenizer
from dottednotes.validation.validator import BANAValidator, Correction
from dottednotes.models.score import Score
from dottednotes.models.staff import Staff
from dottednotes.models.measure import Measure
from dottednotes.models.note import Note, Rest
from dottednotes.models.duration import Duration
from dottednotes.models.dynamic import Dynamic, DynamicLevel


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
    # a measure boundary), so this is a line-boundary reset -- see
    # test_validation_octave_marks_new_measure_same_line below for a case
    # that isolates a measure boundary from a line boundary (and does NOT
    # require a mark there, since the renderer only forces one at a real
    # line start, per Note.to_braille()'s is_measure_start semantics).
    # ⠐⠹ (line 1)
    # ⠱ (line 2, lacks octave mark)
    brf = "⠐⠹\n⠱"
    score = parse_brf(brf)
    validator = BANAValidator()
    result = validator.validate(score, raw_brl_text=brf)
    missing_new_line = [c for c in result.corrections if "new line" in c.message]
    assert len(missing_new_line) == 1

    # Reset point: after numeric indicator (measure number ⠃)
    brf = "⠁⠀⠐⠹\n⠃⠀⠱"  # Line 2 starts with measure number 2, D4 lacks octave mark
    score = parse_brf(brf)
    result = validator.validate(score, raw_brl_text=brf)
    missing_num = [c for c in result.corrections if "after numeric indicator" in c.message]
    assert len(missing_num) == 1


def test_validation_octave_marks_new_measure_same_line():
    # Two measures on ONE line (BRF measure separator '⠀'): the second
    # measure's first note (D4) is a 2nd away from the previous note (C4).
    # Note.to_braille()'s real is_measure_start semantics only force an
    # octave mark for a measure that starts a new physical LINE -- a measure
    # that fits mid-line (like this one) gets no forced mark, so neither a
    # missing-mark nor a redundant-mark correction should fire here.
    brf = "⠐⠹⠀⠱"
    score = parse_brf(brf)
    validator = BANAValidator()
    result = validator.validate(score, raw_brl_text=brf)
    missing = [c for c in result.corrections if "Missing octave mark" in c.message]
    assert len(missing) == 0
    redundant = [c for c in result.corrections if "Redundant" in c.message]
    assert len(redundant) == 0


def test_validation_octave_marks_no_flood_on_multi_measure_per_line_ensemble_fixture():
    # Regression test (S10d-1): _validate_octave_marks used to treat every
    # measure-number change as a reset point, flooding "Missing octave
    # mark" corrections on any real fixture with more than one measure per
    # line -- confirmed empirically at 97 false positives on this exact
    # fixture before the fix (a real 6-staff ensemble BRF, not synthetic).
    # After the fix, the reset check only fires at genuine physical-line
    # starts, and none of the 97 were genuine (this fixture has none
    # missing). This fixture does still report 66 "Redundant octave mark"
    # corrections -- a different, pre-existing check (unmodified by this
    # fix) that was previously masked entirely, since the old buggy code
    # treated every measure-boundary note as a required reset point and
    # never even considered whether an already-present mark was redundant;
    # those are a separate, plausible finding (the fixture likely predates
    # this project's line-start-only octave-marking convention), not the
    # flood this test guards against.
    from dottednotes.parser.input_pipeline import BRLInputPipeline
    from dottednotes.parser.ensemble_parser import EnsembleParser
    from pathlib import Path

    fixtures = Path(__file__).parent / "fixtures"
    text = BRLInputPipeline().load(fixtures / "fengyang_flower_drum.brf")
    score = EnsembleParser().parse(text)
    validator = BANAValidator()
    result = validator.validate(score, raw_brl_text=text)
    missing_octave = [
        c for c in result.corrections
        if c.rule_id == "S9b-3" and "Missing octave mark" in c.message
    ]
    assert len(missing_octave) == 0


def test_validation_octave_marks_reports_real_line_numbers_for_solo_multiline_score():
    # Regression test (S10d-2): line numbers used to fall back to a
    # constant 1 whenever Note.parsed_tokens was empty -- true for every
    # MusicXML/LilyPond-imported note, never just for the first physical
    # line. Build a score long enough to force multiple rendered lines,
    # corrupt the octave mark on a note that starts a later line, and
    # confirm the reported line number is that later line, not 1.
    import copy
    from pathlib import Path
    from dottednotes.parser.input_pipeline import BRLInputPipeline
    from dottednotes.cli import _parse_score

    fixtures = Path(__file__).parent / "fixtures"
    text = BRLInputPipeline().load(fixtures / "g_major_scale.brf")
    score = _parse_score(text)
    staff = score.staves[0]
    base_measures = staff.measures
    new_measures = []
    num = 1
    for _ in range(10):
        for m in base_measures:
            m2 = copy.deepcopy(m)
            m2.number = num
            num += 1
            new_measures.append(m2)
    staff.measures = new_measures

    rendered = score.to_braille()
    validator = BANAValidator()
    result = validator.validate(score, raw_brl_text=rendered)
    octave_corrections = [c for c in result.corrections if c.rule_id == "S9b-3" and "Missing" in c.message]
    reported_lines = {c.line_number for c in octave_corrections}
    # Every reset point after the first should be on a line other than the
    # very first content line -- if the fix regressed to "Line 1" for
    # everything, this set would collapse to {1} (or {2}) alone.
    assert len(reported_lines) > 1


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


def test_validation_line_length_proposes_break_at_a_blank_cell():
    # S10d-14: the break-point proposal used to split on literal ASCII
    # space, which a real over-length line (BRLInputPipeline-normalized,
    # or freshly rendered by BrailleRenderer/BRFWriter) never contains --
    # only '⠀' (U+2800). Before this fix, a real over-length line always
    # got no break-point suggestion at all, regardless of where a blank
    # cell actually was.
    long_line = ('⠹' * 20) + '⠀' + ('⠹' * 25)  # 46 cells, one blank at column 20
    score = parse_brf("⠹")
    validator = BANAValidator(column_limit=40)
    result = validator.validate(score, raw_brl_text=long_line)
    too_long = [c for c in result.corrections if c.rule_id == "S9b-4"]
    assert len(too_long) == 1
    assert too_long[0].proposed_fix == "Break line at column 20"


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


def test_validation_beat_count_uses_staff_time_signature():
    # Regression test: _validate_beat_count() used to read the never-populated
    # Measure.time_signature tuple (always its (4, 4) default) instead of the
    # staff's actual parsed TimeSignature, so every non-4/4 piece was flagged
    # on every measure ("expected 4.0 beats") even when correctly notated.
    # See tests/fixtures/mystery cue.brf (6/8) for the real-world report this
    # came from.
    from dottednotes.models.time_signature import TimeSignature

    # 6/8 measure, full: three quarter-beats via six eighth notes (C4 x6).
    notes = [
        Note(dots=frozenset(), category=None, raw_brl="", note_name="C", octave=4,
             duration=Duration(value=8))
        for _ in range(6)
    ]
    measure = Measure(number=1, notes=notes)
    time_sig = TimeSignature(dots=frozenset(), category=None, raw_brl="", numerator=6, denominator=8)
    staff = Staff(name="Test", time_signature=time_sig, measures=[measure])
    score = Score(staves=[staff])

    validator = BANAValidator()
    result = validator.validate(score)
    beat_errs = [c for c in result.corrections if c.rule_id == "S9c-beat-count"]
    assert beat_errs == []


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


def test_validation_no_redundant_accidental_for_unmarked_key_signature_note():
    # Regression guard: an unmarked F in a G major key signature now parses
    # with an *inferred* (Accidental.explicit=False) sharp -- this must not
    # be reported as a redundant explicit accidental, since none was
    # written in the source at all.
    brf = "⠩\n⠐⠻"
    score = parse_brf(brf)

    validator = BANAValidator(profile="strict")
    result = validator.validate(score)
    red_accs = [c for c in result.corrections if c.rule_id == "S9c-redundant-accidental"]
    assert red_accs == []


def test_validation_measure_repeat():
    # Two identical measures: ⠐⠹⠀⠐⠹
    brf = "⠐⠹⠀⠐⠹"
    score = parse_brf(brf)
    validator = BANAValidator(profile="strict")
    result = validator.validate(score)
    repeats = [c for c in result.corrections if c.rule_id == "S9c-measure-repeat"]
    assert len(repeats) == 1
    assert "Measure 2 is identical to measure 1" in repeats[0].message


def test_validation_measure_repeat_not_suggested_for_whole_measure_rests():
    # BANA Par. 18.2: "It is never, however, used to represent a full
    # measure of rest; the measure rest sign must be used." Two
    # identical whole-measure rests must not trigger the "consider a
    # measure repeat sign" suggestion.
    staff = Staff(name="Violin")
    for n in [1, 2]:
        m = Measure(number=n)
        m.add_note(Rest(dots=frozenset(), category=None, raw_brl="", duration=Duration(value=1, dots=0), is_full_measure=True))
        staff.add_measure(m)
    score = Score(title="T")
    score.add_staff(staff)

    validator = BANAValidator(profile="strict")
    result = validator.validate(score)
    repeats = [c for c in result.corrections if c.rule_id == "S9c-measure-repeat"]
    assert len(repeats) == 0


def _hairpin_note(name, octave, dynamics=None):
    n = Note(dots=frozenset(), category=None, raw_brl="", note_name=name, octave=octave,
              duration=Duration(value=4))
    if dynamics:
        n.dynamics.extend(dynamics)
    return n


def test_validation_hairpin_terminator_omission_reports_reason():
    # "hairpin-terminator-omission" is informational (severity "info"),
    # reporting the same decision BrailleRenderer acts on -- confirmed
    # against MBC-2015 Par. 22.3.3(b)/Table 22(C).
    staff = Staff(name="Violin")
    m = Measure(number=1, bar_line_type='final_double_bar')
    m.add_note(_hairpin_note("C", 5, [Dynamic(level=DynamicLevel.CRESCENDO_START)]))
    m.add_note(_hairpin_note("D", 5, [Dynamic(level=DynamicLevel.CRESCENDO_END)]))
    staff.add_measure(m)
    score = Score(title="T")
    score.add_staff(staff)

    validator = BANAValidator()
    result = validator.validate(score)
    hairpin_corrections = [c for c in result.corrections if c.rule_id == "hairpin-terminator-omission"]
    assert len(hairpin_corrections) == 1
    assert hairpin_corrections[0].severity == "info"
    assert "omitted" in hairpin_corrections[0].message
    assert "final double bar" in hairpin_corrections[0].message


def test_validation_hairpin_terminator_kept_reports_explicit():
    staff = Staff(name="Violin")
    m = Measure(number=1, bar_line_type='measure_separator')
    m.add_note(_hairpin_note("C", 5, [Dynamic(level=DynamicLevel.CRESCENDO_START)]))
    m.add_note(_hairpin_note("D", 5, [Dynamic(level=DynamicLevel.CRESCENDO_END)]))
    m.add_note(_hairpin_note("E", 5))
    staff.add_measure(m)
    score = Score(title="T")
    score.add_staff(staff)

    validator = BANAValidator()
    result = validator.validate(score)
    hairpin_corrections = [c for c in result.corrections if c.rule_id == "hairpin-terminator-omission"]
    assert len(hairpin_corrections) == 1
    assert "brailled explicitly" in hairpin_corrections[0].message


def test_validation_hairpin_terminator_omission_in_both_profiles():
    assert "hairpin-terminator-omission" in BANAValidator(profile="standard").enabled_rules
    assert "hairpin-terminator-omission" in BANAValidator(profile="strict").enabled_rules

