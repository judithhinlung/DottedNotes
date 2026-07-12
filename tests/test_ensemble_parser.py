from __future__ import annotations

import pytest
import warnings
from dottednotes.parser.ensemble_parser import (
    EnsembleParser,
    extract_measure_number,
    extract_line_abbreviation,
    decode_instrument_abbreviation,
)
from dottednotes.parser.input_pipeline import BRLInputPipeline
from dottednotes.models.orchestra_score import OrchestraScore
from dottednotes.models.note import Note, Rest
from dottednotes.models.measure import Measure


def test_extract_measure_number():
    # Input to extract_measure_number is expected to be Unicode braille
    # '⠁' is measure 1 (A), '⠙' is measure 4 (D)
    assert extract_measure_number("⠁⠀⠀⠜⠧⠂⠄") == (1, "⠜⠧⠂⠄")
    assert extract_measure_number("⠙⠀⠜⠧⠆⠄") == (4, "⠜⠧⠆⠄")
    assert extract_measure_number("⠀⠜⠧⠂⠄") == (None, "⠀⠜⠧⠂⠄")
    assert extract_measure_number("⠁") == (1, "")
    assert extract_measure_number("⠁⠀") == (1, "")


def test_extract_line_abbreviation():
    assert extract_line_abbreviation("⠜⠧⠂⠄⠠⠍") == ("⠜⠧⠂⠄", "⠠⠍")
    assert extract_line_abbreviation("⠧⠂⠄⠠⠍") == ("⠧⠂⠄", "⠠⠍")
    # No abbreviation ends with ⠄
    assert extract_line_abbreviation("⠠⠍") == (None, "⠠⠍")


def test_decode_instrument_abbreviation():
    assert decode_instrument_abbreviation("⠜⠧⠂⠄") == ("v", ["1"])
    assert decode_instrument_abbreviation("⠜⠧⠂⠆⠄") == ("v", ["1", "2"])
    assert decode_instrument_abbreviation("⠜⠧⠇⠝⠆⠄") == ("vln", ["2"])


def test_ensemble_parser_basic():
    # Simple ensemble score with Flute and Violin
    # 2 measures. Key: A major? (<<<), Time: 4/4 (#D4)
    # Flute plays C D E F | G A B C
    # Violin plays G A B C | C D E F
    raw = (
        '⠠⠋⠇⠥⠞⠑⠀⠐⠐⠐⠐⠐⠀⠀⠜⠋⠇⠄\n'
        '⠠⠧⠊⠕⠇⠊⠝⠀⠐⠐⠀⠀⠀⠜⠧⠇⠄\n'
        '⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠣⠣⠣⠼⠙⠲\n'
        '⠁⠀⠀⠜⠋⠇⠄⠐⠹⠱⠫⠻⠀⠐⠳⠪⠺⠹\n'
        '⠀⠀⠀⠜⠧⠇⠄⠸⠳⠪⠺⠹⠀⠸⠹⠱⠫⠻\n'
    )
    parser = EnsembleParser()
    score = parser.parse(raw)

    assert isinstance(score, OrchestraScore)
    assert len(score.staves) == 2
    assert score.staves[0].name == "Flute"
    assert score.staves[1].name == "Violin"

    assert len(score.staves[0].measures) == 2
    assert len(score.staves[1].measures) == 2

    # Verify first note of Flute (C4, octave 4)
    first_note = score.staves[0].measures[0].notes[0]
    assert isinstance(first_note, Note)
    assert first_note.note_name == "C"
    assert first_note.octave == 4

    # Verify first note of Violin (G3, octave 3)
    first_vn_note = score.staves[1].measures[0].notes[0]
    assert isinstance(first_vn_note, Note)
    assert first_vn_note.note_name == "G"
    assert first_vn_note.octave == 3


def test_ensemble_parser_parallel_movement():
    # Violin II doubles Violin I
    # System starts at measure 1
    # Violin I plays C D E F (octave 4)
    # Violin II plays unison (⠤) in measure 1, and octave 5 (⠨⠤) in measure 2
    raw = (
        '⠠⠧⠊⠕⠇⠊⠝⠀⠠⠊⠀⠀⠀⠀⠜⠧⠂⠄\n'
        '⠠⠧⠊⠕⠇⠊⠝⠀⠠⠠⠊⠊⠀⠀⠜⠧⠆⠄\n'
        '⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠣⠣⠣⠼⠙⠲\n'
        '⠁⠀⠀⠜⠧⠂⠄⠐⠹⠱⠫⠻⠀⠐⠹⠱⠫⠻\n'
        '⠀⠀⠀⠜⠧⠆⠄⠤⠀⠨⠤\n'
    )
    parser = EnsembleParser()
    score = parser.parse(raw)

    v1 = score.staves[0]
    v2 = score.staves[1]

    assert len(v1.measures) == 2
    assert len(v2.measures) == 2

    # Measure 1: unison
    assert len(v2.measures[0].notes) == 4
    assert [n.note_name for n in v2.measures[0].notes] == ["C", "D", "E", "F"]
    assert [n.octave for n in v2.measures[0].notes] == [4, 4, 4, 4]

    # Measure 2: octave 5 transposition
    assert len(v2.measures[1].notes) == 4
    assert [n.note_name for n in v2.measures[1].notes] == ["C", "D", "E", "F"]
    assert [n.octave for n in v2.measures[1].notes] == [5, 5, 5, 5]


def test_ensemble_parser_consolidated():
    # Violin I and II consolidated as V12
    raw = (
        '⠠⠧⠊⠕⠇⠊⠝⠀⠠⠊⠀⠀⠀⠀⠜⠧⠂⠄\n'
        '⠠⠧⠊⠕⠇⠊⠝⠀⠠⠠⠊⠊⠀⠀⠜⠧⠆⠄\n'
        '⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠣⠣⠣⠼⠙⠲\n'
        '⠁⠀⠀⠜⠧⠂⠆⠄⠐⠹⠱⠫⠻⠀⠐⠹⠱⠫⠻\n'
    )
    parser = EnsembleParser()
    score = parser.parse(raw)

    assert len(score.staves) == 2
    assert score.staves[0].name == "Violin I"
    assert score.staves[1].name == "Violin II"

    # Both should have parsed the same measures
    assert len(score.staves[0].measures) == 2
    assert len(score.staves[1].measures) == 2
    assert [n.note_name for n in score.staves[0].measures[0].notes] == ["C", "D", "E", "F"]
    assert [n.note_name for n in score.staves[1].measures[0].notes] == ["C", "D", "E", "F"]


def test_ensemble_parser_omitted_rests():
    # Flute plays in System 1 (measures 1-2) but is omitted in System 2 (measures 3-4)
    # Violin plays in both
    raw = (
        '⠠⠋⠇⠥⠞⠑⠀⠐⠐⠐⠐⠐⠀⠀⠜⠋⠇⠄\n'
        '⠠⠧⠊⠕⠇⠊⠝⠀⠐⠐⠀⠀⠀⠜⠧⠇⠄\n'
        '⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠣⠣⠣⠼⠙⠲\n'
        '⠁⠀⠀⠜⠋⠇⠄⠐⠹⠱⠫⠻⠀⠐⠹⠱⠫⠻\n'
        '⠀⠀⠀⠜⠧⠇⠄⠸⠳⠪⠺⠹⠀⠸⠹⠱⠫⠻\n'
        '⠉⠀⠀⠜⠧⠇⠄⠸⠳⠪⠺⠹⠀⠸⠹⠱⠫⠻\n'  # Measure 3 (⠉ is 3)
    )
    parser = EnsembleParser()
    score = parser.parse(raw)

    fl = score.staves[0]
    vl = score.staves[1]

    # Violin has 4 measures (since the last system starting at measure 3 has 2 measures)
    assert len(vl.measures) == 4
    # Flute should get rests reconstructed for measures 3-4
    assert len(fl.measures) == 4

    # Measure 3 Flute should be a rest
    assert len(fl.measures[2].notes) == 1
    assert isinstance(fl.measures[2].notes[0], Rest)
    assert fl.measures[2].notes[0].is_full_measure


def test_ensemble_parser_preserves_word_sign_and_dynamic_markings():
    # S5b-8 regression: EnsembleParser used to reconstruct each instrument's
    # cell stream by wrapping already-decoded WORD_SIGN/DYNAMIC token text
    # back in raw braille markers and re-tokenizing, which silently
    # corrupted every dynamic/expression marking that survived the
    # round-trip (e.g. an "mp" marking became garbage like "?mp"). Fixed by
    # BrailleToken.raw preserving the true original cells. This asserts a
    # dynamic marking on the first note comes through intact.
    raw = (
        '⠠⠋⠇⠥⠞⠑⠀⠐⠐⠐⠐⠐⠀⠀⠜⠋⠇⠄\n'
        '⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠣⠣⠣⠼⠙⠲\n'
        '⠁⠀⠀⠜⠋⠇⠄⠜⠍⠏⠄⠐⠹⠱⠫⠻\n'
    )
    score = EnsembleParser().parse(raw)
    first_note = score.staves[0].measures[0].notes[0]
    assert first_note.note_name == "C"
    assert len(first_note.dynamics) == 1
    assert first_note.dynamics[0].level.name == "MP"


def test_ensemble_parser_does_not_drop_first_note_matching_digit_cell():
    # S5b-8 regression: BrailleTokenizer.tokenize() always assumed it was
    # starting at a genuine physical line, so its measure-number heuristic
    # would swallow a real first note as a bogus measure-number token
    # whenever that note's cell happened to also be a literary digit (e.g.
    # '⠚', note B eighth, doubles as digit '0'). Invisible in the
    # single-score path, but EnsembleParser re-tokenizes abbreviation-
    # stripped mid-stream fragments as if they were fresh lines. Fixed via
    # BrailleTokenizer's at_line_start parameter.
    raw = (
        '⠠⠋⠇⠥⠞⠑⠀⠐⠐⠐⠐⠐⠀⠀⠜⠋⠇⠄\n'
        '⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠣⠣⠣⠼⠙⠲\n'
        '⠁⠀⠀⠜⠋⠇⠄⠐⠚⠹⠱⠫\n'
    )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        score = EnsembleParser().parse(raw)
    notes = [n for n in score.staves[0].measures[0].notes if isinstance(n, Note)]
    assert [(n.note_name, n.duration.value) for n in notes] == [
        ("B", 8), ("C", 4), ("D", 4), ("E", 4),
    ]


def test_ensemble_parser_word_sign_terminates_at_articulation_or_repeat_cell():
    # S5b-8 regression: a word-sign/dynamic expression missing its closing
    # END_WORD_SIGN (a real transcription gap in Fengyang_Flower_Drum.brf --
    # e.g. an unclosed ">MP" immediately followed by a staccato mark, or an
    # unclosed ">C" immediately followed by a measure-repeat sign) used to
    # swallow that unrelated cell into the decoded text, corrupting it (e.g.
    # "mp" -> "mp?"). Neither an articulation cell nor the measure-repeat
    # cell ever legitimately appears inside literary word text or a
    # DYNAMIC_CELLS entry, so the tokenizer now treats them as terminators
    # too, leaving them for normal classification instead of swallowing them.
    from dottednotes.models.articulation import ArticulationType

    raw = (
        '⠠⠋⠇⠥⠞⠑⠀⠐⠐⠐⠐⠐⠀⠀⠜⠋⠇⠄\n'
        '⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠣⠣⠣⠼⠙⠲\n'
        '⠁⠀⠀⠜⠋⠇⠄⠜⠍⠏⠦⠐⠹⠱⠫⠻\n'  # ">MP" with no closing END_WORD_SIGN, then a staccato mark
    )
    score = EnsembleParser().parse(raw)
    first_note = score.staves[0].measures[0].notes[0]
    assert len(first_note.dynamics) == 1
    assert first_note.dynamics[0].level.name == "MP"
    assert len(first_note.articulations) == 1
    assert first_note.articulations[0].type == ArticulationType.STACCATO


# --- S7-1: OrchestraScore inherits Score's \header support ---
# OrchestraScore.to_lilypond() has its own \score/\layout/\midi-wrapping
# override (S5b-8, predates S7-1) but never called the shared
# _header_lines() helper, so title/composer were silently dropped for
# every ensemble score even though the plain Score path emitted them.

def test_orchestra_score_to_lilypond_includes_header_when_set():
    raw = (
        '⠠⠋⠇⠥⠞⠑⠀⠐⠐⠐⠐⠐⠀⠀⠜⠋⠇⠄\n'
        '⠠⠧⠊⠕⠇⠊⠝⠀⠐⠐⠀⠀⠀⠜⠧⠇⠄\n'
        '⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠣⠣⠣⠼⠙⠲\n'
        '⠁⠀⠀⠜⠋⠇⠄⠐⠹⠱⠫⠻⠀⠐⠳⠪⠺⠹\n'
        '⠀⠀⠀⠜⠧⠇⠄⠸⠳⠪⠺⠹⠀⠸⠹⠱⠫⠻\n'
    )
    score = EnsembleParser().parse(raw)
    score.title = 'Duet "in D"'
    score.composer = "Traditional"
    ly = score.to_lilypond()
    assert r'\header {' in ly
    assert r'title = "Duet \"in D\""' in ly
    assert 'composer = "Traditional"' in ly
    # header comes after \version and before the music-variable definitions.
    assert ly.index(r'\version') < ly.index(r'\header') < ly.index('Music =')
    # pre-existing S5b-8 score/layout/midi wrapping is unaffected.
    assert r'\score {' in ly
    assert r'\layout { }' in ly
    assert r'\midi { }' in ly


def test_orchestra_score_to_lilypond_no_header_when_unset():
    raw = (
        '⠠⠋⠇⠥⠞⠑⠀⠐⠐⠐⠐⠐⠀⠀⠜⠋⠇⠄\n'
        '⠠⠧⠊⠕⠇⠊⠝⠀⠐⠐⠀⠀⠀⠜⠧⠇⠄\n'
        '⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠣⠣⠣⠼⠙⠲\n'
        '⠁⠀⠀⠜⠋⠇⠄⠐⠹⠱⠫⠻⠀⠐⠳⠪⠺⠹\n'
        '⠀⠀⠀⠜⠧⠇⠄⠸⠳⠪⠺⠹⠀⠸⠹⠱⠫⠻\n'
    )
    score = EnsembleParser().parse(raw)
    assert r'\header' not in score.to_lilypond()
