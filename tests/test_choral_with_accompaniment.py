import pytest
from dottednotes.models import Score, Staff, Note, Duration, Measure, TimeSignature
from dottednotes.renderers.braille_renderer import BrailleRenderer, TranscriptionMode
from dottednotes.parser.choral_with_accompaniment_parser import parse_choral_with_accompaniment
from dottednotes.parser.choral_with_orchestra_parser import parse_choral_with_orchestra
from dottednotes.exceptions import BrailleParseError


def _note(name, octave, **kwargs):
    return Note(dots=frozenset(), category=None, raw_brl="", note_name=name, octave=octave,
                duration=Duration(value=4), **kwargs)


def _voice_staff(name, notes, lyrics):
    staff = Staff(name=name)
    staff.time_signature = TimeSignature(
        dots=frozenset(), category=None, raw_brl="", numerator=4, denominator=4
    )
    m = Measure(number=1)
    for n in notes:
        m.add_note(n)
    staff.add_measure(m)
    staff.lyrics = lyrics
    return staff


def _keyboard_staff(name, notes):
    staff = Staff(name=name)
    staff.time_signature = TimeSignature(
        dots=frozenset(), category=None, raw_brl="", numerator=4, denominator=4
    )
    m = Measure(number=1)
    for n in notes:
        m.add_note(n)
    staff.add_measure(m)
    return staff


def _satb_with_piano_score(lh=True):
    score = Score(title="")
    score.add_staff(_voice_staff(
        "Soprano", [_note("C", 5), _note("D", 5), _note("E", 5), _note("F", 5)],
        ["Sing", "a", "song", "now"],
    ))
    score.add_staff(_voice_staff(
        "Alto", [_note("A", 4), _note("A", 4), _note("A", 4), _note("A", 4)],
        ["Play", "a", "tune", "well"],
    ))
    score.add_staff(_voice_staff(
        "Tenor", [_note("F", 4), _note("F", 4), _note("F", 4), _note("F", 4)],
        ["Hum", "a", "line", "here"],
    ))
    score.add_staff(_voice_staff(
        "Bass", [_note("C", 4), _note("C", 4), _note("C", 4), _note("C", 4)],
        ["Deep", "and", "low", "voice"],
    ))
    score.add_staff(_keyboard_staff(
        "Piano right hand", [_note("C", 5), _note("D", 5), _note("E", 5), _note("F", 5)],
    ))
    if lh:
        score.add_staff(_keyboard_staff(
            "Piano left hand", [_note("C", 3), _note("C", 3), _note("C", 3), _note("C", 3)],
        ))
    return score


def _satb_with_orchestra_score():
    score = Score(title="")
    score.add_staff(_voice_staff(
        "Soprano", [_note("C", 5), _note("D", 5), _note("E", 5), _note("F", 5)],
        ["Sing", "a", "song", "now"],
    ))
    score.add_staff(_voice_staff(
        "Alto", [_note("A", 4), _note("A", 4), _note("A", 4), _note("A", 4)],
        ["Play", "a", "tune", "well"],
    ))
    score.add_staff(_keyboard_staff(
        "Violin", [_note("C", 5), _note("D", 5), _note("E", 5), _note("F", 5)],
    ))
    score.add_staff(_keyboard_staff(
        "Cello", [_note("C", 3), _note("C", 3), _note("C", 3), _note("C", 3)],
    ))
    return score


# ---------------------------------------------------------------------------
# BANA §37.1 + §29.8: a vocal ensemble (2+ voices) with keyboard
# accompaniment is transcribed as two separate blocks -- the ensemble per
# §37.1, the accompaniment separately per §29.8, with an outline of a
# reader-selected lead voice (BANA leaves this to the transcriber's
# judgment, not a fixed "always soprano" rule).
# ---------------------------------------------------------------------------


def test_satb_with_piano_is_detected_as_choral_with_accompaniment():
    score = _satb_with_piano_score()
    renderer = BrailleRenderer(line_width=40)
    assert renderer._detect_transcription_mode(score) == TranscriptionMode.CHORAL_WITH_ACCOMPANIMENT


def test_two_voice_ensemble_with_single_hand_keyboard_is_also_choral_with_accompaniment():
    score = _satb_with_piano_score(lh=False)
    score.staves = score.staves[:2] + score.staves[4:]
    renderer = BrailleRenderer(line_width=40)
    assert renderer._detect_transcription_mode(score) == TranscriptionMode.CHORAL_WITH_ACCOMPANIMENT


def test_satb_alone_is_still_plain_choral_ensemble():
    score = _satb_with_piano_score()
    score.staves = score.staves[:4]
    renderer = BrailleRenderer(line_width=40)
    assert renderer._detect_transcription_mode(score) == TranscriptionMode.CHORAL_ENSEMBLE


def test_default_lead_voice_is_soprano():
    score = _satb_with_piano_score()
    renderer = BrailleRenderer(line_width=40)
    lead = renderer._lead_voice_staff(score.staves[:4])
    assert lead.name == "Soprano"


def test_lead_voice_override_picks_named_staff():
    score = _satb_with_piano_score()
    renderer = BrailleRenderer(line_width=40, lead_voice="Alto")
    lead = renderer._lead_voice_staff(score.staves[:4])
    assert lead.name == "Alto"


def test_lead_voice_override_is_case_insensitive():
    score = _satb_with_piano_score()
    renderer = BrailleRenderer(line_width=40, lead_voice="tenor")
    lead = renderer._lead_voice_staff(score.staves[:4])
    assert lead.name == "Tenor"


def test_unmatched_lead_voice_raises():
    score = _satb_with_piano_score()
    renderer = BrailleRenderer(line_width=40, lead_voice="Baritone")
    with pytest.raises(ValueError):
        renderer._lead_voice_staff(score.staves[:4])


def test_outline_line_present_by_default_and_carries_soprano():
    score = _satb_with_piano_score()
    output = BrailleRenderer(line_width=40).render(score)
    assert '⠐⠜' in output  # solo-outline hand sign


def test_no_accompaniment_outline_omits_outline_line():
    score = _satb_with_piano_score()
    output = BrailleRenderer(line_width=40, include_accompaniment_outline=False).render(score)
    assert '⠐⠜' not in output
    # Right hand still present.
    assert '⠨⠜' in output


def test_choral_with_accompaniment_round_trips_through_parser():
    score = _satb_with_piano_score()
    output = BrailleRenderer(line_width=40).render(score)

    parsed = parse_choral_with_accompaniment(output)

    assert len(parsed.staves) == 6
    soprano = parsed.staves[0]
    assert soprano.lyrics == ["Sing", "a", "song", "now"]
    rh = parsed.staves[4]
    assert [(n.note_name, n.octave) for n in rh.measures[0].notes] == [
        ("C", 5), ("D", 5), ("E", 5), ("F", 5),
    ]


def test_mismatched_measure_counts_between_vocal_and_keyboard_raises():
    score = _satb_with_piano_score()
    extra = Measure(number=2)
    extra.add_note(_note("G", 5))
    score.staves[4].add_measure(extra)  # RH gets an extra measure

    with pytest.raises(ValueError):
        BrailleRenderer(line_width=40).render(score)


# ---------------------------------------------------------------------------
# BANA §37.1 + §33: a vocal ensemble with instrumental-ensemble (orchestral/
# pit) accompaniment is two separate blocks -- no outline mechanism exists
# for a non-keyboard accompaniment.
# ---------------------------------------------------------------------------


def test_satb_with_orchestra_is_detected_as_choral_with_orchestra():
    score = _satb_with_orchestra_score()
    renderer = BrailleRenderer(line_width=40)
    assert renderer._detect_transcription_mode(score) == TranscriptionMode.CHORAL_WITH_ORCHESTRA


def test_choral_with_orchestra_never_renders_an_outline():
    score = _satb_with_orchestra_score()
    output = BrailleRenderer(line_width=40).render(score)
    assert '⠐⠜' not in output


def test_choral_with_orchestra_round_trips_through_parser():
    score = _satb_with_orchestra_score()
    output = BrailleRenderer(line_width=40).render(score)

    parsed = parse_choral_with_orchestra(output)

    assert len(parsed.staves) == 4
    soprano = parsed.staves[0]
    assert soprano.lyrics == ["Sing", "a", "song", "now"]
