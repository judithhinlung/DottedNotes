import pytest
import os
import shutil
import subprocess
import tempfile
import pathlib
import music21

from dottednotes.models import (
    Score, Staff, Measure, Note, Duration,
    Fermata, FermataShape, BreathMark, BreathMarkVariant,
)
from dottednotes.parser.musicxml_parser import load_musicxml
from dottednotes.parser.input_pipeline import BRLInputPipeline
from dottednotes.parser.braille_parser import BrailleParser
from dottednotes.parser.tokenizer import BrailleTokenizer
from dottednotes.renderers.musicxml_renderer import export_musicxml

def test_integration_dichterliebe_musicxml_to_brf():
    # 1. Parse dichterliebe01.musicxml
    fixture_path = "tests/fixtures/dichterliebe01.musicxml"
    assert os.path.exists(fixture_path)
    
    score = load_musicxml(fixture_path)
    
    assert score.title == "Dichterliebe"
    assert score.composer == "Robert Schumann"
    
    # 3 staves: Voice, Piano RH, Piano LH
    assert len(score.staves) == 3
    assert score.staves[0].name == "Voice"
    assert score.staves[1].name == "Piano right hand"
    assert score.staves[2].name == "Piano left hand"
    
    # 2. Render back to compressed braille
    brf_content = score.to_braille(compression_level="minimal")
    
    # Simple check that it rendered braille characters
    assert len(brf_content) > 0
    # Checks that it contains braille Unicode cells
    assert any(ord(c) >= 0x2800 and ord(c) <= 0x28FF for c in brf_content)

def test_bartok_orchestral_musicxml_smoke_converts_without_crashing():
    """Smoke test only, like test_bartok_smoke_parses_without_crashing in
    test_ensemble_integration.py -- this real-world orchestral export (9
    instrument parts) is not developer-verified ground truth, so this
    checks the full load_musicxml -> to_braille pipeline runs end to end
    and produces non-empty braille, not exact pitches/rhythms.

    Found the crash this guards against: Tuplet.to_braille()
    (models/tuplet.py) passed prev_note/is_measure_start/time_signature to
    every item in the tuplet uniformly, but Rest.to_braille() takes no
    arguments at all -- Measure's own item-rendering loop already
    special-cases Rest for exactly this reason (see
    test_tuplet_with_rest_to_braille_does_not_raise in
    test_to_braille.py), Tuplet's did not. An eighth-note triplet with a
    rest in one of its three slots -- common in this orchestral score --
    triggered it.
    """
    fixture_path = "tests/fixtures/Bartok_Bella_Romanian_Folk_Dances_for_Orchestra.xml"
    assert os.path.exists(fixture_path)

    score = load_musicxml(fixture_path)
    assert len(score.staves) == 9

    brf_content = score.to_braille(compression_level="full")
    assert len(brf_content) > 0
    assert any(0x2800 <= ord(c) <= 0x28FF for c in brf_content)

def test_integration_brf_to_musicxml():
    # 1. Parse simple_melody.brf
    brf_path = "tests/fixtures/simple_melody.brf"
    assert os.path.exists(brf_path)
    
    text = BRLInputPipeline().load(brf_path)
    tokens = BrailleTokenizer().tokenize(text)
    score = BrailleParser(tokens=tokens).parse()
    
    # 2. Export to MusicXML
    with tempfile.TemporaryDirectory() as tmp_dir:
        out_path = pathlib.Path(tmp_dir) / "exported_melody.musicxml"
        export_musicxml(score, str(out_path))
        
        assert out_path.exists()
        
        # 3. Read back using music21 and verify
        m21_score = music21.converter.parse(str(out_path))
        
        assert len(m21_score.parts) == 1
        part = m21_score.parts[0]
        measures = list(part.getElementsByClass(music21.stream.Measure))
        assert len(measures) > 0
        
        # Check notes/rests count
        total_notes = sum(len(m.notesAndRests) for m in measures)
        assert total_notes > 0

def test_integration_fermata_breath_mark_volta_round_trip():
    # Score (model) -> MusicXML -> Score (model), confirming a fermata, a
    # breath mark, and a volta ending all survive the full round trip
    # (S10c-4), not just a one-way translation.
    score = Score()
    staff = Staff(name="Melody")

    m1 = Measure(number=1, ending_numbers=[1])
    m1.add_note(Note(
        dots=frozenset(), category=None, raw_brl="", note_name='C', octave=4,
        duration=Duration(value=4),
        fermata=Fermata(shape=FermataShape.SQUARED),
        breath_mark=BreathMark(variant=BreathMarkVariant.FULL),
    ))
    staff.add_measure(m1)

    m2 = Measure(number=2, ending_numbers=[2])
    m2.add_note(Note(dots=frozenset(), category=None, raw_brl="", note_name='D', octave=4, duration=Duration(value=4)))
    staff.add_measure(m2)

    score.add_staff(staff)

    with tempfile.TemporaryDirectory() as tmp_dir:
        out_path = pathlib.Path(tmp_dir) / "round_trip.musicxml"
        export_musicxml(score, str(out_path))

        reimported = load_musicxml(str(out_path))

    reimported_measures = reimported.staves[0].measures
    note1 = reimported_measures[0].notes[0]
    assert note1.fermata is not None
    assert note1.fermata.shape == FermataShape.SQUARED
    assert note1.breath_mark is not None
    assert note1.breath_mark.variant == BreathMarkVariant.FULL
    assert reimported_measures[0].ending_numbers == [1]
    assert reimported_measures[1].ending_numbers == [2]


def test_integration_musicxml_volta_to_lilypond_compiles(tmp_path):
    # Full pipeline: a MusicXML file with a forward repeat + first/second
    # endings -> Score.to_lilypond() -> the real lilypond binary, end to
    # end. Guards against a regression silently reverting to the old
    # "% ending N" comment placeholder.
    m21_score = music21.stream.Score()
    part = music21.stream.Part()
    m1 = music21.stream.Measure(number=1)
    m1.append(music21.note.Note('C4', quarterLength=4))
    m2 = music21.stream.Measure(number=2)
    m2.append(music21.note.Note('D4', quarterLength=4))
    m2.leftBarline = music21.bar.Repeat(direction='start')
    m3 = music21.stream.Measure(number=3)
    m3.append(music21.note.Note('E4', quarterLength=4))
    m4 = music21.stream.Measure(number=4)
    m4.append(music21.note.Note('F4', quarterLength=4))
    part.append(m1)
    part.append(m2)
    part.append(m3)
    part.append(m4)

    rb1 = music21.spanner.RepeatBracket(m3, number='1')
    rb2 = music21.spanner.RepeatBracket(m4, number='2')
    part.insert(0, rb1)
    part.insert(0, rb2)
    m21_score.append(part)

    from dottednotes.parser.musicxml_parser import MusicXMLTranslator
    score = MusicXMLTranslator().translate(m21_score)
    ly = score.to_lilypond()

    assert r'\repeat volta 2 {' in ly
    assert r'\alternative {' in ly
    assert '% ending' not in ly

    if not shutil.which("lilypond"):
        pytest.skip("lilypond binary not found; skipping compile test")

    ly_file = tmp_path / "volta.ly"
    ly_file.write_text(ly, encoding="utf-8")
    result = subprocess.run(
        ["lilypond", "-o", str(tmp_path / "volta"), str(ly_file)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"LilyPond compilation failed:\n{result.stderr}"
    assert "warning" not in (result.stdout + result.stderr).lower(), (
        f"LilyPond reported a warning during compilation:\n{result.stdout}\n{result.stderr}"
    )
    assert (tmp_path / "volta.pdf").exists()
