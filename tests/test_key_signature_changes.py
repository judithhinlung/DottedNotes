"""Sprint 11: mid-piece key signature changes.

Covers S11-1 (BRF parser per-measure key tracking), S11-2 (LilyPond
mid-piece `\\key` emission), S11-3 (braille mid-piece key-signature-cell
emission + octave-mark reset), and S11-4 (MusicXML/LilyPond reverse-parse
mode wiring + `--key-mode` extended to every measure).
"""
import shutil
import subprocess
from pathlib import Path

import music21
import pytest

from dottednotes.bana_symbols import SymbolCategory
from dottednotes.parser.braille_parser import BrailleParser
from dottednotes.parser.input_pipeline import BRLInputPipeline
from dottednotes.parser.lilypond_parser import LilypondParser
from dottednotes.parser.musicxml_parser import MusicXMLTranslator
from dottednotes.parser.tokenizer import BrailleToken, BrailleTokenizer
from dottednotes.renderers.brf_writer import BRFWriter, unicode_to_ascii_braille
from dottednotes.validation.validator import BANAValidator

FIXTURES = Path(__file__).parent / "fixtures"


def _tok(char: str, category: SymbolCategory) -> BrailleToken:
    return BrailleToken(character=char, category=category, position=0, line=1)


def _g_to_d_major_tokens() -> list[BrailleToken]:
    """4/4, measure 1 in G major (1 sharp) with a g-a-b-c ascending quarter-
    note scale, measure 2 changing to D major (2 sharps) with a d-e-f-g
    ascending quarter-note scale -- the same note sequence as the existing
    tests/fixtures/g_major_scale.brf (a proven-correct fixture), so each
    measure is a rhythmically complete 4/4 bar (no LilyPond bar-check
    warnings) and octave inference behaves identically to that fixture.
    Cell values taken directly from bana_symbols.py's KEY_SIGNATURE_CELLS/
    NOTE_CELLS/TIME_SIGNATURE_CELLS tables (not hand-guessed), mirroring
    the existing _make_token-style tests in test_parser.py."""
    return [
        _tok('⠼⠙⠲', SymbolCategory.TIME_SIGNATURE),  # 4/4
        _tok('⠩', SymbolCategory.KEY_SIGNATURE),      # G major, 1 sharp
        _tok('⠐', SymbolCategory.OCTAVE_MARK),
        _tok('⠳', SymbolCategory.NOTE),               # G4 quarter
        _tok('⠪', SymbolCategory.NOTE),               # A4 quarter
        _tok('⠺', SymbolCategory.NOTE),               # B4 quarter
        _tok('⠹', SymbolCategory.NOTE),               # C5 quarter
        _tok('⠀', SymbolCategory.BAR_LINE),           # measure separator
        _tok('⠩⠩', SymbolCategory.KEY_SIGNATURE),     # D major, 2 sharps -- mid-piece change
        _tok('⠐', SymbolCategory.OCTAVE_MARK),
        _tok('⠱', SymbolCategory.NOTE),               # D5 quarter
        _tok('⠫', SymbolCategory.NOTE),               # E5 quarter
        _tok('⠻', SymbolCategory.NOTE),               # F5(#) quarter
        _tok('⠳', SymbolCategory.NOTE),               # G5 quarter
        _tok('⠀', SymbolCategory.BAR_LINE),
    ]


def test_brf_parser_tracks_per_measure_key_signature_on_mid_piece_change():
    score = BrailleParser(tokens=_g_to_d_major_tokens()).parse()
    staff = score.staves[0]
    assert len(staff.measures) == 2
    assert staff.measures[0].key_signature == 1  # G major
    assert staff.measures[1].key_signature == 2  # D major
    # Header key is the FIRST key signature, not the last one seen (S11-1).
    assert staff.key_signature.sharps_or_flats == 1


def test_brf_parser_sets_after_key_change_on_first_note_of_new_key():
    score = BrailleParser(tokens=_g_to_d_major_tokens()).parse()
    staff = score.staves[0]
    # The very first note of the piece also gets this flag (the header key
    # signature counts too, per _handle_key_signature's own comment) --
    # harmless since is_first_note_in_voice already takes priority over it
    # in the validator's branch chain.
    assert staff.measures[0].notes[0].after_key_change is True
    assert staff.measures[0].notes[1].after_key_change is False
    assert staff.measures[1].notes[0].after_key_change is True


def test_lilypond_output_emits_mid_piece_key_change():
    score = BrailleParser(tokens=_g_to_d_major_tokens()).parse()
    ly = score.to_lilypond()
    assert r'\key g \major' in ly
    assert r'\key d \major' in ly
    # The header key is stated once; the change appears after measure 1's
    # own content and before measure 2's first note.
    assert ly.count(r'\key g \major') == 1
    assert ly.index("c4") < ly.index(r'\key d \major') < ly.index("d,4")


def test_lilypond_output_compiles_cleanly_with_mid_piece_key_change(tmp_path: Path):
    if not shutil.which("lilypond"):
        pytest.skip("lilypond binary not found; skipping compile test")

    score = BrailleParser(tokens=_g_to_d_major_tokens()).parse()
    ly_output = score.to_lilypond()

    ly_file = tmp_path / "key_change.ly"
    ly_file.write_text(ly_output, encoding="utf-8")
    result = subprocess.run(
        ["lilypond", "-o", str(tmp_path / "key_change"), str(ly_file)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"LilyPond compilation failed:\n{result.stderr}"
    combined_log = (result.stdout + result.stderr).lower()
    assert "warning" not in combined_log, (
        f"LilyPond reported a warning during compilation:\n{result.stdout}\n{result.stderr}"
    )
    pdf_path = tmp_path / "key_change.pdf"
    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 0


def test_lilypond_output_emits_key_change_inside_volta_group():
    from dottednotes.models.staff import Staff
    from dottednotes.models.measure import Measure
    from dottednotes.models.note import Note
    from dottednotes.models.duration import Duration
    from dottednotes.models.key_signature import KeySignature

    def note_measure(number, key_signature, ending_numbers=None):
        return Measure(number=number, key_signature=key_signature, notes=[
            Note(dots=frozenset(), category=None, raw_brl="", note_name='C', octave=4,
                 duration=Duration(value=4, dots=0)),
            Note(dots=frozenset(), category=None, raw_brl="", note_name='C', octave=4,
                 duration=Duration(value=4, dots=0)),
            Note(dots=frozenset(), category=None, raw_brl="", note_name='C', octave=4,
                 duration=Duration(value=4, dots=0)),
            Note(dots=frozenset(), category=None, raw_brl="", note_name='C', octave=4,
                 duration=Duration(value=4, dots=0)),
        ], ending_numbers=ending_numbers or [])

    shared = note_measure(1, 0)
    ending_1 = note_measure(2, 0, ending_numbers=[1])
    ending_2 = note_measure(3, 2, ending_numbers=[2])  # key change inside \volta 2
    staff = Staff(
        name="Test", measures=[shared, ending_1, ending_2],
        key_signature=KeySignature(dots=frozenset(), category=None, raw_brl="", sharps_or_flats=0, mode="major"),
    )
    ly = staff.to_lilypond()
    assert r'\repeat volta 2' in ly
    assert r'\volta 2' in ly
    # The key change belongs inside the \volta 2 branch, after \repeat volta
    # opens and after \volta 2 itself, not in the shared section.
    assert ly.index(r'\repeat volta 2') < ly.index(r'\volta 2') < ly.index(r'\key d \major')


def test_braille_output_does_not_absorb_key_change_into_compressed_rest_run():
    from dottednotes.models.staff import Staff
    from dottednotes.models.measure import Measure
    from dottednotes.models.score import Score
    from dottednotes.models.note import Rest
    from dottednotes.models.duration import Duration
    from dottednotes.models.key_signature import KeySignature
    from dottednotes.renderers.braille_renderer import BrailleRenderer

    def whole_rest_measure(number, key_signature):
        return Measure(number=number, key_signature=key_signature, notes=[
            Rest(dots=frozenset(), category=None, raw_brl="", duration=Duration(value=1, dots=0), is_full_measure=True),
        ])

    staff = Staff(
        name="Test",
        measures=[whole_rest_measure(1, 0), whole_rest_measure(2, 0), whole_rest_measure(3, 2), whole_rest_measure(4, 2)],
        key_signature=KeySignature(dots=frozenset(), category=None, raw_brl="", sharps_or_flats=0, mode="major"),
    )
    score = Score(staves=[staff])
    brl = BrailleRenderer().render(score)
    # Two separate 2-measure compact rest runs (⠍⠍), split by the D-major
    # key-signature cell (⠩⠩) -- not one merged 4-measure run (⠍⠍⠍⠍).
    assert '⠍⠍⠍⠍' not in brl
    assert brl.count('⠍⠍') == 2
    assert '⠍⠍⠀⠩⠩⠀⠍⠍' in brl


def test_musicxml_import_key_change_produces_correct_braille_output():
    from dottednotes.renderers.braille_renderer import BrailleRenderer

    m21_score = music21.stream.Score()
    part = music21.stream.Part()

    m1 = music21.stream.Measure(number=1)
    m1.insert(0, music21.clef.TrebleClef())
    m1.insert(0, music21.meter.TimeSignature('4/4'))
    m1.insert(0, music21.key.Key('g', 'major'))
    m1.append(music21.note.Note('G4', quarterLength=4))
    part.append(m1)

    m2 = music21.stream.Measure(number=2)
    m2.insert(0, music21.key.Key('e', 'minor'))
    m2.append(music21.note.Note('E4', quarterLength=4))
    part.append(m2)

    m21_score.append(part)
    score = MusicXMLTranslator().translate(m21_score)

    # G major and E minor share the same 1-sharp key signature -- braille
    # has no mode marking, so no key-change cell should appear between the
    # two measures, only the header signature (⠩).
    brl = BrailleRenderer().render(score)
    header, _, body = brl.partition('\n')
    assert header.count('⠩') == 1
    assert '⠩' not in body


def test_lilypond_output_does_not_absorb_key_change_into_compressed_rest_run():
    from dottednotes.models.staff import Staff
    from dottednotes.models.measure import Measure
    from dottednotes.models.note import Rest
    from dottednotes.models.duration import Duration
    from dottednotes.models.key_signature import KeySignature

    def whole_rest_measure(number, key_signature):
        return Measure(number=number, key_signature=key_signature, notes=[
            Rest(dots=frozenset(), category=None, raw_brl="", duration=Duration(value=1, dots=0), is_full_measure=True),
        ])

    staff = Staff(
        name="Test",
        measures=[whole_rest_measure(1, 0), whole_rest_measure(2, 0), whole_rest_measure(3, 2), whole_rest_measure(4, 2)],
        key_signature=KeySignature(dots=frozenset(), category=None, raw_brl="", sharps_or_flats=0, mode="major"),
    )
    ly = staff.to_lilypond()
    assert "R1*2" in ly
    assert ly.count("R1*2") == 2  # two separate 2-measure runs, not one merged 4-measure run
    assert r'\key d \major' in ly


def test_braille_output_emits_mid_piece_key_change_cell_and_forces_octave_mark():
    score = BrailleParser(tokens=_g_to_d_major_tokens()).parse()
    from dottednotes.renderers.braille_renderer import BrailleRenderer
    brl = BrailleRenderer().render(score)
    # The D-major key-signature cell (2 sharps, ⠩⠩) must appear between the
    # two measures' note content, and the note right after it must carry an
    # octave mark (⠐).
    assert '⠩⠩⠀⠐⠱' in brl


def test_braille_round_trip_reparse_preserves_key_change_and_octave_reset():
    score = BrailleParser(tokens=_g_to_d_major_tokens()).parse()
    from dottednotes.renderers.braille_renderer import BrailleRenderer
    brl = BrailleRenderer().render(score)

    from dottednotes.parser.tokenizer import BrailleTokenizer
    reparsed = BrailleParser(tokens=BrailleTokenizer().tokenize(brl)).parse()
    staff = reparsed.staves[0]
    assert staff.measures[1].key_signature == 2
    assert staff.measures[1].notes[0].has_octave_mark is True


def test_validator_does_not_flag_correctly_marked_octave_after_key_change():
    score = BrailleParser(tokens=_g_to_d_major_tokens()).parse()
    result = BANAValidator().validate(score)
    octave_corrections = [c for c in result.corrections if c.rule_id == "S9b-3"]
    assert octave_corrections == []


def test_validator_flags_missing_octave_mark_after_key_change():
    tokens = _g_to_d_major_tokens()
    # Drop the octave mark that precedes the D note in measure 2.
    octave_mark_before_d = tokens[9]
    assert octave_mark_before_d.category == SymbolCategory.OCTAVE_MARK
    tokens = [t for t in tokens if t is not octave_mark_before_d]
    score = BrailleParser(tokens=tokens).parse()
    result = BANAValidator().validate(score)
    assert any(
        c.rule_id == "S9b-3" and "key change" in c.message.lower()
        for c in result.corrections
    )


def test_musicxml_import_tracks_per_measure_mode_on_mid_piece_key_change():
    m21_score = music21.stream.Score()
    part = music21.stream.Part()

    m1 = music21.stream.Measure(number=1)
    m1.insert(0, music21.clef.TrebleClef())
    m1.insert(0, music21.meter.TimeSignature('4/4'))
    m1.insert(0, music21.key.Key('g', 'major'))
    m1.append(music21.note.Note('G4', quarterLength=4))
    part.append(m1)

    m2 = music21.stream.Measure(number=2)
    m2.insert(0, music21.key.Key('e', 'minor'))
    m2.append(music21.note.Note('E4', quarterLength=4))
    part.append(m2)

    m21_score.append(part)
    score = MusicXMLTranslator().translate(m21_score)
    staff = score.staves[0]

    assert staff.measures[0].key_signature == 1
    assert staff.measures[0].key_signature_mode == "major"
    assert staff.measures[1].key_signature == 1  # E minor shares G major's key signature
    assert staff.measures[1].key_signature_mode == "minor"
    # Header reflects the first measure only.
    assert staff.key_signature.mode == "major"

    ly = staff.to_lilypond()
    assert r'\key g \major' in ly
    assert r'\key e \minor' in ly


def test_lilypond_reverse_parse_mid_piece_key_change_tracks_header_and_mode():
    ly_content = """
    \\version "2.26.0"
    \\score {
      \\relative c' {
        \\key g \\major
        g'4 a4 b4 c4 |
        \\key e \\minor
        e4 fis4 g4 a4 |
      }
    }
    """
    score = LilypondParser().parse(ly_content)
    staff = score.staves[0]
    assert staff.measures[0].key_signature == 1
    assert staff.measures[0].key_signature_mode == "major"
    assert staff.measures[1].key_signature == 1
    assert staff.measures[1].key_signature_mode == "minor"
    # Header reflects the FIRST \key, not the last one seen (S11-4).
    assert staff.key_signature.sharps_or_flats == 1
    assert staff.key_signature.mode == "major"


def test_cli_key_mode_applies_to_every_measure_in_multi_key_piece(monkeypatch, tmp_path):
    import sys
    from dottednotes.cli import main

    def _run_main(argv):
        monkeypatch.setattr(sys, "argv", ["dottednotes"] + argv)
        main()

    brf = tmp_path / "test.brf"
    # G major, G4 quarter | D major, D4 quarter -- same cells as _g_to_d_major_tokens.
    brf.write_text("⠩\n⠐⠳⠀⠩⠩⠐⠱", encoding="utf-8")

    out = tmp_path / "out.ly"
    _run_main(["convert", str(brf), str(out), "--key-mode", "minor"])
    content = out.read_text(encoding="utf-8")
    assert r'\key e \minor' in content  # G major's relative minor
    assert r'\key b \minor' in content  # D major's relative minor


# --- Fixture-based tests: tests/fixtures/key_change_test.{ly,brf} ---
#
# key_change_test.ly is hand-authored (2 measures: G major -> D major, an
# ascending quarter-note scale in each, same shape as the existing
# g_major_scale.ly/.brf pair). key_change_test.brf is NOT hand-transcribed
# ASCII braille -- it was generated by actually running key_change_test.ly
# through LilypondParser -> BRFWriter -> unicode_to_ascii_braille (the same
# pipeline test_roundtrip_g_major_scale exercises) and saving the verified
# output, avoiding the transcription-error risk CLAUDE.md warns about for
# hand-guessed dot patterns.

def test_key_change_fixture_lilypond_round_trips_to_expected_brf():
    ly_content = (FIXTURES / "key_change_test.ly").read_text(encoding="utf-8")
    score = LilypondParser().parse(ly_content)

    writer = BRFWriter(line_width=40, page_height=25, show_measure_numbers=False)
    rendered_ascii = unicode_to_ascii_braille(writer.render_to_string(score))

    expected_ascii = (FIXTURES / "key_change_test.brf").read_text(encoding="utf-8")
    rendered_lines = [line.strip() for line in rendered_ascii.splitlines() if line.strip()]
    expected_lines = [line.strip() for line in expected_ascii.splitlines() if line.strip()]
    assert rendered_lines == expected_lines


def test_key_change_fixture_brf_parses_with_correct_per_measure_keys():
    pipeline = BRLInputPipeline()
    text = pipeline.load(FIXTURES / "key_change_test.brf")
    score = BrailleParser(tokens=BrailleTokenizer().tokenize(text)).parse()
    staff = score.staves[0]

    assert len(staff.measures) == 2
    assert staff.measures[0].key_signature == 1  # G major
    assert staff.measures[1].key_signature == 2  # D major
    assert staff.key_signature.sharps_or_flats == 1  # header = first key

    ly = staff.to_lilypond()
    assert r'\key g \major' in ly
    assert r'\key d \major' in ly
