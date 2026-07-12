from dottednotes.models import Score, Staff
from dottednotes.renderers import LilyPondFormatter, FormattingSettings

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

def test_formatter_override():
    formatter = LilyPondFormatter()
    score = Score()
    
    settings = formatter.get_settings(score, category_override="Chamber")
    assert settings.category == "Chamber"
    assert settings.staff_size == 22.2
    assert settings.margin_mm == 15.0

def test_formatter_detects_solo_piano():
    formatter = LilyPondFormatter()
    
    # Empty score defaults to Solo Piano
    assert formatter.get_settings(Score()).category == "Solo Piano"
    
    # 1 Keyboard staff
    score1 = Score()
    score1.add_staff(Staff(name="Piano"))
    assert formatter.get_settings(score1).category == "Solo Piano"

    # 2 Keyboard staves
    score2 = Score()
    score2.add_staff(Staff(name="rh"))
    score2.add_staff(Staff(name="lh"))
    assert formatter.get_settings(score2).category == "Solo Piano"

def test_formatter_detects_art_song():
    formatter = LilyPondFormatter()
    
    # 1 Vocal staff + 1 Keyboard staff
    score = Score()
    score.add_staff(Staff(name="Soprano"))
    score.add_staff(Staff(name="Piano"))
    assert formatter.get_settings(score).category == "Art Song"

def test_formatter_detects_chamber():
    formatter = LilyPondFormatter()
    
    # 4 staves (string quartet)
    score = Score()
    score.add_staff(Staff(name="Violin I"))
    score.add_staff(Staff(name="Violin II"))
    score.add_staff(Staff(name="Viola"))
    score.add_staff(Staff(name="Cello"))
    assert formatter.get_settings(score).category == "Chamber"

def test_formatter_detects_orchestral():
    formatter = LilyPondFormatter()
    
    # > 6 staves
    score = Score()
    for i in range(7):
        score.add_staff(Staff(name=f"Instrument {i}"))
    assert formatter.get_settings(score).category == "Orchestral"
