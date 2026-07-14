# src/dottednotes/renderers/lilypond_formatter.py
from dataclasses import dataclass
from typing import Optional
from ..models.score import Score

@dataclass
class FormattingSettings:
    """Centralized formatting settings for a LilyPond score, derived from Mutopia Project analysis.
    
    Citations from docs/mutopia_analysis.md:
    - Solo Piano: Derived from Beethoven Sonata No. 20 (Op. 49 No. 2)
      - staff_size: 20.0 pt (Mutopia average: 20.0)
      - margin_mm: 20.0 mm
      - basic_distance: 12.0
      - padding: 2.0
      - short_instrument_names: False
      - source_citation: ftp/BeethovenLv/Op49/Sonate-20/Sonate-20.ly
    - Art Song: Derived from Schubert An die Musik (D547)
      - staff_size: 18.0 pt
      - margin_mm: 18.0 mm
      - basic_distance: 14.0
      - padding: 3.0
      - short_instrument_names: False
      - source_citation: ftp/SchubertF/D547/an-die-musik/an-die-musik.ly
    - Chamber: Derived from Mozart String Quartet No. 14 (KV387)
      - staff_size: 16.0 pt
      - margin_mm: 15.0 mm
      - basic_distance: 16.0
      - padding: 4.0
      - short_instrument_names: True
      - source_citation: ftp/MozartWA/KV387/kv387-1/kv387-1.ly
    - Orchestral: Derived from Mozart Symphony No. 40 (KV550)
      - staff_size: 14.1 pt
      - margin_mm: 12.0 mm
      - basic_distance: 18.0
      - padding: 5.0
      - short_instrument_names: True
      - source_citation: ftp/MozartWA/KV550/kv550-1/kv550-1.ly
    - Lead Sheet: NOT derived from a Mutopia anchor (S8b-5 follow-up) --
      Mutopia's corpus is overwhelmingly classical/public-domain and, after
      checking Folk/Jazz/Hymn+Guitar styles, contains no piece using
      \\chordmode/\\new ChordNames to anchor against. Reuses Solo Piano's
      values verbatim as a documented placeholder rather than an invented
      citation; see docs/lilypond_conventions.md.
      - staff_size: 20.0 pt
      - margin_mm: 20.0 mm
      - basic_distance: 12.0
      - padding: 2.0
      - short_instrument_names: False
      - source_citation: none -- see docstring above
    """
    category: str
    staff_size: float
    margin_mm: float
    system_system_spacing_basic_distance: float
    system_system_spacing_padding: float
    short_instrument_names: bool
    source_citation: str

class LilyPondFormatter:
    """Selects and applies formatting settings derived from Mutopia Project analysis."""

    DEFAULTS = {
        "Solo Piano": FormattingSettings(
            category="Solo Piano",
            staff_size=20.0,
            margin_mm=20.0,
            system_system_spacing_basic_distance=12.0,
            system_system_spacing_padding=2.0,
            short_instrument_names=False,
            source_citation="ftp/BeethovenLv/Op49/Sonate-20/Sonate-20.ly",
        ),
        "Art Song": FormattingSettings(
            category="Art Song",
            staff_size=18.0,
            margin_mm=18.0,
            system_system_spacing_basic_distance=14.0,
            system_system_spacing_padding=3.0,
            short_instrument_names=False,
            source_citation="ftp/SchubertF/D547/an-die-musik/an-die-musik.ly",
        ),
        "Chamber": FormattingSettings(
            category="Chamber",
            staff_size=16.0,
            margin_mm=15.0,
            system_system_spacing_basic_distance=16.0,
            system_system_spacing_padding=4.0,
            short_instrument_names=True,
            source_citation="ftp/MozartWA/KV387/kv387-1/kv387-1.ly",
        ),
        "Orchestral": FormattingSettings(
            category="Orchestral",
            staff_size=14.1,
            margin_mm=12.0,
            system_system_spacing_basic_distance=18.0,
            system_system_spacing_padding=5.0,
            short_instrument_names=True,
            source_citation="ftp/MozartWA/KV550/kv550-1/kv550-1.ly",
        ),
        "Lead Sheet": FormattingSettings(
            category="Lead Sheet",
            staff_size=20.0,
            margin_mm=20.0,
            system_system_spacing_basic_distance=12.0,
            system_system_spacing_padding=2.0,
            short_instrument_names=False,
            source_citation=(
                "No Mutopia anchor found -- chord-symbol lead sheets are a "
                "20th-century popular/jazz convention not present in Mutopia's "
                "classical-dominated corpus in \\chordmode/ChordNames form "
                "(checked Folk/Jazz/Hymn+Guitar styles, S8b-5 follow-up). "
                "Reusing Solo Piano's values as a documented placeholder."
            ),
        ),
    }

    def detect_category(self, score: Score) -> str:
        """Heuristically detects the instrumentation category of a score.
        
        This will be fully refined in S7b-3, but supports a basic staff-count
        and family-based classification initially:
        - Solo Piano: 1 or 2 staves, primarily keyboard
        - Art Song: 2 or 3 staves, vocal + piano
        - Chamber: 3 to 6 staves
        - Orchestral: > 6 staves
        """
        from ..models.instrument import InstrumentFamily, get_instrument_family
        
        staves = score.staves
        if not staves:
            return "Solo Piano"
            
        staff_count = len(staves)
        
        # Check if we have keyboard instruments
        has_keyboard = any(get_instrument_family(s.name) == InstrumentFamily.KEYBOARD_HARP for s in staves)
        
        # Check if we have vocal staves
        has_vocal = any(
            get_instrument_family(s.name) == InstrumentFamily.VOCAL or
            any(kw in s.name.lower() for kw in ["voice", "vocal", "lyrics", "soprano", "alto", "tenor", "bass", "lied"])
            for s in staves
        )
        
        if staff_count > 6:
            return "Orchestral"
            
        if has_vocal and has_keyboard:
            return "Art Song"
            
        if staff_count >= 3:
            return "Chamber"
            
        # Default fallback for 1 or 2 staves
        return "Solo Piano"

    def get_settings(self, score: Score, category_override: Optional[str] = None) -> FormattingSettings:
        """Returns the formatting settings to apply to the given Score."""
        category = category_override
        if category is None:
            category = self.detect_category(score)
            
        if category not in self.DEFAULTS:
            # Fallback to Solo Piano
            return self.DEFAULTS["Solo Piano"]
            
        return self.DEFAULTS[category]
