from pathlib import Path
from dottednotes.models import Score, Staff
from dottednotes.renderers import LilyPondFormatter, FormattingSettings
from dottednotes.parser.input_pipeline import BRLInputPipeline
from dottednotes.parser.tokenizer import BrailleTokenizer
from dottednotes.parser.braille_parser import BrailleParser
from dottednotes.parser.ensemble_parser import EnsembleParser

FIXTURES = Path(__file__).parent / "fixtures"

def test_formatter_defaults_exist():
    formatter = LilyPondFormatter()
    for cat in ["Solo Piano", "Art Song", "Chamber", "Orchestral"]:
        assert cat in formatter.DEFAULTS
        settings = formatter.DEFAULTS[cat]
        assert isinstance(settings, FormattingSettings)
        assert settings.category == cat
        assert settings.staff_size > 0
        assert settings.margin_mm > 0
        assert settings.system_system_spacing_basic_distance > 0
        assert settings.system_system_spacing_padding > 0
        assert settings.source_citation.startswith("ftp/")

def test_formatter_override():
    formatter = LilyPondFormatter()
    score = Score()
    
    settings = formatter.get_settings(score, category_override="Chamber")
    assert settings.category == "Chamber"
    assert settings.staff_size == 16.0
    assert settings.margin_mm == 15.0
    assert settings.short_instrument_names is True

def test_formatter_detects_solo_piano_fixture():
    # Use fingering_melody.brf for Solo Piano testing
    formatter = LilyPondFormatter()
    text = BRLInputPipeline().load(FIXTURES / "fingering_melody.brf")
    tokens = BrailleTokenizer().tokenize(text)
    score = BrailleParser(tokens=tokens).parse()
    
    assert formatter.detect_category(score) == "Solo Piano"
    settings = formatter.get_settings(score)
    assert settings.category == "Solo Piano"
    assert settings.staff_size == 20.0
    assert settings.short_instrument_names is False

def test_formatter_detects_chamber_fixture():
    # Use fengyang_flower_drum.brf for Chamber testing
    formatter = LilyPondFormatter()
    text = BRLInputPipeline().load(FIXTURES / "fengyang_flower_drum.brf")
    score = EnsembleParser().parse(text)
    
    assert formatter.detect_category(score) == "Chamber"
    settings = formatter.get_settings(score)
    assert settings.category == "Chamber"
    assert settings.staff_size == 16.0
    assert settings.short_instrument_names is True

def test_formatter_detects_orchestral_bartok():
    # Use instruments from Bartok Romanian Folk Dances for Orchestral testing
    formatter = LilyPondFormatter()
    score = Score()
    score.add_staff(Staff(name="Piccolo"))
    score.add_staff(Staff(name="Flutes I&II"))
    score.add_staff(Staff(name="Clarinets I&II in B-flat"))
    score.add_staff(Staff(name="Bassoons I&II"))
    score.add_staff(Staff(name="Horns in F I&II"))
    score.add_staff(Staff(name="Violins I"))
    score.add_staff(Staff(name="Violins II"))
    score.add_staff(Staff(name="Violas"))
    score.add_staff(Staff(name="Violoncellos"))
    score.add_staff(Staff(name="Double Basses"))
    
    assert formatter.detect_category(score) == "Orchestral"
    settings = formatter.get_settings(score)
    assert settings.category == "Orchestral"
    assert settings.staff_size == 14.1
    assert settings.short_instrument_names is True
