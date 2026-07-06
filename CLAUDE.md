# DottedNotes — Claude Code Project Context

This file gives Claude Code full context for the DottedNotes project.
At the start of each session, read this file first before doing anything else.
Tickets that are done are marked with [x]. Tickets still to do are marked with [ ].
Never mark a ticket done yourself — the developer will check it off.

---

## Project Overview

**Repository:** https://github.com/judithhinlung/DottedNotes
**Language:** Python 3.11+
**Purpose:** Convert braille music notation (.brf/.brl files) to LilyPond (.ly),
enabling blind composers to go from their native braille notation to
PDF scores and MIDI audio without sighted assistance.

**The workflow this tool enables:**
```
composer writes in braille → .brf file
→ dottednotes convert piece.brf → piece.ly
→ lilypond piece.ly → piece.pdf + piece.midi
```

**Background:**
- Developer is a blind composer and former Java software engineer
- Previously contributed to the Freedots project (MusicXML → braille translation)
- DottedNotes originally converted MusicXML to MIDI in Java (preserved on java-legacy branch)
- This Python rewrite focuses on BRF/BRL → LilyPond as the primary direction
- MusicXML support planned for a later sprint (Sprint 10)

---

## Developer Context

- Developer uses VoiceOver on Mac with VS Code
- Developer composes in braille on a BrailleNotetaker device
- Developer uses LilyPond for music notation and Logic Pro for mixing
- All code output, error messages, and CLI output must be screen reader friendly
- No progress bars, ASCII art, or visual-only feedback
- All error messages must be plain text and meaningful

---

## Architecture Overview

### Core principle
Every domain object is responsible for rendering itself.
Each class has both `to_lilypond()` and (eventually) `to_braille()` methods.
The internal domain model is the pivot point for all translation directions.

### Translation directions (current and future)
```
BRF/BRL ──→ Internal Model ──→ LilyPond (.ly) ──→ PDF + MIDI (via lilypond binary)
                  ↕
             MusicXML (via music21, Sprint 10)
                  ↕
             BRF/BRL reverse (Sprint 9)
```

### Project structure
```
DottedNotes/
├── src/
│   └── dottednotes/
│       ├── __init__.py
│       ├── models/
│       │   ├── __init__.py
│       │   ├── note.py          # Note, Rest classes
│       │   ├── duration.py      # Duration class
│       │   ├── accidental.py    # Accidental class
│       │   ├── articulation.py  # Articulation class
│       │   ├── dynamic.py       # Dynamic class
│       │   ├── ornament.py      # Ornament class
│       │   ├── measure.py       # Measure class
│       │   ├── voice.py         # Voice class
│       │   ├── staff.py         # Staff class
│       │   └── score.py         # Score, OrchestraScore classes
│       ├── parser/
│       │   ├── __init__.py
│       │   ├── input_pipeline.py   # BRLInputPipeline, encoding detection
│       │   ├── tokenizer.py        # BrailleTokenizer
│       │   └── braille_parser.py   # BrailleParser (main parser)
│       ├── renderers/
│       │   ├── __init__.py
│       │   └── lilypond_renderer.py
│       └── cli.py               # Command line interface
├── tests/
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_parser.py
│   ├── test_renderers.py
│   └── fixtures/                # .brf test files go here
│       └── fengyang_flower_drum.brf
├── docs/
│   └── bana_reference.md        # BANA symbol table reference
├── examples/
├── LICENSE                      # GPL-2.0
├── README.md
├── pyproject.toml
├── CLAUDE.md                    # This file
└── .github/
    └── workflows/
        └── ci.yml
```

---

## Key Design Decisions

1. **Voice numbers:** All voice numbers are per-part (1-4), never global.
2. **Encoding:** Normalize all input to Unicode braille (U+2800-U+28FF) internally
   regardless of whether the input file uses ASCII braille or Unicode braille.
3. **Relative mode:** All LilyPond output uses `\relative` mode for readability.
4. **Concert pitch:** Default to concert pitch output; transposing instrument
   support added in Sprint 5b.
5. **Restricted LilyPond parser:** The LilyPond → BRF reverse direction (Sprint 9)
   only needs to parse LilyPond that DottedNotes itself generated, not arbitrary
   LilyPond written by humans. This keeps the reverse parser tractable.
6. **No external APIs:** All format conversion is handled internally.
   No network dependencies for core functionality.
7. **Error messages:** Always plain text, always meaningful, always screen-reader
   friendly. Never silent failures.

---

## Domain Model Reference

### BrailleSymbol (base class)
```python
dots: frozenset[int]       # e.g. {1,4,5}
category: SymbolCategory   # NOTE, REST, ARTICULATION, DYNAMIC, etc.
raw_brl: str               # Unicode braille character U+2800-U+28FF
```

### Note
```python
note_name: str             # C, D, E, F, G, A, B
octave: int                # absolute octave number
duration: Duration
accidental: Accidental | None
articulations: list[Articulation]
ornaments: list[Ornament]
def to_lilypond() -> str
def to_braille() -> str    # Sprint 9
```

### Duration
```python
value: int                 # 1, 2, 4, 8, 16, 32, 64
dots: int                  # augmentation dots (0, 1, or 2)
def to_lilypond() -> str   # e.g. "4." for dotted quarter
```

### LilyPond note name conventions
```
c d e f g a b              (natural notes)
cis dis eis fis gis ais bis (sharps, add "is")
ces des ees fes ges aes bes (flats, add "es")
cisis disis ...             (double sharps, add "isis")
ceses deses ...             (double flats, add "eses")
```

### LilyPond octave conventions (relative mode)
```
c,   = C below bass clef staff
c    = C in bass clef range
c'   = middle C
c''  = C above treble clef staff
c''' = high C
```

### LilyPond duration conventions
```
1 2 4 8 16 32 64           (whole through 64th)
4.  = dotted quarter
4.. = double dotted quarter
r4  = quarter rest
R1  = whole measure rest (4/4)
R1*8 = eight measures rest
```

---

## BANA Braille Music Key Facts

- **Note value ambiguity:** The same dot pattern means whole/16th or half/8th
  depending on context. Resolution depends on time signature and rhythmic context.
  This is the hardest algorithmic problem in the parser (Sprint 2).
- **Octave marks:** Octave is marked explicitly only when it changes or is
  ambiguous. The parser must track current octave state.
- **In-accord:** BANA's term for chords — multiple notes played simultaneously,
  notated with a specific separator character.
- **Measure repeat:** Specific dot combination means "repeat previous measure."
  Must be expanded (not passed through) in the output.
- **Interval shorthand:** Common in orchestral scores — only the top note and
  interval number are written; second voice must be reconstructed.

---

## CLI Design

```bash
# Basic conversion
dottednotes convert input.brf output.ly

# Convert and compile to PDF + MIDI (requires lilypond binary installed)
dottednotes convert input.brf output.ly --compile

# Convert with verbose output (lists all symbols parsed and any skipped)
dottednotes convert input.brf output.ly --verbose

# Show help
dottednotes --help

# Show version
dottednotes --version
```

---

## Testing Strategy

- Unit tests for every model class `to_lilypond()` method
- Unit tests for encoding detection and normalization
- Integration tests: parse a .brf fixture → verify Note objects produced
- Round-trip tests (Sprint 9): BRF → LilyPond → BRF, verify output matches input
- Primary test fixture: fengyang_flower_drum.brf (developer's own composition,
  known correct output)
- Run tests with: `pytest tests/ --cov=dottednotes`

---

## Sprint Progress

See TICKETS.md for full ticket details and step-by-step instructions.

- [ ] Sprint 0: Project Setup
- [ ] Sprint 1: Core Symbol Layer
- [ ] Sprint 2: Braille Parser — Notes and Rhythm
- [ ] Sprint 3: Key Signatures, Time Signatures, Clefs
- [ ] Sprint 4: Articulations and Dynamics
- [ ] Sprint 5: Chords and Multiple Voices
- [ ] Sprint 5b: Orchestral Score Support
- [ ] Sprint 6: Ornaments and Advanced Idioms
- [ ] Sprint 7: Score Assembly and Full Pipeline
- [ ] Sprint 8: Accessibility and Polish
- [ ] Sprint 9: Reverse Direction — LilyPond to BRF
- [ ] Sprint 10: MusicXML Bridge

---

## How to Work With This File

At the start of every Claude Code session:
1. Read CLAUDE.md to restore full project context
2. Read TICKETS.md to see which tickets are done and which are next
3. Ask the developer which ticket to work on if not specified
4. Never mark tickets done — the developer checks them off
5. Always run `pytest tests/` before and after making changes
6. Always write tests alongside implementation, never after
7. If you are unsure about a BANA convention, say so explicitly
   rather than guessing — incorrect braille parsing is worse than
   an honest "I don't know, let's look this up"

8. The authoritative dot pattern reference is 
   src/dottednotes/bana_symbols.py. 
   Never guess dot patterns — if a symbol is not 
   in that file, ask the developer to supply it 
   from the BANA manual before implementing.
   9. The BANA Music Braille Code 2015 manual is available at:
   https://www.brailleauthority.org/music/Music_Braille_Code_2015.pdf
   
   At the start of any sprint involving new BANA symbols, fetch 
   the relevant chapter(s) from this URL and cross-reference 
   ASCII braille characters against ASCII_TO_DOTS in 
   bana_symbols.py to get correct dot patterns.
   
   Never guess dot patterns. If the mapping is unclear from 
   the ASCII representation, ask the developer to confirm 
   before implementing.