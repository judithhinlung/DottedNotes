import pytest
import os
import tempfile
import pathlib
import music21

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
