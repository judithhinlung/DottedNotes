"""Tests for BrailleRenderer's multi-measure-rest compaction (S11c-7,
BANA Music Braille Code 2015, Par. 5.3): 2+ consecutive whole-measure
rests must braille as one compact sign, not one whole-rest cell per
measure. Unlike the compression_level/full_measure_repeat passes covered
in test_compression.py/test_full_measure_repeat.py, this is mandatory
BANA transcription and always runs.
"""
import warnings
from pathlib import Path

from dottednotes.models.note import Note, Rest
from dottednotes.models.measure import Measure
from dottednotes.models.duration import Duration
from dottednotes.models.staff import Staff
from dottednotes.models.score import Score
from dottednotes.models.text_marking import TextMarking, TextMarkingType
from dottednotes.renderers.braille_renderer import BrailleRenderer
from dottednotes.parser.input_pipeline import BRLInputPipeline
from dottednotes.parser.ensemble_parser import EnsembleParser

FIXTURES = Path(__file__).parent / "fixtures"


def _note(name="C", octave=5, value=4):
    return Note(dots=frozenset(), category=None, raw_brl="", note_name=name, octave=octave, duration=Duration(value))


def _rest(number, value=4, bar_line_type='measure_separator', text_markings=None, ending_numbers=None):
    m = Measure(number=number, bar_line_type=bar_line_type, ending_numbers=ending_numbers)
    if text_markings:
        m.text_markings = text_markings
    m.add_note(Rest(dots=frozenset(), category=None, raw_brl="", duration=Duration(value), is_full_measure=True))
    return m


def _note_measure(number, name="C", octave=5, value=4):
    return Measure(number=number, notes=[_note(name, octave, value)])


def _solo_score(measures: list[Measure]) -> Score:
    staff = Staff(name="Violin", clef=None, key_signature=None, time_signature=None)
    staff.measures = measures
    return Score(title="", staves=[staff])


def test_solo_merges_consecutive_full_measure_rests_into_compact_sign():
    measures = [_note_measure(1), _rest(2), _rest(3), _rest(4), _note_measure(5, "D")]
    score = _solo_score(measures)
    output = BrailleRenderer(show_measure_numbers=False).render(score)
    assert '⠍⠍⠍' in output
    assert '⠍⠍⠍⠍' not in output
    assert output.count('⠍') == 3


def test_lone_full_measure_rest_is_not_merged():
    measures = [_note_measure(1), _rest(2), _note_measure(3, "D")]
    score = _solo_score(measures)
    output = BrailleRenderer(show_measure_numbers=False).render(score)
    # A single rest measure stays the plain sign, never the numeral form.
    assert '⠍' in output
    assert '⠼' not in output


def test_auto_numbering_counts_a_merged_run_as_its_real_measure_span():
    # 5 real measures: 1 note, then a 3-measure rest run (2-4), then 1
    # more note at real measure 5. After compaction the rendered list is
    # only 3 slots long, but "auto" numbering must still show the note
    # after the run as measure 5, not 3 (which is what position + 1 would
    # give against the shortened list -- the S11c-7 numbering bug this
    # guards against).
    measures = [_note_measure(1), _rest(2), _rest(3), _rest(4), _note_measure(5, "D")]
    score = _solo_score(measures)
    # Force each measure onto its own line so every one gets a margin number.
    output = BrailleRenderer(line_width=1, measure_numbering="auto").render(score)
    lines = [l for l in output.splitlines() if l]
    assert lines[0].startswith('⠼⠁⠀')  # measure 1
    assert lines[-1].startswith('⠼⠑⠀')  # measure 5 (digit 5 = ⠑), not 3


def test_print_score_numbering_reads_the_survivor_measures_own_number():
    # "print_score" mode reads Measure.number directly off the surviving
    # (merged) measure, so it is unaffected by the list-shortening that
    # "auto" mode above needs _measure_span to correct for.
    measures = [_note_measure(1), _rest(2), _rest(3), _rest(4), _note_measure(99, "D")]
    score = _solo_score(measures)
    output = BrailleRenderer(line_width=1, measure_numbering="print_score").render(score)
    lines = [l for l in output.splitlines() if l]
    assert lines[0].startswith('⠼⠁⠀')
    assert lines[1].startswith('⠼⠃⠀')  # the merged run keeps its first real number (2)
    assert lines[-1].startswith('⠼⠊⠊⠀')  # digit 9 = ⠊, so "99"


def test_merge_stops_at_a_duration_change():
    # A differing Rest.duration implies a time-signature change mid-run
    # (a full-measure rest's duration reflects the active time signature's
    # total value) -- the two runs must not merge across it.
    measures = [
        _rest(1, value=4), _rest(2, value=4),
        _rest(3, value=2), _rest(4, value=2), _rest(5, value=2),
    ]
    score = _solo_score(measures)
    output = BrailleRenderer(show_measure_numbers=False).render(score)
    assert '⠍⠍' in output
    assert '⠍⠍⠍' in output
    assert '⠍⠍⠍⠍⠍' not in output


def test_merge_includes_a_special_bar_line_as_the_runs_last_member():
    # A repeat/double bar mid-run still needs its own sign after the
    # compact rest content, not silently dropped -- BANA_symbols maps
    # 'end_repeat' to the 2-cell sequence '⠣⠆'.
    measures = [
        _note_measure(1),
        _rest(2), _rest(3, bar_line_type='end_repeat'),
        _rest(4), _note_measure(5, "D"),
    ]
    score = _solo_score(measures)
    output = BrailleRenderer(show_measure_numbers=False).render(score)
    assert '⠍⠍⠣⠆' in output  # the 2-measure run (2-3), ending in the repeat sign
    assert '⠍⠀' in output    # measure 4 stands alone (run broke at the repeat bar)


def test_merge_does_not_absorb_a_text_marking_or_volta_ending():
    # A tempo/expression marking or a first/second-ending bracket on a
    # rest measure is a real, visible sign in its own right -- must not be
    # silently swallowed into a merged run.
    measures = [
        _note_measure(1),
        _rest(2),
        _rest(3, text_markings=[TextMarking(text="rit.", type=TextMarkingType.TEMPO)]),
        _rest(4),
        _note_measure(5, "D"),
    ]
    score = _solo_score(measures)
    output = BrailleRenderer(show_measure_numbers=False).render(score)
    assert '⠍⠍⠍' not in output  # never a 3-in-a-row compact run
    assert output.count('⠍') == 3  # all 3 rests still present, just not merged into one sign

    volta_measures = [
        _note_measure(1),
        _rest(2),
        _rest(3, ending_numbers=[1]),
        _rest(4),
        _note_measure(5, "D"),
    ]
    volta_score = _solo_score(volta_measures)
    volta_output = BrailleRenderer(show_measure_numbers=False).render(volta_score)
    assert '⠍⠍⠍' not in volta_output


def test_multi_staff_scores_do_not_merge_rests():
    # _render_piano/_render_ensemble walk multiple staves in lockstep by
    # shared measure index -- merging (and so shortening) only one
    # staff's measures list would desync that alignment. Confirmed here
    # with a 2-staff (piano) score: a 3-measure rest run in one hand must
    # stay 3 separate whole-rest cells, not a compact sign.
    rh = Staff(name="piano right hand")
    lh = Staff(name="piano left hand")
    for n in range(1, 4):
        rh.add_measure(_note_measure(n))
        lh.add_measure(_rest(n))
    score = Score(title="", staves=[rh, lh])
    output = BrailleRenderer(show_measure_numbers=False).render(score)
    assert '⠍⠍⠍' not in output
    assert output.count('⠍') == 3


def test_bartok_piccolo_flutes_extracted_part_compacts_its_long_rest_run():
    # Real-world repro (S11c-7): the developer extracted the Piccolo/
    # Flutes I/II part from this fixture (`--part 1`) and found an
    # 87-measure rest run printed as 87 individual whole-rest cells
    # instead of BANA's consolidated count sign. This part also carries
    # ensemble-resolved interval chords (S10d-13), so it renders via a
    # single-staff ENSEMBLE layout, not plain SOLO -- confirming the
    # compaction pass fires for that case too, not just plain solo scores.
    text = BRLInputPipeline().load(FIXTURES / "Bartok_Bella_Romanian_Folk_Dances_for_Orchestra.brl")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        score = EnsembleParser().parse(text)
    part = score.extract_part(0)
    assert part.staves[0].name.startswith("Piccolo")

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        output = part.to_braille()

    # '⠓⠛' = literary digits 8, 7 -- the 87-measure run's compact sign.
    assert '⠼⠓⠛⠍' in output
    # No 87-in-a-row run of bare whole-rest cells remains.
    assert '⠍' * 10 not in output
