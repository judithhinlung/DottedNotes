from __future__ import annotations

import pytest
import warnings
from pathlib import Path
from dottednotes.parser.ensemble_parser import (
    EnsembleParser,
    extract_measure_number,
    extract_all_measure_numbers,
    extract_line_abbreviation,
    decode_instrument_abbreviation,
    has_ensemble_header,
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


def test_extract_all_measure_numbers():
    # Sao Mai's inline multi-measure-number convention (S5b-9): several
    # NUMBER_SIGN+digit markers spaced across one pure header line.
    assert extract_all_measure_numbers("⠼⠁⠀⠀⠼⠃⠀⠀⠼⠙⠀⠀⠼⠑") == [
        (0, 1), (4, 2), (8, 4), (12, 5),
    ]
    # A single marker is BANA's own convention (extract_measure_number's
    # job) -- extract_all_measure_numbers requires 2+ markers.
    assert extract_all_measure_numbers("⠁⠀⠀⠜⠧⠂⠄") is None
    assert extract_all_measure_numbers("⠼⠁⠀⠀⠀") is None
    # Real content (not just blank cells + markers) disqualifies the line,
    # even with 2+ NUMBER_SIGN occurrences -- e.g. a content line where '⠼'
    # is doing double duty as the INTERVAL-4th cell, not a measure marker.
    assert extract_all_measure_numbers("⠜⠧⠇⠁⠄⠀⠸⠦⠐⠻⠤⠱⠼⠀⠄⠄⠄⠄⠄⠀⠸⠦⠱⠼⠶") is None


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


def test_ensemble_parser_sao_mai_inline_multi_measure_numbers():
    # S5b-9: Sao Mai's convention -- several NUMBER_SIGN+digit markers
    # spaced across one header line (rather than BANA's one-number-alone-
    # per-line convention) -- each marking where a later measure's column
    # begins. Flute and Violin content lines are column-sliced at the same
    # marker positions the header declares.
    # Flute plays C D | E F ; Violin plays C D | E F (octave 3).
    header = '⠀⠀⠀⠀⠀⠼⠁⠀⠼⠃'  # measure 1 marker at col 5, measure 2 marker at col 8
    flute_line = '⠜⠋⠇⠄⠀⠐⠹⠱⠐⠫⠻'
    violin_line = '⠜⠧⠇⠄⠀⠸⠹⠱⠸⠫⠻'
    raw = (
        '⠠⠋⠇⠥⠞⠑⠀⠐⠐⠐⠐⠐⠀⠀⠜⠋⠇⠄\n'
        '⠠⠧⠊⠕⠇⠊⠝⠀⠐⠐⠀⠀⠀⠜⠧⠇⠄\n'
        '⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠣⠣⠣⠼⠙⠲\n'
        f'{header}\n{flute_line}\n{violin_line}\n'
    )
    parser = EnsembleParser()
    score = parser.parse(raw)

    assert len(score.staves) == 2
    flute, violin = score.staves
    assert flute.name == "Flute"
    assert violin.name == "Violin"

    assert len(flute.measures) == 2
    assert [n.note_name for n in flute.measures[0].notes] == ["C", "D"]
    assert [n.note_name for n in flute.measures[1].notes] == ["E", "F"]

    assert len(violin.measures) == 2
    assert [n.note_name for n in violin.measures[0].notes] == ["C", "D"]
    assert [n.note_name for n in violin.measures[1].notes] == ["E", "F"]
    assert [n.octave for n in violin.measures[0].notes] == [3, 3]


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


# --- S7-2: hand-sign / word-sign dispatch false positive ---
#
# HAND_SIGN_CELLS ('⠨⠜': 'right', '⠸⠜': 'left') is a two-cell sequence
# whose second cell is literally WORD_SIGN ('⠜'). A two-hand piano piece's
# hand-sign-prefixed line, followed later by an unrelated END_WORD_SIGN
# ('⠄')-shaped cell, used to be textually indistinguishable from a genuine
# instrument-list header line under raw substring matching -- both
# cli.py's dispatch and this module's own inst_lines detection loop did
# `WORD_SIGN in line and END_WORD_SIGN in line`, which can't tell a real
# standalone word-sign token from the tail of a hand sign. Fixed by
# routing through the tokenizer's already-correct, already-tested
# HAND_SIGN vs WORD_SIGN classification instead (see tokenizer.py's
# _CLEF_PREFIX and HAND_SIGN_CELLS branches, and tests/test_parser.py's
# S5-4 hand-sign block).

def test_has_ensemble_header_false_for_hand_sign_line():
    # tests/fixtures/fingering_melody.brf, line 5 (1-indexed): a left-hand
    # sign (⠸⠜) with no leading measure number, immediately followed by an
    # unrelated ⠄ cell -- the exact real-world shape that used to
    # false-positive under raw substring matching.
    hand_sign_line = '⠀⠀⠀⠸⠜⠄⠹⠅⠱⠂⠫⠇⠻⠃⠀⠽⠅⠬⠇⠔⠁⠣⠅'
    assert has_ensemble_header(hand_sign_line) is False


def test_has_ensemble_header_true_for_genuine_header():
    raw = (
        '⠠⠋⠇⠥⠞⠑⠀⠐⠐⠐⠐⠐⠀⠀⠜⠋⠇⠄\n'
        '⠠⠧⠊⠕⠇⠊⠝⠀⠐⠐⠀⠀⠀⠜⠧⠇⠄\n'
    )
    assert has_ensemble_header(raw) is True


def test_fingering_melody_not_routed_to_ensemble_parser():
    # Regression: fingering_melody.brf is a real solo two-hand piano
    # piece. Before the fix, cli.py's dispatch (mirroring this same
    # heuristic) wrongly routed it to EnsembleParser, which then raised
    # "No parallel systems found in ensemble score." -- a confusing
    # failure for a file that was never an ensemble score to begin with.
    text = BRLInputPipeline().load(
        Path(__file__).parent / "fixtures" / "fingering_melody.brf"
    )
    assert has_ensemble_header(text) is False


def test_children_s_piece_not_routed_to_ensemble_parser():
    # Regression: children_s_piece.brf is a real solo two-hand piano piece
    # whose title contains an apostrophe ("Children's Piece"). The
    # apostrophe is END_WORD_SIGN's own dot-3 cell, which used to fool
    # instrument_list._parse_line into treating the title line as a bogus
    # one-instrument header -- routing the whole file to EnsembleParser,
    # which rendered it as nothing but a run of unmarked r16 rests instead
    # of the real music (cli.py's dispatch mirrors this same heuristic).
    text = BRLInputPipeline().load(
        Path(__file__).parent / "fixtures" / "children_s_piece.brf"
    )
    assert has_ensemble_header(text) is False


def test_ensemble_parser_raises_clear_error_on_hand_sign_only_text():
    # With no genuine instrument-list header, EnsembleParser.parse() must
    # still fail -- but with the clear, specific message, not a confusing
    # downstream failure from bogus inst_lines slipping through.
    from dottednotes.exceptions import BrailleParseError

    hand_sign_only = '⠀⠀⠀⠸⠜⠄⠹⠅⠱⠂⠫⠇⠻⠃⠀⠽⠅⠬⠇⠔⠁⠣⠅\n'
    with pytest.raises(BrailleParseError, match="No instrument list header found"):
        EnsembleParser().parse(hand_sign_only)


def test_ensemble_parser_raises_braille_parse_error_when_header_has_no_measures():
    # S7-3: a genuine instrument-list header with no measure content after
    # it (e.g. a truncated transcription) is malformed input, not an
    # internal bug -- must raise BrailleParseError, not a bare ValueError.
    from dottednotes.exceptions import BrailleParseError

    header_only = '⠠⠋⠇⠥⠞⠑⠀⠐⠐⠐⠐⠐⠀⠀⠜⠋⠇⠄\n⠠⠧⠊⠕⠇⠊⠝⠀⠐⠐⠀⠀⠀⠜⠧⠇⠄\n'
    with pytest.raises(BrailleParseError, match="No parallel systems found"):
        EnsembleParser().parse(header_only)


def test_ensemble_parser_skips_title_line_before_instrument_list():
    # Found via Bartok_Bella_Romanian_Folk_Dances_for_Orchestra.brl: a
    # free-text title/attribution line above the real instrument-list
    # header also tokenizes as a WORD_SIGN (any literary text does), and
    # if a blank line separates it from the real header, the old
    # WORD_SIGN-token-presence check would collect the title line as a
    # fake "instrument", then stop at the blank line -- before ever
    # reaching the real instrument list. inst_lines collection must
    # instead require a line to actually parse as a genuine instrument
    # entry (_parse_line), not merely contain a WORD_SIGN token.
    title_line = '⠠⠋⠇⠥⠞⠑'  # "Flute" as bare prose -- no WORD_SIGN...END_WORD_SIGN
    raw = (
        title_line + '\n'
        '\n'
        '⠠⠋⠇⠥⠞⠑⠀⠐⠐⠐⠐⠐⠀⠀⠜⠋⠇⠄\n'
        '⠠⠧⠊⠕⠇⠊⠝⠀⠐⠐⠀⠀⠀⠜⠧⠇⠄\n'
        '⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠣⠣⠣⠼⠙⠲\n'
        '⠁⠀⠀⠜⠋⠇⠄⠐⠹⠱⠫⠻⠀⠐⠳⠪⠺⠹\n'
        '⠀⠀⠀⠜⠧⠇⠄⠸⠳⠪⠺⠹⠀⠸⠹⠱⠫⠻\n'
    )
    score = EnsembleParser().parse(raw)
    assert [s.name for s in score.staves] == ['Flute', 'Violin']


def test_ensemble_parser_raises_clear_error_for_headerless_open_score():
    # A real-world "open score" quartet transcription (found via
    # Tchaikovsky_String_Quartet_No_1_with_header.brf) can have title-page
    # text and a music heading (tempo + key/time signature) but never
    # include a genuine BANA Sec. 33.2 instrument-list header, going
    # straight into per-line abbreviation-prefixed music instead. This
    # must be detected and reported clearly, not silently misparsed by
    # letting the old unbounded instrument-collection loop wander into the
    # music body and mistake scattered per-line abbreviation prefixes
    # (each followed on its own line only by notes, no embedded second
    # word-sign expression here) for header entries.
    from dottednotes.exceptions import BrailleParseError

    title_line = '⠠⠞⠊⠞⠇⠑'  # bare prose title, no header anywhere below it
    raw = (
        title_line + '\n'
        '\n'
        '⠠⠍⠕⠙⠑⠗⠁⠞⠕⠀⠩⠩⠼⠉⠲\n'  # "Moderato" + 2 sharps + 3/4 time (the Music Heading)
        '⠀⠀⠀⠀⠼⠁\n'
        '⠜⠧⠂⠄⠐⠹⠱⠫\n'
        '⠜⠧⠆⠄⠐⠹⠱⠫\n'
        '⠜⠧⠇⠄⠐⠹⠱⠫\n'
        '⠜⠧⠉⠄⠸⠹⠱⠫\n'
    )
    assert has_ensemble_header(raw) is True  # still routes to EnsembleParser
    with pytest.raises(BrailleParseError, match="No instrument list header found") as exc:
        EnsembleParser().parse(raw)
    assert "Sec. 33.2" in str(exc.value)
    assert "v1, v2, vl, vc" in str(exc.value)
