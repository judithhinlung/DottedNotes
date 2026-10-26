import warnings

from dottednotes.models import Score, Staff, Note, Duration, Measure, TimeSignature
from dottednotes.models.dynamic import Dynamic, DynamicLevel
from dottednotes.models.fermata import Fermata
from dottednotes.parser.input_pipeline import BRLInputPipeline
from dottednotes.parser.keyboard_accompaniment_parser import parse_keyboard_accompaniment
from dottednotes.renderers.braille_renderer import (
    BrailleRenderer,
    TranscriptionMode,
    build_solo_outline_measures,
)
from dottednotes.parser.solo_with_accompaniment_parser import parse_solo_with_accompaniment


def _note(name, octave, **kwargs):
    return Note(dots=frozenset(), category=None, raw_brl="", note_name=name, octave=octave,
                duration=Duration(value=4), **kwargs)


def _score_with_lyrics_and_piano(lh=True):
    score = Score(title="")
    soprano = Staff(name="Soprano")
    soprano.time_signature = TimeSignature(
        dots=frozenset(), category=None, raw_brl="", numerator=4, denominator=4
    )
    m = Measure(number=1)
    for note in (_note("C", 5), _note("D", 5), _note("E", 5), _note("F", 5)):
        m.add_note(note)
    soprano.add_measure(m)
    soprano.lyrics = ["Sing", "a", "song", "now"]

    rh = Staff(name="Piano right hand")
    rh.time_signature = soprano.time_signature
    m2 = Measure(number=1)
    for note in (_note("G", 4), _note("G", 4), _note("G", 4), _note("G", 4)):
        m2.add_note(note)
    rh.add_measure(m2)

    score.add_staff(soprano)
    score.add_staff(rh)

    if lh:
        lh_staff = Staff(name="Piano left hand")
        lh_staff.time_signature = soprano.time_signature
        m3 = Measure(number=1)
        for note in (_note("C", 3), _note("C", 3), _note("C", 3), _note("C", 3)):
            m3.add_note(note)
        lh_staff.add_measure(m3)
        score.add_staff(lh_staff)

    return score


# ---------------------------------------------------------------------------
# S11c-10: BANA §29.8 keyboard-accompaniment format -- a solo (vocal or
# instrumental) part with piano accompaniment is transcribed as two
# separate blocks, not one ensemble parallel, with a solo-outline line
# above the right hand.
# ---------------------------------------------------------------------------


def test_solo_with_piano_is_detected_as_its_own_mode_not_ensemble():
    score = _score_with_lyrics_and_piano()
    renderer = BrailleRenderer(line_width=40)
    assert renderer._detect_transcription_mode(score) == TranscriptionMode.SOLO_WITH_ACCOMPANIMENT


def test_solo_instrument_with_single_hand_keyboard_reduction_is_not_piano_mode():
    # A 2-staff (non-keyboard, keyboard) score used to be misdetected as a
    # 2-hand PIANO solo (the old `any()` check), which would have treated
    # the solo instrument's own staff as if it were a piano right hand.
    score = _score_with_lyrics_and_piano(lh=False)
    renderer = BrailleRenderer(line_width=40)
    assert renderer._detect_transcription_mode(score) == TranscriptionMode.SOLO_WITH_ACCOMPANIMENT


def test_build_solo_outline_measures_keeps_notes_ties_fermatas_strips_the_rest():
    m = Measure(number=1)
    n = _note("C", 5, tie=True, fermata=Fermata())
    n.dynamics.append(Dynamic(level=DynamicLevel.F))
    n.slur_start = True
    m.add_note(n)
    n2 = _note("D", 5)
    n2.slur_end = True
    m.add_note(n2)

    outline = build_solo_outline_measures([m])
    outline_notes = outline[0].notes

    assert [(x.note_name, x.octave) for x in outline_notes] == [("C", 5), ("D", 5)]
    assert outline_notes[0].tie is True
    assert outline_notes[0].fermata is not None
    assert outline_notes[0].dynamics == []
    assert outline_notes[0].slur_start is False
    assert outline_notes[1].slur_end is False
    # The original measure is untouched (outline is a deep copy).
    assert m.notes[0].dynamics
    assert m.notes[0].slur_start is True


def test_render_solo_with_accompaniment_layout():
    score = _score_with_lyrics_and_piano()
    output = BrailleRenderer(line_width=40).render(score)
    lines = output.split("\n")

    # Two blocks separated by exactly one blank line (§29.8: transcribed
    # individually, then separately -- not one ensemble parallel).
    blank_indices = [i for i, l in enumerate(lines) if l == ""]
    assert len(blank_indices) >= 1
    solo_block = lines[:blank_indices[0]]
    accompaniment_block = lines[blank_indices[0] + 1:]

    # Solo block: lyric line then music line, no abbreviation (§35.1).
    solo_body = [l for l in solo_block if l]
    assert not solo_body[-2].startswith('⠀')   # lyric line at cell 1
    assert solo_body[-1].startswith('⠀⠀')      # music line at cell 3
    assert '⠨⠜' not in solo_body[-1] and '⠸⠜' not in solo_body[-1]

    # Accompaniment block: outline (⠐⠜, carries the measure number), then
    # right hand (⠨⠜), then left hand (⠸⠜) -- neither hand line carries
    # the measure number (§29.8: it's on the outline line instead).
    accompaniment_body = [l for l in accompaniment_block if l]
    outline_line, rh_line, lh_line = accompaniment_body[-3:]
    assert outline_line.startswith('⠁⠀⠐⠜')
    assert rh_line.lstrip('⠀').startswith('⠨⠜')
    assert lh_line.lstrip('⠀').startswith('⠸⠜')
    assert not rh_line.startswith('⠁')
    assert not lh_line.startswith('⠁')


def test_solo_with_accompaniment_round_trips_through_parser():
    score = _score_with_lyrics_and_piano()
    output = BrailleRenderer(line_width=40).render(score)

    parsed = parse_solo_with_accompaniment(output)

    assert len(parsed.staves) == 3
    solo, rh, lh = parsed.staves
    assert solo.lyrics == ["Sing", "a", "song", "now"]
    assert [(n.note_name, n.octave) for n in solo.measures[0].notes] == [
        ("C", 5), ("D", 5), ("E", 5), ("F", 5),
    ]
    assert [(n.note_name, n.octave) for n in rh.measures[0].notes] == [
        ("G", 4), ("G", 4), ("G", 4), ("G", 4),
    ]
    assert [(n.note_name, n.octave) for n in lh.measures[0].notes] == [
        ("C", 3), ("C", 3), ("C", 3), ("C", 3),
    ]


def test_solo_with_accompaniment_round_trips_with_single_hand_only():
    score = _score_with_lyrics_and_piano(lh=False)
    output = BrailleRenderer(line_width=40).render(score)

    parsed = parse_solo_with_accompaniment(output)

    assert len(parsed.staves) == 2
    solo, rh = parsed.staves
    assert solo.lyrics == ["Sing", "a", "song", "now"]
    assert [(n.note_name, n.octave) for n in rh.measures[0].notes] == [
        ("G", 4), ("G", 4), ("G", 4), ("G", 4),
    ]


# ---------------------------------------------------------------------------
# §29.8 outline-prefixed groups: the outline line's own margin number used
# to be discarded along with the rest of its content, disarming
# `BrailleParser`'s own measure-number cross-check for every group after
# the first; each hand also used to be parsed from one interleaved token
# stream, so a measure dividing across a line boundary (§29.3.1) bled a
# hand's leftover notes into the *other* hand's next measure instead of
# gluing onto its own next line. A right-hand-silent group (no asterisk/
# footnote per §29.6) is backfilled with a whole-measure rest so both
# staves stay the same length, rather than desyncing their measure counts.
# ---------------------------------------------------------------------------

def test_outline_margin_number_is_cross_checked_against_running_count():
    # Group "C" (margin 3) following group "A" (margin 1) skips the real
    # margin 2 -- BrailleParser's own mismatch warning must fire, proving
    # the margin number is actually read from the outline line rather than
    # discarded with the rest of its content.
    ascii_text = (
        '        %%%#F8\n'
        'A .>"F"F"F"F"F"F\n'
        '  _>"F"F"F"F"F"F\n'
        'C ">"F"F"F"F"F"F\n'
        '  .>"F"F"F"F"F"F\n'
        '  _>"F"F"F"F"F"F'
    )
    text = BRLInputPipeline()._ascii_to_unicode(ascii_text)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        parse_keyboard_accompaniment(text)
    messages = [str(w.message) for w in caught]
    assert any("measure number 3 found, expected 2" in m for m in messages), messages


def test_right_hand_silent_group_backfills_a_whole_measure_rest():
    # Group "B" has an outline and a left hand but no right-hand line at
    # all (the right hand rests for that measure, with no §29.6 asterisk/
    # footnote) -- the right hand must still end up with a measure there,
    # as a flagged rest, so both staves stay the same length.
    ascii_text = (
        '        %%%#F8\n'
        'A .>"F"F"F"F"F"F\n'
        '  _>"F"F"F"F"F"F\n'
        'B ">"F"F"F"F"F"F\n'
        '  _>"F"F"F"F"F"F\n'
        'C ">"F"F"F"F"F"F\n'
        '  .>"F"F"F"F"F"F\n'
        '  _>"F"F"F"F"F"F'
    )
    text = BRLInputPipeline()._ascii_to_unicode(ascii_text)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        score = parse_keyboard_accompaniment(text)

    rh, lh = score.staves
    assert [m.number for m in rh.measures] == [1, 2, 3]
    assert [m.number for m in lh.measures] == [1, 2, 3]
    backfilled = rh.measures[1]
    assert backfilled.total_ticks() == lh.measures[1].total_ticks()
    assert len(backfilled.notes) == 1
    assert type(backfilled.notes[0]).__name__ == "Rest"
    assert backfilled.notes[0].is_full_measure is True


def test_measure_divided_across_group_boundary_glues_into_one_measure():
    # A real BANA §29.3.1 case: the right hand's first group (margin 1)
    # closes a full measure, then starts a second one with 3 of its 6
    # eighths, ending mid-measure with a trailing music hyphen (dot 5,
    # last sign of the line) -- group "B" (margin 2) supplies the
    # remaining 3 eighths. That second measure must glue into one 6/8
    # measure (not bleed into the intervening left-hand line, and not be
    # double-counted), with no beat-count mismatch warning for it.
    rh_a = 'A .>' + '"F' * 6 + ' ' + '"F' * 3 + '"'
    lh_a = '  _>' + '"F' * 6 + ' ' + '"F' * 6
    rh_b_outline = 'B ">' + '"F' * 3
    rh_b = '  .>' + '"F' * 3
    lh_b = '  _>' + '"F' * 6
    ascii_text = '\n'.join([
        '        %%%#F8', rh_a, lh_a, rh_b_outline, rh_b, lh_b,
    ])
    text = BRLInputPipeline()._ascii_to_unicode(ascii_text)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        score = parse_keyboard_accompaniment(text)
    messages = [str(w.message) for w in caught]
    assert not any("measure 2" in m.lower() and "beats" in m for m in messages), messages

    rh, lh = score.staves
    assert rh.measures[0].total_ticks() == 72
    assert rh.measures[1].total_ticks() == lh.measures[1].total_ticks() == 72
    assert len(rh.measures[1].notes) == 6
