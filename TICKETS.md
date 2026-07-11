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

### [x] S5-4: Implement Staff class with voice assembly

**Why:** A piano piece has two physical staves — right hand and left hand —
each a separate sequence of measures, rendered together as a LilyPond grand
staff (`\new PianoStaff << \new Staff {...} \new Staff {...} >>`, confirmed
via the LilyPond Notation Reference, "Keyboard and other multi-staff
instruments"). S5-1 through S5-3 handle chords and in-accord voices *within*
a single staff/measure; this ticket adds the layer above that: routing each
hand's line of BANA braille content to its own `Staff` instance and
rendering both as one score.

**Verified BANA hand-sign symbols (developer-confirmed dot patterns, from
`tests/fixtures/children_s_piece.brf`):**

| Sign | ASCII | Cells | Unicode | Notes |
|------|-------|-------|---------|-------|
| Right hand | `.>` | dots(4,6) + dots(3,4,5) | ⠨⠜ | First cell also `OCTAVE_MARKS['⠨']=5`; second cell also `_CLEF_PREFIX` |
| Left hand  | `_>` | dots(4,5,6) + dots(3,4,5) | ⠸⠜ | First cell also `OCTAVE_MARKS['⠸']=3`; second cell also `_CLEF_PREFIX` |

Both signs' second cell (⠜, dots 3,4,5) is already `_CLEF_PREFIX` in
`tokenizer.py`. ⠨ also collides with `IN_ACCORD_CELLS['⠨⠅']`'s first cell.
Resolved by exact 2-character dict-key lookup — same mechanism already used
for `IN_ACCORD_CELLS` vs bare octave marks.

**Disambiguator rule (verified with zero exceptions across every hand-sign
occurrence in the fixture):** a dot-3 cell (`END_WORD_SIGN`, ⠄) immediately
follows the hand sign if and only if the very next real content cell
contains dot 1, 2, or 3. The tokenizer does not predict this — after
emitting the hand-sign token, if the next input cell equals `END_WORD_SIGN`,
consume and discard it, exactly like the existing `END_WORD_SIGN`
consumption in the word-sign collection loop (`tokenizer.py` ~192-194).

**Steps:**

1. Add `HAND_SIGN_CELLS: dict[str, str] = {'⠨⠜': 'right', '⠸⠜': 'left'}` to
   `bana_symbols.py`, following the `IN_ACCORD_CELLS` comment-block
   convention: cite the fixture source, note the overlap with
   `OCTAVE_MARKS`, `_CLEF_PREFIX`, and `IN_ACCORD_CELLS['⠨⠅']`.
2. Add `HAND_SIGN = auto()` to `SymbolCategory` in `bana_symbols.py`.
3. Update `BrailleTokenizer.tokenize()`: insert a new 2-cell lookahead
   immediately before the existing `if two in IN_ACCORD_CELLS:` check,
   reusing the already-computed `two = text[i:i+2]`. Emit
   `SymbolCategory.HAND_SIGN` with the decoded hand string as the token's
   character, set `header_active = False`, and consume a trailing
   `END_WORD_SIGN` if present. Do not modify `at_measure_start` (hand sign
   precedes notes, like key/time/clef tokens).
4. Update `BrailleParser._reset_state()`: add
   `self._current_hand: str | None = None` (routes to the right hand when
   no hand sign has been seen, preserving single-staff behavior).
5. Update `BrailleParser.parse()`:
   - Replace the single `staff = Staff(name="")` with
     `right_staff = Staff(name="right hand")` and
     `left_staff = Staff(name="left hand")`.
   - Route `SymbolCategory.HAND_SIGN` tokens: `self._current_hand = token.character`.
   - In the `BAR_LINE` branch and the trailing-`pending` flush, compute
     `active = left_staff if self._current_hand == 'left' else right_staff`
     and call the new `_next_measure_number_for(active, right_staff, left_staff)`
     helper instead of directly reading/incrementing `self._next_measure_number`.
   - Change `_handle_word_sign`'s third parameter from `staff: Staff` to
     `piece_started: bool`; callers pass
     `bool(right_staff.measures or left_staff.measures)`.
   - At the end of `parse()`: attach parsed key/time signature to **both**
     staves that have measures; attach clef/tempo to `right_staff` only (top
     staff — this fixture never restates them per hand). Call
     `score.add_staff(...)` for each of `right_staff`/`left_staff` that has
     measures.
6. Add `BrailleParser._next_measure_number_for(self, active, right_staff, left_staff) -> int`:
   - If `active is left_staff`: return
     `right_staff.measures[len(left_staff.measures)].number` (mirrors the
     right hand's measure at the same position — always already populated,
     since a right-hand line's tokens, including its bar line, fully
     precede its paired left-hand line's tokens). Fall back to
     `self._next_measure_number` (without advancing) if not yet populated.
   - Otherwise: return `self._next_measure_number`, then increment it —
     the *only* place the shared counter advances, since BANA margin
     numbers are only ever restated on right-hand lines.
7. Update `Score.to_lilypond()` in `src/dottednotes/models/score.py`: keep
   0- and 1-staff behavior unchanged; add a 2-staff branch emitting
   `\new PianoStaff << \new Staff { \relative c' {...} } \new Staff { \relative c' {...} } >>`,
   with `self.staves[0]` (right hand) as the top `\new Staff` block.
8. `Staff._resolve_clef()`'s existing octave-heuristic (octave ≥4 → treble,
   else bass) needs no change — it already operates per-`Staff`-instance,
   so correct routing alone yields treble for the right hand and bass for
   the left hand.
9. Write unit tests covering: both hand signs classify correctly in
   isolation; the disambiguator is consumed when present and left alone
   when absent; `⠨⠜`/`⠸⠜` are not confused with bare octave marks or
   `⠨⠅` (measure_division); a synthetic 2-measure/2-hand snippet routes
   measures to the correct `Staff` with matching, non-double-incrementing
   measure numbers; a no-hand-sign input still produces one staff (now
   named `"right hand"`); `Score.to_lilypond()` emits the `PianoStaff`
   wrapper for 2 staves and is unchanged for 0/1 staves.

**Definition of Done:**
- [x] `HAND_SIGN_CELLS` in `bana_symbols.py` contains both verified hand signs with overlap documented
- [x] `SymbolCategory.HAND_SIGN` exists
- [x] Tokenizer classifies `⠨⠜`/`⠸⠜` as `HAND_SIGN` without breaking existing octave-mark/in-accord/clef classification
- [x] Tokenizer consumes a trailing `END_WORD_SIGN` after a hand sign exactly when present; leaves normal tokenizing untouched otherwise
- [x] `at_measure_start` is unaffected by `HAND_SIGN` tokens
- [x] `BrailleParser.parse()` creates two `Staff` instances and routes measures to the correct one based on the most recent `HAND_SIGN` token
- [x] Left-hand measures receive the same measure number as the right-hand measure at the same position; the shared margin-number counter advances only on right-hand bar lines
- [x] Files with no hand signs still produce exactly one staff, routed and numbered identically to current behavior (staff now named `"right hand"`)
- [x] `Score.to_lilypond()` emits `\new PianoStaff << \new Staff {...} \new Staff {...} >>` for 2 staves; 0- and 1-staff output unchanged
- [x] All new unit tests pass
- [x] `pytest tests/` passes with no regressions

**Senior note:** Two fixture-transcription issues surfaced while integrating
`children_s_piece.brf` and were confirmed and fixed with the developer
directly (not guessed): (1) a stray single `+` character sat alone on its
own line (a hard line-break artifact) and was rejoined onto the preceding
right-hand line; (2) a missing dot-3 separator in `>PS'` (should be `>P'S'`)
had merged a piano dynamic (`⠜⠏` = 'p') and a note (`⠎` = A half/32nd) into
one mis-tokenized word-sign, which — combined with a **separate, pre-existing
bug** — produced a one-measure offset between the two hands partway through
the piece. That separate bug: `_resolve_measure_durations` (S2's whole/16th
ambiguity resolver) evaluates beat overflow across a measure's entire
flattened pending-note buffer, but doesn't account for full-measure in-accord
(S5-2/S5-3) splitting that buffer into independent voices. The developer
confirmed measure 1's intended notation is
`<<{g'8.\mf b16 d4-. g4-.}\\{d4 g4 g4}>>` — the resolver currently drops the
augmentation dot on the first voice's dotted eighth and resolves the
following ambiguous cell to a whole note instead of a 16th, producing a
beat-count warning. This is out of scope for S5-4 (staff routing) and is
**not** fixed here — `children_s_piece.brf` is expected to still produce
`_validate_measure_beat_count` warnings for its full-measure in-accord
measures; only the measure-numbering/staff-routing warning was fixed.
File a follow-up ticket for per-voice duration resolution in in-accord
measures before attempting to silence these warnings.

---

### [x] S5-5: Integration test: two-voice piano piece

**Why:** S5-4 adds the staff-routing machinery; this ticket proves it works
end to end against real two-hand BANA content —
`tests/fixtures/children_s_piece.brf` — the same kind of full-pipeline check
Sprint 2's and Sprint 4's integration tests did for `simple_melody.brf` and
`fengyang_flower_drum.brf`.

**Steps:**

1. Load and tokenize `children_s_piece.brf` via `BRLInputPipeline` +
   `BrailleTokenizer` + `BrailleParser`, following the pattern of
   `test_parse_simple_melody` (`tests/test_parser.py`).
2. Write integration tests asserting:
   - Exactly 2 staves, named `"right hand"` and `"left hand"`.
   - Both staves have equal, correct measure numbers: `list(range(1, 42))`
     (41 measures each, verified by running the parser, not guessed).
   - The right-hand staff resolves to `\clef treble`; the left-hand staff
     resolves to `\clef bass` (via `Staff._resolve_clef()`'s existing
     octave heuristic — no explicit clef cells are expected in this
     fixture).
   - `score.to_lilypond()` produces a well-formed
     `\new PianoStaff << \new Staff {...} \new Staff {...} >>` block
     containing exactly two `\new Staff {` blocks and two
     `\relative c' {` blocks.
3. Do **not** assert zero warnings for this fixture — see the S5-4 Senior
   note. Full-measure in-accord measures trigger pre-existing
   `_validate_measure_beat_count` warnings unrelated to staff routing.
4. Run `pytest tests/` before and after; verify no regressions.

**Definition of Done:**
- [x] `children_s_piece.brf` parses via the full pipeline (warnings allowed; see Senior note)
- [x] Score has exactly 2 staves, named `"right hand"` / `"left hand"`
- [x] Both staves have equal, correct measure counts and matching numbers at every position (1–41)
- [x] Right-hand staff resolves to treble clef, left-hand to bass, via the existing heuristic
- [x] `Score.to_lilypond()` output contains a well-formed `\new PianoStaff << \new Staff {...} \new Staff {...} >>` block
- [x] All new integration tests pass
- [x] `pytest tests/` passes with no regressions

**Senior note:** This is the first fixture with real two-hand content. Two
transcription gaps were found and corrected with the developer during S5-4
(see that ticket's Senior note) — the fixture in its current state produces
`_validate_measure_beat_count` warnings only from the pre-existing,
out-of-scope in-accord duration-resolution limitation, not from anything in
S5-4/S5-5's staff-routing logic.

---

### [x] S5-6: Fix augmentation dots and beat-budget resolution of standalone ambiguous cells

**Why:** Integrating `children_s_piece.brf` for S5-4/S5-5, ~20 of its 41
measures produced `_validate_measure_beat_count` warnings, documented as an
out-of-scope, pre-existing duration-resolution limitation and deferred (see
S5-4's Senior note). Two concrete, compounding causes were found and fixed
together, then verified live against the fixture (implemented and run,
then reverted pending this ticket): warnings dropped from 20 to 1 (see
Scope boundary — a second, unrelated fixture transcription typo found
during this investigation has already been corrected directly in
`children_s_piece.brf`, confirmed against the developer's Lilypond ground
truth, `tests/fixtures/Children_s_Piece.ly`).

**Bug A — augmentation dots are unimplemented.** A lone dot-3 cell (⠄)
immediately after a note/rest is BANA's augmentation (duration) dot,
confirmed by the developer. Today: the tokenizer's `_classify()` fallback
(`tokenizer.py` ~422-437) doesn't recognize `END_WORD_SIGN` (⠄, already
defined in `bana_symbols.py`) as anything, so it falls through to
`SymbolCategory.UNKNOWN`; the main parse loop (`braille_parser.py` ~265) has
a literal no-op for `UNKNOWN` ("handled in later tickets"). No `_PendingNote`
has a dots field, and `_finalize_voice_part` builds every `Duration` as
`Duration(value=dur_value)` with no `dots` argument — even though
`models/duration.py`'s `Duration` already fully supports `dots: int = 0..2`.
Confirmed: measures 13/23/27/39/41 in the fixture are each a single,
unambiguous note resolved to a plain half note (2 beats) inside a 3/4
measure — clearly meant to be a dotted half (3 beats, matching the time
signature exactly).

**Bug B — a standalone ambiguous whole/16th cell always defaults to whole,
even when that overflows the measure.** `_resolve_measure_durations`
(`braille_parser.py` ~837-909) only resolves an ambiguous cell
(`base_duration == 1`) as a 16th via *forward* adjacency to a following
base-8 or base-1 cell (run/individual detection). When neither applies (the
`else` branch), it unconditionally defaults to whole — even when a whole
note plainly can't fit. Confirmed live against measure 1 of
`children_s_piece.brf` (`g'8. b16 d4-. g4-.`, a 3/4 measure): the pending
sequence is `[G:base_8, B:base_1, D:base_4, G:base_4]`. At B, the next cell
is D (`base_4`), so the forward-only check falls into the `else` branch and
resolves B as whole (4 beats) — but a whole note alone already exceeds the
entire 3/4 measure's budget, so it cannot be correct. **Fix:** after the
existing adjacency pass completes, recompute the voice-part's total beats
(now correctly including augmentation dots from Bug A); for any cell that
the `else` branch resolved to whole, if the total exceeds the time
signature's beat budget, re-resolve that cell as 16th and adjust the
running total, continuing until the total fits or no more such cells
remain. This only touches the `else`-branch default — the existing
forward-adjacency run/individual detection (RUN/INDIVIDUAL states) is
**unchanged**, since that's tested, developer-confirmed behavior for actual
16th-note runs (see `test_single_16th_cell_starts_run_with_eighth_cells`,
`tests/test_parser.py` ~289-296, which explicitly documents that a *pure*
global count-based check was tried before and rejected for exactly this
reason — it can't tell a run leader from a genuine whole note). Verified
this reproduces the developer's exact confirmed total for measure 1: 6.5
(pre-fix) → 3.0 (post-fix, exact match).

**Scope boundary:** after both fixes plus the two fixture corrections below,
1 warning remains on `children_s_piece.brf`: measure 22, left hand only.

Three separate problems were found in measure 22 while validating this
ticket against the developer's Lilypond ground truth
(`tests/fixtures/Children_s_Piece.ly`):

- **Right hand, typo #1 — already fixed.** The ground truth
  (`<cis g e>8 <d a fis>8 <e b g>8 <fis cis a>8 <g d b>4`) is four plain
  eighth-note chords plus a closing quarter chord. The fixture had the cell
  for the second chord's D using ⠵ (D, whole/16th-class, base_duration 1)
  instead of ⠑ (D, eighth-class, base_duration 8) — a one-cell slip (ASCII
  'Z' instead of 'E' in the raw `.brf`), the same category of error as the
  two already fixed in S5-4's Senior note. Corrected directly in
  `tests/fixtures/children_s_piece.brf`.
- **Right hand, typo #2 — surfaced by implementing Bug A, already fixed.**
  Once augmentation dots were implemented, a second issue appeared: an
  extra dot-3 cell (⠄, ASCII `'`) sat immediately after the first chord's C
  note (file position 690, before its interval markers), which had
  previously been silently ignored as `UNKNOWN` and so had no effect. Once
  Bug A made it a real augmentation dot, it wrongly made the first chord a
  dotted eighth (0.75 beat), which the ground truth doesn't show (plain
  `<cis g e>8`) — and no other note in that measure has this extra cell
  before its interval markers. Confirmed with the developer and removed
  from `tests/fixtures/children_s_piece.brf`. With both typos fixed, the
  right hand resolves to exactly 3.0 beats with no warning and no dots.
- **Left hand — a real resolver bug, not a transcription issue.** The
  ground truth (`g8.\< fis16 e8 fis8 e4`) is a dotted-8th + a single 16th
  (completing exactly 1 beat: 0.75 + 0.25), then two genuine eighths (1
  beat), then a quarter (1 beat) = 3.0 exactly. `_resolve_measure_durations`
  currently resolves this as `[8, 16, 16, 16, 4]` instead of the correct
  `[8, 16, 8, 8, 4]` — once the run starts (the ambiguous F cell resolves
  to 16th because the next cell is base-8), `state == "run"` never turns
  off, so it keeps converting every subsequent base-8 cell to a 16th
  instead of stopping once a full beat is complete. This is **S5-7**,
  confirmed here with real developer ground truth (previously only
  hypothesized from unverified fixtures — see S5-7 for the update). Not
  fixed in S5-6 — leave this 1 warning and let S5-7 resolve it; do not
  attempt to silence it here.

A related but distinct issue surfaced while checking this: scanning every
other `.brf` fixture for 16th-run lengths (not just `children_s_piece.brf`)
turned up runs of 2, 3, 6, 7, 8, 10, and 12 notes in
`Beethoven_Ludwig_Van_String_Quartet_No_1-1.brf`,
`Faure_Gabriel_Morceau_de_Concours.brf`, and `fengyang_flower_drum.brf` —
all in simple 3/4 or 4/4 time, where a clean run should always be exactly 4
notes (1 beat). This strongly suggests `_resolve_measure_durations`'s
`"run"` state never resets after a full beat's worth of 16ths, silently
chaining multiple beats' runs into one. This is a separate, likely
real bug, but Beethoven/Fauré aren't developer-verified ground truth (per
S0-6, only `fengyang_flower_drum.brf` and `children_s_piece.brf` are), so
there's no confirmed-correct duration set to validate a fix against yet.
Out of scope for S5-6 — see S5-7.

**Steps (Bug A — augmentation dots):**
1. Add a new `SymbolCategory.AUGMENTATION_DOT` category in `bana_symbols.py`.
2. In `tokenizer.py`'s `_classify()`, add a branch: `if char ==
   END_WORD_SIGN: return SymbolCategory.AUGMENTATION_DOT` — safe because by
   the time `END_WORD_SIGN` reaches this fallback, it has NOT been consumed
   by the word-sign collection loop (~192-194) or the S5-4 hand-sign
   disambiguator (both `continue` past this point when they consume it) —
   verified no existing test relies on `END_WORD_SIGN` alone producing
   `UNKNOWN` (`test_tokenizer_unknown_cell` / `_unknown_does_not_raise` use
   different cells).
3. Add `dots: int = 0` to both `_PendingNote` and `_PendingRest`
   (`braille_parser.py` ~129-155) — rests can be dotted too.
4. In `BrailleParser.parse()`, add a branch for
   `SymbolCategory.AUGMENTATION_DOT`: if `pending`, increment
   `pending[-1].dots` (cap at 2, matching `Duration`'s supported range);
   otherwise this cell is malformed input — warn plainly, don't raise.
5. In `_finalize_voice_part` (`braille_parser.py` ~737-793), change
   `Duration(value=dur_value)` to `Duration(value=dur_value,
   dots=pnote.dots)` for both the note and rest construction paths.
6. Write unit tests: tokenizer classifies a dot-3 cell after a note as
   `AUGMENTATION_DOT`; a dotted quarter/half/eighth each resolve to the
   correct `Duration(dots=1)`; a double-dot (two consecutive dot-3 cells,
   if that's confirmed as the correct BANA double-dot encoding — ask the
   developer before assuming) resolves to `dots=2`; a dot-3 cell with no
   preceding note warns rather than crashing.

**Steps (Bug B — beat-budget check on the standalone-whole default):**
1. In `_resolve_measure_durations`, track the indices resolved via the
   `else` branch (base_duration==1, tentatively whole, no run/individual
   adjacency) in a `whole_candidates` list, leaving the rest of the state
   machine untouched.
2. After the main loop, if `whole_candidates` is non-empty: compute total
   beats via `sum(Duration(value=resolved[i], dots=pending[i].dots
   ).duration_in_beats() for i in range(len(pending)))`. While the total
   exceeds `beats` and candidates remain, flip the next candidate's
   `resolved[idx]` from 1 to 16, subtracting its old beat contribution and
   adding the new one to the running total.
3. Update `test_16th_context_does_not_bleed_past_quarter`
   (`tests/test_parser.py` ~307-316): its input (`⠽⠙⠹⠽`) already totals 5.5
   beats under a 4/4 signature before the trailing ambiguous cell resolves
   — that cell overflows as a whole note too, so under the fix it correctly
   becomes a 16th, not a whole note. Update the assertion and docstring to
   reflect the corrected (and more correct) behavior; this is an
   intentional behavior change, not a regression — the old expectation
   encoded the exact bug this ticket fixes.
4. Write unit tests: measure 1's exact voice (`8th, ambiguous, quarter,
   quarter`) resolves to `(8, 16, 4, 4)` with dots applied correctly;
   existing forward-adjacency run/individual tests are unaffected (confirm
   by running the full suite); a standalone whole note that exactly fills
   its measure is unaffected (no false flip when total equals, not
   exceeds, the beat budget).

**Definition of Done:**
- [x] `AUGMENTATION_DOT` category added and tokenized correctly, without
      breaking existing `END_WORD_SIGN` consumption in word-sign/hand-sign contexts
- [x] `_PendingNote.dots` / `_PendingRest.dots` flow through to `Duration.dots`
      in both note and rest paths
- [x] `_resolve_measure_durations` re-checks `else`-branch whole-note
      candidates against the measure's beat budget, without changing
      run/individual adjacency behavior
- [x] `children_s_piece.brf` integration test (S5-5) is tightened to assert
      the corrected durations for measure 1 (per the developer's confirmed
      ground truth: `g'8. b16 d4-. g4-.`) and for measure 22's right hand
      (per `Children_s_Piece.ly`: four eighth-note chords + a closing
      quarter chord)
- [x] `_validate_measure_beat_count` warnings on `children_s_piece.brf` drop
      from 20 to the 1 on measure 22's left hand (documented in Scope
      boundary as S5-7's issue, not this ticket's)
- [x] `test_16th_context_does_not_bleed_past_quarter` updated to reflect the
      corrected behavior (see Steps)
- [x] All new unit tests pass; `pytest tests/` passes with no regressions

**Senior note:** This resolves the duration-resolution limitation deferred
in S5-4's Senior note for all measures except measure 22 (filed separately
per the Scope boundary above). The fix deliberately layers a beat-budget
check on top of the existing adjacency-based run detection rather than
replacing it — a pure global count-based approach for whole/16th cells was
already tried and rejected for run-leader cases (see
`test_single_16th_cell_starts_run_with_eighth_cells`'s comment), so keep
that reasoning in mind if extending this further.

---

### [x] S5-7: Fix 16th-note run state not resetting at beat boundaries

**Why:** While validating S5-6's beat-budget fix, a scan of every 16th-note
run resolved by `_resolve_measure_durations` across all `.brf` fixtures
found run lengths of 2, 3, 6, 7, 8, 10, and 12 notes in
`Beethoven_Ludwig_Van_String_Quartet_No_1-1.brf`,
`Faure_Gabriel_Morceau_de_Concours.brf`, and `fengyang_flower_drum.brf` —
all in simple 3/4 or 4/4 time, where a clean 16th-note run should always
total exactly 1 beat. **Since confirmed directly against
`children_s_piece.brf`'s own Lilypond ground truth
(`tests/fixtures/Children_s_Piece.ly`)**, not just inferred from run
lengths: measure 22's left hand is `g8.\< fis16 e8 fis8 e4` — a dotted-8th
+ one 16th (0.75 + 0.25 = exactly 1 beat), then two genuine eighths (1
beat), then a quarter (1 beat). The parser currently produces
`[8, 16, 16, 16, 4]` instead of `[8, 16, 8, 8, 4]`: it correctly starts the
run at the ambiguous F cell (next cell is base-8), but never stops it once
that first 16th completes the beat, so it keeps sweeping the following two
genuine eighths into the run too.

**Confirmed cause:** in `_resolve_measure_durations` (`braille_parser.py`
~837-909), once `state` becomes `"run"` it stays `"run"` for every
subsequent `base_duration == 8` cell with no limit — there is no check for
how many notes/beats the run has consumed. This is a *different* defect
from S5-6's Bug B (which is about a *standalone* ambiguous cell with no
run at all) — this ticket is about a run that starts correctly but doesn't
stop where it should.

**Confirmed general rule:** the developer confirmed the beat-completion
algorithm directly: a run consumes 16th-equivalents (0.25 beat each) until
the *current beat* — including whatever fraction of it was already
consumed before the run's leader — reaches exactly 1.0 beat, at which point
the run ends. A base-8 cell right after that point is a genuine 8th unless
a **fresh** base-1 leader starts a new run for the next beat. This
naturally covers both the plain case (a run starting at a clean beat
boundary needs exactly 4 notes) and `children_s_piece.brf` measure 22's
case (a run starting after a dotted-8th, which already spent 0.75 of the
beat, needs only 1 note). Triplet (6-note) runs are explicitly **out of
scope**: `Duration` has no tuplet concept (a "16th" is hard-coded to 1/4
beat), so a sextuplet's 1/6-beat notes aren't representable without a
data-model change — deferred to a future ticket.

**Implemented:** `_resolve_measure_durations` now tracks a `beat_progress`
float (fraction of the current beat consumed, reset to 0 whenever it
reaches a whole number) alongside the existing state machine. Once a RUN
cell brings `beat_progress` to exactly 1.0, `state` returns to `"normal"` —
the run/individual adjacency detection itself is otherwise unchanged.

**Steps:**
1. ~~Use `children_s_piece.brf` measure 22 (left hand) as the primary,
   developer-confirmed regression case~~ — done:
   `[8(dots=1), 1, 8, 8, 4]` now resolves to `[8, 16, 8, 8, 4]`, matching
   `g8. fis16 e8 fis8 e4` exactly, with zero warnings on that measure.
2. ~~Confirm the general beat-boundary rule with the developer~~ — done,
   see "Confirmed general rule" above.
3. Done: `_resolve_measure_durations`'s `"run"` state now closes once
   `beat_progress` reaches 1.0; a fresh base-1 leader correctly starts a
   new run for the next beat if one follows.
4. Added unit tests: `test_children_s_piece_measure22_left_hand_matches_lilypond_ground_truth`
   (Step 1's regression case); `test_16th_run_splits_into_two_beat_groups`
   (two fresh-leader 4-note groups); `test_16th_run_without_fresh_leader_does_not_continue_past_a_beat`
   (only one leader for 8 cells — the run ends after 4, the rest resolve as
   genuine 8ths); confirmed all existing run/individual tests
   (`tests/test_parser.py` ~246-316) pass unchanged.
5. Re-ran the fixture scan: `children_s_piece.brf` now parses with **zero**
   `_validate_measure_beat_count` warnings (`test_children_s_piece_has_no_remaining_warnings`).
   Beethoven/Fauré's warning counts (953 / 68) are unchanged by this fix
   (verified by comparing against S5-6-only output) — they're pre-existing,
   out-of-scope, unverified-fixture issues from S5-6, not something this
   ticket introduced or worsened. fengyang_flower_drum.brf's warning count
   actually *improved* (79 → 58).

**Definition of Done:**
- [x] `children_s_piece.brf` measure 22 (left hand) resolves to
      `[8, 16, 8, 8, 4]`; the fixture's last remaining
      `_validate_measure_beat_count` warning (from S5-6) is gone
- [x] Developer has confirmed the general multi-beat grouping rule before
      it's applied beyond the `children_s_piece.brf` case
- [x] `_resolve_measure_durations` resets 16th-note runs at the confirmed
      boundary instead of running unbounded
- [x] All new unit tests pass; `pytest tests/` passes with no regressions
- [ ] `children_s_piece.brf` re-scan shows zero anomalous run lengths

**Senior note:** The core defect is now confirmed with real developer
ground truth and fixed. Beethoven/Fauré's large warning counts remain
unresolved and out of scope — they're not developer-verified ground truth
(per S0-6), and this ticket's fix neither caused nor meaningfully changed
them. Triplet/tuplet support (the "6 notes = 1 beat" case) needs a real
`Duration` data-model change and is deferred to a future ticket.

---

### [x] S5-8: Implement single-cell triplet sign (BANA 8.4)

**Why:** `Duration` has no tuplet concept — a "16th" is hard-coded to 1/4
beat, an "eighth" to 1/2 beat, etc. (flagged as a gap in S5-7's Senior
note). Real braille music marks triplets (3 notes in the time of 2) with a
dedicated single-cell sign, confirmed by fetching *Music Braille Code,
2015* (BANA), Section 8.4, page 71:

> "The single-cell sign is generally used to indicate a triplet of any
> value. The sign may be doubled for four or more successive triplets of
> the same value. The braille note-grouping procedure may be employed
> when the notes of the triplet are all of the same value."

**Confirmed dot pattern:** dots 2-3 (⠆, U+2806, ASCII `'2'` in
`ASCII_TO_DOTS`) — confirmed directly by the developer, cross-referenced
against `ASCII_TO_DOTS` in `input_pipeline.py`.

**Scope boundary (per developer direction — no multi-cell groupings):**
explicitly excludes BANA 8.5 / 8.5.1 / 8.5.2 (the three-/four-cell sign for
irregular groups of any size other than three, including a three-cell
sign used for a triplet nested within another irregular group) and 8.6's
numeral-adding rule as it applies to that three-cell sign. Relevant from
8.6: the single-cell sign itself never carries an explicit numeral ("the
presence or absence of a print numeral is not shown in braille" for
triplets using the single-cell sign) — unlike the three-cell sign, which
always requires one. This means the tokenizer needs no numeral-cell
lookahead for this sign.

**Confirmed duration rule:** a triplet's three notes always total the
duration of *two* notes of that face value — 3 eighth-note-shaped cells
total 1 beat (not 1.5), 3 quarter-note-shaped cells total 2 beats, 3
16th-note-shaped cells total 0.5 beat. (Standard 3-in-the-time-of-2
tuplet math; developer-confirmed with these exact worked examples.)

**Confirmed interaction with leader/continuation runs (S2-4/S5-7):** a
triplet whose face value is 16th-class is written using the *same*
ambiguous-leader (`base_duration==1`) + continuation (`base_duration==8`)
cells as a normal run — e.g. a 16th-note-class leader followed by two
`base_8` continuation cells are all three 16ths, and together form one
triplet group. The difference from a normal run is the *termination
condition*: a plain run (S5-7) ends when it completes a full beat (needing
4 16ths); a triplet-context run always ends after exactly 3 notes,
regardless of beat completion, since the triplet's total duration (0.5
beat for 16th-class) is fixed by the triplet marker itself, not by the
surrounding beat structure.

**Confirmed doubled-sign semantics:** doubling the sign (writing it twice)
opens an unbounded sequence of triplet groups — every subsequent group of
three notes is a triplet, with no repeated sign needed between groups.
This continues until a **single** (undoubled) sign appears; the three
notes immediately following that single sign are the *final* triplet
group, and triplet treatment ends after that group's third note (whether
or not another sign follows immediately after).

**Duration model change — integer ticks, not float beats:** to avoid
float-rounding errors inherent to thirds (e.g. `1/3` isn't exact in binary
floating point — the exact problem a triplet feature would otherwise hit),
switch the duration model from `duration_in_beats()`'s current float
(quarter = `1.0`) to an integer-tick system, matching MusicXML's
`divisions` convention: **quarter note = 24 ticks.** Developer-confirmed
values: 16th = 6, triplet-8th = 8, plain 8th = 12, quarter = 24 (so
half=48, whole=96, 32nd=3, and augmentation dots scale as usual: dotted
quarter=36, double-dotted quarter=42, dotted 8th=18, etc.). This is a
cross-cutting change, not isolated to the new triplet code — every place
that currently calls `duration_in_beats()` needs updating:
- `models/duration.py`: add `TICKS_PER_QUARTER = 24`; replace (or add
  alongside, to be decided during implementation)
  `duration_in_beats()`'s float arithmetic with integer-tick arithmetic;
  apply the triplet's ×2/3 factor here (always exact in ticks — e.g.
  `12 * 2 // 3 == 8`, no rounding).
- `parser/braille_parser.py`: `_resolve_measure_durations`'s S5-6
  whole-note-overflow check and S5-7's `beat_progress` tracking both
  currently use `duration_in_beats()` floats with an `EPSILON` tolerance
  for equality checks — switching to integer ticks makes these exact
  comparisons and **removes the need for `EPSILON` entirely**.
  `_validate_measure_beat_count` also sums `duration_in_beats()`; needs
  the same conversion. Decide (and confirm with the developer) whether its
  warning message keeps showing beat-like numbers for readability (e.g.
  `ticks / TICKS_PER_QUARTER`) or switches to showing ticks directly —
  don't silently pick one.
- `tests/test_models.py` and `tests/test_parser.py`: every existing
  assertion on `duration_in_beats()` float values (e.g. `== 1.75`) needs
  updating to the equivalent tick integer (e.g. `== 42`).

**Known precision limitation (flagging, not blocking):** 24 ticks per
quarter keeps every currently-used value/dot/triplet combination exact
except double-dotted 16th (10.5), any dotted or double-dotted 32nd (4.5 /
5.25), and 64th notes at all (1.5 undotted). None of these are currently
produced by the resolver or exercised by any test (`base_duration==4`
never resolves to 64th, and no existing test uses dots with 32nd/64th), so
this doesn't block the current scope — but note it if 64th-note or
heavily-dotted small-value support is ever added later; a higher
resolution (e.g. 48 or 96 ticks/quarter) would be needed then.

**Steps:**
1. Add `SymbolCategory.TRIPLET_INDICATOR` and the confirmed cell (`⠆`,
   dots 2-3) to `bana_symbols.py`.
2. Add tokenizer classification for `⠆` (no numeral lookahead needed —
   see Scope boundary).
3. Add `TICKS_PER_QUARTER = 24` and integer-tick duration arithmetic to
   `Duration` (`models/duration.py`), per "Duration model change" above.
   Add `is_triplet: bool = False`, applying the confirmed ×2/3 factor.
4. Update `to_lilypond()` to wrap triplet groups in LilyPond's tuplet
   syntax — fetch the LilyPond Notation Reference's tuplet section first
   (per `CLAUDE.md`) to confirm current syntax (e.g. `\tuplet 3/2 { ... }`)
   before implementing.
5. Update `_resolve_measure_durations` (Bug B / S5-6) and its
   `beat_progress` tracking (S5-7) to use integer ticks instead of float
   `duration_in_beats()` + `EPSILON`; update `_validate_measure_beat_count`
   the same way (see the display-format question above — confirm before
   implementing).
6. In `BrailleParser`, when a `TRIPLET_INDICATOR` token appears: mark a
   triplet context active. If doubled, it stays active across unlimited
   groups of three until a single (undoubled) sign appears, whose
   following three notes are the last group (see "Confirmed doubled-sign
   semantics"). Within an active triplet context, the leader/continuation
   adjacency rule (S2-4/S5-7) still determines *which* cells are 16ths,
   but the group always closes after exactly 3 notes, not at beat
   completion (see "Confirmed interaction with leader/continuation runs").
   Apply the ×2/3 tick adjustment to all three notes/rests in each group.
   Confirm with the developer how to handle a triplet whose three notes
   are *not* all the same face value (8.4's note-grouping shorthand only
   applies "when the notes of the triplet are all of the same value" — a
   mixed-value triplet may need different handling; don't assume, ask).
7. Write unit tests: tokenizer classifies `⠆` as `TRIPLET_INDICATOR`;
   three eighth-notes marked as a triplet total exactly 24 ticks (1 beat),
   each note 8 ticks; a triplet of quarters totals 48 ticks, each note 16
   ticks; a 16th-class triplet (leader + 2 continuations) totals 12 ticks
   (0.5 beat), each note 4 ticks; a doubled-sign passage of two triplet
   groups followed by a single-sign final group correctly closes after
   the single sign's third note; `to_lilypond()` output matches confirmed
   LilyPond tuplet syntax; all existing `duration_in_beats()`-based tests
   updated to ticks and still passing; `pytest tests/` passes with no
   regressions.

**Definition of Done:**
- [x] `TRIPLET_INDICATOR` category and `⠆` tokenizer classification added
- [x] `Duration` uses integer ticks (`TICKS_PER_QUARTER = 24`) throughout;
      all call sites (`_resolve_measure_durations`, `beat_progress`,
      `_validate_measure_beat_count`) converted from float beats to ticks;
      `EPSILON`-based float comparisons removed
- [x] `Duration` supports the triplet ratio (×2/3, exact in ticks); both
      `duration_in_beats()`/ticks method and `to_lilypond()` updated and
      the latter verified against the LilyPond Notation Reference
- [x] `BrailleParser` correctly groups triplets (single and doubled-sign
      multi-group forms) per the confirmed semantics above, reusing but
      not duplicating the leader/continuation adjacency logic
- [x] Three-/four-cell irregular-group signs (BANA 8.5, 8.6) remain
      unimplemented — explicitly out of scope for this ticket
- [x] All new and updated unit tests pass; `pytest tests/` passes with no
      regressions

**Senior note:** Scope is deliberately narrow per the developer's explicit
direction: only the single-cell sign (BANA 8.4), covering triplets of any
note *value* but always a 3-in-the-time-of-2 grouping. Three-/four-cell
irregular-group signs (8.5) and nested/mixed-value irregular groupings are
explicitly deferred — do not expand scope to cover them without a
follow-up ticket. The integer-tick duration model is a prerequisite change
touching already-shipped S5-6/S5-7 code, not an isolated addition — budget
time accordingly and re-run the full suite after the conversion, before
adding triplet-specific logic on top.

---

### [x] S5-9: Support mixed-value notes within triplet groups (extends S5-8, BANA 8.4)

**Why:** S5-8 implemented the single-cell triplet sign but explicitly
deferred one question: "Confirm with the developer how to handle a triplet
whose three notes are not all the same face value... don't assume, ask"
(see S5-8 Step 6). Today `_apply_triplet_flag`/`_triplet_group_remaining`
(`braille_parser.py` ~338-362) closes every group after exactly 3 notes
with no duration tracking at all — that only works for BANA 8.4's
"same value" case. This ticket answers the deferred question: groups can
mix note values (e.g. a quarter + an eighth inside an eighth-note
triplet), so completion must be tracked by cumulative duration instead of
note count.

**Confirmed tick model:** Reuses S5-8's existing `TICKS_PER_QUARTER = 24`
and the `×2/3` triplet factor in `Duration.duration_in_ticks()`
(`duration.py` ~47-48) unchanged — no new tick constant. A tripleted
quarter is 16 ticks, a tripleted eighth is 8 ticks, matching what the code
already produces for `is_triplet=True`.

**Confirmed two-note rule:** in a 2-note group, the larger note's duration
is twice the smaller note's tripleted duration (quarter = 2×8 = 16), and
the group's total is 3× the smaller note's duration (3×8 = 24 — a full
eighth-note-triplet beat). Worked example: quarter(16) + eighth(8) = 24,
matching a plain 3-eighth triplet's total.

**Confirmed general group-closing rule:** target = 3× the smallest
tripleted note-duration seen so far in the *current* group (recomputed as
new notes arrive); the group closes once the running total reaches that
target. This applies to every triplet group, single (undoubled) sign or
doubled-sign block alike — developer-confirmed the quarter+eighth example
was not under a doubled sign. This replaces `_triplet_group_remaining`'s
current always-exactly-3-notes closing entirely, not just for doubled-sign
blocks. No fixed upper bound on group size: as many notes as it takes to
reach the target.

**Confirmed overshoot handling:** if adding a note would push the running
total past the target implied by the smallest note seen so far (e.g.
eighth+eighth+quarter = 8+8+16 = 32 vs. a target of 24), raise a hard
error rather than silently reinterpreting or warning — treat this as
malformed BANA input, developer-confirmed.

**Confirmed doubled-sign + ambiguous-value rule:** reuses S5-8's existing
doubled-sign mechanism (`_triplet_open_ended`) — no new BANA symbol. When
ambiguous leader cells (the existing whole/16th, half/8th, quarter/32nd
ambiguity from S5-6/S5-7, `_resolve_measure_durations`) appear within a
doubled-sign block, the target unit is 3× the smallest note value across
the *entire block* (not just the current group), because local per-group
resolution isn't available until the ambiguity resolves.

**Confirmed bar-line rule (corrected after initial implementation):** a
doubled-sign *block* may span a bar line — one group can close at the end
of a measure and a fresh one start in the next with no repeated sign
needed. But an individual *group*'s own notes must complete within a
single measure: e.g. three eighths in one measure followed by three more
in the next, marked within one triplet block, is fine (two separate,
self-contained groups); a quarter note in one measure completed by an
eighth note in the next is **not** — that would be one group's notes
straddling the bar line, which is malformed and raises a hard error
(`TripletDurationError`) at the bar line (or at end-of-input, treated as
an implicit final bar line for this purpose). The first implementation
pass got this wrong — it let an individual group's carried-over items
span a bar line (see `_group_triplets`' original carry-over design) —
corrected once the developer caught it against these two worked examples.

**Confirmed LilyPond rendering:** verified against the LilyPond Notation
Reference (Rhythms → Tuplets, `writing-rhythms#tuplets`): `\tuplet 3/2
{ ... }` wraps an arbitrary music expression — LilyPond does not require a
fixed note count inside the braces, so `\tuplet 3/2 { c4 c8 }` is valid
syntax for a 2-note group. `Tuplet.to_relative_lilypond` (`tuplet.py`
~22-33) already just joins whatever is in `self.items`, so no logic
change is needed there — only its docstring's "exactly 3 notes/rests"
claim (`tuplet.py:8`) needs correcting to reflect variable-length groups.

**Implemented:** Group/block closing moved entirely into the streaming
pass (`_apply_triplet_flag`, `braille_parser.py` ~470-490) rather than a
post-resolution pass, to avoid a circularity: closing decisions need
resolved tick values, but `_resolve_measure_durations`' own run/individual
state machine (for 16th-class leader/continuation triplets) needs to know
where a triplet group ends *while resolving*. Resolved:
- `_provisional_triplet_ticks` computes a tripleted tick value at
  streaming time from each note/rest's raw `base_duration` (1/2/4/8) —
  exact for base_duration 4 and unambiguous base_duration 8, and a
  documented simplifying assumption for base_duration 1 (always treated
  as the BANA 8.4 16th-class leader shorthand, never a whole note — a
  whole-note triplet doesn't occur in practice, and this matches how
  `_resolve_measure_durations` actually resolves a leader-then-base_8
  sequence, so the two stay consistent).
- `_register_triplet_item` runs the confirmed closing rule (target = 3×
  smallest tripleted duration in the group, or block-wide when an
  ambiguous cell — base_duration 1 or 2 — has been seen in the current
  doubled-sign block) and raises `TripletDurationError` on overshoot.
  Group boundaries are recorded via a new `triplet_group_end` flag on
  `_PendingNote`/`_PendingRest`, set the moment a group closes.
- `_resolve_measure_durations`' triplet-aware RUN-closing (S5-8) now
  checks `pending[i].triplet_group_end` instead of counting to 3 —
  simpler than before, and correct for variable-length groups since the
  flag is already known by resolution time.
- `_group_triplets` (`braille_parser.py` ~915-940) purely chunks by
  `triplet_group_end` markers (no duration math of its own) — every group
  it sees is already closed, since `_check_triplet_group_not_open_at_bar_line`
  raises `TripletDurationError` at a bar line (or end-of-input) if a group
  is still mid-flight (`_triplet_group_total_ticks > 0`). **Correction
  after initial implementation:** the first pass let an individual group's
  items carry across `_finalize_measure` calls so a group *itself* could
  span a bar line — the developer caught this against two worked
  examples (three eighths, then three more in the next measure, within
  one doubled-sign block: fine, two self-contained groups; a quarter in
  one measure completed by an eighth in the next: not allowed, one
  group's notes can't straddle a bar line) and it was corrected to the
  hard-error behavior described above. Only the doubled-sign *block*
  (`_triplet_active`/`_triplet_open_ended`/the block-wide accumulators)
  persists across bar lines now — never an individual group's own
  accumulating ticks. This also meant `_finalize_measure`'s
  `_validate_measure_beat_count` skip (added for the incorrect carry-
  over case) was removed — no longer needed, since every measure's
  triplet content is now always fully self-contained.
- **Known simplification (flagging, not blocking):** the block-wide
  smallest-value rule is an eager running minimum, not a fully
  retroactive one — if a doubled-sign block's smallest note only appears
  in a *later* group, earlier already-closed groups in that block keep
  whatever target they closed with rather than being reopened. For
  realistic BANA input this doesn't matter (BANA 8.4's doubled sign is
  specifically for successive triplets of the *same* value, so a block's
  smallest value is consistent throughout in practice); a genuinely
  divergent block would need the fully deferred/two-pass design discussed
  and set aside during scoping.
- **Known simplification (flagging, not blocking):** the streaming-time
  provisional tick calculation doesn't know augmentation dots yet (dot
  cells follow the note they modify) or the measure-wide half/32nd
  overflow rule (S5-6), so a dotted note or a half-note-class ambiguous
  cell inside a triplet group uses its plain face value for the closing
  decision. Not exercised by any current test or real fixture.

**Steps:**
1. ~~Replace `_triplet_group_remaining`'s note-count closing in
   `_apply_triplet_flag`/`_commit_pending_triplet_signs`~~ — done, see
   Implemented above.
2. ~~Extend the doubled-sign path to buffer notes across the whole block
   when ambiguous leader cells are present~~ — done via the block-wide
   `_triplet_block_smallest_ticks`/`_triplet_block_has_ambiguous`
   accumulators (running, not fully retroactive — see Known
   simplification above).
3. ~~Update `Tuplet`'s docstring~~ — done (`tuplet.py`).
4. ~~Update comments describing `is_triplet` groups as same-value~~ —
   done (`_PendingNote`/`_PendingRest` field comments).
5. ~~Write unit tests~~ — done (`tests/test_parser.py`, "S5-9: mixed-value
   notes within triplet groups" section): quarter+eighth 2-note group at
   24 ticks; the two-note rule (larger = 2× smaller); overshoot raises
   `TripletDurationError`; an undoubled single sign closes by duration;
   a single group cannot span a bar line (raises `TripletDurationError`);
   a doubled-sign block *can* span a bar line via two separate self-
   contained groups (three eighths, then three more); an unclosed group
   at end-of-input raises the same error. All 526 pre-existing tests plus
   6 new ones pass (532 total); the `children_s_piece.brf` /
   `fengyang_flower_drum.brf` fixture regression tests are unaffected.

**Definition of Done:**
- [x] `_apply_triplet_flag`/group-closing is duration-based (target = 3×
      smallest note seen in the current group), not note-count-based, for
      all triplet groups — single-sign and doubled-sign alike
- [x] Overshooting a group's implied target raises a hard error
- [x] Doubled-sign blocks with ambiguous leader cells use a block-wide
      smallest-note unit; the block may span a bar line via separate
      self-contained groups, but no individual group's own notes may
      straddle a bar line (hard error if one is left mid-flight there)
- [x] `Tuplet`/`to_lilypond()` docstring corrected; rendering verified
      against the LilyPond Notation Reference for variable-length groups
- [x] All new and existing tests pass; `pytest tests/` passes with no
      regressions

**Senior note:** Direct follow-up to S5-8's deferred "mixed-value
triplet" question, confirmed with the developer via worked examples
(quarter+eighth = 24 ticks) rather than assumed. The rule generalizes
cleanly: target = 3× the smallest tripleted note-duration currently known
for the group (block-wide instead of per-group specifically when
ambiguous leader cells are involved under a doubled sign). This removes
the note-counting shortcut S5-8 relied on and is a real behavior change to
`_apply_triplet_flag`, not an additive one — the full S5-8 test suite
was re-run after this change since every existing same-value-triplet test
now exercises the new duration-based closing path instead of the old
counter (all still pass unchanged). The two "known simplification" notes
above (non-retroactive block-wide minimum; dots/half-note ambiguity not
factored into the streaming-time closing decision) are deliberate scope
boundaries given real BANA input doesn't seem to exercise them — flagged
rather than silently assumed, per the project's own convention; revisit
if a real fixture ever hits them. One correction happened after the
initial pass: the first implementation let an individual triplet
*group*'s notes span a bar line (conflating it with the *block*-can-span-
a-bar-line rule) — the developer caught this with two worked examples and
it's now a hard error, per the "Confirmed bar-line rule (corrected...)"
note above.

---

# Sprint 5b: Orchestral Score Support

Estimated time: 1.5–2 weeks.

**Research basis for this sprint:** BANA *Music Braille Code, 2015*, Section
33 "Instrumental Ensemble Scores" (print pp. 270-288, §§33.1-33.7.1) and
Table 29 "Abbreviations for Instrument Names" (print pp. 28-31), plus the
LilyPond Learning Manual v2.26, §4.4.5 "Scores and Parts". Both fetched and
read in full before drafting these tickets, per `CLAUDE.md`'s "fetch before
implementing" rule. Section/page citations below refer to this edition.

**Real fixtures already in the repo** (`tests/fixtures/`, see
`tests/fixtures/README.md`) directly relevant to this sprint:
- `fengyang_flower_drum.brf` — flute and strings, developer-authored,
  **developer-verified ground truth** (per `CLAUDE.md`: "the most reliable
  ground-truth test case in the suite"). Its inline part abbreviations
  (`>VNI'`, `>VNII'`, `>VA'`, `>VC'`, `>BA'`) already match Table 29(A)'s
  Violin I / Violin II / Viola / Violoncello / Double bass entries.
- `Bartok_Bella_Romanian_Folk_Dances_for_Orchestra.brl` — full orchestra, has a
  literal §33.2 instrument-list header (Piccolo, Flutes I/II, Clarinets
  I/II in B-flat, Bassoons I/II, Horns in F I/II, Violins I, Violins II,
  Violas, Violoncellos, Double Basses) — not developer-verified, useful as
  a stress-test/smoke-test fixture only (same status as Beethoven/Fauré in
  S5-6/S5-7's Senior notes).
- `Beethoven_Ludwig_Van_String_Quartet_No_1-1.brf` (string quartet) and
  `Faure_Gabriel_Morceau_de_Concours.brf` (flute and piano) — also
  not-yet-developer-verified, per the fixtures README.

**Known codebase gap this sprint must close:** `Score.to_lilypond()`
(`models/score.py` ~19-27) currently hard-codes exactly one staff (plain
`\relative` block) or exactly two staves (`\new PianoStaff`, the Sprint
4/5 piano-hands case) — its own docstring says "More than two staves is
not yet supported." `Staff.name` (`models/staff.py`) is currently just an
ad hoc string ("right hand" / "left hand"), with no instrument-abbreviation
or ensemble concept at all. Every ticket below either builds toward or
depends on removing this ≤2-staff ceiling (S5b-7 is where it's actually
removed).

**Open question flagged across this sprint (ask before starting S5b-1):**
Table 29's abbreviation cells and §33.2.2's numbering-digit signs were only
visible in the BANA PDF as braille glyph images, not extractable as literal
text by this research pass. Per `CLAUDE.md`, dot patterns must never be
guessed from a scan — they need to be cross-referenced against
`ASCII_TO_DOTS` in `input_pipeline.py` (or `bana_symbols.py` directly) or
confirmed with the developer before any ticket below writes dot-pattern
constants.

### [x] S5b-1: Implement instrument abbreviation lookup table

**Why:** §33.2 "List of Instruments" (p. 270-271): immediately after the
title, an ensemble score has a two-column table — full instrument names
(column 1, in the print score's original order, including transposing-
instrument keys and any info given on the print score's first page) and
abbreviations (column 2, left-aligned 2 cells beyond the longest name). No
existing code parses this header or has any instrument-name/abbreviation
concept — `Staff.name` is just a free string today.

**Research (§33.2, Table 29):**
- (a) No contractions are employed in the names.
- (b) UEB accidental/letter-modifier signs are used when English is the
  score's language; accented letters in a foreign-language score use that
  language's own characters.
- (c) An overflow name line is indented to cell 3, or cell 5 if there are
  two or more same-named instruments on separate staves.
- (d) Two or more dot-5 guide dots fill the gap when a name ends 3+ cells
  before the abbreviation column.
- (e) If title + instrument table + music heading + first parallel don't
  fit on page 1, the heading and first parallel move to page 2 together.
- §33.2.1: Table 29 gives English/Italian/French/German abbreviations for
  the standard orchestral roster (piccolo, flute, oboe, English horn,
  clarinet, bass clarinet, bassoon, double bassoon, horn, trumpet,
  trombone, tuba, timpani, cymbals, triangle, snare/bass drum, harp L/R
  hand, piano L/R hand, violin I/II, viola, violoncello, double bass).
  Instruments absent from Table 29 need a transcriber-devised 2-3 letter
  abbreviation "conveying an immediate suggestion of the name" (BANA's own
  examples: "glo" for glockenspiel, "tt" for tam-tam) — this needs to be
  overridable/suppliable, not silently invented per input.
- §33.2.2: multiple like instruments (e.g. "Violins I/II") get their
  number as a lower-cell digit, no numeric indicator, immediately before
  the abbreviation's closing dot-3; when combined on one staff, numbered
  lowest-to-highest matching interval/in-accord order (ties into S5b-3).
  A further-divided part (e.g. "Violins I-1" / "Violins I-2") adds a
  *second*, upper-cell digit before the dot-3.
- §33.2.3: a multi-staff instrument (piano, organ, harp) has each hand
  treated as its own separate named "instrument" line in the ensemble
  parallel — the Sprint 4/5 two-hand-only keyboard rules do not apply
  here.

**Steps:**
1. Confirm Table 29's dot patterns and §33.2.2's numbering-digit signs
   with the developer / against `ASCII_TO_DOTS` (see the sprint-level open
   question above) before adding any constants.
2. Add an instrument name→abbreviation lookup (English at minimum; decide
   with the developer whether Italian/French/German are in scope for this
   ticket or a later one — Table 29 has all four, but no fixture currently
   needs anything but English).
3. Parse the §33.2 two-column instrument-list header into an ordered list
   of (full_name, abbreviation, part_number) entries, applying §33.2.2's
   numbering and §33.2.3's per-hand splitting for multi-staff instruments.
4. Implement the transcriber-abbreviation fallback path for instruments
   outside Table 29 (explicit, visible in output — not a silent guess).
5. Unit tests against a synthetic instrument-list input and against
   `Fengyang_Flower_Drum.brf`'s real header.

**Definition of Done:**
- [x] Table 29 abbreviations available as a lookup (at least English)
- [x] §33.2 instrument-list header parses into ordered (name, abbreviation,
      number) entries, including §33.2.2 numbering and §33.2.3 per-hand
      splitting for piano/organ/harp
- [x] Fallback abbreviation path for instruments outside Table 29
- [x] All dot patterns confirmed against `bana_symbols.py`/developer, not
      guessed from the BANA PDF scan
- [x] Tests pass against synthetic input and the Fengyang fixture header

**Senior note:** This ticket is the foundation every other S5b ticket
depends on (an instrument name/abbreviation is needed before staves can be
labeled, grouped, or transposed). Do not guess at Table 29's braille cells
from the PDF scan — confirm first.

---

### [ ] S5b-2: Implement MeasureRepeat class with expand() method

**Why:** `CLAUDE.md`'s BANA key facts already flag this: "Measure repeat:
Specific dot combination means 'repeat previous measure.' Must be expanded
(not passed through) in the output." §33.4.3 "Braille Repeats" (p. 276)
confirms this is specifically relevant to ensemble scores, not just solo
music: "Very obvious measure or part-measure repeats may be used when they
occur on the same braille line as the original passage." The same
paragraph also scopes this ticket:
- Braille **numeral** repeats (§19) **may not be used** in ensemble
  scores — explicitly out of scope here, even though they exist elsewhere
  in BANA.
- Da capo and dal segno (§20) may be used for extensive repetitions "when
  all details of the affected passages are identical" — a distinct,
  larger-scale repeat mechanism, not this ticket's `MeasureRepeat`.

**Steps:**
1. Confirm the measure-repeat cell's dot pattern against
   `bana_symbols.py`/`ASCII_TO_DOTS` (not yet in the codebase — do not
   guess; the developer has not yet supplied this pattern per the
   existing `bana_symbols.py` convention).
2. Add `SymbolCategory`/tokenizer classification for the sign.
3. Implement a `MeasureRepeat` model with an `expand(previous_measure)`
   method that materializes a full copy of the previous measure's notes —
   per §33.4.3, only valid when the repeat sign is on the *same braille
   line* as the measure being repeated; flag/warn if that adjacency
   doesn't hold rather than silently expanding the wrong measure.
4. Wire into `BrailleParser`/`_finalize_measure` so the expansion happens
   before a `Measure` is added to a `Staff` — downstream code (LilyPond
   rendering, beat-count validation) should never see an unexpanded
   repeat marker.
5. Unit tests: single measure repeat expands correctly; part-measure
   repeat (§18.3) expands only the repeated portion; numeral-repeat cells
   are explicitly rejected/unsupported in this scope, not silently
   mis-parsed as a measure repeat.

**Definition of Done:**
- [ ] Measure-repeat dot pattern confirmed with the developer, not guessed
- [ ] `MeasureRepeat.expand()` materializes the previous measure's notes,
      validated against §33.4.3's same-line requirement
- [ ] Numeral repeats remain unsupported/out of scope, per §33.4.3
- [ ] Tests pass; `pytest tests/` no regressions

**Senior note:** Needed before S5b-8's integration tests, since condensed
ensemble parallels lean on measure repeats heavily (§33.4.3) — most real
orchestral parts are mostly repeats and rests, not fresh notes every bar.

---

### [x] S5b-3: Implement interval shorthand detection and voice reconstruction

**Why:** `CLAUDE.md`'s BANA key facts already flag interval shorthand as
"common in orchestral scores." §33.4.2 "Intervals and In-Accords" (p. 275)
adds an ensemble-specific constraint not covered by the general interval
rules: "Intervals and in-accords are read upward in all parts. The braille
interval signs should be used freely, **except in divisi parts for string
instruments**. In string music, braille intervals must be reserved for
double, triple or quadruple stops; the only exception to this restriction
is a divisi passage in octaves." Example 33.4.2-1 (Bassoons/Cellos, an
octave interval) and 33.4.2-2 (Flutes/Violins, `div.` marking) illustrate
both sides of this rule.

**What this means for implementation:** the existing interval-shorthand
reconstruction (built for chords in earlier sprints — see
`BrailleParser._handle_interval`/`_apply_interval`) needs a *staff-type-
aware* branch for ensemble scores: on a string-instrument staff, an
interval sign normally means "this is a stop on the same instrument" (a
`Chord`, one performer), **not** "reconstruct a second independent voice"
— unless the passage is explicitly marked divisi in octaves, in which case
it *is* a second voice/staff, same as on a non-string instrument. This
needs to know "is this staff a string instrument," which depends on
S5b-1's instrument table.

**Steps:**
1. Confirm with the developer whether "divisi in octaves" is detected from
   an explicit print marking already captured as a word-sign expression
   (`div.` per Example 33.4.2-2) or needs a dedicated signal — don't guess.
2. Add a staff-instrument-family concept (string vs. not) sourced from
   S5b-1's instrument table.
3. On string staves, default interval signs to chord/stop reconstruction;
   only reconstruct a second voice when the divisi-in-octaves condition
   from Step 1 is detected.
4. On non-string staves, keep the existing (non-ensemble) interval
   handling — this ticket only adds the string-specific carve-out.
5. Unit tests reproducing Examples 33.4.2-1 (octave divisi, allowed as a
   second voice) and 33.4.2-2 (plain string interval, must resolve as a
   stop/chord, not a second voice).

**Definition of Done:**
- [x] String-instrument staves default interval signs to stop/chord
      reconstruction, not second-voice reconstruction
- [x] Divisi-in-octaves is detected and reconstructs a second voice, per
      §33.4.2's stated exception
- [x] Non-string staves' existing interval handling is unaffected
- [x] Tests pass against Examples 33.4.2-1/33.4.2-2 patterns

**Senior note:** This is a correctness trap, not a missing feature — using
the existing (non-string-aware) interval logic unmodified on an ensemble
string part would silently misread double-stops as two separate melodic
lines. Don't skip the staff-family check to save time.

---

### [x] S5b-4: Implement staff grouping and bracket markers

**Research finding — likely scope correction needed:** §33.1-§33.7 (read
in full for this sprint) describe the condensed bar-over-bar parallel
format as **an ordered, flat list of instrument lines** — "each parallel
containing only the music of the instruments that have music to play in
those measures" (§33.1) — with no braille sign anywhere in Section 33 for
a visual bracket/brace grouping instrument families (strings, winds,
brass) the way a *print* orchestral score groups staves. §33.2's
instrument-list header is a plain two-column table, not a bracketed tree.
The only place §33 groups staves at all is §33.2.3 (a keyboard/harp/
organ's hands are adjacent lines, no special bracket sign either).

**This means:** "staff grouping and bracket markers" as originally titled
may not be a BANA-parsing concern at all — it may really be a *LilyPond
output* decision (e.g. wrapping a `\new StaffGroup { ... }` or
`\new PianoStaff { ... }` around related instruments in the generated
`.ly`/PDF for readability), inferred from instrument family (via S5b-1's
table) rather than parsed from the braille input. **Flag to the developer
before starting:** confirm whether this ticket should be rescoped to
"LilyPond output staff grouping" (cosmetic, PDF-readability only, no BANA
parsing involved) or dropped/merged into S5b-7 (`OrchestraScore`), since
there may be no braille signal to parse here at all.

**Steps (pending the scope confirmation above):**
1. Confirm rescoping with the developer.
2. If proceeding: define instrument-family groupings (strings/winds/
   brass/percussion/keyboard) from S5b-1's table.
3. Emit `\new StaffGroup` (or nested groups, e.g. strings as one group,
   with the piano/organ hands already grouped via `\new PianoStaff` per
   S5b-1 §33.2.3) around family-adjacent instruments in
   `OrchestraScore.to_lilypond()` (S5b-7) — fetch the LilyPond Notation
   Reference's staff-grouping section first, per `CLAUDE.md`'s mandate,
   before writing the syntax.
4. Tests: Bartók fixture (has all five families) renders valid LilyPond
   with the expected group structure.

**Definition of Done:**
-x[x] Scope confirmed with developer (BANA-driven vs. output-only)
-x[x] If output-only: instrument-family grouping emits correct
      `\new StaffGroup`/`\new PianoStaff` LilyPond, verified against the
      Notation Reference
-x[x] Tests pass against the Bartók fixture

**Senior note:** Don't build a BANA-side bracket parser without first
confirming this scope correction — nothing found in §33 supports one, and
building unused parsing code would be wasted effort in the wrong
direction.

---

### [x] S5b-5: Implement tacet and multi-measure rest parsing

**Why:** §33.1 states the core mechanic directly: "each parallel
contain[s] only the music of the instruments that have music to play in
those measures. An instrument that has only rests in those measures is
omitted from the parallel." This means a resting instrument doesn't get an
explicit multi-measure rest sign in the condensed braille at all in the
general case — it's represented by *absence* from however many parallels
cover its silent measures. The parser needs to track, per instrument,
which measures it's absent from, and reconstruct the correct total rest
duration for those gaps when materializing that instrument's full part
(needed for `OrchestraScore`/S5b-7's per-staff `Measure` list, where every
staff needs *something* — a note or a rest — in every measure, unlike the
condensed input).

**Cross-reference to LilyPond side (Learning Manual §4.4.5):** the
Learning Manual's own multi-measure-rest guidance is directly relevant to
the *output* half of this ticket — a resting instrument's reconstructed
gap should render as LilyPond's multi-measure rest syntax
(`R2*3`-style: `R` + duration + `*` + count), and `\compressMMRests { … }`
is the documented way to compress that in a formatted individual part
(relevant if/when individual-part extraction is ever built, per that same
Learning Manual section's overall workflow — not required for this ticket,
but the reason to keep the reconstructed-rest data explicit rather than
just "not present").

**Not yet researched — fetch before implementing:** BANA §5.3
"Multiple-Measure Rests" (print p. 58) describes the *explicit* braille
sign for a multi-measure rest (used when a print score does show one, as
opposed to §33.1's implicit-by-omission case) — this session's reading was
scoped to §33 only, so §5.3 needs its own fetch-and-confirm pass (per
`CLAUDE.md`'s mandate) before this ticket is implemented, to know whether
this ticket is only the implicit/omission case or also the explicit sign.

**Steps:**
1. Fetch and read BANA §5.3 before starting (see above).
2. Track, per instrument in an `OrchestraScore` parse, which measure
   numbers it's present vs. absent for (§33.1's omission rule).
3. Reconstruct a multi-measure `Rest` (or a run of per-measure rests) for
   each gap, sized to that instrument's own time signature if it differs
   per part (ties to S5b-7's per-part key/time signature handling).
4. If §5.3 turns up an explicit sign distinct from the omission case,
   implement that too and confirm its dot pattern before use.
5. Unit tests: an instrument absent for several consecutive parallels in
   a synthetic ensemble input gets a correctly-sized rest run in its
   reconstructed part.

**Definition of Done:**
- [x] BANA §5.3 fetched and cross-referenced (not assumed)
- [x] Per-instrument presence/absence tracked correctly across parallels
- [x] Reconstructed rests are correctly sized and placed for §33.1's
      implicit-omission case
- [x] Tests pass

**Senior note:** This is a quiet but load-bearing ticket — get it wrong
and every instrument's part in `OrchestraScore` silently loses whichever
measures it wasn't mentioned in.

---

### [ ] S5b-6: Implement transposing instrument table and concert pitch flag

**Why:** `CLAUDE.md`'s existing Key Design Decision #4 already commits to
this: "Concert pitch: Default to concert pitch output; transposing
instrument support added in Sprint 5b." §33.2 confirms what BANA itself
does with transposing instruments: the instrument-name column "includes
all of the information that is given on the first page of the printed
music, **including the keys of transposing instruments**" — i.e. BANA
preserves the instrument's key as *text* (e.g. "Clarinet in B♭"), but the
note cells themselves encode **written pitch** (what the performer reads),
not concert pitch. BANA does not transpose; DottedNotes has to, to honor
Decision #4's concert-pitch default.

**LilyPond mechanism (Learning Manual §4.4.5):** the documented approach
is exactly `\transpose f c' \hornNotes` — wrapping a written-pitch music
expression in `\transpose <written-key> <concert-key>` to sound at concert
pitch. This maps directly onto this ticket: parse the instrument's key
from the §33.2 name text already captured by S5b-1 (e.g. "Horn in F",
"Clarinet in B♭"), look up its transposition interval, and wrap that
staff's `to_lilypond()` output in the corresponding `\transpose` call —
controlled by a concert-pitch flag, so a future "written pitch" output
mode (useful for generating individual parts, per the same Learning
Manual section) can skip the wrap.

**Steps:**
1. Build a transposing-instrument name/key → transposition-interval table
   (standard orchestral transpositions: clarinet in B♭/A, horn in F,
   trumpet in B♭/C, English horn in F, etc.) — verify each interval
   against a reliable source rather than assuming from memory (these are
   easy to get backwards — confirm direction, e.g. "Horn in F sounds a
   perfect fifth *below* written," before encoding).
2. Parse the instrument key text captured by S5b-1's §33.2 name column.
3. Add the concert-pitch flag (per Decision #4, concert pitch is the
   default) and wrap transposing staves' output in `\transpose`,
   confirming exact syntax against the LilyPond Notation Reference (not
   just the Learning Manual example) before implementing, per
   `CLAUDE.md`'s mandate.
4. Unit tests: a synthetic "Horn in F" and "Clarinet in B♭" part transpose
   correctly in both concert-pitch and written-pitch output modes.

**Definition of Done:**
- [ ] Transposition interval table built and each interval verified (not
      assumed from memory)
- [ ] Instrument key parsed from the §33.2 name text
- [ ] Concert-pitch flag controls whether `\transpose` is applied,
      defaulting to concert pitch per Decision #4
- [ ] `\transpose` syntax verified against the LilyPond Notation Reference
- [ ] Tests pass for at least horn and clarinet transpositions

**Senior note:** Get the transposition direction and interval verified,
not assumed — a backwards transposition is a silent musical error, not a
crash, and would be easy to miss without a developer with perfect pitch
or a reference score checking the output.

---

### [ ] S5b-7: Implement OrchestraScore class

**Why:** `Score.to_lilypond()` (`models/score.py` ~19-27) currently only
handles exactly one staff or exactly two (the Sprint 4/5 piano-hands
case) — its own docstring says "More than two staves is not yet
supported." This ticket is where that ceiling is actually removed for
ensembles, bringing together S5b-1 through S5b-6.

**Research grounding this model (§33.3-§33.7):**
- §33.3 Page Layout: every parallel must complete on the page it begins,
  unless there are too many parts to fit, in which case it may split
  across a left/right page pair at a natural instrument-group boundary
  with roughly equal line counts on each side.
- §33.4 The Parallel: each line begins with the instrument abbreviation
  (plus a per-part key signature if parts differ — §33.4.1); the first
  signs of every measure are vertically aligned across *all* parts in the
  parallel, with guide dots for gaps over six cells.
- §33.4.1 Key Signatures: a shared signature goes in the music heading
  only if *every* part has the same one; otherwise it's omitted from the
  heading and appended per-line after each instrument's abbreviation.
- §33.4.5 Placing Longer Expressions: an expression can apply to (a) all
  parts, (b) one line, or (c) a successive subset of parts — each with
  its own placement/abbreviation-listing convention. `OrchestraScore`
  needs to preserve which of these three scopes an expression had.
- §33.4.6 Measure Numbers and Rehearsal References: a new parallel must
  start wherever a rehearsal mark or measure number appears in the print
  score.
- §33.4.7 Run-over Lines: a single line whose one-measure content is too
  long for the parallel's width continues on an indented run-over line.
- §33.5 Dividing a Measure between Parallels: a too-long measure splits
  at the same rhythmic point in every part, using the music hyphen or
  measure-division sign, continuing in the next parallel.
- §33.6 Parallel Movement: a melody doubled at the unison/octave by other
  instruments can be written once and referenced via the parallel-
  movement sign in the doubling parts (with rules for when instruments
  are score-adjacent vs. distant, and for restating the reference vs.
  letting it continue).
- §33.7 Consolidating Identical Parts: two or more same-instrument parts
  that stay in unison for a whole parallel can be combined onto one
  braille line, showing all their numbers in the line's abbreviation
  (ties to S5b-1 §33.2.2's numbering rule) — including §33.7.1's "a2"
  wind convention, shown once as a word-sign expression rather than
  repeated every system.

**What this means for the data model:** unlike today's `Staff`/`Measure`
(where every staff has a `Measure` for every bar), an `OrchestraScore`'s
source parallels are inherently *sparse* per measure (§33.1) — unlike a
"full score" concept where every part has something (a note or a rest,
via S5b-5) in every measure. `OrchestraScore` needs to reconcile these:
parse the sparse parallel structure faithfully, but still be able to
materialize a complete, gap-free per-instrument part for
`to_lilypond()`.

**Steps:**
1. Design `OrchestraScore` (new file, `models/orchestra_score.py` or
   similar) as an ordered list of named instrument parts (from S5b-1),
   each with its own optional key signature (§33.4.1) and a measure list
   reconciled via S5b-5's rest reconstruction for the instrument's silent
   measures.
2. Parse the sparse §33.4 parallel structure in `BrailleParser` (or a
   dedicated ensemble parser path) into this model, including run-over
   lines (§33.4.7) and mid-measure division (§33.5).
3. Implement §33.6 parallel-movement doubling and §33.7 identical-part
   consolidation, both as ways to *avoid re-parsing* the same music twice
   internally (mirrors the Learning Manual §4.4.5 shared-variable
   philosophy — reuse the already-parsed music object for a doubling/
   consolidated part rather than re-deriving it).
4. Extend `to_lilypond()` to emit each instrument as its own `\new Staff`
   (wrapped per S5b-4's grouping decision, transposed per S5b-6's flag),
   removing the current ≤2-staff limitation.
5. Unit tests building up from small synthetic parallels to the full
   Fengyang and Bartók fixtures (S5b-8).

**Definition of Done:**
- [ ] `OrchestraScore` models an ordered list of named, independently-
      keyed instrument parts with gap-free per-instrument measure lists
- [ ] §33.4's parallel structure (vertical alignment, run-over lines,
      mid-measure division) parses correctly
- [ ] §33.6 parallel movement and §33.7 consolidated parts avoid
      duplicating already-parsed music
- [ ] `to_lilypond()` emits an arbitrary number of staves, removing
      `Score`'s current 1-or-2-staff ceiling
- [ ] Tests pass, building up to the fixtures in S5b-8

**Senior note:** This is the sprint's centerpiece and by far its largest
ticket — budget accordingly, and expect it to surface refinements needed
in S5b-1 through S5b-6 as real parsing is attempted against the Bartók
fixture's full orchestral roster.

---

### [ ] S5b-8: Integration test using Fengyang orchestral score

**Why:** `fengyang_flower_drum.brf` (flute and strings) is already in the
repo (`tests/fixtures/`, also `examples/`) and is, per `CLAUDE.md`, "the
primary integration test fixture... the developer arranged it and knows
the expected LilyPond output exactly... the most reliable ground-truth
test case in the suite." Its inline abbreviations (`>VNI'`, `>VNII'`,
`>VA'`, `>VC'`, `>BA'`) already match Table 29(A)'s Violin I/II, Viola,
Violoncello, and Double bass entries — real, concrete validation for
S5b-1 through S5b-7 together, exactly analogous to how `children_s_piece.
brf` grounded S5-6/S5-7's regression tests.

**Fixture status (per `tests/fixtures/README.md`):** only
`fengyang_flower_drum.brf` is developer-verified ground truth for this
sprint. `Bartok_Bella_Romanian_Folk_Dances_for_Orchestra.brl` (auto-transcribed
by Sao Mai Braille software), `Beethoven_Ludwig_Van_String_Quartet_No_1-1.brf`,
and `Faure_Gabriel_Morceau_de_Concours.brf` (both from IMSLP/braillemuse.net)
are real-world scores but **not**
developer-verified — same status Beethoven/Fauré already have in S5-6/
S5-7's Senior notes for the solo-piano sprints. Treat them as smoke-test/
warning-count-tracking fixtures only, not exact-output assertions, unless
the developer verifies specific measures against a reference score (as
was done for `children_s_piece.brf` measures 1 and 22 in S5-6/S5-7).

**Steps:**
1. Parse `fengyang_flower_drum.brf` end-to-end through `OrchestraScore`
   (S5b-7) and assert the resulting LilyPond output matches the
   developer's known-correct expectation, at least measure-by-measure for
   a representative sample (mirroring S5-7's
   `test_children_s_piece_measure1_matches_lilypond_ground_truth` pattern)
   — confirm the exact expected output with the developer rather than
   assuming it from this fixture's braille alone.
2. Confirm zero unexpected `_validate_measure_beat_count`-style warnings
   on this fixture, matching the "zero remaining warnings" bar set by
   `test_children_s_piece_has_no_remaining_warnings` in S5-7.
3. Add smoke tests (parses without crashing, warning counts tracked but
   not required to be zero) for the Bartók/Beethoven/Fauré fixtures,
   flagging their warning counts as a baseline to watch for regressions,
   not a pass/fail bar — same treatment as Beethoven/Fauré already get in
   S5-6/S5-7.

**Definition of Done:**
- [ ] `fengyang_flower_drum.brf` parses through `OrchestraScore` and
      matches developer-confirmed LilyPond output for its representative
      sample measures
- [ ] Zero unexpected beat-count warnings on `fengyang_flower_drum.brf`
- [ ] Bartók/Beethoven/Fauré smoke tests pass (no crash) with warning
      counts recorded as a regression baseline

**Senior note:** This ticket is the sprint's acceptance test, not new
parsing logic — it should mostly be assembling S5b-1 through S5b-7's
pieces against real input and confirming output with the developer, the
same role `children_s_piece.brf`'s tests played across S5-6/S5-7.

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
