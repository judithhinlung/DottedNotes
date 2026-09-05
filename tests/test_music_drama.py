import warnings

from dottednotes.models import Score, Staff, Note, Duration, Measure, TimeSignature
from dottednotes.renderers.braille_renderer import BrailleRenderer, TranscriptionMode
from dottednotes.parser.choral_ensemble_parser import parse_choral_ensemble


def _note(name, octave):
    return Note(dots=frozenset(), category=None, raw_brl="", note_name=name, octave=octave,
                duration=Duration(value=4))


def _two_character_score():
    score = Score(title="")
    amelia = Staff(name="Amelia")
    amelia.time_signature = TimeSignature(
        dots=frozenset(), category=None, raw_brl="", numerator=4, denominator=4
    )
    barbara = Staff(name="Barbara")
    barbara.time_signature = amelia.time_signature

    m1 = Measure(number=1)
    for name in ("C", "D", "E", "F"):
        m1.add_note(_note(name, 5))
    amelia.add_measure(m1)
    amelia.lyrics = ["Who's", "at", "the", "door"]

    m2 = Measure(number=1)
    for name in ("A", "B", "C", "D"):
        m2.add_note(_note(name, 4))
    barbara.add_measure(m2)
    barbara.lyrics = ["I'll", "answer", "it", "now"]

    score.add_staff(amelia)
    score.add_staff(barbara)
    return score


# ---------------------------------------------------------------------------
# S11c-17: BANA §38.1/§38.2 music-drama character lists -- a 2+-character
# score is a choral ensemble (§37, S11c-12/13/14) whose voice names are
# character names, with a "List of Characters" table (name + identifier)
# at the start of the score.
# ---------------------------------------------------------------------------


def test_character_names_are_not_recognized_as_vocal_by_get_instrument_family():
    # Sanity check grounding why include_character_list must participate
    # in mode detection on its own (character names aren't recognizable
    # instrument-family names the way "Soprano"/"Alto" are).
    from dottednotes.models.instrument import InstrumentFamily, get_instrument_family
    assert get_instrument_family("Amelia") != InstrumentFamily.VOCAL


def test_music_drama_score_is_detected_as_choral_ensemble():
    score = _two_character_score()
    renderer = BrailleRenderer(line_width=40, include_character_list=True)
    assert renderer._detect_transcription_mode(score) == TranscriptionMode.CHORAL_ENSEMBLE


def test_music_drama_renders_character_list_table_before_signature():
    score = _two_character_score()
    output = BrailleRenderer(line_width=40, include_character_list=True).render(score)
    lines = [l for l in output.split("\n") if l]

    # Two table rows (name + identifier), then the signature line.
    assert lines[0].endswith("⠄") or '⠜' in lines[0]
    assert '⠜' in lines[0] and '⠜' in lines[1]
    assert lines[2].lstrip('⠀').startswith('⠼')  # time signature


def test_music_drama_round_trips_character_names_and_lyrics():
    score = _two_character_score()
    output = BrailleRenderer(line_width=40, include_character_list=True).render(score)

    parsed = parse_choral_ensemble(output)

    assert [s.name for s in parsed.staves] == ["Amelia", "Barbara"]
    assert parsed.staves[0].lyrics == ["Who's", "at", "the", "door"]
    assert parsed.staves[1].lyrics == ["I'll", "answer", "it", "now"]
    assert [(n.note_name, n.octave) for n in parsed.staves[0].measures[0].notes] == [
        ("C", 5), ("D", 5), ("E", 5), ("F", 5),
    ]


def test_music_drama_without_character_list_names_are_not_recoverable():
    # Confirms the documented limitation: without the table, a choral
    # ensemble parse can't recover real names (same as S11c-9's vocal solo).
    score = _two_character_score()
    output = BrailleRenderer(line_width=40, include_character_list=False).render(score)
    # Without the table, character names aren't VOCAL-family-recognizable,
    # so this never even reaches CHORAL_ENSEMBLE mode -- confirms the table
    # (and therefore include_character_list) is load-bearing, not optional
    # decoration, for a music-drama score.
    mode = BrailleRenderer(line_width=40)._detect_transcription_mode(score)
    assert mode != TranscriptionMode.CHORAL_ENSEMBLE


def test_disallowed_single_letter_identifier_warns():
    # §38.2: "The single-letter identifiers c, d, f, and p should not be
    # used, to avoid appearing to be dynamic markings."
    from dottednotes.renderers.braille_renderer import render_name_abbreviation_table
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        render_name_abbreviation_table(["C"], 40, warn_disallowed_single_letters=True)
    assert any("c/d/f, or p" in str(w.message) for w in caught)


def test_ordinary_instrument_list_does_not_warn_about_single_letters():
    # The c/d/f/p restriction is §38.2-specific (characters), not §33's
    # ordinary instrument list -- must not fire there.
    from dottednotes.renderers.braille_renderer import render_name_abbreviation_table
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        render_name_abbreviation_table(["C"], 40)  # warn_disallowed_single_letters defaults to False
    assert not any("c/d/f, or p" in str(w.message) for w in caught)


# ---------------------------------------------------------------------------
# S11c-18: BANA §38.3 stage directions -- "Single words or short phrases
# may be placed in the word lines of the characters to whom they apply,"
# rendered in italics. Covers only the short inline form; the longer
# numbered-footnote form is deferred (see TICKETS.md S11c-23).
# ---------------------------------------------------------------------------


def test_music_drama_stage_directions_round_trip():
    score = _two_character_score()
    score.staves[0].stage_directions = [(0, "dials impatiently")]
    score.staves[1].stage_directions = [(4, "smiles")]  # anchored after all lyrics

    output = BrailleRenderer(line_width=40, include_character_list=True).render(score)
    parsed = parse_choral_ensemble(output)

    assert parsed.staves[0].stage_directions == [(0, "dials impatiently")]
    assert parsed.staves[1].stage_directions == [(4, "smiles")]
    # Lyrics are unaffected by the stage direction splice.
    assert parsed.staves[0].lyrics == ["Who's", "at", "the", "door"]
    assert parsed.staves[1].lyrics == ["I'll", "answer", "it", "now"]


def test_music_drama_stage_direction_forces_identified_word_lines():
    # Even if both characters happened to share identical words, a stage
    # direction anchored in the parallel must force S11c-14's per-voice
    # identified lines (S11c-13's shared-line compression would make it
    # ambiguous whose direction it is).
    score = _two_character_score()
    score.staves[0].lyrics = ["Hello"]
    score.staves[1].lyrics = ["Hello"]
    score.staves[0].measures[0].notes = score.staves[0].measures[0].notes[:1]
    score.staves[1].measures[0].notes = score.staves[1].measures[0].notes[:1]
    score.staves[0].stage_directions = [(0, "waves")]

    output = BrailleRenderer(line_width=40, include_character_list=True).render(score)
    lines = [l for l in output.split("\n") if l]
    # lines[0:2] are the character-list table rows, lines[2] the signature.
    word_lines = lines[3:5]
    assert all(l.startswith('⠜') for l in word_lines)


def test_vocal_solo_stage_direction_single_word_uses_word_indicator_not_passage():
    from dottednotes.bana_symbols import ITALIC_WORD_INDICATOR, ITALIC_PASSAGE_INDICATOR
    from dottednotes.renderers.braille_renderer import encode_italic_phrase
    assert encode_italic_phrase("smiles").startswith(ITALIC_WORD_INDICATOR)
    assert encode_italic_phrase("dials impatiently").startswith(ITALIC_PASSAGE_INDICATOR)
    assert encode_italic_phrase("dials impatiently").endswith('⠬')
