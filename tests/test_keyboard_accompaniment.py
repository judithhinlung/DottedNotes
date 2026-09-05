from dottednotes.models import Score, Staff, Note, Duration, Measure, TimeSignature
from dottednotes.models.dynamic import Dynamic, DynamicLevel
from dottednotes.models.fermata import Fermata
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

    # Accompaniment block: outline (bare ⠜, carries the measure number),
    # then right hand (⠨⠜), then left hand (⠸⠜) -- neither hand line
    # carries the measure number (§29.8: it's on the outline line instead).
    accompaniment_body = [l for l in accompaniment_block if l]
    outline_line, rh_line, lh_line = accompaniment_body[-3:]
    assert outline_line.startswith('⠁⠀⠜')
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
