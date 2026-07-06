ƒ# DottedNotes — Project Tickets

This file contains all sprints and tickets for the DottedNotes project.
Check off tickets as you complete them: change `[ ]` to `[x]`.
Each ticket includes step-by-step instructions and a Definition of Done (DoD).

---

## How to read this file

- **Why:** The reason this ticket exists and why it matters
- **Steps:** Concrete implementation steps in order
- **Definition of Done:** The ticket is not complete until every item here is true
- **Senior note:** Advice from a senior engineer perspective on common pitfalls

---

# Sprint 0: Project Setup

Goal: A clean, working Python repository that compiles, tests pass,
and Claude Code has full context on every future session.
Estimated time: 1–2 days.

---

### [x] S0-1: Create java-legacy branch and clean main

**Why:** Preserve the original Java work permanently before removing it from main.
Losing history is unprofessional and unnecessary.

**Steps:**
1. In your terminal, navigate to your local DottedNotes clone
2. Run: `git checkout -b java-legacy`
3. Run: `git push origin java-legacy`
4. Run: `git checkout main`
5. Run: `git rm -r src/`
6. Run: `git rm pom.xml`
7. Run: `git commit -m "Remove Java implementation, beginning Python rewrite"`
8. Run: `git push origin main`
9. Verify on GitHub that the java-legacy branch exists and main no longer has Java files

**Definition of Done:**
- [x] java-legacy branch exists on GitHub with all original Java files intact
- [x] main branch no longer contains src/ (Java) or pom.xml
- [x] git log on main shows the removal commit
- [ ] No data was lost — java-legacy branch is a complete copy of the original

**Senior note:** Never force-push to main on a public repository. Always use
a clean commit to remove files so the history is readable.

---

### [ ] S0-2: Set up Python project structure

**Why:** A consistent directory structure makes the project navigable for
contributors and signals professional practice.

**Steps:**
1. On main, create the following directory structure:
```
src/dottednotes/__init__.py
src/dottednotes/models/__init__.py
src/dottednotes/parser/__init__.py
src/dottednotes/renderers/__init__.py
tests/__init__.py
tests/fixtures/
docs/
examples/
```
2. Create each `__init__.py` as an empty file for now
3. Create `pyproject.toml` with this content:
```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.backends.legacy:build"

[project]
name = "dottednotes"
version = "0.1.0"
description = "Braille music to LilyPond converter for blind composers"
readme = "README.md"
license = {file = "LICENSE"}
requires-python = ">=3.9"
dependencies = []

[project.scripts]
dottednotes = "dottednotes.cli:main"

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
```
4. Run: `pip install -e ".[dev]"` to install the package in development mode
5. Verify the install worked: `python -c "import dottednotes; print('OK')"`

**Definition of Done:**
- [x] All directories and `__init__.py` files exist
- [x] `pyproject.toml` is present and valid
- [x] `pip install -e ".[dev]"` completes without errors
- [x] `import dottednotes` works in a Python shell
- [x] All files committed to main

**Senior note:** The `-e` flag in `pip install -e` means "editable install" —
changes you make to the source code are immediately reflected without
reinstalling. Always use this during development.

---

### [x] S0-3: Set up pytest and write a hello-world test

**Why:** Establishing that the test suite runs before writing any real code
means you will catch CI setup problems early rather than after weeks of work.

**Steps:**
1. Create `tests/test_hello.py` with this content:
```python
def test_project_imports():
    """Verify the package installs and imports correctly."""
    import dottednotes
    assert dottednotes is not None

def test_placeholder():
    """Placeholder test — replace with real tests in Sprint 1."""
    assert 1 + 1 == 2
```
2. Run: `pytest tests/` from the project root
3. Verify both tests pass and output is clean plain text (no visual decorations)
4. Run: `pytest tests/ --cov=dottednotes` to verify coverage reporting works

**Definition of Done:**
- [x] `pytest tests/` runs without errors
- [x] Both placeholder tests pass
- [x] Coverage report generates without errors (0% coverage is fine at this stage)
- [x] Test output is readable by VoiceOver (no progress bar decorations)

**Senior note:** If the coverage output has visual bar graphs that are
noisy with VoiceOver, add this to pyproject.toml to suppress them:
```toml
[tool.coverage.report]
show_missing = true
skip_covered = false
```

---

### [d] S0-4: Set up GitHub Actions CI

**Why:** CI means every push is automatically tested. This catches regressions
before they accumulate and signals to potential employers that you practice
professional engineering.

**Steps:**
1. Create `.github/workflows/ci.yml` with this content:
```yaml
name: CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.9", "3.11"]

    steps:
      - uses: actions/checkout@v4
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install dependencies
        run: pip install -e ".[dev]"
      - name: Run tests
        run: pytest tests/ --cov=dottednotes --cov-report=term-missing
```
2. Commit and push to main
3. Go to the Actions tab on GitHub and verify the workflow runs green

**Definition of Done:**
- [x] `.github/workflows/ci.yml` exists and is valid YAML
- [x] CI runs automatically on push to main
- [x] CI passes on both Python 3.9 and 3.11
- [x] GitHub Actions badge is visible on the repository page

**Senior note:** Testing on two Python versions (3.9 and 3.11) catches
compatibility issues early. Python 3.9 is the minimum we support;
3.11 is the current stable version most users will have.

---

### [x] S0-5: Document the BANA symbol table

**Why:** This is the ground truth reference for the entire project.
Having it as a Python dictionary means every other module can import it
rather than hardcoding braille dot patterns in multiple places.

**Steps:**
1. Create `src/dottednotes/bana_symbols.py`
2. Define the core symbol dictionaries. Start with notes:
```python
"""
BANA Braille Music symbol table.
Each entry maps a Unicode braille character to its dot pattern and meaning.
Reference: BANA Braille Music Technical Manual
https://www.brailleauthority.org/music/music.html
"""

from enum import Enum, auto

class SymbolCategory(Enum):
    NOTE = auto()
    REST = auto()
    ACCIDENTAL = auto()
    OCTAVE_MARK = auto()
    KEY_SIGNATURE = auto()
    TIME_SIGNATURE = auto()
    ARTICULATION = auto()
    DYNAMIC = auto()
    ORNAMENT = auto()
    BAR_LINE = auto()
    REPEAT = auto()
    INTERVAL = auto()
    CHORD_INDICATOR = auto()
    IN_ACCORD = auto()
    UNKNOWN = auto()

# Note cells: maps Unicode braille char to (note_name, duration_value)
# Duration values: 1=whole/16th, 2=half/8th, 4=quarter/32nd (ambiguous by design)
# Ambiguity is resolved in the parser using rhythmic context
NOTE_CELLS = {
    '\u2800': None,  # blank cell (rest or space)
    # Add full BANA note table here during Sprint 1
    # Format: unicode_char: (note_name, base_duration)
}

# Octave marks
OCTAVE_MARKS = {
    # Add BANA octave mark cells here
    # Format: unicode_char: octave_number (1-7)
}

# Accidental cells
ACCIDENTAL_CELLS = {
    # Add BANA accidental cells here
    # Format: unicode_char: accidental_type_string
}
```
3. Create `docs/bana_reference.md` as a human-readable reference document
   listing the same symbols with descriptions — this is for contributors
   who want to understand the symbol table without reading code
4. Source the BANA Braille Music Technical Manual from:
   https://www.brailleauthority.org/music/music.html
   and begin populating the NOTE_CELLS dictionary

**Definition of Done:**
- [x] `bana_symbols.py` exists with SymbolCategory enum defined
- [x] At least the 7 natural note names (C through B) for quarter note duration
      are correctly entered in NOTE_CELLS
- [x] `docs/bana_reference.md` exists with a human-readable symbol table
- [x] Module imports without errors: `from dottednotes.bana_symbols import NOTE_CELLS`

**Senior note:** Do not try to enter the entire BANA symbol table at once —
it is large and error-prone to do all at once. Enter enough to support
Sprint 1, and add more symbols as each sprint requires them.
Accuracy matters more than completeness at this stage.

---

### [ ] S0-6: Collect test fixture files

**Why:** Real .brf files as test cases ensure your parser handles actual
braille music, not just ideal cases you constructed yourself.
Bugs always hide in real data.

**Steps:**
1. Export the Fengyang Flower Drum Song from your BrailleNotetaker as a .brf file
2. Save it as `tests/fixtures/fengyang_flower_drum.brf`
3. Find 2 additional .brf files from public sources:
   - NLS (National Library Service): nlsbard.loc.gov has downloadable braille music
   - RNIB: rnib.org.uk has braille music downloads
   - Choose simple pieces (a short song, a simple piano piece)
4. Save them in `tests/fixtures/` with descriptive names
5. Add a `tests/fixtures/README.md` explaining what each file is and its source

**Definition of Done:**
- [x] At least 3 .brf fixture files exist in `tests/fixtures/`
- [x] Fengyang Flower Drum is one of them (developer-authored, known correct output)
- [x] `tests/fixtures/README.md` documents each file's title, composer, and source
- [x] All fixture files are committed to the repository

**Senior note:** The Fengyang file is your most valuable test case because you
know exactly what the correct LilyPond output should look like — you wrote it
by hand during your composition brief. Every other test case is less certain.
Keep that file and its known-good .ly output together.

---

### [ ] S0-7: Implement BRLInputPipeline with encoding detection

**Why:** Braille music files exist in both ASCII braille encoding and Unicode
braille encoding. Your tool must handle both transparently so users never
have to think about encoding.

**Steps:**
1. Create `src/dottednotes/parser/input_pipeline.py`
2. Implement the ASCII braille to Unicode braille mapping table.
   ASCII braille uses printable characters (space=0 dots, a=dot1, etc.):
```python
# ASCII braille character to dot pattern mapping
# Based on North American Braille ASCII standard
ASCII_TO_DOTS = {
    ' ': 0b000000,  # no dots
    'A': 0b000001,  # dot 1
    '1': 0b000001,  # dot 1 (digits map same as letters in some encodings)
    # ... complete the table
}

def ascii_braille_char_to_unicode(char: str) -> str:
    """Convert a single ASCII braille character to Unicode braille."""
    dots = ASCII_TO_DOTS.get(char.upper(), 0)
    return chr(0x2800 + dots)
```
3. Implement `BRLInputPipeline` class:
```python
class BRLInputPipeline:
    def load(self, filepath: str) -> str:
        """Load a .brf or .brl file and return normalized Unicode braille."""
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            raw = f.read()
        encoding = self._detect_encoding(raw)
        if encoding == 'ascii':
            return self._ascii_to_unicode(raw)
        return raw  # already Unicode braille

    def _detect_encoding(self, content: str) -> str:
        """Detect whether content is ASCII braille or Unicode braille."""
        for char in content:
            if char.strip():
                if 0x2800 <= ord(char) <= 0x28FF:
                    return 'unicode'
                return 'ascii'
        return 'unknown'

    def _ascii_to_unicode(self, text: str) -> str:
        """Convert ASCII braille text to Unicode braille."""
        result = []
        for char in text:
            if char in ('\n', '\r', '\t'):
                result.append(char)
            else:
                result.append(ascii_braille_char_to_unicode(char))
        return ''.join(result)
```
4. Write unit tests in `tests/test_parser.py`:
```python
def test_detect_unicode_encoding():
    pipeline = BRLInputPipeline()
    unicode_text = '\u2801\u2803'  # Unicode braille
    assert pipeline._detect_encoding(unicode_text) == 'unicode'

def test_detect_ascii_encoding():
    pipeline = BRLInputPipeline()
    ascii_text = 'ABC'  # ASCII braille
    assert pipeline._detect_encoding(ascii_text) == 'ascii'

def test_same_content_both_encodings():
    """Same musical content in both encodings should normalize identically."""
    pipeline = BRLInputPipeline()
    # Use known equivalent ASCII and Unicode representations of the same cell
    # (fill in with actual values from BANA table)
    pass  # complete during implementation
```

**Definition of Done:**
- [x] `BRLInputPipeline` class exists and imports without errors
- [x] `_detect_encoding()` correctly identifies Unicode and ASCII braille
- [x] `_ascii_to_unicode()` converts ASCII braille to correct Unicode characters
- [x] `load()` accepts both .brf and .brl file extensions
- [x] All unit tests pass
- [x] Loading the Fengyang .brf fixture file does not raise an exception

---

### [x] S0-8: Update README.md

**Why:** The README is the first thing potential employers, collaborators,
and users see. It should tell the story of the project clearly.

**Steps:**
1. Replace the existing README.md with a new version that includes:
   - Project title and one-sentence description
   - Why this project exists (the accessibility gap it fills)
   - Current status (active development, Sprint 0)
   - Planned workflow (BRF → LilyPond → PDF + MIDI)
   - Installation instructions
   - Usage example (the CLI commands from CLAUDE.md)
   - Background (Freedots connection, blind composer perspective)
   - Contributing section
   - License
2. Add a CI status badge at the top once GitHub Actions is passing:
```markdown
![CI](https://github.com/judithhinlung/DottedNotes/actions/workflows/ci.yml/badge.svg)
```
3. Commit with message: "Update README for Python rewrite"

**Definition of Done:**
- [x] README accurately describes the Python project, not the Java version
- [x] Installation instructions work when followed from scratch
- [x] CI badge is present and shows passing status
- [x] Accessibility motivation is clearly stated in the README
- [x] No references to Maven or Java remain in the README

---

### [x] S0-9: Add CLAUDE.md and TICKETS.md to repository

**Why:** These files give Claude Code full context on every future session,
eliminating the need to re-explain the project from scratch each time.

**Steps:**
1. Copy CLAUDE.md (this file's companion) into the repository root
2. Copy TICKETS.md (this file) into the repository root
3. Commit both files: `git commit -m "Add Claude Code context files"`
4. Push to main

**Definition of Done:**
- [x] CLAUDE.md exists in the repository root
- [x] TICKETS.md exists in the repository root
- [x] Both files are committed to main
- [x] Checked off tickets in TICKETS.md reflect actual project state

---

# Sprint 1: Core Symbol Layer

Goal: All domain model classes exist, have correct fields,
and their `to_lilypond()` methods produce valid LilyPond syntax.
Estimated time: 3–4 days.

---

### [x] S1-1: Implement BrailleSymbol base class

**Why:** Every musical symbol in braille is a BrailleSymbol.
Having a base class enforces consistent structure and
allows type checking throughout the codebase.

**Steps:**
1. Create `src/dottednotes/models/base.py`:
```python
from dataclasses import dataclass, field
from typing import Optional
from dottednotes.bana_symbols import SymbolCategory

@dataclass
class BrailleSymbol:
    """Base class for all braille music symbols."""
    dots: frozenset
    category: SymbolCategory
    raw_brl: str  # the Unicode braille character

    def to_lilypond(self) -> str:
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement to_lilypond()"
        )

    de  f __repr__(self) -> str:
        return (f"{self.__class__.__name__}("
                f"dots={self.dots}, "
                f"category={self.category.name})")
```
2. Write unit tests:
```python
def test_braille_symbol_requires_to_lilypond():
    """BrailleSymbol subclasses must implement to_lilypond."""
    import pytest
    sym = BrailleSymbol(
        dots=frozenset([1,2]),
        category=SymbolCategory.NOTE,
        raw_brl='\u2803'
    )
    with pytest.raises(NotImplementedError):
        sym.to_lilypond()
```

**Definition of Done:**
- [x] `BrailleSymbol` class exists in `models/base.py`
- [x] Class has `dots`, `category`, and `raw_brl` fields
- [x] `to_lilypond()` raises `NotImplementedError` when called on base class
- [x] `__repr__` produces a readable string without visual decorations
- [x] Unit test for NotImplementedError passes

---
                    
### [x] S1-2: Implement Duration class

**Why:** Duration is the most frequently used supporting class —
every Note and Rest has one. Getting it right early prevents
cascading errors in all other classes.

**Steps:**
1. Create `src/dottednotes/models/duration.py`:
```python
from dataclasses import dataclass

# LilyPond duration values
VALID_DURATIONS = {1, 2, 4, 8, 16, 32, 64}

@dataclass
class Duration:
    """Represents a note or rest duration."""
    value: int      # 1=whole, 2=half, 4=quarter, 8=eighth, etc.
    dots: int = 0   # augmentation dots (0, 1, or 2)

    def __post_init__(self):
        if self.value not in VALID_DURATIONS:
            raise ValueError(
                f"Invalid duration value: {self.value}. "
                f"Must be one of {sorted(VALID_DURATIONS)}"
            )
        if self.dots not in (0, 1, 2):
            raise ValueError(
                f"Invalid dot count: {self.dots}. Must be 0, 1, or 2."
            )

    def to_lilypond(self) -> str:
        """Return LilyPond duration string e.g. '4', '4.', '4..'"""
        return str(self.value) + ('.' * self.dots)

    def duration_in_beats(self, beats_per_whole: int = 4) -> float:
        """Return duration as a float number of beats (quarter = 1.0)."""
        base = beats_per_whole / self.value
        if self.dots == 1:
            return base * 1.5
        elif self.dots == 2:
            return base * 1.75
        return base
```
2. Write unit tests covering all valid durations, dotted durations,
   and invalid inputs:
```python
def test_quarter_note_duration():
    d = Duration(value=4)
    assert d.to_lilypond() == "4"

def test_dotted_quarter():
    d = Duration(value=4, dots=1)
    assert d.to_lilypond() == "4."

def test_double_dotted_half():
    d = Duration(value=2, dots=2)
    assert d.to_lilypond() == "2.."

def test_invalid_duration_raises():
    import pytest
    with pytest.raises(ValueError):
        Duration(value=3)  # 3 is not a valid duration

def test_duration_in_beats():
    assert Duration(value=4).duration_in_beats() == 1.0
    assert Duration(value=4, dots=1).duration_in_beats() == 1.5
    assert Duration(value=2).duration_in_beats() == 2.0
```

**Definition of Done:**
- [x] `Duration` class exists with `value` and `dots` fields
- [x] `__post_init__` validates both fields and raises `ValueError` on bad input
- [x] `to_lilypond()` produces correct LilyPond strings for all valid durations
- [x] `duration_in_beats()` returns correct float values including dotted durations
- [x] All unit tests pass

---

### [x] S1-3: Implement Note class

**Why:** Note is the central class of the entire project.
Everything else exists to support Notes.

**Steps:**
1. Create `src/dottednotes/models/note.py`:
```python
from dataclasses import dataclass, field
from typing import Optional
from dottednotes.models.base import BrailleSymbol
from dottednotes.models.duration import Duration
from dottednotes.bana_symbols import SymbolCategory

# LilyPond note name mapping from standard names
NOTE_NAME_TO_LILYPOND = {
    'C': 'c', 'D': 'd', 'E': 'e', 'F': 'f',
    'G': 'g', 'A': 'a', 'B': 'b'
}

@dataclass
class Note(BrailleSymbol):
    """A single pitched note."""
    note_name: str          # 'C', 'D', 'E', 'F', 'G', 'A', 'B'
    octave: int             # absolute octave (middle C = octave 4)
    duration: Duration
    accidental: Optional[object] = None   # Accidental | None
    articulations: list = field(default_factory=list)
    ornaments: list = field(default_factory=list)

    def __post_init__(self):
        if self.note_name not in NOTE_NAME_TO_LILYPOND:
            raise ValueError(f"Invalid note name: {self.note_name}")
        if not 0 <= self.octave <= 8:
            raise ValueError(f"Octave {self.octave} out of range (0-8)")

    def _octave_marks(self) -> str:
        """Return LilyPond octave marks for absolute octave number."""
        # Middle C (C4) = c' in LilyPond
        # C5 = c'', C3 = c, C2 = c,, C1 = c,,,
        if self.octave == 4:
            return "'"
        elif self.octave == 5:
            return "''"
        elif self.octave == 6:
            return "'''"
        elif self.octave == 3:
            return ""
        elif self.octave == 2:
            return ","
        elif self.octave == 1:
            return ",,"
        elif self.octave == 7:
            return "''''"
        return "'"

    def to_lilypond(self) -> str:
        """Return LilyPond note string e.g. 'c4', 'bes2.', 'fis8'"""
        ly_name = NOTE_NAME_TO_LILYPOND[self.note_name]
        accidental_str = self.accidental.to_lilypond() if self.accidental else ''
        octave_str = self._octave_marks()
        duration_str = self.duration.to_lilypond()
        articulation_str = ''.join(
            a.to_lilypond() for a in self.articulations
        )
        return f"{ly_name}{accidental_str}{octave_str}{duration_str}{articulation_str}"
```
2. Write unit tests:
```python
def test_middle_c_quarter():
    note = Note(
        dots=frozenset(),
        category=SymbolCategory.NOTE,
        raw_brl='\u2800',
        note_name='C',
        octave=4,
        duration=Duration(value=4)
    )
    assert note.to_lilypond() == "c'4"

def test_b_flat_half_note():
    from dottednotes.models.accidental import Accidental, AccidentalType
    note = Note(
        dots=frozenset(),
        category=SymbolCategory.NOTE,
        raw_brl='\u2800',
        note_name='B',
        octave=4,
        duration=Duration(value=2),
        accidental=Accidental(AccidentalType.FLAT)
    )
    assert note.to_lilypond() == "bes'2"

def test_invalid_note_name_raises():
    import pytest
    with pytest.raises(ValueError):
        Note(
            dots=frozenset(),
            category=SymbolCategory.NOTE,
            raw_brl='\u2800',
            note_name='H',  # invalid
            octave=4,
            duration=Duration(value=4)
        )
```

**Definition of Done:**
- [x] `Note` class exists and inherits from `BrailleSymbol`
- [x] `to_lilypond()` produces correct output for all 7 natural note names
- [x] `to_lilypond()` includes octave marks for all octaves 1–7
- [x] `t    o_lilypond()` includes accidental when present
- [x] `to_lilypond()` appends articulation strings when present
- [    x] Invalid note names raise `ValueError`
- [x] All unit tests pass

---

### [x] S1-4: Implement Rest class

**Why:** Rests are as important as notes.
A piece withmissing rests will have incorrect rhythmic structure.

**Steps:**
1. Add `Rest` class to `src/dottednotes/models/note.py`:
```python
@dataclass
class Rest(BrailleSymbol):
    """A rest (silence) of a given duration."""
    duration: Duration
    is_full_measure: bool = False  # True for whole-measure rests (R1 in LilyPond)

    def to_lilypond(self) -> str:
        """Return LilyPond rest string e.g. 'r4', 'R1', 'r2.'"""
        if self.is_full_measure:
            return f"R{self.duration.to_lilypond()}"
        return f"r{self.duration.to_lilypond()}"
```
2. Write unit tests:
```python
def test_quarter_rest():
    rest = Rest(
        dots=frozenset(),
        category=SymbolCategory.REST,
        raw_brl='\u2800',
        duration=Duration(value=4)
    )
    assert rest.to_lilypond() == "r4"

def test_full_measure_rest():
    rest = Rest(
        dots=frozenset(),
        category=SymbolCategory.REST,
        raw_brl='\u2800',
        duration=Duration(value=1),
        is_full_measure=True
    )
    assert rest.to_lilypond() == "R1"

def test_dotted_half_rest():
    rest = Rest(
        dots=frozenset(),
        category=SymbolCategory.REST,
        raw_brl='\u2800',
        duration=Duration(value=2, dots=1)
    )
    assert rest.to_lilypond() == "r2."
```

**Definition of Done:**
- [x] `Rest` class exists with `duration` and `is_full_measure` fields
- [x] `to_lilypond()` produces `r` prefix for regular rests
- [x] `to_lilypond()` produces `R` prefix for full-measure rests
- [x] Dotted rests produce correct output
- [x] All unit tests pass

---

### [x] S1-5: Implement Accidental class

**Why:** Accidentals are necessary for correct pitch representation
in any key other than C major / A minor.

**Steps:**
1. Create `src/dottednotes/models/accidental.py`:
```python
from dataclasses import dataclass
from enum import Enum, auto
from dottednotes.models.base import BrailleSymbol
from dottednotes.bana_symbols import SymbolCategory

class AccidentalType(Enum):
    SHARP = auto()
    FLAT = auto()
    NATURAL = auto()
    DOUBLE_SHARP = auto()
    DOUBLE_FLAT = auto()

# Maps AccidentalType to LilyPond note name suffix
ACCIDENTAL_TO_LILYPOND_SUFFIX = {
    AccidentalType.SHARP: 'is',
    AccidentalType.FLAT: 'es',
    AccidentalType.NATURAL: '',      # natural is implied by absence of suffix
    AccidentalType.DOUBLE_SHARP: 'isis',
    AccidentalType.DOUBLE_FLAT: 'eses',
}

@dataclass
class Accidental(BrailleSymbol):
    """An accidental (sharp, flat, natural, etc.)"""
    type: AccidentalType

    def to_lilypond(self) -> str:
        """Return LilyPond accidental suffix e.g. 'is', 'es', 'isis'"""
        return ACCIDENTAL_TO_LILYPOND_SUFFIX[self.type]
```
2. Note: in LilyPond, the accidental is part of the note name, not a
   separate symbol. `Note.to_lilypond()` already calls
   `self.accidental.to_lilypond()` and appends it to the note name.
   So `B flat` → `bes`, `F sharp` → `fis`. This is already handled.
3. Write unit tests for all five accidental types.

**Definition of Done:**
- [x] `Accidental` class with `AccidentalType` enum exists
- [x] `to_lilypond()` returns correct suffix for all five types
- [x] Natural accidental returns empty string (correct LilyPond behavior)
- [x] All unit tests pass

---

### [x] S1-6: Implement Articulation class

**Why:** Staccato, accent, tenuto, and other articulations
are essential for correct musical expression.

**Steps:**
1. Create `src/dottednotes/models/articulation.py`:
```python
from dataclasses import dataclass
from enum import Enum, auto
from dottednotes.models.base import BrailleSymbol
from dottednotes.bana_symbols import SymbolCategory

class ArticulationType(Enum):
    STACCATO = auto()
    ACCENT = auto()
    TENUTO = auto()
    MARCATO = auto()
    PORTATO = auto()    # tenuto + staccato
    STACCATISSIMO = auto()

ARTICULATION_TO_LILYPOND = {
    ArticulationType.STACCATO: '-.',
    ArticulationType.ACCENT: '->',
    ArticulationType.TENUTO: '--',
    ArticulationType.MARCATO: '-^',
    ArticulationType.PORTATO: '-_',
    ArticulationType.STACCATISSIMO: '-!',
}

@dataclass
class Articulation(BrailleSymbol):
    """An articulation mark attached to a note."""
    type: ArticulationType

    def to_lilypond(self) -> str:
        return ARTICULATION_TO_LILYPOND[self.type]
```
2. Write unit tests for all articulation types.

**Definition of Done:**
- [x] `Articulation` class with `ArticulationType` enum exists
- [x] `to_lilypond()` returns correct LilyPond string for all types
- [x] All unit tests pass

---

### [x] S1-7: Implement Dynamic class

**Why:** Dynamics are essential for musical expression and
are present in virtually every real score.

**Steps:**
1. Create `src/dottednotes/models/dynamic.py`:
```python
from dataclasses import dataclass
from enum import Enum, auto
from dottednotes.models.base import BrailleSymbol
from dottednotes.bana_symbols import SymbolCategory

class DynamicLevel(Enum):
    PPP = auto()
    PP = auto()
    P = auto()
    MP = auto()
    MF = auto()
    F = auto()
    FF = auto()
    FFF = auto()
    SF = auto()
    SFZ = auto()
    FP = auto()
    CRESCENDO_START = auto()   # hairpin <
    CRESCENDO_END = auto()     # end of hairpin
    DECRESCENDO_START = auto() # hairpin >
    DECRESCENDO_END = auto()   # end of hairpin

DYNAMIC_TO_LILYPOND = {
    DynamicLevel.PPP: r'\ppp',
    DynamicLevel.PP: r'\pp',
    DynamicLevel.P: r'\p',
    DynamicLevel.MP: r'\mp',
    DynamicLevel.MF: r'\mf',
    DynamicLevel.F: r'\f',
    DynamicLevel.FF: r'\ff',
    DynamicLevel.FFF: r'\fff',
    DynamicLevel.SF: r'\sf',
    DynamicLevel.SFZ: r'\sfz',
    DynamicLevel.FP: r'\fp',
    DynamicLevel.CRESCENDO_START: r'\<',
    DynamicLevel.CRESCENDO_END: r'\!',
    DynamicLevel.DECRESCENDO_START: r'\>',
    DynamicLevel.DECRESCENDO_END: r'\!',
}

@dataclass
class Dynamic(BrailleSymbol):
    """A dynamic marking."""
    level: DynamicLevel

    def to_lilypond(self) -> str:
        return DYNAMIC_TO_LILYPOND[self.level]
```
2. Write unit tests for all dynamic levels.

**Definition of Done:**
- [x] `Dynamic` class with `DynamicLevel` enum exists
- [x] `to_lilypond()` returns correct LilyPond string for all levels
- [x] Hairpin dynamics (crescendo/decrescendo) produce correct output
- [x] All unit tests pass

---

### [x] S1-8: Write Sprint 1 integration test

**Why:** Individual unit tests verify each class in isolation.
An integration test verifies they work correctly together.

**Steps:**
1. Add to `tests/test_models.py`:
```python
def test_note_with_all_components():
    """Integration test: note with accidental, duration, and articulation."""
    from dottednotes.models.note import Note
    from dottednotes.models.duration import Duration
    from dottednotes.models.accidental import Accidental, AccidentalType
    from dottednotes.models.articulation import Articulation, ArticulationType
    from dottednotes.bana_symbols import SymbolCategory

    note = Note(

dots=frozenset([1,4]),
        category=SymbolCategory.NOTE,
        raw_brl='\u2809',
        note_name='B',
        octave=4,
        duration=Duration(value=4, dots=1),
        accidental=Accidental(
            dots=frozenset(),
            category=SymbolCategory.ACCIDENTAL,
            raw_brl='\u2800',
            type=AccidentalType.FLAT
        ),
        articulations=[
            Articulation(
                dots=frozenset(),
                category=SymbolCategory.ARTICULATION,
                raw_brl='\u2800',
                type=ArticulationType.STACCATO
            )
        ]
    )
    # B-flat, octave 4, dotted quarter, staccato
    assert note.to_lilypond() == "bes'4.-."
```
2. Run `pytest tests/` and verify all Sprint 1 tests pass
3. Run `pytest tests/ --cov=dottednotes` and verify models/ has >80% coverage

**Definition of Done:**
- [x] Integration test passes
- [x] All Sprint 1 unit tests pass (no regressions)
- [x] `models/` directory has >80% test coverage
- [x] `pytest tests/` runs clean with no warnings

---

# Sprint 2: Braille Parser — Notes and Rhythm

Goal: Parse a simple single-voice braille melody from a .brf file
and produce correct Note objects with correct pitches and durations.
Estimated time: 1.5–2 weeks.

---

### [x] S2-1: Implement BrailleTokenizer

**Why:** The tokenizer is the first stage of parsing — it converts
a raw stream of Unicode braille characters into a sequence of
typed tokens that the parser can reason about.

**Steps:**
1. Create `src/dottednotes/parser/tokenizer.py`
2. Implement a `BrailleToken` dataclass and a `BrailleTokenizer` class
3. The tokenizer reads the normalized Unicode braille string from
   `BRLInputPipeline` and produces a list of `BrailleToken` objects
4. Each token has: `symbol` (the BrailleSymbol), `position` (character index),
   `line` (line number for error reporting)
5. Unrecognized symbols should produce a token with
   `category=SymbolCategory.UNKNOWN` rather than raising an exception —
   the parser handles unknown symbols gracefully

**Definition of Done:**
- [x] `BrailleTokenizer` class exists
- [x] Tokenizer produces correct token types for note cells
- [x] Tokenizer produces correct token types for bar lines
- [x] Unknown symbols produce UNKNOWN tokens, not exceptions
- [x] Token includes position information for error reporting
- [x] Unit tests pass

---

### [x] S2-2: Implement BrailleParser skeleton

**Why:** The parser is the core of the project.
Starting with a skeleton and filling it in incrementally
is safer than trying to write it all at once.

**Steps:**
1. Create `src/dottednotes/parser/braille_parser.py`
2. Implement `BrailleParser` class with:
   - `__init__` that accepts a token stream
   - `parse()` method that returns a `Score` object
   - Internal state tracking: current octave, current duration context,
     current key signature, current time signature
3. For now, `parse()` can return an empty `Score` — fill in logic in S2-3 and S2-4
4. Write a test that the parser accepts a token stream and returns a Score:
```python
def test_parser_returns_score():
    from dottednotes.parser.braille_parser import BrailleParser
    from dottednotes.models.score import Score
    parser = BrailleParser(tokens=[])
    result = parser.parse()
    assert isinstance(result, Score)
```

**Definition of Done:**
- [x] `BrailleParser` class exists and imports without errors
- [x] `parse()` method exists and returns a `Score`
- [x] Parser state (octave, duration, key, time) is initialized correctly
- [x] Unit test passes

---

### [x] S2-3: Implement octave mark recognition and tracking

**Why:** Octave tracking is stateful and critical for correct pitch output.
A wrong octave propagates through every subsequent note until
the next explicit octave mark appears.

**Steps:**
1. Add octave mark cells to `bana_symbols.py`
2. In `BrailleParser`, implement `_parse_octave_mark(token)` method
3. Implement octave tracking state:
   - Store `self._current_octave: int`
   - Update it whenever an octave mark token is encountered
   - Apply it to the next note parsed after the mark
4. BANA rule: an octave mark applies to the next note only.
   After that note, the current octave remains until
   the next explicit mark or interval jump.
5. Write tests:
```python
def test_octave_mark_sets_octave():
    # Parse a sequence: octave-5-mark, note-C
    # Result: Note C in octave 5
    pass  # implement with real token stream

def test_octave_persists_without_mark():
    # Parse: octave-4-mark, note-C, note-D (no new octave mark)
    # Result: C in octave 4, D also in octave 4
    pass
```

**Definition of Done:**
- [x] Octave mark tokens are recognized and consumed by the parser
- [x] `_current_octave` state is updated on each octave mark
- [x] Notes following an octave mark use the correct octave
- [x] Notes without a preceding octave mark use the last known octave
- [x] Unit tests pass

---

### [x] S2-4: Implement note value ambiguity resolution

**Why:** This is the hardest problem in the entire project.
In braille music, the dot pattern for a whole note is identical to
a 16th note, and a half note is identical to an 8th note.
The parser must determine the intended duration from rhythmic context.

**Approach implemented:** measure-level buffering with a three-state
sequential machine.  All notes in a measure are collected as
`_PendingNote` objects (with `base_duration` from the symbol table),
then `_resolve_measure_durations()` resolves every note at once at the
bar line.  No value indicator is used (see `VALUE_INDICATOR_CELL` in
`bana_symbols.py` — left as `None`, never found in real music).

**Three-state machine — NORMAL / RUN / INDIVIDUAL**

Initial state: NORMAL.

**NORMAL:**
- `base_1`, next cell is `base_8`   → resolve as 16th, enter RUN
- `base_1`, next cell is `base_1`   → resolve as 16th, enter INDIVIDUAL
- `base_1`, any other next (or end) → resolve as whole note, stay NORMAL
- `base_8`                          → genuine 8th note, stay NORMAL
- `base_2`                          → half or 32nd (count-based, see below), stay NORMAL
- `base_4`                          → quarter note, stay NORMAL

**RUN** (a single `base_1` cell started a 16th-note run):
- `base_8`                          → 16th note (run continuation), stay RUN
- `base_1`, next cell is `base_8`   → 16th note (new run leader), stay RUN
- `base_1`, next cell is `base_1`   → 16th note, enter INDIVIDUAL
- `base_1`, any other next (or end) → whole note, enter NORMAL
- `base_2` / `base_4`               → half/32nd or quarter, enter NORMAL

**INDIVIDUAL** (two or more consecutive `base_1` cells):
- `base_1`                          → 16th note, stay INDIVIDUAL
- `base_8`                          → genuine 8th note (NOT a run continuation), enter NORMAL
- `base_2` / `base_4`               → half/32nd or quarter, enter NORMAL

**Key rule:** only a *single* `base_1` cell can start a run.  Two or
more consecutive `base_1` cells enter INDIVIDUAL state; any `base_8`
cell that follows them is a genuine 8th note, never a run continuation.

**Half/32nd resolution (count-based):**
Count all `base_2` cells in the measure.  If `count_2 × 2 > beats`
(they would overflow the measure as half notes), resolve all `base_2`
cells as 32nd notes; otherwise resolve all as half notes.

**Quarter resolution:** `base_4` cells are always quarter notes.

**16th-note runs — BANA rule (BANA Chapter 15):**
The first note of a run uses a whole/16th-class cell; subsequent notes
use 8th-class cells.  When 16th notes are immediately followed by a
genuine 8th note, the transcriber CANNOT use a run — individual
16th-note cells must be written instead.  This makes the notation
self-delimiting: in valid BANA braille, a `base_8` cell after a single
`base_1` run leader is always a run continuation, never a genuine 8th.

**Triplet exception (not yet implemented):**
A triplet run of six 16th notes may be written as one `base_1` cell
followed by five `base_8` cells.  Verify against BANA manual before
implementing; the current machine would misread this as one 16th note
followed by five genuine 8th notes.

**Steps:**
1. In `BrailleParser`, add `_PendingNote` dataclass:
```python
@dataclass
class _PendingNote:
    note_name: str
    octave: int
    base_duration: int   # 1, 2, 4, or 8 from NOTE_CELLS
    raw_brl: str
```
2. In `parse()`, buffer notes into a `pending` list and call
   `_finalize_measure(pending, measure_number)` at each BAR_LINE token
   and at end of input.
3. Implement `_resolve_measure_durations(pending)` using the three-state
   machine described above.
4. Implement `_validate_measure_beat_count(measure)` — warn (plain text)
   if resolved beat total does not match the time signature; do not raise.
5. Write unit tests:
   - Single `base_1` cell alone → whole note
   - Two consecutive `base_1` cells → both 16th notes
   - Single `base_1` + three `base_8` cells → four 16th notes (run)
   - Two `base_1` cells + two `base_8` cells → two 16th notes + two genuine 8th notes
   - Run interrupted by a quarter cell: `base_1`, `base_8`, `base_4`, `base_8` → 16th, 16th, quarter, genuine 8th
   - Single `base_1` cell followed by a quarter cell → whole note, quarter

**Definition of Done:**
- [x] `_resolve_measure_durations()` exists and implements the three-state machine
- [x] `_validate_measure_beat_count()` warns on beat-count mismatch (plain text)
- [x] No value indicator logic needed — `VALUE_INDICATOR_CELL` stays `None`
- [x] All unit tests listed in Steps pass
- [x] `pytest tests/` passes with no regressions

**Senior note:** The value indicator cited in older BANA literature has
never been observed in real music (confirmed by the developer).  Do not
implement it speculatively.  The three-state machine handles all known
real-world cases.  If you encounter a `.brf` file that the machine
misparsed, add a failing test first, then extend the machine.

---

### [x] S2-5: Implement bar line recognition

**Why:** Bar lines delimit measures. Without correct bar line parsing,
the Measure structure will be wrong and the LilyPond output
will have incorrect bar groupings.

**Steps:**
1. Add bar line cells to `bana_symbols.py`:
   - Regular bar line
   - Double bar line
   - Final bar line
   - Repeat bar lines (start and end)
2. In `BrailleParser`, implement `_parse_bar_line(token)` method
3. When a bar line is encountered, finalize the current measure
   and start a new one
4. Validate that the beat count of the completed measure matches
   the time signature — log a warning if it does not
   (do not raise an exception — real BRF files sometimes have
   notation ambiguities that we want to parse best-effort)

**Definition of Done:**
- [x] All four bar line types are recognized
- [x] Bar line tokens trigger measure finalization
- [x] Beat count validation runs and produces a warning on mismatch
- [x] Warning is plain text and screen-reader friendly
- [x] Unit tests pass

---

### [x] S2-6: Sprint 2 integration test — parse a simple melody

**Why:** End-to-end test of the full parsing pipeline
from .brf file to Note objects.

**Steps:**
1. Create a simple test BRF file in `tests/fixtures/simple_melody.brf`
   containing a short melody (8 bars, single voice, C major,
   4/4 time, only quarter and half notes — the simplest possible case)
2. Write an integration test:
```python
def test_parse_simple_melody():
    from dottednotes.parser.input_pipeline import BRLInputPipeline
    from dottednotes.parser.tokenizer import BrailleTokenizer
    from dottednotes.parser.braille_parser import BrailleParser

    pipeline = BRLInputPipeline()
    text = pipeline.load('tests/fixtures/simple_melody.brf')

    tokenizer = BrailleTokenizer()
    tokens = tokenizer.tokenize(text)

    parser = BrailleParser(tokens)
    score = parser.parse()

    # Verify structure
    assert len(score.staves) == 1
    assert len(score.staves[0].voices) == 1
    assert len(score.staves[0].voices[0].measures) == 8

    # Verify first note
    first_note = score.staves[0].voices[0].measures[0].notes[0]
    assert first_note.note_name == 'C'
    assert first_note.octave == 4
    assert first_note.duration.value == 4  # quarter note
```
3. Run the integration test and iterate until it passes

**Definition of Done:**
- [x] Integration test passes end-to-end
- [x] Correct number of measures parsed
- [x] First note has correct pitch, octave, and duration
- [x] No exceptions raised during parsing
- [x] `pytest tests/` passes with no regressions

---

### [x] S2-7: Integration test — render parsed melody to LilyPond

**Why:** Parsing is only useful if the output compiles.
This test closes the loop from .brf all the way to valid LilyPond.

**Steps:**
1. Extend the Sprint 2-6 integration test to render to LilyPond:
```python
def test_simple_melody_renders_to_lilypond():
    # ... parse as in S2-6 ...
    score = parser.parse()
    ly_output = score.to_lilypond()

    # Verify LilyPond output is a non-empty string
    assert isinstance(ly_output, str)
    assert len(ly_output) > 0
    assert r'\version' in ly_output
    assert r'\relative' in ly_output

    # If lilypond binary is available, compile and verify no errors
    import subprocess, shutil
    if shutil.which('lilypond'):
        result = subprocess.run(
            ['lilypond', '--silent', '-'],
            input=ly_output,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"LilyPond compilation failed:\n{result.stderr}"
        )
```

**Definition of Done:**
- [x] `score.to_lilypond()` returns a valid string
- [x] LilyPond output contains required header elements
- [x] If lilypond binary is available, output compiles without errors
- [x] Test is skipped gracefully if lilypond is not installed
      (do not fail CI just because lilypond is not in the CI environment)

(dots 4-6 followed by dots 1-4-5-6)
- Left-hand sign (dots 4-6 followed by dots 2-4-5-6)
- Word sign (dots 4-5-6)
- Any note cell directly

The tokenizer must not mistake these literary number cells
for musical number cells, and must not prepend a number sign
when they appear in the margin position.

**Literary braille upper-cell digit dot patterns:**
These are the digits 1-9 and 0 as they appear in measure
number position (no number sign prefix):
- 1: dots 2-4-5
- 2: dots 2-4-5-6
- 3: dots 2-4-5-6  (verify against manual — 2 and 3 differ)
- 4: dots 1-4-5
- 5: dots 1-4-5-6
- 6: dots 1-2-4-5
- 7: dots 1-2-4-5-6
- 8: dots 1-2-5-6
- 9: dots 2-4
- 0: dots 2-4-5 (with preceding context — verify)

Note: verify all dot patterns against BANA manual Chapter 1
before implementing, as literary braille digits must be
confirmed from the authoritative source.

**Steps:**
1. Add literary braille digit cells to bana_symbols.py:
```python
# Literary braille digits (upper cell, no number sign)
# Used for measure numbers in score margins
LITERARY_DIGITS = {
    frozenset({2,4,5}):       1,
        frozenset({2,4,5,6}):     2,
	    # complete from BANA manual verification
	    }
	    ```

2. Add a MeasureNumber token type to SymbolCategory enum
   in bana_symbols.py:
   ```python
   class SymbolCategory(Enum):
       # existing categories...
           MEASURE_NUMBER = auto()
	   ```

3. Implement margin position detection in BrailleTokenizer.
   A cell is in margin position when it appears either:
      - At the very start of the input stream
         - Immediately after a newline character
	    The tokenizer must track line position state:
	    ```python
	    class BrailleTokenizer:
	        def __init__(self):
		        self._at_line_start = True  # True at beginning of each line
			        self._current_line = 1
				        self._current_col = 0

    def _is_margin_position(self) -> bool:
            """True when tokenizer is at the start of a new line."""
	            return self._at_line_start

    def _handle_newline(self):
            self._at_line_start = True
	            self._current_line += 1
		            self._current_col = 0
			    ```

4. Implement measure number token accumulation.
   When in margin position and the current cell matches
      a LITERARY_DIGITS entry, accumulate digit cells until
         a space cell is reached, then emit a single
	    MEASURE_NUMBER token with the full integer value:
	    ```python
	    def _try_parse_measure_number(
	        self,
		    chars: list[str],
		        pos: int
			) -> tuple[BrailleToken | None, int]:
			    """
			        Attempt to parse a measure number from margin position.
				    Returns (token, chars_consumed) or (None, 0) if no
				        measure number found at this position.
					    """
					        if not self._is_margin_position():
						        return None, 0

    digits = []
        i = pos
	    while i < len(chars):
	            dots = self._char_to_dots(chars[i])
		            if dots in LITERARY_DIGITS:
			                digits.append(LITERARY_DIGITS[dots])
					            i += 1
						            elif chars[i] == '\u2800':  # space cell = end of number
							                break
									        else:
										            # Not a digit — not a measure number
											                # Reset and return nothing
													            return None, 0

    if not digits:
            return None, 0

    # Convert digit list to integer e.g. [1,2] → 12
        number = int(''.join(str(d) for d in digits))
	    token = BrailleToken(
	            symbol=BrailleSymbol(
		                dots=frozenset(),
				            category=SymbolCategory.MEASURE_NUMBER,
					                raw_brl=''.join(chars[pos:i])
							        ),
								        value=number,
									        position=pos,
										        line=self._current_line
											    )
											        # Consume the trailing space cell too
												    return token, i - pos + 1

```

5. Update BrailleTokenizer.tokenize() to call
   _try_parse_measure_number() first at each line start,
      before attempting any other token type.
         If a measure number is found, set _at_line_start = False
	    and continue tokenizing the musical content.

6. Update BrailleParser to handle MEASURE_NUMBER tokens.
   When a MEASURE_NUMBER token is encountered, update the
      parser's current measure number state and use it to
         number the next Measure object created:
	 ```python
	 def _handle_measure_number_token(
	     self, token: BrailleToken
	     ) -> None:
	         """
		     Update current measure number from margin token.
		         Also validates continuity — warn if the measure number
			     is not sequential from the previous line's last measure.
			         """
				     expected = self._last_measure_number + 1
				         if token.value != expected:
					         self._warn(
						             f"Line {token.line}: measure number {token.value} "
							                 f"found, expected {expected}. "
									             f"Score may have missing or repeated measures."
										             )
											         self._current_measure_number = token.value
												 ```

7. Add measure_number field to Measure dataclass:
```python
@dataclass
class Measure:
    notes: list
        time_signature: TimeSignature
	    key_signature: KeySignature
	        bar_line: BarLine
		    measure_number: int = 0   # 0 = unnumbered
		        dynamics: list = field(default_factory=list)
			```

8. Write unit tests:
```python
def test_measure_number_at_line_start():
    """Measure number in margin is parsed as MEASURE_NUMBER token."""
        tokenizer = BrailleTokenizer()
	    # Construct input: literary digit 1, space, then a note cell
	        input_str = literary_digit(1) + '\u2800' + note_cell('C', 4)
		    tokens = tokenizer.tokenize(input_str)
		        assert tokens[0].symbol.category == SymbolCategory.MEASURE_NUMBER
			    assert tokens[0].value == 1

def test_two_digit_measure_number():
    """Two-digit measure numbers are accumulated correctly."""
        tokenizer = BrailleTokenizer()
	    input_str = literary_digit(1) + literary_digit(2) + '\u2800'
	        tokens = tokenizer.tokenize(input_str)
		    assert tokens[0].value == 12

def test_measure_number_not_parsed_mid_line():
    """Literary digit cells mid-line are not parsed as measure numbers."""
        tokenizer = BrailleTokenizer()
	    # A digit cell appearing after a note cell should not
	        # be interpreted as a measure number
		    input_str = note_cell('C', 4) + literary_digit(1)
		        tokens = tokenizer.tokenize(input_str)
			    assert tokens[0].symbol.category == SymbolCategory.NOTE
			        assert tokens[1].symbol.category != SymbolCategory.MEASURE_NUMBER

def test_measure_number_continuity_warning():
    """Non-sequential measure numbers produce a warning."""
        parser = BrailleParser(tokens=[
	        make_measure_number_token(1),
		        # measures...
			        make_measure_number_token(3),  # skipped 2 — should warn
				    ])
				        with pytest.warns(UserWarning, match="expected 2"):
					        parser.parse()

def test_measure_number_assigned_to_measure():
    """Parsed measure number is assigned to the Measure object."""
        # Parse a score with measure number 5 at line start
	    # Verify the resulting Measure has measure_number=5
	        pass  # implement with fixture file
		```

9. Add a fixture file tests/fixtures/numbered_measures.brf
   containing a short score with explicit measure numbers
      in the margins, and write an integration test that
         verifies correct measure numbers are assigned throughout.

10. Before implementing, fetch and read:
    - BANA manual Chapter 1 (literary braille number cells)
        - BANA manual Chapter 2 (score layout and margin conventions)
	    - LilyPond Notation Reference → Rhythms → Bar numbers
	          to understand how measure numbers appear in LilyPond output

**Definition of Done:**
- [ ] LITERARY_DIGITS table populated with verified dot patterns
      from BANA manual — no guessed patterns
      - [ ] SymbolCategory.MEASURE_NUMBER enum value exists
      - [ ] BrailleTokenizer tracks line-start position state correctly
      - [ ] Measure numbers at line start are parsed as MEASURE_NUMBER tokens
      - [ ] Multi-digit measure numbers (10, 24, 100+) are accumulated correctly
      - [ ] Literary digit cells appearing mid-line are NOT parsed as
            measure numbers
	    - [ ] BrailleParser assigns measure numbers to Measure objects
	    - [ ] Non-sequential measure numbers produce a plain text warning
	          (not an exception — best-effort parsing continues)
		  - [ ] measure_number field exists on Measure dataclass
		  - [ ] All unit tests pass including the mid-line non-parsing test
		  - [ ] Integration test with numbered_measures.brf fixture passes
		  - [ ] pytest tests/ passes with no regressions

**Senior note:** The mid-line non-parsing test (S2-8 step 8 test 3)
is the most important test in this ticket. Literary digit cells
appear in musical contexts too — interval numbers, fingering,
and other symbols use overlapping dot patterns. The tokenizer
must use position state (margin vs mid-line) as the primary
discriminator, not dot pattern alone. If you rely only on dot
patterns to identify measure numbers you will get false positives
throughout the score. Position state is the key.

Also note that some scores do not include measure numbers at all,
and some include them only at the start of every system rather
than every line. The parser must handle all three cases
gracefully:
- Measure numbers on every line: use them directly
- Measure numbers on some lines only: use where present,
  infer sequentially where absent
  - No measure numbers: assign sequentially from 1
  ```

---

# Sprint 3: Key Signatures, Time Signatures, Clefs

Goal: Parse key signatures, time signatures, and clef signs from a .brf file
and produce correct LilyPond output. After this sprint, the parser handles
any standard key and time signature, not just C major 4/4.
Estimated time: 3–4 days.

---

### [x] S3-1: Implement KeySignature class

**Why:** Without a key signature class, the renderer cannot emit `\key` directives
and every note with an accidental has to carry its own `\accidental` mark in the
LilyPond output — which is wrong. The key signature is also needed by the parser
to track which accidentals are "in force" for the current measure.

**Steps:**
1. Create `src/dottednotes/models/key_signature.py`:
```python
from dataclasses import dataclass
from dottednotes.models.base import BrailleSymbol
from dottednotes.bana_symbols import SymbolCategory

# Maps sharps_or_flats count → (lilypond_note, mode_string)
# Positive = sharps, negative = flats, 0 = C major
KEY_TO_LILYPOND: dict[int, tuple[str, str]] = {
     7: ('cis', 'major'),
     6: ('fis', 'major'),
     5: ('b',   'major'),
     4: ('e',   'major'),
     3: ('a',   'major'),
     2: ('d',   'major'),
     1: ('g',   'major'),
     0: ('c',   'major'),
    -1: ('f',   'major'),
    -2: ('bes', 'major'),
    -3: ('ees', 'major'),
    -4: ('aes', 'major'),
    -5: ('des', 'major'),
    -6: ('ges', 'major'),
    -7: ('ces', 'major'),
}

@dataclass
class KeySignature(BrailleSymbol):
    """A key signature.  sharps_or_flats > 0 = sharps, < 0 = flats, 0 = C major."""
    sharps_or_flats: int    # range –7 … +7

    def __post_init__(self):
        if not -7 <= self.sharps_or_flats <= 7:
            raise ValueError(
                f"sharps_or_flats must be –7 … +7, got {self.sharps_or_flats}"
            )

    def to_lilypond(self) -> str:
        note, mode = KEY_TO_LILYPOND[self.sharps_or_flats]
        return f'\\key {note} \\{mode}'
```
2. Populate `KEY_SIGNATURE_CELLS` in `bana_symbols.py` — map each Unicode braille
   character to its `sharps_or_flats` value.
   Verify every cell against BANA Braille Music Technical Manual, Chapter 6
   (Key Signatures) before entering it.  Do not guess.
   The table should cover at minimum 0 through ±4 sharps/flats; add ±5–7 if
   they appear in the manual.
3. Add `KEY_SIGNATURE_CELLS: dict[str, int]` to the `bana_symbols.py` exports.
4. Update `SymbolCategory.KEY_SIGNATURE` — it is already defined; no change needed.
5. Write unit tests in `tests/test_models.py`:
```python
def test_key_c_major():
    ks = KeySignature(..., sharps_or_flats=0)
    assert ks.to_lilypond() == r'\key c \major'

def test_key_g_major():
    ks = KeySignature(..., sharps_or_flats=1)
    assert ks.to_lilypond() == r'\key g \major'

def test_key_f_major():
    ks = KeySignature(..., sharps_or_flats=-1)
    assert ks.to_lilypond() == r'\key f \major'

def test_key_signature_out_of_range_raises():
    import pytest
    with pytest.raises(ValueError):
        KeySignature(..., sharps_or_flats=8)
```
   Test every key in KEY_TO_LILYPOND.

**Definition of Done:**
- [x] `KeySignature` class exists in `models/key_signature.py`
- [x] `sharps_or_flats` field validated to –7 … +7
- [x] `to_lilypond()` returns correct `\key <note> \major` for all 15 standard keys
- [x] `KEY_SIGNATURE_CELLS` in `bana_symbols.py` is populated and verified against
      the BANA manual (not guessed)
- [x] All unit tests pass
- [x] `pytest tests/` passes with no regressions

**Senior note:** Only implement major keys now — the same key signature cell covers
both a major key and its relative minor.  Adding a `mode` field (MAJOR/MINOR) is
Sprint 4 or later work.  Do not add it speculatively.
The LilyPond note name for keys with accidentals uses `is` (sharp) and `es` (flat)
suffixes (e.g. `fis`, `bes`), which matches the note name convention already used
by the `Note` class.

---

### [x] S3-2: Implement TimeSignature class

**Why:** The parser already hard-codes `(4, 4)` for the time signature.
A real `TimeSignature` class lets the parser read the actual time signature from
the file and pass it through to the LilyPond output and the beat-count validator.

**Steps:**
1. Create `src/dottednotes/models/time_signature.py`:
```python
from dataclasses import dataclass
from dottednotes.models.base import BrailleSymbol
from dottednotes.bana_symbols import SymbolCategory

VALID_DENOMINATORS = {1, 2, 4, 8, 16, 32}

@dataclass
class TimeSignature(BrailleSymbol):
    """A time (meter) signature."""
    numerator: int      # beats per measure (top number)
    denominator: int    # beat unit — must be a power of 2 (bottom number)

    def __post_init__(self):
        if self.numerator < 1:
            raise ValueError(f"numerator must be >= 1, got {self.numerator}")
        if self.denominator not in VALID_DENOMINATORS:
            raise ValueError(
                f"denominator must be a power of 2, got {self.denominator}"
            )

    def beats_per_measure(self) -> float:
        """Total duration of one measure expressed as quarter-note beats."""
        return self.numerator * (4 / self.denominator)

    def to_lilypond(self) -> str:
        return f'\\time {self.numerator}/{self.denominator}'

    def as_tuple(self) -> tuple[int, int]:
        """Return (numerator, denominator) for compatibility with legacy code."""
        return (self.numerator, self.denominator)
```
2. Populate `TIME_SIGNATURE_CELLS` in `bana_symbols.py`.
   In BANA braille music, time signatures are written with a number indicator
   (⠼, dots 3,4,5,6) followed by digit cells.
   After the number indicator, digit cells use the same dot patterns as
   literary braille letters a–j, mapping to digits 1–9 and 0 respectively.
   The separator between the top and bottom numbers is a specific cell —
   verify its dot pattern from the BANA manual before entering it.
   Also verify whether common time (C, equivalent to 4/4) and cut time
   (alla breve, equivalent to 2/2) have dedicated single-cell symbols.
3. Add `NUMBER_SIGN: str` and `TIME_SIGNATURE_SEPARATOR: str` constants to
   `bana_symbols.py` so the tokenizer and parser can look them up by name
   rather than hardcoding dot patterns.
4. Write unit tests:
```python
def test_time_4_4():
    ts = TimeSignature(..., numerator=4, denominator=4)
    assert ts.to_lilypond() == r'\time 4/4'
    assert ts.beats_per_measure() == 4.0

def test_time_3_4():
    ts = TimeSignature(..., numerator=3, denominator=4)
    assert ts.to_lilypond() == r'\time 3/4'
    assert ts.beats_per_measure() == 3.0

def test_time_6_8():
    ts = TimeSignature(..., numerator=6, denominator=8)
    assert ts.to_lilypond() == r'\time 6/8'
    assert ts.beats_per_measure() == 3.0  # 6 * (4/8) = 3.0

def test_time_invalid_denominator_raises():
    import pytest
    with pytest.raises(ValueError):
        TimeSignature(..., numerator=4, denominator=3)
```

**Definition of Done:**
- [x] `TimeSignature` class exists in `models/time_signature.py`
- [x] `beats_per_measure()` returns the correct float for all tested meters
- [x] `to_lilypond()` returns the correct `\time n/d` string
- [x] `NUMBER_SIGN` and `TIME_SIGNATURE_SEPARATOR` constants are in `bana_symbols.py`
      and verified against the BANA manual
- [x] All unit tests pass
- [x] `pytest tests/` passes with no regressions

**Senior note:** `beats_per_measure()` replaces the `self._time_signature[0]` raw
number currently used in `BrailleParser._resolve_measure_durations()`.
When you wire the parser in S3-4, update that call to use `TimeSignature.beats_per_measure()`.
For 6/8 time the beat unit is the dotted quarter (= 3 eighth notes), but
`_resolve_measure_durations()` reasons in terms of quarter-note beats — so
`beats_per_measure()` must return 3.0 for 6/8, not 6.

---

### [x] S3-3: Implement Clef class

**Why:** The LilyPond renderer needs to emit `\clef treble` or `\clef bass` at the
start of each staff.  Treble is the implicit default in LilyPond, so without a
clef directive the output is technically correct for treble-only scores — but
rendering a bass-clef passage without `\clef bass` will place all the notes on
the wrong lines for sighted performers.

**Steps:**
1. Create `src/dottednotes/models/clef.py`:
```python
from dataclasses import dataclass
from enum import Enum, auto
from dottednotes.models.base import BrailleSymbol
from dottednotes.bana_symbols import SymbolCategory

class ClefType(Enum):
    TREBLE = auto()
    BASS = auto()
    ALTO = auto()    # viola clef
    TENOR = auto()   # upper strings in high passage

CLEF_TO_LILYPOND = {
    ClefType.TREBLE: 'treble',
    ClefType.BASS:   'bass',
    ClefType.ALTO:   'alto',
    ClefType.TENOR:  'tenor',
}

@dataclass
class Clef(BrailleSymbol):
    """A clef sign."""
    clef_type: ClefType

    def to_lilypond(self) -> str:
        return f'\\clef {CLEF_TO_LILYPOND[self.clef_type]}'
```
2. Populate `CLEF_CELLS` in `bana_symbols.py` — map each Unicode braille character
   to the corresponding `ClefType`.
   Verify every cell from the BANA manual before entering it.
   Implement at minimum treble and bass; alto and tenor if they appear in
   the manual and you have time.
3. Add `CLEF_CELLS: dict[str, ClefType]` to the exports in `bana_symbols.py`.
4. Write unit tests:
```python
def test_clef_treble():
    clef = Clef(..., clef_type=ClefType.TREBLE)
    assert clef.to_lilypond() == r'\clef treble'

def test_clef_bass():
    clef = Clef(..., clef_type=ClefType.BASS)
    assert clef.to_lilypond() == r'\clef bass'
```

**Definition of Done:**
- [x] `Clef` class with `ClefType` enum exists in `models/clef.py`
- [x] `to_lilypond()` returns correct `\clef <type>` for all implemented clef types
- [x] `CLEF_CELLS` in `bana_symbols.py` is populated and verified against the BANA manual
- [x] All unit tests pass
- [x] `pytest tests/` passes with no regressions

**Senior note:** Clef changes mid-staff are rare in the pieces you are likely to
parse first.  Do not add mid-staff clef-change logic yet; a plain `\clef` at the
top of the staff is sufficient for Sprint 3.

---

### [x] S3-4: Add key and time signature parsing to BrailleParser

**Why:** The parser currently ignores key signature and time signature cells.
All the logic from S3-1 through S3-3 is useless unless the parser reads the
cells and updates its state — and unless the renderer emits the directives
before the first note.

**Steps:**
1. Update `BrailleTokenizer` to recognize the new cell categories:
   - Cells in `KEY_SIGNATURE_CELLS` → `SymbolCategory.KEY_SIGNATURE`
   - Cells in `CLEF_CELLS` → `SymbolCategory.CLEF`
   - `NUMBER_SIGN` cell → new `SymbolCategory.NUMBER_SIGN` or handle with
     lookahead (see below)
   For time signatures, the tokenizer must use lookahead: when it sees the
   number indicator (⠼), peek ahead to consume the digit cells and the
   separator, and emit a single `TIME_SIGNATURE` token carrying the full
   multi-character sequence.  This avoids the digit cells being misread as
   8th-note pitch cells (they share the same dot patterns).
2. Update `BrailleParser._reset_state()` to use the new class types:
```python
self._key_signature: KeySignature = KeySignature(
    dots=frozenset(), category=SymbolCategory.KEY_SIGNATURE,
    raw_brl='', sharps_or_flats=0
)
self._time_signature: TimeSignature = TimeSignature(
    dots=frozenset(), category=SymbolCategory.TIME_SIGNATURE,
    raw_brl='', numerator=4, denominator=4
)
self._clef: Clef = Clef(
    dots=frozenset(), category=SymbolCategory.CLEF,
    raw_brl='', clef_type=ClefType.TREBLE
)
```
3. Add token handlers to `BrailleParser.parse()`:
```python
elif token.category == SymbolCategory.KEY_SIGNATURE:
    self._handle_key_signature(token)
elif token.category == SymbolCategory.TIME_SIGNATURE:
    self._handle_time_signature(token)
elif token.category == SymbolCategory.CLEF:
    self._handle_clef(token)
```
4. Implement the three handlers:
```python
def _handle_key_signature(self, token: BrailleToken) -> None:
    from dottednotes.bana_symbols import KEY_SIGNATURE_CELLS
    self._key_signature = KeySignature(
        dots=frozenset(), category=SymbolCategory.KEY_SIGNATURE,
        raw_brl=token.character,
        sharps_or_flats=KEY_SIGNATURE_CELLS[token.character],
    )

def _handle_time_signature(self, token: BrailleToken) -> None:
    # token.character holds the full sequence e.g. "⠼⠙⠲⠙" for 4/4
    # Parse numerator and denominator from the sequence
    ...

def _handle_clef(self, token: BrailleToken) -> None:
    from dottednotes.bana_symbols import CLEF_CELLS
    self._clef = Clef(
        dots=frozenset(), category=SymbolCategory.CLEF,
        raw_brl=token.character,
        clef_type=CLEF_CELLS[token.character],
    )
```
5. Store key/time/clef on the `Staff` object so the renderer can use them:
   - After parsing, call `staff.key_signature = self._key_signature` etc.
   - Add `key_signature`, `time_signature`, and `clef` fields to `Staff`.
6. Update `_resolve_measure_durations()` to use
   `self._time_signature.beats_per_measure()` in place of
   `float(self._time_signature[0])`.
7. Update `_validate_measure_beat_count()` similarly.
8. Update `Staff.to_lilypond()` to prepend key, time, and clef directives
   before the first measure:
```python
def to_lilypond(self, start_midi: int = 60) -> str:
    header_parts = []
    if self.key_signature.sharps_or_flats != 0:
        header_parts.append('    ' + self.key_signature.to_lilypond())
    header_parts.append('    ' + self.time_signature.to_lilypond())
    if self.clef.clef_type != ClefType.TREBLE:
        header_parts.append('    ' + self.clef.to_lilypond())
    # ... then measure lines as before
```
   Only emit `\key c \major` if there are accidentals in the piece; omit it
   for C major since LilyPond defaults to C major.
   Always emit `\time` since the default 4/4 is not guaranteed.
9. Write unit tests for parser state:
```python
def test_parser_reads_key_signature():
    # Build token stream: key_sig_cell + note
    ...
    assert parser._key_signature.sharps_or_flats == 1  # G major

def test_parser_reads_time_signature():
    # Build token stream: time_sig_sequence + notes
    ...
    assert parser._time_signature.numerator == 3
    assert parser._time_signature.denominator == 4
```

**Definition of Done:**
- [x] Tokenizer classifies key signature, time signature, and clef cells correctly
- [x] Tokenizer handles the number indicator context so digit cells are not
      misread as note cells
- [x] Parser updates `_key_signature`, `_time_signature`, and `_clef` state on
      each recognized token
- [x] `Staff` stores key, time, and clef after parsing
- [x] `Staff.to_lilypond()` prepends the appropriate `\key`, `\time`, `\clef`
      directives before the first measure
- [x] `_resolve_measure_durations()` uses `TimeSignature.beats_per_measure()`
- [x] All new unit tests pass
- [x] `pytest tests/` passes with no regressions

**Senior note:** The hardest part of this ticket is the tokenizer context switch for
time signatures.  The number indicator (⠼) followed by digit cells is the only
place in BANA music notation where cells that look like 8th-note pitch cells are
not notes.  The safest fix is to use the same lookahead pattern already used for
multi-cell bar lines: when the tokenizer sees ⠼, consume everything up to and
including the bottom-number digits and emit a single `TIME_SIGNATURE` token.
Avoid leaving this to the parser — the token stream is simpler to reason about
when every token is unambiguously categorized.

---

### [x] S3-5: Integration test — parse a non-C-major piece

**Why:** Every piece of code written in S3-1 through S3-4 must be exercised
end-to-end before Sprint 3 can be called done.  A G major piece exercises
key signature parsing, F# accidental handling, and LilyPond key output.

**Steps:**
1. Create `tests/fixtures/g_major_scale.brf` — a short G major scale in 4/4,
   containing:
   - A G major key signature cell (1 sharp)
   - A 4/4 time signature
   - 8 quarter notes ascending G–A–B–C–D–E–F#–G across two measures
   Create this on your BrailleNotetaker and export it, or construct it manually
   using the BANA cells verified in S3-1 through S3-4.
2. Add a matching `tests/fixtures/g_major_scale.ly` file with the expected
   LilyPond output, for reference during debugging.
3. Write the integration test in `tests/test_parser.py`:
```python
def test_parse_g_major_scale():
    pipeline = BRLInputPipeline()
    text = pipeline.load(FIXTURES / 'g_major_scale.brf')
    score = BrailleParser(tokens=BrailleTokenizer().tokenize(text)).parse()

    assert len(score.staves) == 1
    staff = score.staves[0]

    # Key signature: 1 sharp (G major)
    assert staff.key_signature.sharps_or_flats == 1

    # Time signature: 4/4
    assert staff.time_signature.numerator == 4
    assert staff.time_signature.denominator == 4

    # Two measures, 4 notes each
    assert len(staff.measures) == 2
    assert len(staff.measures[0].notes) == 4
    assert len(staff.measures[1].notes) == 4

    # First note: G in octave 4, quarter duration
    first_note = staff.measures[0].notes[0]
    assert first_note.note_name == 'G'
    assert first_note.octave == 4
    assert first_note.duration.value == 4
```
4. Write a render test:
```python
def test_g_major_scale_renders_to_lilypond():
    pipeline = BRLInputPipeline()
    text = pipeline.load(FIXTURES / 'g_major_scale.brf')
    score = BrailleParser(tokens=BrailleTokenizer().tokenize(text)).parse()

    ly = score.to_lilypond()

    assert r'\key g \major' in ly
    assert r'\time 4/4' in ly
    # F# appears as fis in LilyPond
    assert 'fis' in ly
```
5. If the lilypond binary is available, add a compile check (same pattern as
   `test_simple_melody_lilypond_compiles`).

**Definition of Done:**
- [x] `tests/fixtures/g_major_scale.brf` exists and is verified correct braille
- [x] `tests/fixtures/g_major_scale.ly` exists as a reference
- [x] Integration test passes: correct staves, measures, and first note
- [x] Render test passes: `\key g \major`, `\time 4/4`, and `fis` all appear
      in the LilyPond output
- [x] If lilypond binary is present, the output compiles without errors
- [x] `pytest tests/` passes with no regressions

**Senior note:** The F# in G major will be written in the .brf file as an
explicit accidental before the F note cell (since the parser does not yet carry
key signature context into note-level pitch resolution — that is Sprint 4 work).
The test should assert `fis` appears in the output but should not assert that
the accidental is gone from the braille — that simplification comes later.
If constructing the fixture manually, double-check the octave mark before the
first note: G major scales often start on G4 or G3 depending on register.

---

# Sprint 4: Articulations, Dynamics, Ornaments, and Text

Goal: Parse articulations, dynamics, slurs, ties, ornaments (trill, mordent,
grace notes), and word-sign text markings from a .brf file and produce correct
LilyPond output for all of them.
Estimated time: 1-1.5 weeks.

---

### [x] S4-1: Add articulation parsing to BrailleParser

**Why:** The `Articulation` model and its `to_lilypond()` method already exist
(Sprint 1).  This ticket wires the BANA symbol table and parser to actually
produce articulation-carrying notes from a real .brf file.

**Verified BANA symbols (developer-confirmed dot patterns):**

| Articulation     | Braille cells    | Unicode  | LilyPond      |
|------------------|------------------|----------|---------------|
| Staccato         | 2,3,6            | ⠦        | `-.`          |
| Staccatissimo    | 6 + 2,3,6        | ⠠⠦      | `-!`          |
| Mezzo staccato   | 5 + 2,3,6        | ⠐⠦      | `-_`          |
| Tenuto           | 4,5,6 + 2,3,6    | ⠸⠦      | `--`          |
| Accent           | 4,6 + 2,3,6      | ⠨⠦      | `->`          |
| Expressive accent| 4,5 + 2,3,6      | ⠘⠦      | `-^`          |
| Swell            | 3,6 + 3          | ⠤⠄      | `\espressivo` |

Reversed accent (dots 4 + 2,3,6) skipped — no LilyPond equivalent.
Arpeggios deferred to Sprint 5.

**BANA placement rule:** Articulations come BEFORE the note they modify.
The order within a cell sequence is: articulation → accidental → octave mark → note.
Octave marks are always the cell immediately before the note.

**Doubling rule:** Any articulation sign (except swell) may be doubled to
indicate it applies to 4 or more successive notes.  A doubled sign (same sign
twice with no note between them) activates carry mode for that type.  A single
instance of the sign while carry mode is active marks the last note and ends carry.

**Steps:**
1. Add `ARTICULATION_CELLS: dict[str, str]` to `bana_symbols.py` using the
   verified cells in the table above.
2. Update `BrailleTokenizer` to check 2-cell articulation pairs (longest match
   first) immediately before the `_classify()` fallthrough.  Several 2-cell
   pair first-cells (⠠, ⠐, ⠸, ⠨, ⠘) are also OCTAVE_MARKS; the 2-cell check
   must come first.  The second cell ⠦ (dots 2,3,6) never follows an octave
   mark legitimately so this is always unambiguous.
3. Update `models/articulation.py`: rename `MARCATO` → `EXPRESSIVE_ACCENT`
   and `PORTATO` → `MEZZO_STACCATO` to match BANA terminology; add `SWELL`.
4. In `BrailleParser._reset_state()`, add:
   ```python
   self._pending_articulations: list[Articulation] = []
   self._active_articulations: set[ArticulationType] = set()
   self._terminating_articulations: set[ArticulationType] = set()
   self._last_articulation_seen: ArticulationType | None = None
   ```
5. Add `_handle_articulation(token)` with carry-mode logic:
   - Type in `_active_articulations` → terminator: add to pending, mark terminating.
   - Type == `_last_articulation_seen` → doubled sign: activate carry, reset last_seen.
   - Otherwise → single sign: add to pending, set last_seen.
6. In `_buffer_note()`, combine `_pending_articulations` and `_active_articulations`
   (deduplicated); clear pending; end carry for terminating types; reset last_seen.
7. In `_finalize_measure()`, pass `articulations=pnote.articulations` to `Note(...)`.
8. Write unit tests covering: single articulation attachment, no carry-forward for
   single signs, doubled sign carry mode, terminator sign ending carry.

**Definition of Done:**
- [x] `ARTICULATION_CELLS` in `bana_symbols.py` is populated with verified cells
- [x] Tokenizer classifies all 7 articulation cells/pairs as `SymbolCategory.ARTICULATION`
- [x] 2-cell articulation pairs take priority over OCTAVE_MARK classification
- [x] Parser attaches articulations to the note that follows them
- [x] Single sign does not carry forward to subsequent notes
- [x] Doubled sign activates carry mode; terminator sign ends it
- [x] `Note.to_lilypond()` includes articulation suffixes
- [x] All unit tests pass
- [x] `pytest tests/` passes with no regressions

---

### [x] S4-2: Add dynamic parsing to BrailleParser

**Why:** Dynamics are present in virtually every piece of real music.
Without them the LilyPond output plays at a uniform volume and is incomplete.
The `Dynamic` model already exists; this ticket adds recognition and
attachment to notes.

**Verified BANA dynamic sequences (developer-confirmed):**

All dynamic markings begin with the word sign ⠜ (dots 3,4,5).
The word sign also serves as the clef prefix; the tokenizer checks clef
sequences first, then dynamic sequences.

| Dynamic | Braille sequence          | Unicode  |
|---------|---------------------------|----------|
| ppp     | word sign + p + p + p     | ⠜⠏⠏⠏   |
| pp      | word sign + p + p         | ⠜⠏⠏    |
| p       | word sign + p             | ⠜⠏     |
| mp      | word sign + m + p         | ⠜⠍⠏    |
| mf      | word sign + m + f         | ⠜⠍⠋    |
| f       | word sign + f             | ⠜⠋     |
| ff      | word sign + f + f         | ⠜⠋⠋    |
| fff     | word sign + f + f + f     | ⠜⠋⠋⠋   |
| sf      | word sign + s + f         | ⠜⠎⠋    |
| sfz     | word sign + s + f + z     | ⠜⠎⠋⠵   |
| fp      | word sign + f + p         | ⠜⠋⠏    |
| cresc.  | word sign + c (dots 1,4)  | ⠜⠉     |
| decresc.| word sign + d (dots 1,4,5)| ⠜⠙     |
| end cresc. | word sign + lower c (dots 2,5)  | ⠜⠒ |
| end decresc.| word sign + lower d (dots 2,5,6)| ⠜⠲ |

**End word sign:** ⠄ (dot 3). Required after a dynamic when the next cell
starts with dots 1, 2, or 3 (which includes all notes and articulations).
The tokenizer consumes ⠄ when present and does not emit it as a token.

**Placement rules:**
- All dynamics except end marks appear BEFORE the note they affect.
  Order: dynamic → articulation → accidental → octave mark → note.
- End crescendo (⠜⠒) and end decrescendo (⠜⠲) appear AFTER the last note
  of the passage. The tokenizer emits them as DYNAMIC tokens; the parser
  attaches them to `pending[-1]` (the most recently buffered note).

**Steps:**
1. Add `WORD_SIGN`, `END_WORD_SIGN`, and `DYNAMIC_CELLS` to `bana_symbols.py`.
   Entries must be ordered longest-first so the tokenizer can greedy-match.
2. In `BrailleTokenizer`, extend the ⠜ (word sign / clef prefix) block:
   after ruling out clef sequences, try lengths 4, 3, 2 against `DYNAMIC_CELLS`.
   If matched, consume an optional trailing ⠄. If nothing matches, emit UNKNOWN.
   Add an explicit `continue` at the end of the block.
3. Add `dynamics: list[Dynamic]` to the `Note` dataclass (before `articulations`).
   Update `to_lilypond()` and `to_relative_lilypond()` to emit dynamics before
   articulations: `{note}{duration}{dynamics}{articulations}`.
4. In `BrailleParser._reset_state()`, add `_pending_dynamics: list[Dynamic]`.
   In `_buffer_note()`, capture and clear `_pending_dynamics`.
   In `parse()`, handle `SymbolCategory.DYNAMIC` inline:
   - End marks → `pending[-1].dynamics.append(dynamic)` (if pending non-empty).
   - All other marks → `_pending_dynamics.append(dynamic)`.
5. In `_finalize_measure()`, pass `dynamics=pnote.dynamics` to `Note(...)`.
6. Write unit tests covering all 15 dynamic sequences, end-word-sign consumption,
   longest-match resolution (ppp over pp, sfz over sf), attachment to the correct
   note, no carry-forward, and LilyPond rendering.

**Definition of Done:**
- [x] `DYNAMIC_CELLS` in `bana_symbols.py` is populated with verified sequences
- [x] Tokenizer emits `SymbolCategory.DYNAMIC` for all 15 sequences
- [x] Tokenizer correctly consumes optional ⠄ end word sign
- [x] Clef recognition is unaffected
- [x] `Note` dataclass has a `dynamics: list[Dynamic]` field
- [x] `Note.to_lilypond()` emits dynamics before articulations
- [x] Pre-note dynamics attach to the following note; do not carry forward
- [x] End marks attach to the preceding (last buffered) note
- [x] All unit tests pass
- [x] `pytest tests/` passes with no regressions

---

### [x] S4-3: Implement slur and tie parsing

**Why:** Ties connect two same-pitch notes into a single sustained sound.
Slurs group notes into phrases.  Without them a legato melody becomes
detached and phrasing information is lost entirely.

**Steps:**
1. Add tie and slur cells to `bana_symbols.py`.
   **Verify against BANA section 13 before entering.**
   Starting points (confirm before use):
   - Tie: U+2809 (dots 1,4) -- appears between the two tied notes
   - Short slur (single-cell): verify from manual
   - Slur begin (multi-note phrase): verify from manual
   - Slur end: verify from manual
   Define named constants:
   ```python
   TIE_CELL: str = '...'         # verify from BANA section 13
   SLUR_BEGIN_CELL: str = '...'  # verify from BANA section 13
   SLUR_END_CELL: str = '...'    # verify from BANA section 13
   ```
2. Add `SymbolCategory.TIE` and `SymbolCategory.SLUR` to the enum in
   `bana_symbols.py`.
3. Update `BrailleTokenizer` to classify tie and slur cells.
4. Add fields to the `Note` dataclass:
   ```python
   tied: bool = False        # True if this note is tied to the next
   slur_begin: bool = False  # True if a slur starts on this note
   slur_end: bool = False    # True if a slur ends on this note
   ```
5. Update `Note.to_lilypond()`:
   - Tie: emit `~` after the note (e.g. `c'4~`)
   - Slur begin: emit `(` after duration (e.g. `g4(`)
   - Slur end: emit `)` after duration (e.g. `a4)`)
   - Combined: `fis4(~` is valid LilyPond (tied slur start); keep `tied`
     and `slur_begin` as independent booleans.
6. In `BrailleParser.parse()`:
   - A `TIE` token sets `tied = True` on the most recently finalized note.
   - A `SLUR_BEGIN` token sets `slur_begin = True` on the following note.
   - A `SLUR_END` token sets `slur_end = True` on the most recently
     finalized note.
7. Write unit tests:
   ```python
   def test_tie_sets_tied_flag():
       notes = _parse('⠐⠹' + TIE_CELL + '⠹')
       assert notes[0].tied is True
       assert notes[1].tied is False

   def test_tie_renders_tilde():
       notes = _parse('⠐⠹' + TIE_CELL + '⠹')
       assert '~' in notes[0].to_lilypond()

   def test_slur_begin_and_end():
       notes = _parse('⠐' + SLUR_BEGIN + '⠹⠱⠫' + SLUR_END)
       assert notes[0].slur_begin is True
       assert notes[2].slur_end is True
       assert notes[1].slur_begin is False
   ```

**Definition of Done:**
- [x] `TIE_CELL`, `SLUR_BEGIN_CELL`, `SLUR_END_CELL` in `bana_symbols.py`
      verified against BANA section 13
- [x] `Note` has `tied`, `slur_begin`, `slur_end` fields
- [x] `Note.to_lilypond()` emits `~`, `(`, `)` correctly
- [x] A note that is both tied and slur-begin renders correctly (`c4(~`)
- [x] All unit tests pass
- [x] `pytest tests/` passes with no regressions

**Senior note:** Ties always connect two notes of the same pitch; slurs can
cross any interval.  The parser does not need to validate pitch equality for
ties -- just set the flag.  Grace notes (Sprint 4-4) do not participate in
ties; a tie token after a grace note should attach to the main note.

---

### [x] S4-4: Implement Ornament model and add ornament parsing

**Why:** Trills, mordents, and grace notes appear constantly in Baroque and
Classical repertoire, and grace notes are common in folk music.  Without
ornament support the output is musically incomplete for much real-world
repertoire.

**Steps:**
1. Create `src/dottednotes/models/ornament.py`:
   ```python
   from dataclasses import dataclass
   from enum import Enum, auto

   class OrnamentType(Enum):
       TRILL = auto()
       MORDENT = auto()          # lower mordent (standard)
       UPPER_MORDENT = auto()    # prall (upper mordent)
       TURN = auto()
       TREMOLO = auto()
       GRACE_NOTE = auto()       # appoggiatura (slurred grace note)
       ACCIACCATURA = auto()     # crushed grace note (short slash)

   ORNAMENT_TO_LILYPOND: dict[OrnamentType, str] = {
       OrnamentType.TRILL:         r'\trill',
       OrnamentType.MORDENT:       r'\mordent',
       OrnamentType.UPPER_MORDENT: r'\prall',
       OrnamentType.TURN:          r'\turn',
       OrnamentType.TREMOLO:       ':32',
   }

   @dataclass
   class Ornament:
       type: OrnamentType

       def to_lilypond(self) -> str:
           return ORNAMENT_TO_LILYPOND[self.type]
   ```
   Grace notes and acciaccaturas are NOT handled by `Ornament.to_lilypond()`
   -- they require a full `Note` object to wrap (see step 3).
2. The `Note` dataclass already has an `ornaments: list` field (Sprint 1).
   Verify `Note.to_lilypond()` appends ornament strings after duration
   (e.g. `c4\trill`).
3. Add a `GraceNote` dataclass to `models/ornament.py`:
   ```python
   @dataclass
   class GraceNote:
       note: 'Note'
       acciaccatura: bool = False  # True -> \acciaccatura; False -> \grace

       def to_lilypond(self) -> str:
           prefix = r'\acciaccatura' if self.acciaccatura else r'\grace'
           return f'{prefix} {{ {self.note.to_lilypond()} }}'
   ```
   Add `grace_note: GraceNote | None = None` to the `Note` dataclass.
   When present, `Note.to_lilypond()` prepends the grace note block:
   `\grace { c8 } c4` for an appoggiatura on a C quarter note.
4. Add `ORNAMENT_CELLS: dict[str, str]` to `bana_symbols.py`.
   Map each Unicode braille sequence to an `OrnamentType` name string.
   **Verify every cell against BANA section 15 before entering.**
   Also add named constants:
   ```python
   GRACE_NOTE_INDICATOR: str = '...'    # verify from BANA section 15
   ACCIACCATURA_INDICATOR: str = '...'  # verify (may differ from grace note)
   ```
5. Update `BrailleTokenizer` to classify ornament and grace note indicator
   cells as `SymbolCategory.ORNAMENT`.
6. In `BrailleParser.parse()`:
   - Standard ornament cell: buffer and attach to the next note's `ornaments`
     list (ornaments precede the note they modify in BANA).
   - Grace note indicator: consume the following NOTE token as a `GraceNote`
     and attach to the next real note's `grace_note` field.  The grace note
     cell is typically an 8th-note-class cell.
7. Write unit tests:
   ```python
   def test_trill_attaches_to_following_note():
       notes = _parse(TRILL_CELL + '⠐⠹')
       assert any(o.type == OrnamentType.TRILL for o in notes[0].ornaments)

   def test_trill_renders_in_lilypond():
       notes = _parse(TRILL_CELL + '⠐⠹')
       assert r'\trill' in notes[0].to_lilypond()

   def test_grace_note_wraps_note_object():
       from dottednotes.models.ornament import GraceNote
       notes = _parse(GRACE_NOTE_INDICATOR + '⠨⠙' + '⠐⠹')
       assert isinstance(notes[0].grace_note, GraceNote)
       assert notes[0].grace_note.note.note_name == 'C'

   def test_grace_note_renders_before_main_note():
       notes = _parse(GRACE_NOTE_INDICATOR + '⠨⠙' + '⠐⠹')
       ly = notes[0].to_lilypond()
       assert r'\grace' in ly
       assert ly.index(r'\grace') < ly.index("c'")
   ```

**Definition of Done:**
- [x] `Ornament` class with `OrnamentType` enum exists in `models/ornament.py`
- [x] `GraceNote` dataclass exists and wraps a `Note`
- [x] `Note` has `grace_note: GraceNote | None` field
- [x] `Note.to_lilypond()` prepends grace note block when present
- [x] `Note.to_lilypond()` appends standard ornament strings (e.g. `\trill`)
- [x] `ORNAMENT_CELLS`, `GRACE_NOTE_INDICATOR`, `ACCIACCATURA_INDICATOR`
      in `bana_symbols.py` verified against BANA section 15
- [x] Tokenizer classifies ornament cells as `SymbolCategory.ORNAMENT`
- [x] Parser attaches ornaments and grace notes to the correct notes
- [x] Grace notes are excluded from `_validate_measure_beat_count()`
- [x] All unit tests pass
- [x] `pytest tests/` passes with no regressions

**Senior note:** Grace notes do not count toward the measure beat total --
skip them in `_validate_measure_beat_count()`.  A grace note without a
following real note (e.g. at end of input) should emit a parser warning,
not an exception.  In BANA the grace note indicator is followed immediately
by the grace note cell (a real note cell, usually 8th-note class), then the
main note; the parser must consume the grace note cell specially, not treat
it as a `_PendingNote` in the measure.

---

### [x] S4-5: Implement word sign / text marking parsing

**Why:** Tempo markings and expression directions (Allegro, dolce, con moto)
appear at the start of pieces and throughout a score.  They are encoded in
BANA braille music using a word sign that switches context to literary braille.
Without this, the parser silently drops these markings and the LilyPond output
contains no tempo information -- important for both human performers and MIDI.

**Steps:**
1. Create `src/dottednotes/models/text_marking.py`:
   ```python
   from dataclasses import dataclass
   from enum import Enum, auto

   TEMPO_TERMS = frozenset({
       'Allegro', 'Andante', 'Adagio', 'Presto', 'Moderato',
       'Largo', 'Vivace', 'Lento', 'Prestissimo', 'Allegretto',
   })

   class TextMarkingType(Enum):
       TEMPO = auto()       # e.g. Allegro, Andante
       EXPRESSION = auto()  # e.g. dolce, espressivo, con moto
       REHEARSAL = auto()   # rehearsal letters or numbers
       GENERAL = auto()     # any other in-score text

   @dataclass
   class TextMarking:
       text: str
       type: TextMarkingType = TextMarkingType.GENERAL

       def to_lilypond(self) -> str:
           if self.type == TextMarkingType.TEMPO:
               return f'\\tempo "{self.text}"'
           return f'\\mark \\markup {{ "{self.text}" }}'
   ```
   Extend `TEMPO_TERMS` with any Italian terms the developer commonly uses.
2. Add `SymbolCategory.WORD_SIGN` to the enum in `bana_symbols.py`.
3. Add the word sign cell to `bana_symbols.py`:
   ```python
   WORD_SIGN: str = '...'          # verify from BANA word sign chapter
   WORD_SIGN_END: str | None = ... # None if words end at blank cell
   ```
   **Verify against the BANA manual before entering.**  The word sign in
   music context signals that what follows should be read as literary braille
   letters until a blank cell or line break.  Check both the 1997 and 2015
   BANA revisions and note which the developer's files use.
4. In `BrailleTokenizer`, implement a WORD_MODE state machine:
   - Entering WORD_MODE: tokenizer sees the WORD_SIGN cell
   - In WORD_MODE: each cell is decoded as a literary braille letter
     (reverse the `ASCII_TO_DOTS` mapping in `input_pipeline.py`)
     and appended to a text buffer
   - Exiting WORD_MODE: a blank cell (U+2800) or newline returns to
     MUSIC_MODE and emits the accumulated text as a single WORD_SIGN token
   Do not use lookahead for this -- use an explicit state variable.
5. Add fields to `Measure` and `Staff`:
   ```python
   # Measure
   text_markings: list[TextMarking] = field(default_factory=list)

   # Staff
   tempo: TextMarking | None = None
   ```
6. In `BrailleParser.parse()`, when a `WORD_SIGN` token is encountered:
   - Classify the text against `TEMPO_TERMS`; create a `TextMarking`.
   - If it appears before the first measure, assign to `staff.tempo`.
   - Otherwise, append to the current measure's `text_markings` list.
7. Update `Staff.to_lilypond()` to emit `\tempo` before the first measure
   when `staff.tempo` is set.  Update `Measure.to_lilypond()` to prepend
   expression markings.
8. Write unit tests:
   ```python
   def test_word_sign_produces_text_token():
       tokens = BrailleTokenizer().tokenize(WORD_SIGN + BANA_LETTERS_ALLEGRO)
       assert tokens[0].category == SymbolCategory.WORD_SIGN

   def test_allegro_classified_as_tempo():
       score = parse_text(WORD_SIGN_ALLEGRO + '⠐⠹⠀')
       assert score.staves[0].tempo.type == TextMarkingType.TEMPO
       assert score.staves[0].tempo.text == 'Allegro'

   def test_tempo_renders_in_lilypond():
       score = parse_text(WORD_SIGN_ALLEGRO + '⠐⠹⠀')
       assert r'\tempo "Allegro"' in score.to_lilypond()

   def test_expression_renders_as_mark():
       # "dolce" is EXPRESSION, not TEMPO
       score = parse_text(WORD_SIGN_DOLCE + '⠐⠹⠀')
       assert r'\mark \markup { "dolce" }' in score.to_lilypond()
   ```

**Definition of Done:**
- [x] `TextMarking` class with `TextMarkingType` enum exists in
      `models/text_marking.py`
- [x] `WORD_SIGN` cell verified against BANA manual and added to
      `bana_symbols.py`
- [x] Tokenizer state machine correctly enters and exits WORD_MODE
- [x] `Measure` has `text_markings: list[TextMarking]` field
- [x] `Staff` has `tempo: TextMarking | None` field
- [x] Common Italian tempo terms are classified as `TextMarkingType.TEMPO`
- [x] `Staff.to_lilypond()` emits `\tempo` before the first measure
- [x] `Measure.to_lilypond()` prepends expression markings
- [x] All unit tests pass
- [x] `pytest tests/` passes with no regressions

**Senior note:** The WORD_MODE state switch is the key implementation
challenge.  The same dot patterns that represent notes in music context
represent letters in literary context -- the tokenizer must not process
any cell in WORD_MODE as a note.  The TEMPO_TERMS set is a curated list,
not an exhaustive one; anything not in the set falls back to EXPRESSION.
Metronome marks (e.g. `\tempo 4 = 120`) are Sprint 6 work; for now a
quoted string is sufficient.

---

### [x] S4-6: Integration test — sprint_4_melody with all Sprint 4 elements

**Why:** Sprints 1–3 were each verified end-to-end with fixture files.
Sprint 4 introduces five new categories of musical information.
This ticket verifies all five work together in the full pipeline using
`sprint_4_melody.brf`, a piece composed by the developer to exercise
every Sprint 4 feature in a single file.

**Fixture characteristics (developer-verified):**
- 25 measures, G major (1 sharp), 4/4 time
- Header tempo: "Allegro moderato" — capital indicator (⠠) + literary
  period (⠲) encoding
- Mid-piece expression: "dolce" at measure 17 — word sign (⠜) +
  end word sign (⠄) encoding
- Dynamics: forte (measure 1), piano (measure 17)
- Articulations: accent (measures 1, 3–8), staccato (measures 9, 11,
  13–16), tenuto (measures 4, 23)
- Ornaments: trill (measure 15), prall / upper mordent (measure 21),
  mordent / lower mordent (measure 21), upmordent / extended upper
  mordent (measure 22), downmordent / extended lower mordent (measure 22)
- Short grace notes: paired two-note grace groups in measures 9 and 11
- Slurs: measures 10, 12
- Tie: measure 24
- Reference output: `tests/fixtures/sprint_4_melody.ly`

**Steps:**
1. Write a smoke test:
   ```python
   def test_sprint4_melody_parses_without_error():
       text = BRLInputPipeline().load(FIXTURES / 'sprint_4_melody.brf')
       score = BrailleParser(tokens=BrailleTokenizer().tokenize(text)).parse()
       assert len(score.staves) == 1
       assert len(score.staves[0].measures) == 25
   ```
2. Add header/key/time assertions:
   ```python
   def test_sprint4_melody_header_tempo():
       assert staff.tempo.text == 'Allegro moderato'
       assert staff.tempo.type == TextMarkingType.TEMPO

   def test_sprint4_melody_key_and_time():
       assert staff.key_signature.sharps_or_flats == 1  # G major
       assert staff.time_signature.numerator == 4
       assert staff.time_signature.denominator == 4
   ```
3. Add one assertion per Sprint 4 category:
   ```python
   def test_sprint4_melody_contains_articulations():
       assert any(n.articulations for n in all_notes)

   def test_sprint4_melody_contains_dynamics():
       assert any(n.dynamics for n in all_notes)

   def test_sprint4_melody_contains_ornament():
       assert any(n.ornaments for n in all_notes)

   def test_sprint4_melody_contains_grace_note():
       assert any(n.grace_note is not None for n in all_notes)

   def test_sprint4_melody_contains_slur():
       assert any(n.slur_begin or n.slur_end for n in all_notes)

   def test_sprint4_melody_contains_tie():
       assert any(n.tied for n in all_notes)

   def test_sprint4_melody_mid_piece_dolce():
       all_markings = [tm for m in staff.measures for tm in m.text_markings]
       assert any(tm.text == 'dolce' for tm in all_markings)
   ```
4. Add a LilyPond render test:
   ```python
   def test_sprint4_melody_renders_to_lilypond():
       ly = score.to_lilypond()
       assert r'\version' in ly
       assert r'\relative' in ly
       assert r'\tempo "Allegro moderato"' in ly
       assert r'\key g \major' in ly
       assert r'\time 4/4' in ly
       assert '->' in ly      # accent
       assert '-.' in ly      # staccato
       assert '--' in ly      # tenuto
       assert r'\f' in ly     # forte
       assert r'\p' in ly     # piano
       assert r'\trill' in ly
   ```
5. Add a compile test (skip if lilypond not installed):
   ```python
   def test_sprint4_melody_lilypond_compiles():
       import shutil, subprocess
       if not shutil.which('lilypond'):
           pytest.skip('lilypond not installed')
       result = subprocess.run(
           ['lilypond', '--silent', '-'],
           input=score.to_lilypond(),
           capture_output=True, text=True
       )
       assert result.returncode == 0, f"LilyPond failed:\n{result.stderr}"
   ```

**Definition of Done:**
- [x] `test_sprint4_melody_parses_without_error` passes (25 measures)
- [x] Key signature: 1 sharp; time signature: 4/4; tempo: "Allegro moderato"
- [x] All 7 Sprint 4 category assertions pass
- [x] Mid-piece "dolce" text marking verified
- [x] `test_sprint4_melody_renders_to_lilypond` passes
- [x] Compile test passes if lilypond is installed
- [x] No regressions in any earlier sprint tests
- [x] `pytest tests/` passes clean

**Senior note:** The file is ASCII braille (.brf), so `BRLInputPipeline.load()`
converts it to Unicode before tokenizing — this is already implemented.
Use `sprint_4_melody.ly` as ground truth when a test fails: compare the
parser's output against the reference to identify which feature needs attention.

---

# Sprint 5: Chords and Multiple Voices

Estimated time: 1.5–2 weeks.

### [ ] S5-1: Implement Chord class and interval parsing

**Why:** BANA music braille encodes chords as a written note followed by one or
more interval cells.  Each interval cell specifies a diatonic distance from the
written note; for treble/alto clef the interval descends, for bass/tenor it
ascends.  This ticket adds the `Chord` model, the interval symbol table, the
tokenizer classification, and the parser logic to build `Chord` objects from
braille input.

**Verified BANA interval symbols (developer-confirmed dot patterns):**

| Interval | Dot pattern | Unicode | Notes |
|----------|-------------|---------|-------|
| 2nd      | 3,4         | ⠌       |       |
| 3rd      | 3,4,6       | ⠬       |       |
| 4th      | 3,4,5,6     | ⠼       | Same cell as NUMBER_SIGN; context-disambiguated |
| 5th      | 3,5         | ⠔       |       |
| 6th      | 3,5,6       | ⠴       |       |
| 7th      | 2,5         | ⠒       |       |
| 8th      | 3,6         | ⠤       | Same first cell as swell (⠤⠄); 2-cell check takes priority |

**Direction rule:** treble/alto clef → intervals descend from the written note.
Bass/tenor clef → intervals ascend from the written note.

**Pitch calculation:** `raw = written_index ± (interval_number - 1)` (subtract
for descending, add for ascending), using 0-based index into `['C','D','E','F',
'G','A','B']`.  `note_name = diatonic_notes[raw % 7]`,
`octave = written_octave + (raw // 7)` using Python floor division so negative
raws wrap correctly.

**Accidentals on interval notes:** An explicit accidental cell before the
interval sign overrides the key signature for that interval note only.  If no
explicit accidental is present, the key signature accidental is inferred.
Sharps order: F C G D A E B.  Flats order: B E A D G C F.

**Octave marks on interval notes:** An explicit octave mark before an interval
sign overrides the calculated octave for that interval note only.

**Interval doubling (carry mode, BANA 9.3):**
Intervals always come AFTER the note they modify.  The sequence is:
```
note1  [int_sign]         → note1 gets interval from this first sign
       [int_sign]         → same sign again (no note between) activates carry
note2                     → carry auto-applies interval
note3                     → carry auto-applies interval
note4  [int_sign]         → carry auto-applies interval; this single sign is the
                            terminator — it just clears carry (BANA 9.3.2)
note5                     → no interval
```
Minimum meaningful test sequence: note + int + int, note, note, note + int
(four notes receive the interval, terminator after the fourth).

**Multiple doublings terminated together (BANA 9.3.3):** When two or more
intervals are simultaneously doubled (each doubled separately on the same
sequence of notes), terminating any one carry clears all active carries at once.

**Steps:**
1. Add `INTERVAL_CELLS: dict[str, int]` to `bana_symbols.py` using the
   verified cells in the table above.
2. Update `BrailleTokenizer`:
   - In the `⠼` (NUMBER_SIGN) handler, emit `SymbolCategory.INTERVAL` when
     `at_measure_start` is False (mid-measure = 4th interval, not key/time sig).
   - In `_classify()`, add a check: if `char in INTERVAL_CELLS and char != '⠼'`
     → return `SymbolCategory.INTERVAL`.  The `⠼` exclusion is because its
     classification is already handled by the NUMBER_SIGN block above.
3. Add `Chord` dataclass in `src/dottednotes/models/chord.py`:
   - `notes: list[Note]` (written note at index 0; interval notes follow)
   - `duration` property returning `notes[0].duration`
   - `to_lilypond()` for absolute mode
   - `to_relative_lilypond(prev_midi)` → `(str, int)` for relative mode;
     each note inside `<...>` is relative to the previous chord note;
     after the chord, `prev_midi` advances to the first note's MIDI pitch
     (LilyPond rule).
   - `NOTE_PITCH_ONLY(note)` helper: pitch name + accidental only (no octave,
     no duration).
   - `_chord_extras(written)` helper: collects articulations, ornaments, tie,
     dynamics, slur marks from the written note.
4. Add `Note._relative_pitch_str(prev_midi) → (str, int)` to `note.py` for use
   inside chord `<...>` blocks (same nearest-neighbour logic as
   `to_relative_lilypond` but without duration or extras).
5. Update `models/__init__.py` to export `Chord`.
6. Update `models/measure.py`: add `NoteOrChord = Union[Note, Chord]`;
   change `notes: list[Note]` → `notes: list[NoteOrChord]` and likewise
   `add_note`.
7. Add module-level helpers to `braille_parser.py`:
   - `_DIATONIC_NOTES`, `_SHARP_ORDER`, `_FLAT_ORDER` constants.
   - `_key_sig_accidental(note_name, sharps_or_flats) → AccidentalType | None`
   - `_interval_pitch(written_name, written_octave, interval_number,
     descending) → (str, int)`
8. Add interval carry state to `BrailleParser._reset_state()`:
   ```python
   self._active_intervals: dict[int, AccidentalType | None] = {}
   self._last_interval_seen: int | None = None
   self._interval_octave_override: int | None = None
   self._octave_mark_pending: bool = False
   ```
9. Add `interval_notes: list[tuple[str, int, Accidental | None]]` to
   `_PendingNote`.
10. Update `_handle_octave_mark` to set `_octave_mark_pending = True`.
11. Update `_buffer_note` to:
    - Clear `_octave_mark_pending` (octave mark consumed by the note).
    - Apply all active carry intervals via `_apply_interval` for each key in
      `sorted(self._active_intervals)`.
    - Reset `_last_interval_seen = None`.
12. Add `_handle_interval(token, pending)` with three cases:
    - **Case 1** (carry active, sign after note = terminator): clear
      `_active_intervals` and `_last_interval_seen`.  Do NOT re-apply the
      interval — the preceding note already received it from carry.
    - **Case 2** (same sign seen twice, no note between = doubling): activate
      carry by adding `interval_number` to `_active_intervals`; reset
      `_last_interval_seen`.
    - **Case 3** (first occurrence): set `_last_interval_seen`; if a note is
      pending, call `_apply_interval` immediately.
13. Add `_apply_interval(interval_number, pnote)`:
    - Compute pitch via `_interval_pitch`.
    - Override octave if `_interval_octave_override` is set (then clear it).
    - Use `_pending_accidental` if set (then clear it), else infer from key
      signature via `_key_sig_accidental`.
    - Append `(iname, ioctave, iacc)` to `pnote.interval_notes`.
14. Update `_finalize_measure`: if `pnote.interval_notes` is non-empty, build
    interval `Note` objects and wrap the written note plus interval notes in a
    `Chord`; otherwise produce a plain `Note` as before.
15. Update bar line handling to call `_active_intervals.clear()` and reset
    `_last_interval_seen` at double bar and section end.
16. Update `_validate_measure_beat_count` to use `item.duration` (works for
    both `Note` and `Chord`).
17. Write unit tests covering:
    - `INTERVAL_CELLS` contains all 7 entries.
    - Tokenizer classifies all 6 unambiguous interval cells as `INTERVAL`.
    - `⠼` mid-measure → `INTERVAL`; `⠼` at measure start → `KEY_SIGNATURE` or
      `TIME_SIGNATURE` as before.
    - `⠤⠄` (swell, 2-cell) still classified as `ARTICULATION`, not `INTERVAL`.
    - Single interval creates a `Chord` (treble descending, bass ascending).
    - Multi-interval creates a chord with the correct number of notes.
    - Explicit accidental before interval overrides key signature.
    - Key signature accidental is inferred when no explicit accidental.
    - Interval doubling carry mode: 4-note sequence (note + int + int, 2 carry
      notes, terminator note + int); all four notes become `Chord` objects.
    - Terminator note has exactly one interval note (not duplicated).
    - BANA 9.3.3: terminating one doubled interval clears all active carries.
    - Carry terminates at final double bar.
    - `Chord.to_relative_lilypond()` produces correct LilyPond syntax.
    - Chord duration matches the written note's duration.

**Definition of Done:**
- [ ] `INTERVAL_CELLS` in `bana_symbols.py` contains all 7 verified interval cells
- [ ] Tokenizer classifies all 6 unambiguous interval cells as `SymbolCategory.INTERVAL`
- [ ] `⠼` mid-measure is classified as `INTERVAL`; at measure boundary it still routes to key/time sig handling
- [ ] `⠤⠄` (swell) is still classified as `ARTICULATION`, not `INTERVAL`
- [ ] `Chord` class exists in `models/chord.py` with `to_lilypond()` and `to_relative_lilypond()`
- [ ] Single interval sign after a note produces a `Chord` with the correct interval note pitch
- [ ] Treble/alto clef intervals descend; bass/tenor clef intervals ascend
- [ ] Key signature accidentals are correctly inferred for interval notes
- [ ] Explicit accidental before an interval sign overrides the key signature
- [ ] Interval doubling carry mode works for a 4-note series
- [ ] Terminator sign clears carry without duplicating the interval on the last note
- [ ] BANA 9.3.3: terminating one doubled interval terminates all simultaneously active doublings
- [ ] Active doublings clear at a double bar or section end
- [ ] `Measure.notes` accepts `NoteOrChord`; `to_lilypond()` delegates to `Chord.to_relative_lilypond()` correctly
- [ ] All unit tests pass
- [ ] `pytest tests/` passes with no regressions

---

### [x] S5-2: Implement in-accord parsing

**Why:** When a measure contains two or more independent rhythmic lines that
cannot be expressed as interval chords (different rhythms, different rests,
etc.), BANA notation uses the "in-accord" device: the lines are written in
succession, separated by an in-accord sign, all within the same measure.
This ticket adds the sign table, tokenizer classification, parser logic, the
`InAccord` domain model, and LilyPond rendering via `<< { voice1 } \\ { voice2 } >>`.

**Source:** BANA Music Braille Code 2015, Chapter 11 (pages 87–91), Table 11.

**Verified BANA in-accord symbols** (dot patterns derived from Table 11 ASCII
representations via `ASCII_TO_DOTS` in `input_pipeline.py` — developer to
confirm before implementation):

| Sign | ASCII | First cell | Second cell | Decoded Unicode | Notes |
|------|-------|-----------|-------------|----------------|-------|
| Full-measure in-accord | `<>` | `<` = dots 1,2,6 | `>` = dots 3,4,5 | `⠣⠜` | U+2823 U+281C |
| Part-measure in-accord | `"1` | `"` = dot 5 | `1` = dot 2 | `⠐⠂` | U+2810 U+2802 |
| Measure division | `.k` | `.` = dots 4,6 | `k` = dots 1,3 | `⠨⠅` | U+2828 U+2805 |

**Tokenizer disambiguation:** All three signs share their first cell with signs
that have other meanings in isolation:
- `⠣` (dots 1,2,6) is the BAR_LINE_PREFIX; `⠣⠜` must be recognized as
  in-accord before the bar-line checks fall through to flat accidental.
- `⠐` (dot 5) is the octave-4 mark; `⠐⠂` must be recognized before
  `_classify()` emits OCTAVE_MARK.  Since `⠂` (dot 2) is never a valid
  note/rest/ornament cell, this 2-cell sequence is unambiguous.
- `⠨` (dots 4,6) is the octave-5 mark; `⠨⠅` must be recognized before
  `_classify()`.  Since `⠅` (dots 1,3) ≠ `⠦` (dots 2,3,6, the articulation
  second cell), there is no conflict with `⠨⠦` (accent articulation).

**BANA 11.1 rules:**

*Full-measure in-accord (11.1.1):* Both sides of `⠣⠜` must contain exactly a
full measure of note values.  The voices are written treble-clef top-to-bottom
(highest voice first, then lower) and bass-clef bottom-to-top (lowest first).
An octave mark is required for the first note after the in-accord sign and
also at the start of the measure following an in-accord measure.

*Part-measure in-accord (11.1.2):* The measure is divided into sections by
`⠨⠅` (measure-division sign).  Within each section the two parts are joined
by `⠐⠂`.  The music on each side of `⠐⠂` must contain the same total note
value.  Reconstructing the voices means: voice 1 = all section-A parts + all
section-B parts etc.

*Nested in-accords (11.1.3):* A part-measure in-accord may appear within a
full-measure in-accord.  Deferred to a later sprint; not in scope for S5-2.

**BANA 11.2 — Restating accidentals:** Accidentals written before an
in-accord sign or measure-division sign do not carry over to notes written
after the sign.  The parser must reset any in-measure accidental state at
each in-accord boundary.

**Domain model — `InAccord`:**

```python
@dataclass
class InAccord:
    parts: list[list[NoteOrChord]]   # one list per voice, in order written
    in_accord_type: str = 'full'     # 'full' or 'part'

    def to_relative_lilypond(self, prev_midi: int) -> tuple[str, int]:
        # Each voice renders relative to the same prev_midi reference
        # (LilyPond resets context for each voice inside << >>).
        # After >>, the reference is the last note of parts[0] (primary voice).
        ...
```

`Measure.notes` will be extended to `list[NoteOrChord | InAccord]` via a
wider `MeasureItem` union type.  `Measure.to_lilypond()` already dispatches
via `hasattr(item, 'to_relative_lilypond')`, so `InAccord` fits naturally.

**LilyPond mapping:**

```lilypond
<< { c'4 d' e' f' } \\ { g4 e f d } >> |
```

For three or more voices, additional `\\ { voice_n }` blocks are appended.

**Steps:**
1. Add `IN_ACCORD_CELLS: dict[str, str]` to `bana_symbols.py` using the
   three verified signs: `{'⠣⠜': 'full_measure', '⠐⠂': 'part_measure',
   '⠨⠅': 'measure_division'}`.  Include dot-pattern comments.
2. Update `BrailleTokenizer`:
   - Inside the `⠣` (BAR_LINE_PREFIX) handler block, after the bar-line
     sequence checks but before the key-signature/flat-accidental checks,
     add: if `two == '⠣⠜'` → emit `SymbolCategory.IN_ACCORD`, advance 2,
     continue.
   - In the main multi-cell section (after the slur check, before
     `_classify()`), add: if `two in IN_ACCORD_CELLS` → emit
     `SymbolCategory.IN_ACCORD`, advance 2, continue.
   - Do NOT change `at_measure_start` for in-accord tokens; they are
     mid-measure separators, not bar lines or notes.
3. Create `src/dottednotes/models/in_accord.py` with the `InAccord` dataclass:
   - `parts: list[list[NoteOrChord]]`
   - `in_accord_type: str = 'full'`
   - `to_relative_lilypond(prev_midi) → (str, int)`:
     render each voice as `{ note1 note2 ... }` relative to `prev_midi`;
     return `<< {v1} \\ {v2} ... >>` and the MIDI pitch of the last
     note/chord in `parts[0]`.
4. Update `models/__init__.py` to export `InAccord`.
5. Update `models/measure.py`: change `NoteOrChord` to `MeasureItem` (a
   wider union adding `InAccord`), or add `InAccord` to the existing union.
   Keep `NoteOrChord` as an alias for backward compatibility.
6. Add in-accord parser state to `BrailleParser._reset_state()`:
   ```python
   self._in_accord_parts: list[list[_PendingNote]] = []
   self._in_accord_type: str = 'full'
   ```
7. Add `_finalize_voice_part(pending: list[_PendingNote]) → list[NoteOrChord]`
   to `BrailleParser`.  This is a refactor of the note-building loop in
   `_finalize_measure`, extracted as a reusable helper.
8. Add `_handle_in_accord(token)` to `BrailleParser`:
   - Snapshot `pending` → call `_finalize_voice_part(pending)` → append to
     `_in_accord_parts`.
   - Clear `pending` for the next voice.
   - Reset `_pending_accidental = None` (BANA 11.2 accidental reset).
   - Set `_in_accord_type` based on `IN_ACCORD_CELLS[token.character]`.
9. Update `_finalize_measure` to check `_in_accord_parts`:
   - If non-empty: add the final `pending` as the last voice, build
     `InAccord(parts=_in_accord_parts, in_accord_type=...)`, add it to the
     measure via `measure.add_note(in_accord)`, clear `_in_accord_parts`.
   - Otherwise: existing single-voice logic unchanged.
10. Route `SymbolCategory.IN_ACCORD` tokens to `_handle_in_accord` in the
    main parse loop.
11. Write unit tests covering:
    - `IN_ACCORD_CELLS` contains all three signs.
    - Tokenizer emits `IN_ACCORD` for each of the three signs.
    - `⠣⠜` is not classified as flat accidental + clef prefix.
    - `⠐⠂` is not classified as octave-4 mark + unknown.
    - `⠨⠅` is not classified as octave-5 mark + unknown.
    - Parser: full-measure in-accord produces one `InAccord` in the measure
      with the correct number of voice parts.
    - Each voice part contains the correct notes in the correct order.
    - Accidental from voice 1 does not carry into voice 2 (BANA 11.2).
    - `InAccord.to_relative_lilypond()` produces `<< { ... } \\ { ... } >>`.
    - Two voices correctly handled for treble clef (highest voice first).
    - `pytest tests/` passes with no regressions.

**Scope for S5-2:** Full-measure in-accord only (11.1.1).  Part-measure
in-accord (11.1.2) and nested in-accords (11.1.3) are deferred to S5-3.
The tokenizer recognizes all three sign types, but the parser only needs to
handle `'full_measure'` for now; `'part_measure'` and `'measure_division'`
can raise a `NotImplementedError` or a `warnings.warn` with a "not yet
supported" message.

**Definition of Done:**
- [x] `IN_ACCORD_CELLS` in `bana_symbols.py` contains all three verified sign sequences
- [x] Tokenizer emits `SymbolCategory.IN_ACCORD` for all three signs without false-positives on `⠣⠜` / `⠐⠂` / `⠨⠅` in isolation
- [x] `InAccord` class exists in `models/in_accord.py` with `to_relative_lilypond()`
- [x] `InAccord.to_relative_lilypond()` produces `<< { voice1 } \\ { voice2 } >>` with correct relative-mode pitches
- [x] Parser correctly splits a full-measure in-accord measure into two (or more) voice parts
- [x] BANA 11.2: accidentals do not carry across the in-accord sign boundary
- [x] `Measure.notes` accepts `InAccord` items; `Measure.to_lilypond()` renders them correctly
- [x] All unit tests pass
- [x] `pytest tests/` passes with no regressions

---

### [x] S5-3: Implement part-measure in-accord parsing (BANA 11.1.2)

**Why:** Full-measure in-accord (S5-2) handles the case where both voices
span the entire measure. Part-measure in-accord handles the more common
case where only part of a measure has multiple voices — for example, two
voices on beats 1–2 and a single melody on beats 3–4. Without this, any
.brf file that uses `⠐⠂` or `⠨⠅` produces a warning and incorrect output.

**BANA rules:**
- `⠐⠂` (part-measure in-accord sign, dot 5 + dot 2): joins two voices
  covering the same beats within one temporal section.
- `⠨⠅` (measure-division sign, dots 4,6 + dots 1,3): splits the measure
  into temporal sections. The sections concatenate to fill the measure.
- BANA 11.2: accidentals do not carry across either sign (same rule as
  full-measure in-accord).
- Out of scope: nested in-accords (`⠐⠂` within a `⠣⠜` measure) — deferred
  to a later sprint.

**Example structure** (4/4 time, first half two-voice, second half
single voice):

```
[half_C] ⠐⠂ [quarter_E quarter_F] ⠨⠅ [quarter_G quarter_A] | barline
```

Expected LilyPond:
```lilypond
<< { c2 } \\ { e4 f4 } >> g4 a4
```

**Steps:**

1. Add new parser state in `BrailleParser._reset_state()`:
   `_in_accord_sections: list[list[list]]` and
   `_current_section_parts: list[list]`. Keep the existing
   `_in_accord_parts` and `_in_accord_type` for the full-measure path.
2. Update `_handle_in_accord()` to branch on `in_accord_type`:
   `'full_measure'` (⠣⠜) unchanged; `'part_measure'` (⠐⠂) snapshots
   pending into the current section; `'measure_division'` (⠨⠅) closes
   the current section and starts a new one. Clear `_pending_accidental`
   at all three boundaries (BANA 11.2).
3. Update `_finalize_measure()` to close the final section and, for each
   section, add its notes directly to the measure if it has one voice,
   or wrap it in an `InAccord(in_accord_type='part_measure')` if it has
   two or more.
4. Update `_validate_measure_beat_count()` so each in-accord's beat
   contribution uses the longest voice, not just the first.
5. `InAccord.to_relative_lilypond()` needed no change — the existing
   `<< {v1} \\ {v2} >>` rendering works for part-measure sections too.
6. Write unit tests covering: two-voice first section + single-voice
   second section; accidental non-carry at both the part-measure sign
   and the measure-division sign; single-voice sections rendered as
   flat notes (no `InAccord` wrapper); correct LilyPond output.
7. Run `pytest tests/` before and after; verify no regressions.

**Definition of Done:**
- [x] `_in_accord_sections` and `_current_section_parts` state variables
      exist in `_reset_state()`
- [x] `_handle_in_accord()` handles all three sign types without warnings
      for part_measure and measure_division
- [x] `_finalize_measure()` creates a mix of `InAccord(part_measure)` items
      and direct Notes when sections are present
- [x] Single-voice sections add notes directly (no InAccord wrapper)
- [x] `_validate_measure_beat_count()` counts beats correctly for
      part-measure measures
- [x] BANA 11.2 accidental non-carry holds at all in-accord boundaries
- [x] New unit tests pass
- [x] `pytest tests/` passes with no regressions

**Senior note:** The part-measure path must not interfere with the
full-measure path — they are mutually exclusive per measure. Full-measure
in-accord never has `⠨⠅`; part-measure in-accord never has `⠣⠜`. The two
sets of state variables are separate, and `_finalize_measure()` checks
them in order.

---

###[ ] S5-4: Implement Staff class with voice assembly
### [ ] S5-5: Integration test: two-voice piano piece

*Detailed steps for S5-4 and S5-5 to be written when S5-3 is complete.*

---

# Sprint 5b: Orchestral Score Support

Estimated time: 1.5–2 weeks.

### [ ] S5b-1: Implement instrument abbreviation lookup table
### [ ] S5b-2: Implement MeasureRepeat class with expand() method
### [ ] S5b-3: Implement interval shorthand detection and voice reconstruction
### [ ] S5b-4: Implement staff grouping and bracket markers
### [ ] S5b-5: Implement tacet and multi-measure rest parsing
### [ ] S5b-6: Implement transposing instrument table and concert pitch flag
### [ ] S5b-7: Implement OrchestraScore class
### [ ] S5b-8: Integration test using Fengyang orchestral score

*Detailed steps to be written when Sprint 5 is complete.*

---

# Sprint 6: Ornaments and Advanced Idioms

Estimated time: 1–1.5 weeks.

### [ ] S6-1: Implement Ornament class (trill, mordent, turn, tremolo)
### [ ] S6-2: Implement fingering notation
### [ ] S6-3: Implement repeat signs
### [ ] S6-4: Implement tempo markings
### [ ] S6-5: Implement grace notes and acciaccatura
### [ ] S6-6: Integration test suite covering all implemented idioms

*Detailed steps to be written when Sprint 5b is complete.*

---

# Sprint 7: Score Assembly and Full Pipeline

Estimated time: 4–5 days.

### [ ] S7-1: Implement Score and Staff to_lilypond() with full header block
### [ ] S7-2: Implement CLI with convert command
### [ ] S7-3: Add error handling and meaningful plain-text error messages
### [ ] S7-4: Add --verbose flag
### [ ] S7-5: End-to-end test: .brf in, compiled PDF out
### [ ] S7-6: Write user-facing README with installation and usage

*Detailed steps to be written when Sprint 6 is complete.*

---
**Sprint 7b: LilyPond Formatting Library**
- [ ] S7b-1: Download and analyze 50 representative Mutopia scores programmatically — extract common header patterns, paper settings, staff spacing values, and rehearsal mark styles
- [ ] S7b-2: Implement `LilyPondFormatter` class with evidence-based defaults derived from Mutopia analysis
- [ ] S7b-3: Implement instrumentation detection and template selection
- [ ] S7b-4: Curate 4 formatting templates (solo piano, art song, chamber, orchestral) based on high-quality Mutopia examples
- [ ] S7b-5: Implement page layout defaults (paper size A4/Letter, margins, system spacing) for each template
- [ ] S7b-6: Implement `\header` block generation with title, composer, copyright, and Mutopia-style tagline
- [ ] S7b-7: Integration test: generate a formatted score and verify it compiles to a professional-looking PDF
- [ ] S7b-8: Document all formatting rules in `docs/lilypond_conventions.md` with source citations

---

# Sprint 8: Accessibility and Polish

Estimated time: 3–4 days.

### [ ] S8-1: Audit all CLI output for screen reader friendliness
### [ ] S8-2: Write developer documentation
### [ ] S8-3: Add CONTRIBUTING.md with blind-contributor guidance
### [ ] S8-4: Submit to accessibility and music technology communities

*Detailed steps to be written when Sprint 7 is complete.*

---

# Sprint 9: Reverse Direction — LilyPond to BRF

Estimated time: 1.5–2 weeks.

### [ ] S9-1: Add to_braille() method to all domain model classes
### [ ] S9-2: Implement BrailleRenderer
### [ ] S9-3: Implement restricted LilyPond parser for tool-generated output
### [ ] S9-4: Implement BRF file writer with BANA line length and pagination
### [ ] S9-5: Round-trip integration test

*Detailed steps to be written when Sprint 8 is complete.*

---
**Sprint 9c: BANA Formatting Rule Library**
- [ ] S9c-1: Compile complete list of BANA mandatory formatting rules from the Technical Manual
- [ ] S9c-2: Compile complete list of BANA optional shorthand conventions
- [ ] S9c-3: Implement each rule as a discrete, testable method on `BANAValidator`
- [ ] S9c-4: Document every rule in `docs/bana_reference.md` with manual citation and example
- [ ] S9c-5: Build a rule registry so rules can be enabled/disabled individually — useful for different BANA editions (UK vs US braille music conventions differ slightly)


---

# Sprint 10: MusicXML Bridge

Estimated time: 1–1.5 weeks.

### [ ] S10-1: Integrate music21 for MusicXML parsing
### [ ] S10-2: Implement MusicXML to Internal Model translation
### [ ] S10-3: Implement Internal Model to MusicXML translation
### [ ] S10-4: Integration test: import MuseScore MusicXML, export as BRF
### [ ] S10-5: Integration test: import BRF, export as MusicXML for MuseScore

*Detailed steps to be written when Sprint 9 is complete.*
**Sprint 9b: BANA Validator (between Sprint 9 and Sprint 10)**
- [ ] S9b-1: Implement `BANAValidator` class with rule registry
- [ ] S9b-2: Implement articulation series shorthand rule (your specific case)
- [ ] S9b-3: Implement octave mark validation and auto-insertion
- [ ] S9b-4: Implement line length checking and automatic line breaking
- [ ] S9b-5: Implement `Correction` dataclass and `ValidationResult`
- [ ] S9b-6: Add `--report` flag to CLI that outputs plain text correction list
- [ ] S9b-7: Add validation step to web UI with corrections displayed after upload
- [ ] S9b-8: Integration test: input your Fengyang score with known rule violations, verify corrections match expected BANA output
- [ ] S9b-9: Document all implemented BANA rules in `docs/bana_reference.md`
- [ ] S9b-10: Implement `BrailleRenderer` class with `compression_level` parameter
- [ ] S9b-11: Implement measure repeat detection using `musical_equals()`
- [ ] S9b-12: Implement section repeat detection using sliding window comparison
- [ ] S9b-13: Implement articulation series shorthand detection at voice level
- [ ] S9b-14: Integration test: expanded Internal Model → compressed braille → verify against hand-formatted BANA output
- [ ] S9b-15: Add `musical_equals()` to Note, Rest, Chord, and Measure classes
- [ ] S9b-16: Implement `compression_level` parameter with full, minimal, and none modes


**Sprint 11: Web Interface (2–3 weeks after Sprint 7)**
- [ ] S11-1: Add FastAPI to project dependencies and create `web.py`
- [ ] S11-2: Implement file upload endpoint with DottedNotes conversion
- [ ] S11-3: Implement LilyPond subprocess call with timeout and error handling
- [ ] S11-4: Create accessible HTML frontend with ARIA live regions
- [ ] S11-5: Write Dockerfile with LilyPond pre-installed
- [ ] S11-6: Deploy to Render or Fly.io and verify end-to-end
- [ ] S11-7: Test entire UI with VoiceOver before launch
- [ ] S11-8: Share with braille music community for feedback
**Sprint 11b: Interactive Web Editor (after Sprint 11)**
- [ ] S11b-1: Implement session management with UUID-based temp workspaces
- [ ] S11b-2: Implement incremental measure re-parsing with MeasureContext
- [ ] S11b-3: Implement Score.replace_measure() with octave cache invalidation
- [ ] S11b-4: Build accessible measure-by-measure HTML editor with ARIA labels
- [ ] S11b-5: Implement in-browser MIDI playback with Tone.js
- [ ] S11b-6: Implement seek-to-measure in MIDI playback
- [ ] S11b-7: Connect edit events to server re-parse and MIDI refresh
- [ ] S11b-8: Implement per-measure validation status announcements via aria-live
- [ ] S11b-9: Add dot-number display toggle as alternative to Unicode braille display
- [ ] S11b-10: Session cleanup — delete temp files after download or timeout
- [ ] S11b-11: Full VoiceOver testing of complete edit-hear-correct loop
- [ ] S11b-12: Test with a real composition error (wrong octave) end to end
