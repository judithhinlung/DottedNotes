import pytest
from dottednotes.models import Score, Staff, Note, Rest, Duration, Measure, TimeSignature
from dottednotes.renderers.braille_renderer import BrailleRenderer, TranscriptionMode
from dottednotes.parser.choral_ensemble_parser import parse_choral_ensemble
from dottednotes.exceptions import BrailleParseError


def _note(name, octave, **kwargs):
    return Note(dots=frozenset(), category=None, raw_brl="", note_name=name, octave=octave,
                duration=Duration(value=4), **kwargs)


def _rest(**kwargs):
    return Rest(dots=frozenset(), category=None, raw_brl="", duration=Duration(value=1),
                is_full_measure=True, **kwargs)


def _two_voice_score():
    score = Score(title="")
    sop = Staff(name="Soprano")
    sop.time_signature = TimeSignature(
        dots=frozenset(), category=None, raw_brl="", numerator=4, denominator=4
    )
    alto = Staff(name="Alto")
    alto.time_signature = sop.time_signature

    m1 = Measure(number=1)
    for note in (_note("C", 5), _note("D", 5), _note("E", 5), _note("F", 5)):
        m1.add_note(note)
    sop.add_measure(m1)
    sop.lyrics = ["Sing", "a", "song", "now"]

    m2 = Measure(number=1)
    for note in (_note("A", 4), _note("A", 4), _note("A", 4), _note("A", 4)):
        m2.add_note(note)
    alto.add_measure(m2)
    alto.lyrics = ["Play", "a", "tune", "well"]

    score.add_staff(sop)
    score.add_staff(alto)
    return score


# ---------------------------------------------------------------------------
# S11c-12: BANA §37.1 expanded bar-over-bar format for vocal ensembles --
# word lines (cell 1) for every voice, then that parallel's music lines
# (cell 3), never interleaved per voice the way §33's ENSEMBLE format is.
# Word-line content here follows S11c-14's baseline (always one identified
# line per voice) -- S11c-13 layers the §37.2 shared-line case on top.
# ---------------------------------------------------------------------------


def test_choral_ensemble_is_detected_as_its_own_mode_not_ensemble():
    score = _two_voice_score()
    renderer = BrailleRenderer(line_width=40)
    assert renderer._detect_transcription_mode(score) == TranscriptionMode.CHORAL_ENSEMBLE


def test_choral_ensemble_renders_word_lines_then_music_lines():
    score = _two_voice_score()
    output = BrailleRenderer(line_width=40).render(score)
    lines = [l for l in output.split("\n") if l]

    # lines[0] is the cell-9 signature header.
    word_lines = lines[1:3]
    music_lines = lines[3:5]

    for wl in word_lines:
        assert not wl.startswith('⠀')          # cell 1
        assert wl.startswith('⠜')               # identified (S11c-14)
    for ml in music_lines:
        assert ml.startswith('⠀⠀⠜')             # cell 3, identified


def test_choral_ensemble_round_trips_through_parser():
    score = _two_voice_score()
    output = BrailleRenderer(line_width=40).render(score)

    parsed = parse_choral_ensemble(output)

    assert len(parsed.staves) == 2
    soprano, alto = parsed.staves
    assert soprano.lyrics == ["Sing", "a", "song", "now"]
    assert alto.lyrics == ["Play", "a", "tune", "well"]
    assert [(n.note_name, n.octave) for n in soprano.measures[0].notes] == [
        ("C", 5), ("D", 5), ("E", 5), ("F", 5),
    ]
    assert [(n.note_name, n.octave) for n in alto.measures[0].notes] == [
        ("A", 4), ("A", 4), ("A", 4), ("A", 4),
    ]


def test_choral_ensemble_round_trips_across_multiple_parallels_with_run_overs():
    score = Score(title="")
    sop = Staff(name="Soprano")
    sop.time_signature = TimeSignature(
        dots=frozenset(), category=None, raw_brl="", numerator=4, denominator=4
    )
    alto = Staff(name="Alto")
    alto.time_signature = sop.time_signature

    for i in range(3):
        ms = Measure(number=i + 1)
        ma = Measure(number=i + 1)
        for name in ("C", "D", "E", "F"):
            ms.add_note(_note(name, 5))
            ma.add_note(_note("A", 4))
        sop.add_measure(ms)
        alto.add_measure(ma)

    sop.lyrics = ["One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten", "Eleven", "Twelve"]
    alto.lyrics = ["Un", "Deux", "Trois", "Quatre", "Cinq", "Six", "Sept", "Huit", "Neuf", "Dix", "Onze", "Douze"]

    score.add_staff(sop)
    score.add_staff(alto)

    output = BrailleRenderer(line_width=20).render(score)
    parsed = parse_choral_ensemble(output)

    assert len(parsed.staves) == 2
    assert parsed.staves[0].lyrics == sop.lyrics
    assert parsed.staves[1].lyrics == alto.lyrics
    assert len(parsed.staves[0].measures) == 3
    assert len(parsed.staves[1].measures) == 3


def test_choral_ensemble_omits_tacet_voice_from_its_own_parallel():
    # BANA §37.1(c): "A part that has rests throughout the music included
    # in a parallel is omitted in that parallel."
    score = Score(title="")
    sop = Staff(name="Soprano")
    sop.time_signature = TimeSignature(
        dots=frozenset(), category=None, raw_brl="", numerator=4, denominator=4
    )
    alto = Staff(name="Alto")
    alto.time_signature = sop.time_signature

    m1s, m1a = Measure(number=1), Measure(number=1)
    for name in ("C", "D", "E", "F"):
        m1s.add_note(_note(name, 5))
        m1a.add_note(_note("A", 4))
    m2s, m2a = Measure(number=2), Measure(number=2)
    for name in ("G", "A", "B", "C"):
        m2s.add_note(_note(name, 5))
    m2a.add_note(_rest())

    sop.add_measure(m1s); sop.add_measure(m2s)
    alto.add_measure(m1a); alto.add_measure(m2a)
    sop.lyrics = ["Sing", "a", "song", "now", "La", "la", "la", "la"]
    alto.lyrics = ["Play", "a", "tune", "well"]

    score.add_staff(sop)
    score.add_staff(alto)

    # Narrow width forces one measure per parallel, so the tacet measure
    # becomes its own parallel where alto can be genuinely omitted.
    output = BrailleRenderer(line_width=15).render(score)
    body_lines = [l for l in output.split("\n") if l]

    # The second parallel's word+music lines must not mention alto ("al").
    second_parallel_lines = body_lines[-3:]
    assert not any('⠜⠁⠇⠄' in l for l in second_parallel_lines)

    # The resulting per-voice measure-count mismatch is a documented,
    # explicit parser limitation (not yet supported) -- must raise clearly,
    # never silently misalign the voices.
    with pytest.raises(BrailleParseError):
        parse_choral_ensemble(output)


def test_choral_ensemble_does_not_compress_repeated_measure_into_measure_repeat_sign():
    score = Score(title="")
    sop = Staff(name="Soprano")
    sop.time_signature = TimeSignature(
        dots=frozenset(), category=None, raw_brl="", numerator=4, denominator=4
    )
    alto = Staff(name="Alto")
    alto.time_signature = sop.time_signature
    for i in range(2):
        ms, ma = Measure(number=i + 1), Measure(number=i + 1)
        for name in ("C", "D", "E", "F"):
            ms.add_note(_note(name, 5))
            ma.add_note(_note("A", 4))
        sop.add_measure(ms)
        alto.add_measure(ma)
    sop.lyrics = ["One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight"]
    alto.lyrics = ["Un", "Deux", "Trois", "Quatre", "Cinq", "Six", "Sept", "Huit"]
    score.add_staff(sop)
    score.add_staff(alto)

    output = BrailleRenderer(line_width=15).render(score)
    assert '⠶' not in output

    parsed = parse_choral_ensemble(output)
    assert parsed.staves[0].lyrics == sop.lyrics
    assert parsed.staves[1].lyrics == alto.lyrics


# ---------------------------------------------------------------------------
# S11c-13: BANA §37.2 shared word line -- one unidentified word line when
# every active voice sings the same words, instead of S11c-14's baseline
# one-identified-line-per-voice.
# ---------------------------------------------------------------------------


def _shared_lyrics_score():
    score = Score(title="")
    sop = Staff(name="Soprano")
    sop.time_signature = TimeSignature(
        dots=frozenset(), category=None, raw_brl="", numerator=4, denominator=4
    )
    alto = Staff(name="Alto")
    alto.time_signature = sop.time_signature

    m1 = Measure(number=1)
    for name in ("C", "D", "E", "F"):
        m1.add_note(_note(name, 5))
    sop.add_measure(m1)
    sop.lyrics = ["Sing", "a", "song", "now"]

    m2 = Measure(number=1)
    for name in ("A", "B", "C", "D"):
        m2.add_note(_note(name, 4))
    alto.add_measure(m2)
    alto.lyrics = ["Sing", "a", "song", "now"]  # identical words, different notes/rhythm

    score.add_staff(sop)
    score.add_staff(alto)
    return score


def test_choral_ensemble_shared_lyrics_render_as_one_unidentified_word_line():
    score = _shared_lyrics_score()
    output = BrailleRenderer(line_width=40).render(score)
    lines = [l for l in output.split("\n") if l]

    # lines[0] is the signature header; lines[1] is the (single) word line.
    assert not lines[1].startswith('⠜')
    # Exactly one word line, followed directly by two identified music lines.
    assert lines[2].lstrip('⠀').startswith('⠜')
    assert lines[3].lstrip('⠀').startswith('⠜')


def test_choral_ensemble_shared_lyrics_round_trip():
    score = _shared_lyrics_score()
    output = BrailleRenderer(line_width=40).render(score)

    parsed = parse_choral_ensemble(output)

    assert len(parsed.staves) == 2
    soprano, alto = parsed.staves
    assert soprano.lyrics == ["Sing", "a", "song", "now"]
    assert alto.lyrics == ["Sing", "a", "song", "now"]
    assert [(n.note_name, n.octave) for n in soprano.measures[0].notes] == [
        ("C", 5), ("D", 5), ("E", 5), ("F", 5),
    ]
    assert [(n.note_name, n.octave) for n in alto.measures[0].notes] == [
        ("A", 4), ("B", 4), ("C", 4), ("D", 4),
    ]


def test_choral_ensemble_differing_lyrics_still_use_per_voice_identified_lines():
    # Sanity check that S11c-13's shared-line detection doesn't fire when
    # words actually differ (S11c-14's baseline still applies).
    score = _two_voice_score()
    output = BrailleRenderer(line_width=40).render(score)
    lines = [l for l in output.split("\n") if l]
    assert lines[1].startswith('⠜')
    assert lines[2].startswith('⠜')
