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

### [x] S5b-6: Implement transposing instrument table and concert pitch flag

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
- [x] Transposition interval table built and each interval verified (not
      assumed from memory)
- [x] Instrument key parsed from the §33.2 name text
- [x] Concert-pitch flag controls whether `\transpose` is applied,
      defaulting to concert pitch per Decision #4
- [x] `\transpose` syntax verified against the LilyPond Notation Reference
- [x] Tests pass for at least horn and clarinet transpositions

**Senior note:** Get the transposition direction and interval verified,
not assumed — a backwards transposition is a silent musical error, not a
crash, and would be easy to miss without a developer with perfect pitch
or a reference score checking the output.

---

### [x] S5b-7: Implement OrchestraScore class

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
- [x] `OrchestraScore` models an ordered list of named, independently-
      keyed instrument parts with gap-free per-instrument measure lists
- [x] §33.4's parallel structure (vertical alignment, run-over lines,
      mid-measure division) parses correctly
- [x] §33.6 parallel movement and §33.7 consolidated parts avoid
      duplicating already-parsed music
- [x] `to_lilypond()` emits an arbitrary number of staves, removing
      `Score`'s current 1-or-2-staff ceiling
- [x] Tests pass, building up to the fixtures in S5b-8

**Senior note:** This is the sprint's centerpiece and by far its largest
ticket — budget accordingly, and expect it to surface refinements needed
in S5b-1 through S5b-6 as real parsing is attempted against the Bartók
fixture's full orchestral roster.

---

### [x] S5b-8: Integration test using Fengyang orchestral score

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
- [x] `fengyang_flower_drum.brf` parses through `OrchestraScore` and
      matches developer-confirmed LilyPond output for its representative
      sample measures
- [x] Zero unexpected beat-count warnings on `fengyang_flower_drum.brf`
- [x] Bartók/Beethoven/Fauré smoke tests pass (no crash) with warning
      counts recorded as a regression baseline

**Senior note:** This ticket is the sprint's acceptance test, not new
parsing logic — it should mostly be assembling S5b-1 through S5b-7's
pieces against real input and confirming output with the developer, the
same role `children_s_piece.brf`'s tests played across S5-6/S5-7.

---

### [x] S5b-9: Support Sao Mai's inline multi-measure-number-per-line convention (Bartók smoke test)

**Why:** `test_bartok_smoke_documents_current_crash`
(`tests/test_ensemble_integration.py`) is a `strict=True` xfail
documenting that `Bartok_Bella_Romanian_Folk_Dances_for_Orchestra.brl`
doesn't parse. Two distinct bugs were blocking it, found while
investigating for S7b-7:
1. A false positive in `EnsembleParser.parse()`'s instrument-list
   detection — the file's two free-text title/attribution lines above
   the real instrument-list header also tokenized as `WORD_SIGN` (any
   literary text does), got collected as fake "instruments," and the
   collection loop stopped at the following blank line before ever
   reaching the real header. **Already fixed** (this ticket, alongside
   the fix) — see `EnsembleParser.parse()`'s `inst_lines` loop and
   `test_ensemble_parser_skips_title_line_before_instrument_list`.
2. **Still open, this ticket's actual scope:** once (1) is fixed, parsing
   gets to measure ~172 before crashing with
   `AttributeError: '_PendingRest' object has no attribute 'dynamics'`.
   Root cause: Sao Mai Braille software (which auto-transcribed this
   fixture) puts **multiple measure-number markers inline on one physical
   line**, e.g. line 16 of the normalized file:
   `⠼⠁⠀⠀⠀⠀⠀⠀⠀⠼⠃⠀⠀⠼⠙⠀⠀⠀⠀⠀⠀⠼⠑` — four separate
   `NUMBER_SIGN`+digit groups (`⠼⠁`=1, `⠼⠃`=2, `⠼⠙`=4, `⠼⠑`=5), spaced
   apart mid-line, each apparently marking where a new measure's content
   begins. `extract_measure_number` (`ensemble_parser.py`) only recognizes
   a number-sign+digit group *alone at the start* of a line (BANA §33.4.6
   convention — see its docstring) — it has no concept of multiple inline
   measure boundaries within a single line. Everything after the first
   recognized number on such a line gets silently absorbed into that first
   measure's content instead of being split at each subsequent `⠼X`
   marker, which misaligns measure boundaries badly enough that, deep
   enough into the piece, a dynamic marking ends up attached to an
   unresolved pending rest (`_PendingRest` has no `dynamics` field — only
   real notes/rests being built as notes do).

**Steps:**
1. Confirm the inline-multi-measure-number hypothesis against more of the
   file than the sample above (grep for `NUMBER_SIGN` occurrences per
   line — the fixture has several, not just line 16) — verify it's a
   consistent convention throughout, not a one-off.
2. Extend measure-boundary detection (`extract_measure_number` and/or its
   caller in `EnsembleParser.parse()`) to recognize `NUMBER_SIGN`+digit as
   a measure boundary marker *anywhere* in a line, not only at the start —
   splitting the line's remaining content at each marker into separate
   per-measure chunks, each still processed through the existing
   per-instrument parsing path.
3. Don't let this regress BANA's own standalone-line convention (Fengyang,
   the developer-verified fixture) — the two conventions need to coexist,
   selected by what a given file actually uses, not a global flag.
4. Once parsing succeeds end-to-end, remove `test_bartok_smoke_documents_
   current_crash`'s `xfail` marker and replace it with real assertions
   (staff count, a representative measure or two) — per `TICKETS.md`'s
   existing S5b-8 guidance, this fixture is still not developer-verified
   ground truth, so treat it as a smoke test (parses without crashing,
   warning counts tracked as a baseline), not exact-output assertions,
   unless the developer verifies specific measures.

**Definition of Done:**
- [x] `Bartok_Bella_Romanian_Folk_Dances_for_Orchestra.brl` parses through
      `EnsembleParser` without raising
- [x] Sao Mai's inline multi-measure-number convention is handled without
      regressing BANA's standalone-line convention (Fengyang's tests still
      pass unchanged)
- [x] `test_bartok_smoke_documents_current_crash`'s `xfail` marker is
      removed and replaced with real smoke-test assertions

**Senior note:** Don't guess at Sao Mai's exact convention from one
sample — verify it holds across the whole file (or find where it doesn't)
before writing the splitting logic, the same "verify before implementing"
discipline this project applies to BANA dot patterns and LilyPond syntax.
This fixture is not developer-verified ground truth (S5b-8), so the bar
here is "parses correctly structurally," not "produces the exact right
notes" — don't over-invest in exact-output assertions against a fixture
nobody has confirmed against a reference score.

---

# Sprint 6: Fingering Notation

Estimated time: 4–6 days.

**Research basis for this sprint:** BANA *Music Braille Code, 2015*, Section 15 "Fingering" (print pp. 147-152, §§15.1-15.4.1) and Table 15 "Fingerings" (print p. 28), plus the LilyPond Notation Reference v2.26, §1.7.2 "Fingering". Section/page citations below refer to this edition.

**Known codebase gap this sprint must close:** There is currently no domain representation for musical fingering, nor any parser support to consume fingering symbols from the braille stream. Because fingering cells (such as `⠁`, `⠃`, `⠇`, `⠂`, `⠅`, `⠉`, `⠠`, `⠄`) collide directly with note, octave, duration, or word sign markings in a stateless tokenizer, they must be resolved contextually in the parser when they follow a note/chord (and optional dot).

### [x] S6-1: Implement Fingering Models and Symbol Recognition

**Why:** We need a domain representation for fingerings (which compile to post-events like `-1` or `-\markup ...` in LilyPond) and helper structures to map them to the BANA symbols defined in Table 15.

**Research (Table 15):**
- Fingerings use specific left-side cell configurations:
  - First finger (thumb): `⠁` (dot 1) -> LilyPond `-1`
  - Second finger (index): `⠃` (dots 1,2) -> LilyPond `-2`
  - Third finger (middle): `⠇` (dots 1,2,3) -> LilyPond `-3`
  - Fourth finger (ring): `⠂` (dot 2) -> LilyPond `-4`
  - Fifth finger (little): `⠅` (dots 1,3) -> LilyPond `-5`
- These cells collide with other categories but are unique when parsed immediately following a note, chord, or dot.

**Steps:**
1. Add `FINGERING` to `SymbolCategory` in `src/dottednotes/bana_symbols.py`.
2. Define a `FINGERING_CELLS` dict mapping Unicode cells to their finger values (1 to 5).
3. Create a `Fingering` domain model class representing a finger mark, with a `to_lilypond()` method.
4. Attach a list of `fingerings` to the `Note` and `Chord` domain classes.

**Definition of Done:**
- [x] `FINGERING` added to `SymbolCategory`
- [x] `Fingering` domain model class implemented and attached to `Note` and `Chord`
- [x] Table 15 basic finger cell mappings registered in `bana_symbols.py`

---

### [x] S6-2: Parse Single Fingerings and Handle Dotted/Tied Notes

**Why:** §15.1 "Placing Fingering Signs": basic fingerings are brailled immediately after the note (or after the dot if the note is dotted). If a note is tied, the fingering is placed before the tie.

**Steps:**
1. Update `BrailleParser` to inspect the token stream immediately following a note or chord.
2. If any of the basic finger cells are found, parse and consume them as a `Fingering` and attach them to the current note/chord.
3. If an `AUGMENTATION_DOT` (`⠄`) is present, ensure the fingering is parsed after the dot.
4. If a note is tied, ensure the fingering is attached to the note itself before compiling the tie event.
5. Implement basic fingering serialization in `to_lilypond()` (e.g. `c4-1`).

**Definition of Done:**
- [x] Parser extracts single fingerings for notes and chords
- [x] Dotted notes place their fingerings after the dot (e.g. `c4.-1`)
- [x] Tied notes place their fingerings before the tie (e.g. `c4-1 ~ c4`)
- [x] Unit tests cover notes, chords, dots, and ties with single fingerings

---

### [x] S6-3: Parse Change of Fingering and Adjacent Notes

**Why:** §15.2 "Change of Fingering": a change of fingers on a single note or interval is indicated by placing the "change of fingers" sign (`⠉`, dots 1,4) between two finger signs. §15.3 "Adjacent Notes with One Finger" requires that if a finger plays two adjacent notes, the fingering is written after each note.

**Research (§15.2, §15.3):**
- Transition sign: `⠉` (dots 1,4). Example: `⠁⠉⠃` (finger 1 changed to finger 2).
- In LilyPond, change of fingering can be represented using markup or a dash-separated sequence (e.g. `c4-1-2` or `c4-1_2`). We will implement it as `c4-1-2` or standard stacked lyric/dash notation.
- §15.3 requires no special syntax: the single finger is simply written after both notes consecutively, which is parsed naturally.

**Steps:**
1. Define `FINGERING_CHANGE_CELL = '⠉'` (dots 1,4) in `bana_symbols.py`.
2. Update the parser's fingering loop: if a finger sign is followed by `⠉`, consume the `⠉` and the subsequent finger sign.
3. Represent this change in the `Fingering` model (e.g., as `FingerChange(first=1, second=2)`).
4. Update `to_lilypond()` to output the transition format.
5. Add unit tests for change of fingering.

**Definition of Done:**
- [x] `FINGERING_CHANGE_CELL` registered in `bana_symbols.py`
- [x] Parser correctly handles the change transition `⠉` and consumes both finger signs
- [x] LilyPond rendering correctly outputs change transitions (e.g. `c4-1-2`)

---

### [x] S6-4: Parse Alternative Fingerings and Omission Place-markers

**Why:** §15.4 "Alternative Fingerings": alternative fingerings are brailled consecutively with no symbol or space between them (e.g. `⠁⠃` representing alternatives 1 and 2). If one alternative is omitted, place-markers are used: dot 6 (`⠠`) for the first omission, dot 3 (`⠄`) for the second.

**Research (§15.4, §15.4.1):**
- First alternative omitted placeholder: `⠠` (dot 6). Example: `⠠⠃` (first omitted, second is finger 2).
- Second alternative omitted placeholder: `⠄` (dot 3). Example: `⠁⠄` (first is finger 1, second omitted).
- LilyPond renders alternative fingerings as stacked columns, e.g. `-\markup \center-column { "2" "1" }`. Omissions render with empty space or placeholders.
- §15.4.1: If more than two fingerings are present, they are split into in-accord voices, which are handled naturally by standard in-accord parsing.

**Steps:**
1. Define `OMISSION_FIRST_FINGERING_CELL = '⠠'` and `OMISSION_SECOND_FINGERING_CELL = '⠄'` in `bana_symbols.py`.
2. Update the parser to support alternative fingerings by checking for a second consecutive fingering or omission cell.
3. Store both alternatives in the `Fingering` model, keeping track of any omitted slots (`None`).
4. Update `to_lilypond()` to generate stacked LilyPond column markup for alternative fingerings.

**Definition of Done:**
- [x] Omission placeholder cells registered in `bana_symbols.py`
- [x] Parser correctly extracts alternative fingering pairs, including those with omission placeholders
- [x] Stacked markup (e.g. `-\markup \center-column { "2" "1" }`) generated for alternative fingerings in LilyPond
- [x] Unit tests cover all combinations of alternative fingerings and omissions

---

### [x] S6-5: Integration and Regression Test Suite

**Why:** We must verify the end-to-end flow of all fingering rules, ensuring they compile correctly to LilyPond and do not introduce regressions on solo or ensemble scores.

**Steps:**
1. Create a synthetic test file `tests/fixtures/fingering_test_suite.brf`.
2. Write integration tests loading and parsing this suite, asserting the expected LilyPond structures.
3. Run the full test suite to guarantee zero regression.

**Definition of Done:**
- [x] Integration test suite passes on the new fingering fixture
- [x] Zero regressions across existing solo/orchestral test files

---

### [x] S6-6: Implement Tremolo Notation (Repeated-Note and Alternating-Note Tremolos)

**Why:** We need to support repeated-note tremolos (fractioning) and alternating-note tremolos. This enables blind composers to transcribe orchestral and keyboard tremolo shorthand to standard LilyPond output.

**Research (BANA Section 14, Table 14 / Table 10 & LilyPond §1.4.2 "Short repeats"):**
- **Repeated-Note Tremolo (Fractioning, §14.2):** Indicates a single note or chord repeated rapidly.
  - Prefix cell is `⠘` (dots 4,5, ASCII `^`).
  - Followed by a rhythmic value indicator cell:
    - 8ths: `⠃` (dots 1,2, ASCII `b`) -> `⠘⠃`
    - 16ths: `⠇` (dots 1,2,3, ASCII `l`) -> `⠘⠇`
    - 32nds: `⠂` (dot 2, ASCII `1`) -> `⠘⠂`
    - 64ths: `⠅` (dots 1,3, ASCII `k`) -> `⠘⠅`
    - 128ths: `⠄` (dot 3, ASCII `'`) -> `⠘⠄`
  - Placement: Placed immediately after the affected note or last interval of a chord (only separated by dots or fingerings).
  - Doubling: If 4+ successive notes are fractioned in the same value, write the second cell twice (`bb`, `ll`, `11`, `kk`, `''`) to start the doubling, and the full sign (`^b`, `^l`, etc.) after the last fractioned note.
- **Alternating-Note Tremolo (§14.3):** Indicates alternation between two notes or chords.
  - Prefix cell is `⠨` (dots 4,6, ASCII `.`).
  - Followed by a rhythmic value indicator cell:
    - 8ths: `⠃` (dots 1,2, ASCII `b`) -> `⠨⠃`
    - 16ths: `⠇` (dots 1,2,3, ASCII `l`) -> `⠨⠇`
    - 32nds: `⠂` (dot 2, ASCII `1`) -> `⠨⠂`
    - 64ths: `⠁` (dot 1, ASCII `a`) -> `⠨⠁` (Note: `.a` is used instead of `.k` to avoid collision with "Measure division" `.k`).
    - 128ths: `⠄` (dot 3, ASCII `'`) -> `⠨⠄`
  - Placement: Placed after the first of the pair of alternating notes/chords. The two notes/chords are written in their full print values. Cannot be doubled.
- **LilyPond Rendering:**
  - Single repeated-note tremolo compiles to: `note:subdivision` (e.g., `c4:16`).
  - Alternating tremolo compiles to: `\repeat tremolo <count> { note1 note2 }` where `<count>` = (duration of note1) / (tremolo subdivision). For example, a pair of half notes (duration 2) with 16th-note alternation compiles to `\repeat tremolo 4 { a16 b16 }`.

**Steps:**
1. Add `TREMOLO` to `SymbolCategory` in `src/dottednotes/bana_symbols.py`.
2. Register the prefix cells (`⠘` and `⠨`) and value cells (`⠃`, `⠇`, `⠂`, `⠅`, `⠄`, `⠁`) in `bana_symbols.py`.
3. Create a `Tremolo` domain model class representing repeated-note or alternating-note tremolo.
4. Attach `tremolo` attribute to `Note` and `Chord` models.
5. Update `BrailleParser` to parse repeated-note tremolos immediately following a note, chord, or fingering. Implement doubling detection (consuming doubled value cells and parsing the terminating sign).
6. Update `BrailleParser` to parse alternating-note tremolos (which link the current note/chord and the next note/chord in the sequence).
7. Update `Note.to_lilypond()` and `Chord.to_lilypond()` to serialize single-note repeated tremolos using the colon syntax (e.g. `c4:16`).
8. Update the parser or staff formatter to serialize alternating tremolos using the `\repeat tremolo` structure, calculating the correct repeat count.
9. Write unit and integration tests covering both types of tremolos (including doubled fractioning and alternating chords).

**Definition of Done:**
- [x] `TREMOLO` category and all associated symbols registered in `bana_symbols.py`
- [x] Parser correctly handles repeated-note tremolos with/without doubling and compiles them (e.g. `c4:16`)
- [x] Parser correctly handles alternating-note tremolos and compiles them to `\repeat tremolo count { note1 note2 }`
- [x] Unit tests cover 8th, 16th, 32nd, 64th, and 128th subdivision values for both repeated and alternating tremolos
- [x] Zero regressions across the existing test suite

---


# Sprint 7: Score Assembly and Full Pipeline

Estimated time: 4–5 days.

**Research basis for this sprint:** LilyPond Notation Reference v2.26,
"Titles and headers" chapter (`\header` block syntax and field names) and
"MIDI output" chapter (the `\midi {}` block inside `\score {}` is what
actually produces a `.midi` file — see CLAUDE.md's own quick-reference
list). Fetch both before touching `Score.to_lilypond()` in S7-1, per
CLAUDE.md's "fetch before implementing" rule — this sprint should not guess
`\header`/`\score`/`\midi` syntax from memory.

**Known codebase gap this sprint must close:** `Score.to_lilypond()`
(`models/score.py:70`) only ever emits a bare `\version` line followed by
the staff content — there is no `\header`, `\score`, `\layout`, or `\midi`
block anywhere in its output, even though `Score.title` and `Score.composer`
are real, populated fields. Separately, `cli.py` does not call
`Score.to_lilypond()` at all: it calls the much simpler
`LilypondRenderer.render()` (`renderers/lilypond_renderer.py`), whose
`_render_staff()` flattens every measure into `"{ note note note }"` with no
clef, key signature, time signature, or bar lines — none of the structure
that `Staff.to_lilypond()` (used everywhere in the test suite's
ground-truth comparisons) actually produces. In its current state,
`dottednotes convert` does not produce the same output the tests verify.

---

### [x] S7-1: Implement Score.to_lilypond() header/score/midi wrapping and retire the legacy renderer

**Why:** Two separate problems, not one: (1) `Score.to_lilypond()` has
`title`/`composer` fields but never emits a `\header` block, and never
wraps its output in `\score { ... \layout {} \midi {} }` — without the
`\midi {}` block, `lilypond file.ly` will not produce a `.midi` file at
all, which breaks the workflow CLAUDE.md documents (".brf → .ly → PDF +
MIDI"). (2) `LilypondRenderer`, the class the CLI actually calls, is a
parallel, much simpler implementation that ignores clefs/keys/time
signatures/bar lines entirely. Fixing only (1) without also fixing (2)
leaves the CLI emitting flat, structurally wrong output.

**Steps:**
1. Fetch the LilyPond Notation Reference "Titles and headers" section and
   confirm exact `\header {}` field syntax (field names are unquoted
   identifiers, values are quoted strings) before writing code.
2. In `Score.to_lilypond()`, after the `\version` line, emit a
   `\header { title = "..." composer = "..." }` block only when `title` or
   `composer` is set (mirror the existing single-field-omission behavior —
   don't emit an empty `title = ""` line if only one is set).
3. Escape embedded `"` characters in `title`/`composer` before interpolating
   them into the header (a literal quote in an unescaped field would
   currently produce broken LilyPond — the same latent bug already present
   in `LilypondRenderer.render()`).
4. Wrap the staff content in `\score { ... \layout {} \midi {} }` rather
   than emitting the staff blocks directly at top level.
5. Delete `renderers/lilypond_renderer.py` (or reduce it to a thin
   `LilypondRenderer.render(score) -> score.to_lilypond()` shim if
   something outside `cli.py` still imports the class name) and update
   `cli.py` to call `Score.to_lilypond()` directly.
6. Update every test that currently asserts on `score.to_lilypond()`'s
   exact structure — **31 call sites** across `tests/*.py` as of this
   sprint (grep `score\.to_lilypond()` before starting; this is the
   majority of the ticket's actual effort) — to account for the new
   `\header`/`\score`/`\midi` wrapping and the resulting indentation shift.
7. Update `tests/test_renderers.py` accordingly, or fold its cases into
   `test_parser.py`/`test_models.py` if `LilypondRenderer` is removed
   outright.

**Definition of Done:**
- [x] `Score.to_lilypond()` emits `\header` with escaped title/composer
      when either is set, and omits the block entirely when neither is set
- [x] `Score.to_lilypond()` output is wrapped in
      `\score { ... \layout {} \midi {} }`
- [x] Running `lilypond` on generated output produces both a `.pdf` and a
      `.midi` file (verified manually or in S7-5)
- [x] `cli.py` no longer imports or calls `LilypondRenderer`
- [x] All ~31 existing call sites that assert on `to_lilypond()` structure
      are updated and pass
- [x] All package unit tests pass

**Senior note:** This ticket is bigger than it looks. The `\header`/`\midi`
addition itself is a handful of lines; updating every existing test that
pattern-matches on the current unwrapped output is the real work. Do the
wrapping change first, run the full suite, and triage the failures as a
checklist rather than trying to predict all 31 call sites up front — don't
guess at what breaks. Same "verify before implementing" discipline the
`bana_symbols.py` dot-pattern tickets require, applied to LilyPond syntax
instead of braille.

---

### [x] S7-2: Implement CLI `convert` subcommand, `--compile`, `--version`, and fix input loading

**Why:** The current CLI (`cli.py`) takes a bare positional `input` path
with no subcommand at all — it doesn't match the
`dottednotes convert input.brf output.ly [--compile] [--verbose]`
interface `CLAUDE.md` documents, and has no `--version`. This ticket
introduces the subcommand structure; it is not a small addition to an
existing `convert` command — the flat interface changes.

**A confirmed bug this ticket must also fix:** `cli.py` loads input via
`InputPipeline(args.input).read()` (`parser/input_pipeline.py`), which is
a raw pass-through — unlike `BRLInputPipeline.load()` (the class every
other real caller in this codebase uses: `braille_parser.py`,
`ensemble_parser.py`, every fixture-based test), it never converts ASCII
braille to Unicode braille. Of the 10 real `.brf`/`.brl` fixtures in this
repo, 8 are ASCII-encoded (checked by hex-dumping each file's leading
bytes) — **ASCII is the common case for real `.brf` files, not the
exception**, since that's what a BrailleNotetaker actually exports (see
`CLAUDE.md`'s Developer Context). Feeding raw ASCII text to the tokenizer
means it never recognizes a single cell.

This was originally logged as two separate bugs — the CLI's
ensemble-vs-solo detection heuristic (`has_ensemble_header` in `main()`,
checking `WORD_SIGN`/`END_WORD_SIGN`) silently failing on
`fengyang_flower_drum.brf` and producing an empty score — but it's one
root cause, not two: `WORD_SIGN`/`END_WORD_SIGN` are Unicode braille
characters, so they can never appear in unconverted raw ASCII text
regardless of whether the file's content matches BANA orchestral-score
conventions. Confirmed directly: re-running the exact same detection
logic against `BRLInputPipeline.load()`'s output for
`fengyang_flower_drum.brf` (which does follow §33.2's instrument-list
header conventions correctly) correctly returns `has_ensemble_header =
True`.

**Correction, found while implementing this ticket and smoke-testing the
fix above end-to-end against every real fixture, not just Fengyang:** the
paragraph above originally concluded "the detection heuristic itself is
not the bug — don't spend this ticket's time rewriting it." That was
correct for Fengyang specifically but wrong in general — there is a
*second*, independent bug in the same heuristic, only reachable once the
ASCII-conversion fix above unblocks real input from reaching it.
`HAND_SIGN_CELLS` (`bana_symbols.py`) is a two-cell sequence (`⠨⠜` /
`⠸⠜`, right/left hand) whose second cell is literally `WORD_SIGN`
(`⠜`). A two-hand piano piece's hand-sign-prefixed line, followed later
in the same line by an unrelated `⠄`-shaped cell that's just ordinary
note content, is textually indistinguishable from a genuine
instrument-list header line under raw substring matching. Confirmed on
`tests/fixtures/fingering_melody.brf` (a real solo two-hand piece): both
`cli.py`'s dispatch *and* `EnsembleParser.parse()`'s own internal
`inst_lines` detection loop (`ensemble_parser.py`, ~line 279-291 — an
independent copy of the identical flawed check) wrongly treat it as an
ensemble score, and `EnsembleParser` then crashes with a confusing
`ValueError: No parallel systems found in ensemble score.`

The fix is **not** a rewrite of the heuristic's structure (measure-number-
based line partitioning is unchanged) — it's swapping the raw substring
test for a tokenizer-based one. `BrailleTokenizer` (`tokenizer.py`) already
correctly and positionally distinguishes a `HAND_SIGN` token (`⠨`/`⠸` as
the *first* cell of an exact 2-cell dict lookup) from a standalone
`WORD_SIGN` token (only emitted when `⠜` appears as the current cell
*alone*) — a hand sign never produces a `WORD_SIGN` token. This is already
well-tested (`tests/test_parser.py`'s S5-4 hand-sign block). Add
`has_ensemble_header(text)` and a private `_line_has_word_sign(line)`
helper to `ensemble_parser.py` (tokenizing each candidate line and
checking for a real `SymbolCategory.WORD_SIGN` token, instead of `WORD_SIGN
in line and END_WORD_SIGN in line`), have `EnsembleParser.parse()`'s own
`inst_lines` loop call the same helper, and have `cli.py` import and call
`has_ensemble_header` directly instead of duplicating the loop — this also
fixes the duplication that let the exact same bug exist unnoticed in two
divergent copies in the first place.

**Steps:**
1. Restructure `src/dottednotes/cli.py`'s `argparse` setup to use
   `add_subparsers()` with a `convert` subcommand taking `input`
   (positional, required) and `output` (positional, optional — CLAUDE.md's
   examples show `dottednotes convert input.brf output.ly`, not `-o`;
   decide whether to keep `-o/--output` too for backward compatibility
   with the current interface, or replace it, and note the choice in the
   PR).
2. Add `--compile` as a flag on the `convert` subcommand.
3. Add a top-level `--version` flag. Use
   `importlib.metadata.version("dottednotes")` (stdlib since Python 3.8)
   rather than reading `pyproject.toml` directly — the installed package
   won't have `pyproject.toml` sitting next to it in `site-packages`, so a
   file-path read only works from a source checkout, not from
   `pip install dottednotes`.
4. Replace `InputPipeline(args.input).read()` with
   `BRLInputPipeline().load(args.input)`. Then retire the `InputPipeline`
   class (`parser/input_pipeline.py`) entirely — grep confirms it has
   exactly one real caller (`cli.py`) plus its own three tests in
   `test_parser.py` (`test_input_pipeline_read`,
   `test_input_pipeline_lines`, `test_input_pipeline_missing_file`); delete
   those three and, if `.lines()`-style line splitting turns out to still
   be needed somewhere, add it to `BRLInputPipeline` instead of keeping
   two parallel, inconsistent input-loading classes around.
5. Fix the hand-sign/word-sign false positive described above: add
   `_line_has_word_sign(line)` and `has_ensemble_header(text)` to
   `ensemble_parser.py` (tokenizer-based, replacing the raw substring
   test), update `EnsembleParser.parse()`'s own `inst_lines` loop to call
   `_line_has_word_sign`, and have `cli.py` import and call
   `has_ensemble_header(text)` directly instead of maintaining its own
   copy of the detection loop.
6. Render via `Score.to_lilypond()` (post S7-1 — this ticket depends on
   S7-1 landing first, since it removes `LilypondRenderer`).
7. If `--compile` is set: resolve an output path (write to a temp `.ly`
   file if none was given — `--compile` without an output path can't work,
   since `lilypond` compiles a file, not stdin), then invoke `lilypond` via
   `subprocess.run([...], check=True)` — **pass the command as a list,
   never `shell=True`**, since the input filename is user-controlled.
8. Before invoking `subprocess.run`, check
   `shutil.which("lilypond") is not None` and fail with a clear plain-text
   message (ties into S7-3) rather than letting `subprocess` raise
   `FileNotFoundError` if the binary isn't installed.
9. Write CLI tests in `tests/test_cli.py` covering: `convert` with/without
   `output`, `--compile` (mocking or skipping actual `lilypond` invocation
   — see S7-5 for the real end-to-end version), `--version`, and — as
   regression tests for both bugs found in this ticket — converting
   `tests/fixtures/fengyang_flower_drum.brf` (ASCII-encoded, real BANA
   orchestral-score conventions) end to end and asserting the output
   actually contains multiple named staves (e.g. `instrumentName =
   "Flute"`), not just a bare `\version` line; and separately converting
   `tests/fixtures/fingering_melody.brf` (a real two-hand piano piece)
   end to end and asserting it is *not* misrouted to `EnsembleParser`
   (produces a two-staff `PianoStaff`, no `instrumentName` field).

**Definition of Done:**
- [x] CLI supports `convert <input> [output]` with the subcommand structure
- [x] CLI loads input via `BRLInputPipeline.load()`; `InputPipeline` and
      its now-redundant tests are removed
- [x] `dottednotes convert tests/fixtures/fengyang_flower_drum.brf`
      produces a real multi-staff orchestral score (flute, violin I,
      violin II, viola, cello, bass), not an empty `\version`-only file
- [x] `dottednotes convert tests/fixtures/fingering_melody.brf` succeeds
      via the solo parser (not misrouted to `EnsembleParser`)
- [x] `EnsembleParser.parse()` on hand-sign-only text (no genuine header)
      raises the clear `"No instrument list header found..."` message,
      not a downstream `"No parallel systems found..."` failure caused by
      a false-positive header match
- [x] CLI supports `--compile`, invoking `lilypond` via `subprocess.run`
      with an argument list (not a shell string)
- [x] CLI supports `--version`, sourced from installed package metadata,
      not a `pyproject.toml` file read
- [x] Missing `lilypond` binary produces a clear plain-text message instead
      of a raw `FileNotFoundError` traceback
- [x] `tests/test_cli.py` exists and covers the above, including both the
      Fengyang and fingering_melody regression cases
- [x] `tests/test_ensemble_parser.py` covers `has_ensemble_header` directly
      for both the genuine-header and hand-sign-false-positive cases

**Senior note:** Since `\score {}` already contains a `\midi {}` block
(S7-1), plain `lilypond file.ly` with no extra flags produces both the PDF
and the MIDI file in one invocation — resist the urge to add separate
`--pdf`/`--midi`-style flags or multiple `lilypond` invocations; that
complexity isn't needed here. Separately: both bugs found in this ticket
are a good example of why a silent empty-score fallback (and duplicated
detection logic) is dangerous for an accessibility tool specifically — a
sighted developer testing with a small hand-typed Unicode-braille snippet
(as most of this codebase's own tests do) would never have hit either
one, but a blind composer converting their actual BrailleNotetaker export
(ASCII-encoded, real BANA conventions, real two-hand piano hand signs)
would hit both. This is exactly the failure mode S7-3's error handling
should also make loud instead of silent. The duplication angle matters
too: the hand-sign bug existed identically in two places (`cli.py` and
`ensemble_parser.py`) because the same flawed check was copy-pasted rather
than shared — fixing it in only one place would have left the other
silently broken.

---

### [x] S7-3: Add error handling and meaningful plain-text error messages

**Why:** For accessibility, especially for blind composers using
VoiceOver, all error messages must be plain text and meaningful. Right now
nothing in the tokenizer/parser/CLI path raises a purpose-built exception —
a malformed file currently either produces silently wrong output (unknown
cells already degrade gracefully to `UNKNOWN` tokens, per S2-1) or an
unhandled Python exception with a full traceback dumped to the terminal.

**Steps:**
1. Create `src/dottednotes/exceptions.py` with a `DottedNotesError` base
   class and specific subclasses: at minimum `BrailleParseError`
   (parser-level failures) and `LilyPondCompileError` (wraps a
   non-zero-exit `lilypond` subprocess failure — captures its stderr).
2. Audit `braille_parser.py` and `ensemble_parser.py` for places that
   currently raise bare `ValueError`/`IndexError`/`KeyError` on malformed
   input (e.g. an unterminated in-accord, a missing time signature) and
   convert the ones reachable from real user input to `BrailleParseError`
   with the measure/line context already available on parser state. Don't
   convert exceptions that only fire on programmer error (e.g. an
   assertion that a fully-internal invariant holds) — those should keep
   failing loudly in development.
3. In `cli.py`'s `main()`, wrap the parse/render/compile calls in a
   `try/except DottedNotesError` (plus `OSError` for file-not-found) that
   prints a one-line plain-text message to `stderr` and exits with a
   non-zero status via `sys.exit(1)`.
4. Add unit tests feeding deliberately malformed `.brf` content through the
   CLI (via `capsys`-style invocation) and asserting on the `stderr`
   message text and exit code.

**Definition of Done:**
- [x] `exceptions.py` defines `DottedNotesError` and at least
      `BrailleParseError`, `LilyPondCompileError`
- [x] Parser-reachable failure paths raise these instead of bare built-in
      exceptions
- [x] CLI catches them and prints a single plain-text line to `stderr`, no
      traceback, non-zero exit code
- [x] Unit tests verify both the message and exit code for at least one
      parser failure and one missing-file case

**Senior note:** Don't wrap `main()`'s body in a bare `except Exception`.
That would silently swallow real bugs (a `TypeError` from a genuine coding
mistake would print as if it were a user-facing "your file is malformed"
message, actively hiding defects during development). Only catch the
specific exception types defined above, plus the narrow set of expected
`OSError` cases (file not found, permission denied).

---

### [x] S7-4: Add --verbose flag

**Why:** Diagnosing translation issues requires inspecting what the
tokenizer and parser actually did to a given input — right now the only
way to do that is to read source or drop into a debugger.

**Steps:**
1. Add `--verbose` to the `convert` subcommand.
2. Add tracing to `BrailleTokenizer`/`BrailleParser` (a simple list
   collected during the pass and returned/attached to the result is
   enough — avoid reaching for the `logging` module's global state here,
   since it doesn't compose well with capturing output in tests) covering:
   detected input encoding, each token's category and raw braille
   character, and any beat-count/validation warnings already raised via
   `warnings.warn` (S2-4 and later — these already exist; `--verbose` just
   needs to surface them clearly rather than relying on Python's default
   warning formatting).
3. Print the trace to `stderr`, one item per line, plain text.
4. Add unit tests that capture `stderr` (`capsys`) and check the trace
   contains expected token categories/warning text for a small fixture.

**Definition of Done:**
- [x] `--verbose` flag exists on `convert`
- [x] Tokenizer/parser trace and existing validation warnings are printed
      to `stderr` in plain text, one item per line
- [x] Unit tests verify verbose output content

**Senior note:** `stdout` and `stderr` are not interchangeable here: S7-2's
`convert` prints the rendered `.ly` to `stdout` when no output path is
given, and composers may pipe that (`dottednotes convert piece.brf |
lilypond -`). Any verbose trace that leaks onto `stdout` would silently
corrupt that piped LilyPond source. Everything from `--verbose` must go to
`stderr`, never `stdout` — same reasoning as the existing
`"Written to {path}"` message in today's `cli.py`, which already gets this
right.

---

### [x] S7-5: End-to-end test: .brf in, compiled PDF + MIDI out

**Why:** Every other test in the suite stops at the `Score`/string-of-
LilyPond level. Nothing currently proves that `dottednotes convert
--compile` actually produces a working PDF and MIDI via a real `lilypond`
invocation, which is the entire point of the tool per `CLAUDE.md`'s
workflow diagram.

**Steps:**
1. Implement `test_e2e_conversion` in `tests/test_cli.py`, using
   `tests/fixtures/fengyang_flower_drum.brf` — the one fixture `CLAUDE.md`
   calls out as developer-verified ground truth.
2. Invoke the CLI's `main()` (or the underlying convert function directly)
   with `--compile` against a `tmp_path` (pytest's built-in
   temp-directory fixture — don't write into `tests/fixtures/` itself; see
   the Senior note).
3. Guard the whole test with
   `@pytest.mark.skipif(shutil.which("lilypond") is None, reason="lilypond not installed")`
   so the suite still passes in environments (e.g. CI images) without the
   binary.
4. Pass `timeout=` to the underlying `subprocess.run` call (or wrap the
   test call site) — a hung or misbehaving `lilypond` process should fail
   the test after a bounded time, not hang CI indefinitely.
5. Assert the expected `.ly`, `.pdf`, and `.midi` files exist in the temp
   directory and are non-empty (`stat().st_size > 0` — a 0-byte PDF from a
   crashed compile is a common false-positive).

**Definition of Done:**
- [x] `test_e2e_conversion` parses a real fixture and produces a `.ly` file
      via the CLI
- [x] When `lilypond` is installed, the test additionally verifies
      non-empty `.pdf` and `.midi` output; the test is skipped (not
      failed) when it isn't
- [x] The subprocess call has a timeout, so a hung `lilypond` process fails
      the test rather than hanging the run
- [x] All output is written under pytest's `tmp_path`, never into
      `tests/fixtures/`

**Senior note:** This project's working tree has already accumulated real
`.pdf`/`.midi` files under `tests/fixtures/` from ad hoc manual
`--compile` runs (`fengyang_flower_drum.pdf`, `fingering_melody.pdf`,
etc.) — don't repeat that pattern here. Committed binary artifacts don't
belong in the fixtures directory (nothing else there is a compiled output;
every other fixture is a `.brf`/`.brl` input paired with a hand-authored
`.ly` ground truth at most). Write everything this test produces to
`tmp_path` and let pytest clean it up.

---

### [x] S7-6: Write user-facing README with installation and usage

**Why:** Composers using the tool need clear instructions on installation,
the external LilyPond dependency, and the actual CLI surface — which,
after S7-1 through S7-4, will have changed shape (subcommand instead of
flat positional, plus `--compile`/`--verbose`/`--version`).

**Steps:**
1. Update `README.md`'s usage section to match the final
   `convert`-subcommand CLI from S7-2, not the flat
   `dottednotes input.brf` interface it may still describe from before
   this sprint.
2. Document installing the `lilypond` binary itself on macOS (Homebrew),
   Windows, and Linux — this is a separate install from
   `pip install dottednotes` and easy to gloss over.
3. Show CLI examples for: default conversion (stdout), writing to a file,
   `--compile`, and `--verbose`.
4. Keep the accessibility-motivation section already present from S0-8 —
   extend it, don't duplicate it with a second "why accessibility matters"
   block.
5. Read the result back as plain text (no tables/ASCII diagrams that don't
   degrade well under a screen reader) before considering this done.

**Definition of Done:**
- [ ] `README.md` usage section matches the actual S7-2 CLI surface
      exactly (subcommand, flags, argument order)
- [ ] LilyPond binary installation is documented per-platform
- [ ] `convert`, `--compile`, `--verbose`, `--version` are each shown with
      an example
- [ ] No duplicate accessibility-motivation section (extends S0-8's,
      doesn't repeat it)

**Senior note:** Write this ticket last, after S7-1 through S7-5 actually
land — a README written against a planned interface tends to quietly
drift from what got built. If the CLI's final shape differs from what's
speculated in S7-2 (e.g. `-o/--output` kept instead of replaced), the
README must describe what actually shipped.

---

# Sprint 7b: LilyPond Formatting Library

Estimated time: 1.5–2 weeks.

**Why this sprint exists:** `Score.to_lilypond()` (post S7-1) is
functionally correct but visually generic — fixed margins, no distinction
between a solo piano piece and a full orchestral score, no rehearsal
marks, no evidence-based paper/spacing defaults. Sprint 7b's premise is to
derive formatting defaults from a corpus of real, high-quality engraved
LilyPond scores (the Mutopia Project, mutopiaproject.org, which
distributes public-domain sheet music with its LilyPond `.ly` source)
rather than guessing at "reasonable" spacing values.

**Before starting S7b-1:** confirm the Mutopia Project's terms of use
permit bulk/programmatic downloading of source files for this kind of
analysis (rather than one-off manual browsing), and rate-limit requests
either way. This sprint only needs the *statistical patterns* extracted
from the `.ly` source (header field usage, paper/margin values, spacing
numbers) — it does not need to redistribute or commit any of the
downloaded scores themselves into this repository, and shouldn't.

### [x] S7b-1: Download and analyze representative Mutopia scores for formatting patterns

**Why:** Tickets S7b-2 through S7b-6 need real numbers (margins, staff
spacing, common header fields) to build evidence-based defaults from,
rather than values invented from memory — the same "don't guess, verify"
principle CLAUDE.md applies to BANA dot patterns and LilyPond syntax
elsewhere in this project applies here too.

**Steps:**
1. Write a script (e.g. `scripts/analyze_mutopia_corpus.py`, not part of
   the installed package) that downloads a representative sample of
   Mutopia `.ly` source files, stratified across the instrumentation
   categories relevant to S7b-4's templates: solo piano, art song (voice +
   piano), chamber (string quartet or similar small ensemble), and
   orchestral. Aim for roughly even coverage across the four categories
   rather than skewing toward whichever category happens to be most
   numerous on the site.
2. For each downloaded score, extract (via simple text/regex extraction,
   not a full LilyPond parser): `\header` field names actually used,
   `\paper` block settings (paper size, margins), any `\layout`/spacing-
   related settings, and rehearsal-mark style (`\mark`, letter vs. number
   sequences).
3. Aggregate results into a summary (e.g. `docs/mutopia_analysis.md` or a
   structured JSON file under `docs/`) showing frequency/distribution per
   instrumentation category — this is the artifact S7b-2 and S7b-4
   consume.
4. Keep the downloaded `.ly` corpus itself out of version control (a local
   cache directory, gitignored) — only the extracted summary is committed.

**Definition of Done:**
- [x] Download/analysis script exists and is runnable independently of the
      main package
- [x] A representative, roughly-balanced sample across the four target
      instrumentation categories has been analyzed (document the actual
      count and category breakdown achieved — it does not need to hit an
      exact number if Mutopia's catalog doesn't support even coverage)
- [x] A committed summary artifact (not the raw corpus) captures
      header/paper/spacing/rehearsal-mark patterns per category
- [x] Mutopia's terms of use for bulk download were checked before running
      the script at scale

**Senior note:** Resist treating "50 scores" as a hard requirement handed
down from nowhere — it's a rough sample-size placeholder. What actually
matters for S7b-2 through S7b-6 is category coverage (having enough
orchestral examples to derive orchestral defaults, not just piano ones),
not hitting a specific total count.

### [x] S7b-2: Implement `LilyPondFormatter` class with evidence-based defaults

**Why:** Centralize the formatting decisions derived from S7b-1's analysis
into one class that S7b-3 through S7b-6 build on, rather than scattering
magic numbers across `Score.to_lilypond()`.

**Steps:**
1. Create `src/dottednotes/renderers/lilypond_formatter.py` with a
   `LilyPondFormatter` class holding the paper/margin/spacing defaults
   extracted in S7b-1, keyed by instrumentation category.
2. Give it a method that, given a `Score` (or an explicit category
   override), returns the formatting settings to apply — this is a pure
   data-selection step; actual `\paper`/`\layout` string generation
   belongs to S7b-5/S7b-6.
3. Cite the specific S7b-1 analysis numbers backing each default directly
   in a comment or docstring (traceability back to the evidence, not just
   the value).

**Definition of Done:**
- [x] `LilyPondFormatter` exists with defaults sourced from
      `docs/mutopia_analysis.md` (or equivalent), not invented values
- [x] Each default is traceable to the S7b-1 summary that justifies it
- [x] Unit tests cover default selection for at least one case per
      instrumentation category

### [x] S7b-3: Implement instrumentation detection and template selection

**Why:** `LilyPondFormatter` (S7b-2) needs to know which of the four
S7b-4 templates applies to a given `Score` without the caller specifying
it manually every time.

**Steps:**
1. Reuse the instrument-family grouping already implemented for S5b
   (`Score._group_by_family`, `models/instrument.py`'s
   `InstrumentFamily`) rather than re-deriving instrumentation logic from
   scratch.
2. Classify a `Score` into one of: solo piano (single `KEYBOARD_HARP`
   staff), art song (voice + piano — check whether the codebase has a
   voice/vocal staff concept yet; if not, flag that as a dependency this
   ticket surfaces rather than silently guessing), chamber (small
   `StaffGroup`, e.g. ≤6 staves of strings/winds), orchestral (larger
   multi-family `StaffGroup`).
3. Add a manual override parameter for the cases the heuristic gets wrong.

**Definition of Done:**
- [x] `Score` → template-category classification implemented, reusing
      existing `InstrumentFamily` grouping
- [x] Manual override supported
- [x] Unit tests cover all four categories plus at least one
      ambiguous/edge case

**Senior note:** If art-song detection turns out to need a vocal-staff
concept that doesn't exist yet in the domain model, don't invent one
silently inside this ticket — surface it back as a blocking dependency
rather than papering over it with a heuristic guess.

### [x] S7b-4: Curate 4 formatting templates from Mutopia examples

**Why:** Concrete, per-category presets (solo piano, art song, chamber,
orchestral) are what S7b-3's classification actually selects between.

**Steps:**
1. From the S7b-1 analysis, hand-select a small number of representative
   high-quality examples per category (not just the statistical average —
   engraving quality varies across Mutopia's corpus, so "representative"
   means typical of well-engraved scores in that category, confirmed by
   eye, not just whatever the script downloaded first).
2. For each of the 4 categories, define a template: paper size, margins,
   staff spacing, and any category-specific defaults (e.g. orchestral
   scores commonly use smaller staff size and instrument-name
   abbreviations after the first system — verify this against the actual
   S7b-1 sample rather than assuming).
3. Document the source examples each template was drawn from.

**Definition of Done:**
- [x] 4 templates defined (solo piano, art song, chamber, orchestral) with
      concrete paper/margin/spacing values
- [x] Each template cites the specific Mutopia example(s) it was derived
      from
- [x] Templates are consumable by `LilyPondFormatter` (S7b-2)

### [x] S7b-5: Implement page layout defaults (paper size, margins, system spacing) per template

**Why:** Translate S7b-4's curated template values into actual LilyPond
`\paper {}` block output.

**Steps:**
1. Fetch the LilyPond Notation Reference's "Page layout" chapter and
   confirm exact `\paper {}` field names (e.g. `paper-size`, margin field
   names) before writing generation code — don't guess the field names
   from general LilyPond familiarity.
2. Implement `\paper {}` block generation per template in
   `LilyPondFormatter`.
3. Support both A4 and Letter paper size, selectable independently of the
   instrumentation template (a US-based and a European composer using the
   same orchestral template shouldn't be forced into one paper size).

**Definition of Done:**
- [x] `\paper {}` generation implemented and verified against the
      Notation Reference's actual field syntax
- [x] A4/Letter selectable independently of template
- [x] Unit tests assert generated `\paper {}` content per template

### [x] S7b-6: Implement `\header` block generation with title, composer, copyright, and Mutopia-style tagline

**Why:** Extends S7-1's minimal `\header` (title/composer only) with the
fuller field set common in well-engraved scores, per the S7b-1 analysis of
which `\header` fields Mutopia scores actually use in practice.

**Steps:**
1. Extend `\header {}` generation (building on S7-1's implementation, not
   duplicating it) to optionally include `copyright` and a `tagline`.
2. Only emit fields that have a value — don't emit empty `copyright = ""`
   lines, matching the existing title/composer omission behavior from
   S7-1.
3. Escape embedded quote characters in all fields (same latent issue
   flagged in S7-1's Senior note — if S7-1 already added an escaping
   helper, reuse it rather than reimplementing it here).

**Definition of Done:**
- [x] `\header {}` supports title, composer, copyright, tagline, each
      optional
- [x] Field values are quote-escaped
- [x] Unit tests cover all-fields-present, some-fields-present, and
      no-fields-present cases

### [x] S7b-7: Integration test: generate a formatted score and verify it compiles to a professional-looking PDF

**Why:** Prove the formatting pipeline (S7b-2 through S7b-6) produces
LilyPond that actually compiles — the same "don't just check the string,
check it really works" principle as S7-5.

**Steps:**
1. Reuse S7-5's `shutil.which("lilypond")` skip-if pattern and `tmp_path`
   output convention — don't reinvent fixture/output handling this ticket
   already established.
2. Generate output for at least one fixture per template category (reuse
   existing fixtures — `fengyang_flower_drum.brf` for chamber/small-
   ensemble, `children_s_piece.brf` for solo piano, etc. — rather than
   authoring new ones unless no existing fixture fits a category).
3. Compile via `lilypond` and assert non-empty PDF output, same non-zero-
   byte check as S7-5.
4. "Professional-looking" isn't machine-checkable from a compiled PDF's
   bytes alone — treat this test as verifying successful compilation with
   the formatting applied (no LilyPond warnings/errors in the compile
   log), and pair it with a manual visual check of at least one generated
   PDF per category before closing this ticket.

**Definition of Done:**
- [x] Integration test compiles a formatted score per template category
      (skipped when `lilypond` isn't installed)
- [x] Compile log is checked for LilyPond-side warnings/errors, not just
      process exit code
- [x] At least one generated PDF per category has been manually visually
      reviewed (documented in the PR, not automated)

### [x] S7b-8: Document all formatting rules in docs/lilypond_conventions.md with source citations

**Why:** Every formatting default in this sprint was derived from evidence
(S7b-1's analysis), and that traceability needs to survive past the PR
that introduced it — future changes to a default should be checked
against the same evidence, not against whatever the code currently
happens to do.

**Steps:**
1. Write `docs/lilypond_conventions.md` documenting each default from
   S7b-2 through S7b-6, with a citation back to the specific Mutopia
   example(s) or S7b-1 analysis numbers that justified it (mirror
   `docs/bana_reference.md`'s role as a human-readable companion to
   `bana_symbols.py`).
2. Cross-link from `CLAUDE.md`'s project structure listing, the way
   `docs/bana_reference.md` already is.

**Definition of Done:**
- [x] `docs/lilypond_conventions.md` exists, covering every default
      introduced in S7b-2 through S7b-6
- [x] Each default cites its source evidence
- [x] Referenced from `CLAUDE.md`'s docs/ listing

---

### [x] S7b-9: Implement Vocal Support and Art Song Rendering

**Why:** The `LilyPondFormatter` layout templates include `"Art Song"` (voice +
piano), but the codebase currently lacks any domain concept or parsing rules
for vocals or lyrics. We need to introduce a vocal family/instrument category,
add parser/model support for lyrics and vocal parts, and verify this using a
real vocal test fixture.

**Steps:**
1. Add `VOCAL = "Vocal"` to `InstrumentFamily` in
   `src/dottednotes/models/instrument.py`.
2. Register common vocal parts (e.g., "Soprano", "Alto", "Tenor", "Bass",
   "Voice", "Vocal") in `_NAME_TO_FAMILY` in
   `src/dottednotes/models/instrument.py` mapping to `InstrumentFamily.VOCAL`.
3. Add a new test fixture `tests/fixtures/vocal_test.brf` containing a simple
   vocal line with lyrics and a piano accompaniment (art song format). Also add
   `tests/fixtures/vocal_test.ly` as the ground-truth LilyPond target.
4. Extend the parser (`BrailleParser` or a new vocal/lyrics parser module) to
   recognize literary braille lyric text cells in the BRF stream and attach them
   as lyric syllables/texts to the corresponding note elements.
5. Update `Staff` or `Score` rendering logic to format vocal staves with
   aligned `\addlyrics` blocks containing the parsed lyric syllables, and
   ensure the vocal staff is properly paired alongside the keyboard (or other
   instrumental) accompaniment in the generated LilyPond score context.
6. Write integration tests in `tests/test_vocal.py` ensuring that
   `vocal_test.brf` parses successfully, correctly groups vocal staves under
   `InstrumentFamily.VOCAL`, associates the lyrics with notes, and renders valid
   LilyPond code matching `vocal_test.ly`.

**Definition of Done:**
- [x] `InstrumentFamily.VOCAL` is added and integrated into instrument family
      matching
- [x] Vocal parts (Soprano, Alto, Tenor, Bass, Voice) are recognized as `VOCAL`
- [x] `vocal_test.brf` and `vocal_test.ly` fixtures are added to
      `tests/fixtures/`
- [x] Parser extracts lyrics from the braille stream and associates them with
      Note objects
- [x] `to_lilypond()` outputs `\addlyrics` blocks for vocal staves, correctly
      aligned and paired with the accompaniment staves
- [x] Integration tests verify the end-to-end translation of `vocal_test.brf`
      to the correct LilyPond art song structure

---

### [x] S7b-10: Command-Line Overrides for Formatting Options and Category via `--format` and `--category`

**Why:** While `LilyPondFormatter` heuristically detects the layout category and
applies high-quality defaults, users should be able to override these settings
directly from the command line. Specifying the category with `--category` (e.g.,
overriding an art song to chamber) also assists the braille parser in distinguishing
between braille lyrics and braille music once vocal scores are supported.

**Steps:**
1. Update `cli.py` to add a new command-line argument `--category` to the
   `convert` parser, accepting a string category (e.g., `Chamber`, `Art Song`,
   `Orchestral`, `Solo Piano`).
2. Update `cli.py` to add a new command-line argument `--format` to the
   `convert` parser, accepting a comma-separated list of key-value pairs (e.g.
   `--format "paper_size=a4,margin_mm=12,staff_size=18"`).
3. Write a helper function in `cli.py` or a utility module to parse the
   `--format` option string into a dictionary of formatting overrides (e.g.,
   `{"paper_size": "a4", "margin_mm": 12.0, "staff_size": 18.0}`). Support
   validation and type conversion for keys like `paper_size` (str), `margin_mm`
   (float), `staff_size` (float), `basic_distance` (float), and `padding`
   (float).
4. Update parser entrypoints (e.g. `_parse_score`) to accept the parsed
   `category` override, allowing the parser to use this information when
   distinguishing between braille lyrics and braille music.
5. Update `to_lilypond()` of `Score` and `OrchestraScore` to accept a category
   override and/or formatting overrides and apply them directly instead of
   or on top of the template defaults.
6. Integrate the `--category` and `--format` overrides in the CLI handler,
   passing them to the parser and the score rendering pipeline.
7. Write unit tests in `tests/test_cli.py` to verify that invalid `--category`
   or `--format` arguments raise appropriate error messages and that valid
   options are correctly parsed.
8. Write integration tests verifying that converting a BRF file with `--category
   Chamber` or `--format "paper_size=a4,margin_mm=10"` applies the overrides.

**Definition of Done:**
- [x] `--category` CLI option added to the `convert` command and documented in CLI help
- [x] `--format` CLI option added to the `convert` command and documented in CLI help
- [x] CLI passes `--category` override to the parser to assist in distinguishing braille lyrics and braille music
- [x] Key-value option parser handles correct type casting and warns/errors on unknown/invalid keys
- [x] `Score.to_lilypond()` and `OrchestraScore.to_lilypond()` apply category and format overrides
- [x] CLI tests cover valid and invalid category and format option strings
- [x] Integration tests verify compiled output has the specified category and custom paper settings/margins


---

### [x] S7b-11: Fix grace-note slur and hairpin-termination rendering bugs (found via S7b-7)

**Why:** S7b-7's integration test compiles `children_s_piece.brf` and checks
LilyPond's actual compile *log*, not just its exit code — and caught 4 real
warnings that every earlier test missed, because nothing before it looked
past a 0 exit code: three `warning: cannot end slur` and one
`warning: unterminated decrescendo`. `children_s_piece.brf` compiles
successfully despite these, so S7b-7 currently uses `fingering_melody.brf`
for its Solo Piano case instead (see that file's comments) — this ticket is
what unblocks switching it back, per the developer's request to compare the
current output against `Children_s_Piece.ly` (the hand-authored ground
truth) before assuming which side — the `.brf` transcription or the parser
— is wrong. That comparison is done below; it turns out to be two distinct
answers for two distinct bugs.

**Investigation (verified by tokenizing the exact raw `.brf` measures with
the real `BrailleTokenizer` — not by guessing BANA meanings):**

1. **Measures 11, 14, and 15 (right hand) — genuine parser bug.** Each
   measure's raw braille tokenizes as
   `ORNAMENT(grace) NOTE(grace pitch) SLUR NOTE(main note) ...` — a `SLUR`
   token really is present in the source, sitting between a grace note's
   pitch and the main note it decorates. `Children_s_Piece.ly` confirms
   this is meaningful: `\grace {c8(} b4)` (measure 11), `\grace {b'8(}
   a4\<)` (measure 14), `\grace {d8(} c4)` (measure 15) — a slur from the
   grace note into the main note, closed immediately. DottedNotes's output
   only ever emits the closing `)` on the main note; the grace note never
   gets the matching `(`.

   Root cause pinned down precisely: `Note.slur_start` and `GraceNote`
   (`models/note.py`, `models/ornament.py`) already fully support this —
   `GraceNote.to_lilypond()` just calls `to_lilypond()` on each contained
   `Note`, and a `Note` with `slur_start=True` already renders correctly
   elsewhere in this exact file (e.g. `f8( e8)` in measure 2). The gap is
   entirely in the parser: `_build_grace_note_cell()`
   (`braille_parser.py:934`) constructs the grace note's `Note` object but
   never sets `slur_start` on it, unlike the regular (non-grace) note path,
   which does exactly that (`pending[-1].slur_start = True` at
   `braille_parser.py:277` and `:669`) when a `SLUR` token is encountered
   in the right position. Grace notes go through a completely separate
   construction path that was never wired up to slur detection.

2. **Measure 10 (right hand) — looks like a real transcription gap, not a
   parser bug.** Tokenizing this measure's raw content produces
   `ORNAMENT NOTE INTERVAL NOTE INTERVAL ARTICULATION ARTICULATION NOTE
   INTERVAL INTERVAL NOTE NOTE ARTICULATION NOTE INTERVAL` — **no `SLUR`
   token anywhere**, even though `Children_s_Piece.ly` shows the identical
   grace-note-slur pattern here too (`\grace {a8(} g4\<)`). DottedNotes
   correctly renders no slur for this measure, because there genuinely is
   no slur cell in the `.brf` source to parse. Per `CLAUDE.md`'s "never
   guess dot patterns" rule, **do not add a slur cell to the fixture to
   make this match** — confirm with the developer first whether this is a
   real omission from the original braille transcription (worth fixing in
   the fixture) or an editorial addition made only in the hand-authored
   `.ly` reference (in which case the `.brf`, and DottedNotes's output for
   it, are both already correct, and it's `Children_s_Piece.ly` that's the
   outlier for this one measure).

3. **Measure 26 (right hand) — hairpin termination, a separate bug from
   both of the above.** The `DYNAMIC` word-sign block here opens a
   decrescendo (matching `Children_s_Piece.ly`'s `g8(\>`), but no cell
   anywhere in this measure or the next explicitly closes it. The ground
   truth closes it by hand with an explicit `\!` on the last note before
   the next dynamic marking (`\p`, measure 27) — standard defensive
   engraving practice. DottedNotes's renderer never emits a closing `\!`
   for any hairpin, so it's still open when LilyPond reaches the end of
   the piece. The same gap exists at measures 10 and 14's crescendo
   hairpins too (also missing `\!`) but doesn't trigger its own warning —
   LilyPond only flags the one hairpin still open at end-of-score.

**Steps:**
1. Confirm with the developer whether measure 10's missing slur cell is a
   transcription gap in `children_s_piece.brf` (check against the original
   BrailleNotetaker export if available) or an intentional `.ly`-only
   addition, before touching the fixture at all.
2. Fix `_build_grace_note_cell()` (`braille_parser.py:934`) to set
   `slur_start=True` on the grace note it builds when a `SLUR` token
   immediately follows the grace note's pitch cell — mirroring the
   existing `pending[-1].slur_start = True` pattern already used for
   regular notes.
3. Fix hairpin rendering so an open crescendo/decrescendo gets an explicit
   `\!` terminator emitted (end of the hairpin's phrase, or immediately
   before the next dynamic marking) instead of being left open
   indefinitely.
4. Once both are fixed, switch S7b-7's `test_formatted_solo_piano_score_compiles_cleanly`
   (`tests/test_lilypond_formatter.py`) back to `children_s_piece.brf`
   (removing the `fingering_melody.brf` workaround and its explanatory
   comment) and confirm zero LilyPond warnings in the compile log.
5. Extend `tests/test_parser.py`'s existing `test_children_s_piece_*`
   suite with a case asserting the exact slur/hairpin output at measures
   11, 14, 15, and 26 matches `Children_s_Piece.ly`'s ground truth, so this
   can't silently regress again.

**Definition of Done:**
- [x] Developer has confirmed whether measure 10's missing slur is a
      transcription gap or an intentional `.ly`-only addition, and the
      fixture (if wrong) or this ticket's scope (if not) updated accordingly
- [x] Grace notes immediately followed by a `SLUR` token render with the
      slur spanning grace-note-to-main-note, matching
      `Children_s_Piece.ly`'s `\grace {X8(} Y4)` pattern
- [x] Open crescendo/decrescendo hairpins get an explicit `\!` terminator
      in rendered output
- [x] `children_s_piece.brf` compiles via `lilypond` with zero warnings in
      the log (not just exit code 0)
- [x] S7b-7's Solo Piano integration test uses `children_s_piece.brf`
      again, matching that ticket's original suggestion, with no
      workaround needed
- [x] New regression tests lock in correct slur/hairpin output for the
      specific measures identified above

**Senior note:** The three "cannot end slur" warnings and the "unterminated
decrescendo" warning read like one bug because they share a fixture, but
they're two unrelated defects at different points in the pipeline (`SLUR`
token handling in grace-note construction vs. hairpin-close emission) —
fix and test them separately rather than assuming one fix resolves both.
Also don't skip step 1: measure 10 looks identical to measures 11/14/15 on
the surface (same grace-note-into-main-note shape in the ground truth
`.ly`), but the tokenizer evidence shows its `.brf` source is genuinely
different from the other three. Treating all four measures as "the same
bug" would be the wrong fix for measure 10 specifically.

---

# Sprint 8: Accessibility and Polish

Estimated time: 3–4 days.

**Why this sprint exists:** Sprints 0–7b built the conversion pipeline
itself; this sprint is about the two things that determine whether anyone
outside the developer can actually use or contribute to it — the CLI's
output has never had a dedicated accessibility pass since S7-3/S7-4 first
landed `--verbose` and centralized error handling, and the project has no
docs yet for a contributor who isn't Claude Code reading CLAUDE.md. S8-4 is
the one ticket in this sprint that is not a code change at all.

---

### [x] S8-1: Audit all CLI output for screen reader friendliness

**Why:** CLAUDE.md's Developer Context section is explicit — the developer
uses VoiceOver on Mac with VS Code, and "no progress bars, ASCII art, or
visual-only feedback" plus "all error messages must be plain text and
meaningful" are stated as hard requirements, not aspirations. `cli.py` has
grown several distinct output paths since S7-3/S7-4 (`--verbose`'s trace,
the plain conversion output, `--compile`'s confirmation line, every
`DottedNotesError`/`OSError` path in `main()`), and none of them have had a
dedicated accessibility pass — they were each written correct-by-intent
at the time, not verified under an actual screen reader.

**Steps:**
1. Catalog every `print(...)` call site in `cli.py`: the rendered `.ly`
   written to stdout, the `f"Written to {output_path}"` line, `--compile`'s
   `f"Compiled {output_basename}.pdf and {output_basename}.midi"` line,
   `--verbose`'s `f"Detected encoding: ..."` and per-token
   `f"Token: {token.category.name} {token.raw}"` lines in
   `_print_verbose_trace`, each `f"Warning: {w.message}"` line, and both
   `f"Error: {e}"` paths in `main()`.
2. Specifically review `main()`'s handling of `LilyPondCompileError.stderr`
   (the `if isinstance(e, LilyPondCompileError) and e.stderr: print(e.stderr,
   file=sys.stderr)` branch) — this is the one place DottedNotes passes
   through another program's raw output verbatim rather than composing its
   own message. LilyPond's own compiler diagnostics use source-location
   pointers (a caret under the offending column of a quoted source line),
   which is a visual-alignment convention that may not read sensibly under
   VoiceOver. Decide, with the developer, whether to pass it through as-is,
   summarize it, or reformat it into plain sentences.
3. Review `--verbose`'s per-token trace line for whether
   `token.raw` — a single raw Unicode braille character (U+2800–U+28FF) — is
   sufficient on its own, or whether it should also surface the numeric dot
   pattern (the same `dots: frozenset[int]` representation `BrailleSymbol`
   already carries internally) since that's the developer's native mental
   model for a braille cell, not the rendered glyph.
4. Note that `argparse`'s own `--help`/usage/error output (invalid
   arguments, `--version`) is generated by the standard library, not by
   DottedNotes's own code, and can't be reworded without a custom
   `HelpFormatter`. Confirm it's actually fine under VoiceOver rather than
   assuming so by default; if it isn't, that's a separate, larger fix and
   should be scoped as its own follow-up rather than folded silently into
   this ticket.
5. Have the developer run an actual VoiceOver pass over: a successful
   `convert` to stdout, `convert` with an output path, `--compile`,
   `--verbose`, and each error path (missing input file, malformed braille
   input, failed lilypond compile with `--compile`). A sighted contributor
   reading the text of a message cannot substitute for this — screen reader
   ergonomics (pacing, punctuation-driven pauses, how a message is announced
   mid-sentence) aren't reliably predictable by eye.
6. Fix whatever the pass turns up (e.g. reformatting the lilypond stderr
   passthrough, adding dot-pattern info to the verbose trace) and add or
   update tests in `tests/test_cli.py` asserting the plain-text shape of
   each fixed message so it can't silently regress.

**Definition of Done:**
- [x] Every stdout/stderr write site in `cli.py` is catalogued and reviewed
- [x] `LilyPondCompileError.stderr` passthrough reviewed and, if needed,
      reformatted so it doesn't rely on visual column alignment
- [x] `--verbose` token trace reviewed with the developer for whether raw
      braille glyphs alone are sufficient or need accompanying dot-number
      notation
- [x] `argparse`'s built-in `--help`/usage/error output confirmed acceptable
      under VoiceOver, or a follow-up ticket filed if not
- [x] Developer has run a VoiceOver pass over `convert`, `--compile`,
      `--verbose`, and all error paths and confirmed no screen-reader-hostile
      output remains
- [x] Any fixes made are covered by new or updated tests in `test_cli.py`

**Senior note:** Don't mark this done off a text-only review of the code.
The whole point of the ticket is that no one has verified these messages
under an actual screen reader yet — a sighted read-through of the f-strings
can confirm they're grammatically plain text, but not that they announce
well. Get the developer's own VoiceOver pass before checking off the last
item above.

---

### [x] S8-2: Write developer documentation

**Why:** CLAUDE.md is written to bootstrap a Claude Code session (it opens
with "read this file first," includes session-specific rules like "never
mark a ticket done yourself," and is structured as an operating manual for
an AI agent, not a codebase orientation doc). `docs/` currently only holds
reference material for the domain (`bana_reference.md`,
`lilypond_conventions.md`, `mutopia_analysis.md`) — there is nothing that
walks a new human contributor through how the pipeline fits together or how
to extend it. That gap blocks both S8-3's contributor onboarding and S8-4's
outreach: anyone who arrives from a submitted announcement and wants to
open a PR has nowhere to start.

**Steps:**
1. Create `docs/development.md` with an architecture walkthrough aimed at a
   human contributor: the `BRF/BRL → Internal Model → LilyPond` pipeline
   from CLAUDE.md's Architecture Overview, but explained with a short worked
   example (trace one real measure from raw braille cell through
   `BRLInputPipeline` → `BrailleTokenizer` → `BrailleParser` → a domain model
   object → `to_lilypond()`) rather than restating CLAUDE.md's reference
   tables verbatim.
2. Document how to add a new BANA symbol: where `bana_symbols.py`'s
   dot-pattern tables live, how a new `SymbolCategory` entry gets added, and
   restate CLAUDE.md's "never guess dot patterns — cite the Music Braille
   Code 2015 manual or ask" rule in a form aimed at someone who hasn't read
   CLAUDE.md.
3. Document how to add a new domain model class end to end: the
   `BrailleSymbol` base contract, the required `to_lilypond()` method,
   where it plugs into `braille_parser.py`, and which test files need a
   matching addition (`test_models.py` plus an integration-test fixture).
4. Document the testing conventions from CLAUDE.md's Testing Strategy
   section for a contributor audience, including the ASCII-vs-Unicode
   braille fixture gotcha (S7-2 — always load fixtures through
   `BRLInputPipeline`, never a raw file read) since that bug has already
   shipped once.
5. Cross-link to `docs/bana_reference.md` and `docs/lilypond_conventions.md`
   rather than duplicating their content.
6. Read the finished doc back as plain text — no ASCII-art diagrams or
   tables that degrade poorly under a screen reader — consistent with the
   project's accessibility bar applying to its own documentation, not just
   CLI output.
7. Add a link to `docs/development.md` from `README.md` for contributors
   who want the architecture, distinct from the install/usage instructions
   already there.

**Definition of Done:**
- [x] `docs/development.md` exists and covers the pipeline architecture (with
      a worked example), adding a BANA symbol, adding a domain model class,
      and the testing conventions
- [x] The ASCII/Unicode braille fixture gotcha (S7-2) is documented
- [x] No content is duplicated from `bana_reference.md` /
      `lilypond_conventions.md` — cross-linked instead
- [x] Doc reads as plain text with no diagrams/tables that don't degrade
      well under a screen reader
- [x] `README.md` links to `docs/development.md`

**Senior note:** Keep this separate from S8-3's `CONTRIBUTING.md` — this
ticket is "how the code works," S8-3 is "how to work with us as a
contributor," including the accessibility of the contribution process
itself. Don't merge them into one file; they serve different readers at
different points in the contribution flow.

---

### [x] S8-3: Add CONTRIBUTING.md with blind-contributor guidance

**Why:** DottedNotes exists specifically to serve blind composers, and per
CLAUDE.md the primary developer works via VoiceOver + VS Code +
BrailleNotetaker. A generic templated `CONTRIBUTING.md` would miss the
point — this project's own contribution process needs to hold itself to the
same accessibility bar S8-1 audits in the CLI, and should be genuinely
usable by blind contributors, not just written about them for a sighted
audience.

**Steps:**
1. Draft the standard sections: filing an issue, dev environment setup
   (link to `README.md`'s install steps plus `pytest`/dev dependencies),
   branch/PR conventions, and code style (referencing whatever linting/
   formatting config exists in `pyproject.toml`).
2. Add an "Accessibility of this codebase" section: any change touching CLI
   output, error messages, or documentation must stay screen-reader
   friendly — no ASCII art, no color/ANSI-only signaling, no tables that
   don't degrade to plain text — with S8-1's audit cited as the concrete bar
   new PRs are held to, not a restated abstract principle.
3. Add a dedicated section for blind/low-vision contributors: known-working
   tooling (VS Code + VoiceOver, since that's what the primary developer
   already uses), how to run `pytest` and read its output via a screen
   reader, and how to review a diff in a screen-reader-friendly way (`git
   diff` in a terminal vs. GitHub's web PR view, which is not uniformly
   accessible) — concrete tooling guidance, not generic advice.
4. Restate CLAUDE.md's BANA-accuracy rule (never guess dot patterns; cite
   the Music Braille Code 2015 manual; ask the developer if unsure) for
   external contributors, since they won't have read CLAUDE.md.
5. Have the developer review the draft specifically for whether the
   blind-contributor section is accurate and actually useful, not just
   well-intentioned — a sighted-written accessibility guide is exactly the
   kind of content that needs sign-off from someone who'll actually use it
   before it's published.
6. Link `CONTRIBUTING.md` from `README.md`.

**Definition of Done:**
- [x] `CONTRIBUTING.md` created at the repo root with issue/PR/dev-setup/
      code-style sections
- [x] "Accessibility of this codebase" section present, citing S8-1's audit
      as the concrete bar
- [x] Blind/low-vision-contributor section present with concrete tooling and
      workflow guidance
- [x] BANA dot-pattern accuracy rule documented for external contributors
- [x] Developer has reviewed and confirmed the blind-contributor guidance is
      accurate, not just well-intentioned
- [x] `README.md` links to `CONTRIBUTING.md`

**Senior note:** Don't ship this without the developer's sign-off in step 5.
Inaccurate accessibility guidance is worse than none — it can send another
blind contributor down a workflow that doesn't actually work, and they'd
have every reason to trust a project whose entire premise is accessibility.

---

### [x] S8-4: Submit to accessibility and music technology communities

**Why:** The tool has no users yet outside its own developer. This sprint's
title is "Accessibility and Polish," and the polish only matters once
someone outside the project can find it — this ticket is the one place in
the sprint that's outreach, not a code change, and it's the only Sprint 8
ticket whose action (a public post) can't be quietly reverted afterward.

**Steps:**
1. Compile a short candidate list of venues: blind/low-vision assistive-tech
   communities, music-notation-software communities (e.g. the LilyPond user
   list/forum), and accessibility-focused tech communities. This should be
   led by the developer's own existing contacts (e.g. from the Freedots
   project background noted in CLAUDE.md) rather than guessed at by whoever
   picks up the ticket — community norms and moderation expectations vary
   enough that an unfamiliar submitter can misjudge fit or come across as
   spam.
2. Draft a short, plain-text announcement: what DottedNotes does, the
   workflow it enables (braille → LilyPond → PDF/MIDI), current status and
   known limitations (link to TICKETS.md's sprint progress so expectations
   set by the post match what actually ships), and how to install and
   report issues.
3. Confirm `README.md` and `CONTRIBUTING.md` (S8-3) are in a postable state
   before any submission goes out — external readers will land there first,
   and a broken install doc undermines the announcement itself.
4. Have the developer review and explicitly approve both the exact
   announcement text and the venue list before anything is posted — this is
   a public, effectively irreversible action taken on the developer's
   behalf, not an internal code change, and needs sign-off up front rather
   than after the fact.
5. Post/submit per each venue's own norms (forum post, mailing list intro,
   issue tracker, etc.), keeping a record of where submissions went so
   follow-up questions have somewhere to be answered.
6. Track any resulting feedback, issues, or PRs and file them as follow-up
   tickets rather than trying to resolve them ad hoc as part of this one.

**Definition of Done:**
- [x] Candidate venue list compiled and confirmed by the developer, not
      guessed at
- [x] Announcement text drafted and explicitly approved by the developer
- [x] `README.md` and `CONTRIBUTING.md` confirmed postable before submission
- [x] Submissions made to the approved venue list
- [x] Resulting feedback/issues logged as follow-up tickets, not resolved
      inline mid-ticket

**Senior note:** This is the one ticket in the sprint that can't be
undone once done — a mailing list message or forum post can't be
unsent. Treat "I drafted it" as distinct from "I have permission to post
it": get explicit developer sign-off on both the wording and the venue
list before submitting anything, don't treat drafting as implied
authorization to publish.

---

### [x] S8-5: Raise exception when braille numeral repeats are encountered

**Why:** DottedNotes does not support BANA Section 19 braille numeral repeats due to their layout-specific nature, high parsing complexity (including octave and dynamic modifications, and cross-measure tie resolution), and explicit prohibition in ensemble scores (§33.4.3). Instead of silently ignoring or mis-parsing these symbols, the parser should raise a clear, plain-text error to guide the user.

**Steps:**
1. Identify the braille symbols and cell patterns used for BANA Section 19 numeral repeats (such as backward-numeral and measure-number repeats, typically involving lower-cell numbers).
2. Add tokenization/classification in `BrailleTokenizer` and `BrailleParser` for these numeral repeat indicators.
3. In `BrailleParser`, when a numeral repeat sequence is encountered, raise a descriptive `BrailleParseError` (e.g., "Braille numeral repeats (BANA §19) are not supported.").
4. Write unit tests in `tests/test_parser.py` with mock input containing numeral repeats to assert that they correctly raise `BrailleParseError` with the expected error message.

**Definition of Done:**
- [x] Numeral repeat symbols are detected during parsing.
- [x] `BrailleParseError` is raised with a meaningful message when numeral repeats are encountered.
- [x] Unit tests verify the exception behavior on numeral repeat inputs.

---

### [x] S8-6: Add `--measure-numbers` CLI option to emit measure-number comments in LilyPond output

**Why:** Generated `.ly` files can run to hundreds of lines with no landmarks, which makes them slow to navigate with a screen reader once something needs fixing by hand (e.g. cross-referencing a `_validate_measure_beat_count` warning like "Measure 31: expected 4 beats but counted 3" back to the actual line in the output). A `% <number>` comment before each measure's line turns that into a direct search target. Developer-requested, in the spirit of S8-1's screen-reader-friendliness audit.

**Steps:**
1. Add a `--measure-numbers` boolean flag (`store_true`, alongside the existing `--compile`/`--verbose` flags) to the `convert` subcommand in `cli.py`, documented in `--help`.
2. Thread a `measure_numbers: bool = False` parameter through `Score.to_lilypond()`, `OrchestraScore.to_lilypond()`, and `Staff.to_lilypond()`, defaulting to off everywhere so every existing `assert ly_output == ground_truth` fixture test (`fengyang_flower_drum.ly`, `vocal_test.ly`, `lead_sheet_test.ly`, etc.) is unaffected unless the flag is explicitly passed.
3. In `Staff.to_lilypond()`'s `measure_lines` assembly loop, when the flag is on, prefix each emitted line with `% N` using the real `Measure.number` already tracked from parsing (`measure.number`, set via `_handle_measure_number`/`_next_measure_number_for` in `braille_parser.py`) — not a freshly-enumerated count — so the comment matches the actual BANA margin number from the source, including non-sequential cases like a `0`-numbered pickup measure.
4. Handle the rest-run consolidation case: consecutive whole-measure rests are already merged onto a single line (the `run`/lookahead loop earlier in `Staff.to_lilypond()`), so a consolidated line spanning measures 12–15 needs a comment reflecting that range (e.g. `% 12-15`), not just the first measure's number.
5. Decide (with the developer) whether lead-sheet `ChordNames` output (`chord_names.py`) also gets measure comments, since it renders on a separate track from the melody staff it's aligned to — out of scope if it turns out not to align cleanly.
6. Write unit tests covering: a simple multi-measure staff with the flag on/off, a consolidated rest-run line producing a range comment, and a pickup/non-sequential-numbered fixture (e.g. reusing `lead_sheet_test.brf`'s measure-0 pickup) to confirm the real margin number is used, not a synthetic recount.
7. Write a CLI integration test converting an existing fixture with `--measure-numbers` and asserting the expected `% N` comments appear at the right lines.

**Definition of Done:**
- [x] `--measure-numbers` CLI option added to the `convert` command and documented in `--help`.
- [x] Default behavior (flag omitted) is byte-identical to current output — no existing ground-truth fixture test needs updating.
- [x] With the flag on, each measure line is preceded by a `% N` comment using the real parsed margin number, and consolidated rest-run lines show a range.
- [x] Unit and CLI integration tests pass.

---

# Sprint 8b: Advanced Braille Parsing Features

Estimated time: 1.5–2 weeks.

**Research basis for this sprint:** Before starting, review the BANA Music Braille Code 2015 tables (Tables 21, 22, 23, 24, 25, 29, 30, 31, 33) and the LilyPond Notation Reference (for pitches, rhythms, expressive marks, vocal music, chord mode, piano pedaling, and string articulations).

---

### [x] S8b-1: Implement parsing for the Breve (Double Whole Note/Rest)

**Why:** To support early music, classical transcriptions, and choral works that contain double whole notes and double whole rests (breve). DottedNotes' `Duration` model currently only supports durations from whole note (1) down to 128th note.

**Steps:**
1. Identify the braille representation for a breve note and rest in BANA (typically involves the whole note cell preceded by a duration/breve sign).
2. Update `src/dottednotes/models/duration.py` to support `breve` (or value 0.5/whole-note factor 2) or custom breve indicator in the duration class.
3. Update `src/dottednotes/parser/tokenizer.py` and `braille_parser.py` to tokenize and parse the breve symbols for both notes and rests.
4. Update `Note.to_lilypond()` and `Rest.to_lilypond()` to serialize to LilyPond's `\breve` and `R\breve` (or `r\breve`).
5. Write unit tests in `tests/test_models.py` and `tests/test_parser.py` for breve notes and rests.

**Definition of Done:**
- [x] Breve note cell sequences are successfully tokenized and parsed.
- [x] LilyPond output correctly renders `\breve` and `R\breve`.
- [x] Unit tests verify parsing and LilyPond rendering of breves.

---

### [x] S8b-2: Implement parsing for string bowing signs (Up-bow/Down-bow)

**Why:** Bowing signs (down-bow and up-bow) are critical for string instrument execution in chamber and orchestral music. DottedNotes supports multi-staff scores and string instruments, so parsing these symbols is a high priority.

**Steps:**
1. Add definitions for down-bow (`⠣⠃`) and up-bow (`⠣⠄`) signs to `src/dottednotes/bana_symbols.py`.
2. Update the tokenizer to classify bowing signs as articulations or a custom bowing category.
3. Update `BrailleParser` to parse bowing signs immediately preceding a note or chord, appending them to the note's articulations list.
4. Support doubled bowing signs (where a sign is doubled to indicate it continues).
5. Update `Note.to_lilypond()` and `Chord.to_lilypond()` to serialize these to LilyPond's `\downbow` and `\upbow`.
6. Write unit tests in `tests/test_parser.py` and a dedicated integration test.

**Definition of Done:**
- [x] Up-bow and down-bow symbols are parsed correctly.
- [x] Bowing marks are rendered as `\upbow` and `\downbow` in LilyPond.
- [x] Unit tests verify single and doubled bowing marks.

---

### [x] S8b-3: Implement parsing for damper/sustain pedal signs

**Why:** Sustain pedal down/release commands are essential for piano and keyboard scores. Without them, translated keyboard scores lack pedal engraving, which is standard in printed music.

**Steps:**
1. Identify the BANA sustain pedal down/release symbols (commonly involving `⠣⠉` and `⠡⠉` or similar cell patterns).
2. Create a `Pedal` model or add pedal fields to measure/notes.
3. Update `BrailleParser` to parse pedal down and pedal release symbols. Pedal down typically precedes a note; pedal release follows a note.
4. Update LilyPond serialization to output `\sustainOn` and `\sustainOff` at correct places.
5. Write unit tests in `tests/test_parser.py` and verify formatting in a piano-style score.

**Definition of Done:**
- [x] Sustain pedal down and release symbols are parsed successfully.
- [x] LilyPond compiles with correct `\sustainOn` and `\sustainOff` markings.
- [x] Unit tests verify the pedaling state and output format.

---

### [x] S8b-4: Support chord ties and doubled interval shorthand

**Why:** Real keyboard music and contrapuntal string music contain complex chord shapes with ties and interval doublings. Currently, the parser only handles simple single-note ties or individual in-accords.

**Steps:**
1. Update `Chord` and `Note` models to support ties for individual chord members (chord ties, e.g., `<c e g> ~ <c e g>`).
2. Implement parsing for doubled intervals (BANA Table 31 shorthand where an interval sign is doubled to mean "continue this interval for subsequent notes").
3. Update `BrailleParser` to track doubled interval state and apply it to subsequent notes until terminated.
4. Ensure `to_lilypond()` on `Chord` correctly places the tie symbol `~` within or after chord brackets as appropriate.
5. Add tests in `tests/test_parser.py` asserting doubled intervals expand correctly.

**Definition of Done:**
- [ ] Doubled intervals are correctly parsed and expanded to standard chords.
- [ ] Chord ties serialize correctly to LilyPond syntax.
- [ ] Unit tests pass.

---

### [x] S8b-5: Implement parsing for chord symbols (Lead Sheets)

**Why:** Many popular songs, hymnals, and jazz lead sheets feature chord symbols (e.g. C, G7, Am) written above or inline with the melody. Parsing these allows DottedNotes to support popular lead sheets.

**Steps:**
1. Define the braille symbols for chord facsimile symbols in `bana_symbols.py` (BANA Table 23).
2. Implement a parser component or staff layout that detects a chord symbols track/line.
3. Convert these symbols to LilyPond's `\chordmode` block, rendering them as a `ChordNames` staff above the melody.
4. Write tests in `tests/test_parser.py` verifying melody + chord symbol alignment.

**Definition of Done:**
- [x] Chord symbol signs are parsed into a dedicated `ChordNames` structure.
- [x] LilyPond output contains a working `\new ChordNames \chordmode { ... }` track.
- [x] Tests verify correct alignment and parsing of chords like maj, min, 7th, and dim.

---

### [x] S8b-6: Implement parsing for glissandi and wind mute signs

**Why:** Glissandi and mute signs are common expressive markings for brass, woodwinds, and strings.

**Steps:**
1. Identify glissando and wind mute signs in BANA (Chapter 21 / Table 30).
2. Update the tokenizer and parser to parse glissando indicators between notes, and mute/unmute indicators.
3. Render glissandi as `\glissando` in LilyPond.
4. Render mutes as text markups (e.g., `^"mute"` / `^"con sord."`) or appropriate LilyPond mute articulations.
5. Write unit tests for both features.

**Definition of Done:**
- [x] Glissandi and wind mute signs are parsed and represented in the model.
- [x] LilyPond output contains correct `\glissando` and mute markups.
- [x] Tests verify correct output.

---

### [Won't Do] S8b-7: Support Section-by-Section (Paragraph) format parsing

**Why not:** Section-by-Section (paragraph) format is historical and no longer recommended by BANA. Not supporting it.

<details>
<summary>Original ticket text</summary>

**Why:** BANA Chapter 33 allows music to be formatted in paragraph-style sequential blocks (Section-by-Section) instead of line-by-line parallel systems. Supporting this format allows parsing of older keyboard or vocal scores that use paragraph layouts.

**Steps:**
1. Implement a format detector in `EnsembleParser` to distinguish Section-by-Section format from parallel systems.
2. In Section-by-Section format, parse sequential paragraphs (blocks of measures) for each voice/part and concatenate them under the correct staff.
3. Wire the parsed sequential parts back to the unified `Score` model.
4. Write unit tests using section-by-section mock BRF files.

**Definition of Done:**
- [ ] The parser auto-detects and successfully parses Section-by-Section formatted files.
- [ ] Unified `Score` objects are constructed correctly from paragraph blocks.
- [ ] Unit tests cover multiple staves in paragraph layout.

</details>

---

### [x] S8b-8: Support strophic songs and multi-verse vocal formats

**Why:** Vocal music (hymns, folk songs) frequently features multiple verses of lyrics under the same melody, or strophic structures. Currently, the lyric parser does not align multiple verses or handle refrain markings.

**Steps:**
1. Extend `EnsembleParser` / `BrailleParser` to parse multiple lyric lines (verses) associated with a single music line (BANA Chapter 26).
2. Parse verse numbers and handle refrains.
3. Map each verse's syllables to the same note sequence in the model.
4. Update the LilyPond generator to output multiple `\new Lyrics \lyricsto ...` blocks.
5. Write integration tests for multi-verse vocal scores.

**Definition of Done:**
- [x] Multiple verses of lyrics are parsed and aligned to a single melody.
- [x] LilyPond output renders multiple verse lines cleanly under the music.
- [x] Integration tests pass.

---

### [x] S8b-9: Compose a lead-sheet test fixture + real-compile integration tests

**Why:** S8b-5 (lead-sheet chord symbols) only has unit- and parser-level tests today — string-equality checks in `test_chord_symbols.py` on isolated chord-symbol lines, never a full hand-authored `.brf` run through the real `lilypond` binary. This can't be folded into a combined fixture with the other S8b features (see S8b-10): a lead sheet is structurally just a melody line paired with a chord-symbol line (BANA Sec. 27's two-line parallel, `parse_lead_sheet()`), invoked via its own explicit code path (`--category "Lead Sheet"`, not the ensemble/solo parser) — there's no staff to hang bowing, pedal, breve, or glissando/mute off of in that format, so it needs its own fixture rather than a section of a larger one.

**Fixture requirements** (developer-authored `.brf`, added to `tests/fixtures/` with an entry in `tests/fixtures/README.md` per the existing table format):
1. Strict melody/chords two-line alternation starting at physical line 0, per `parse_lead_sheet()`'s documented scope (no header lines, single non-ensemble melody staff).
2. Chord symbols covering, at minimum, maj, min, 7th, and dim (per existing `test_chord_symbols.py` coverage) plus at least one slash/bass-note chord (e.g. `G/D`), so the fixture exercises more than the simplest case.
3. Enough melody notes/measures for the chord symbols to align meaningfully above more than one segment.
4. Developer provides (or confirms, if drafted first) the hand-authored ground-truth `.ly` output, same as `fengyang_flower_drum.brf`.

**Planned integration tests** (new file, e.g. `tests/test_lead_sheet_integration.py`), to be written once the fixture text and ground truth are confirmed:
- `test_lead_sheet_fixture_parses_without_warnings` — `parse_lead_sheet()` end to end, asserts no validation warnings.
- `test_lead_sheet_fixture_matches_ground_truth_ly` — compares generated `to_lilypond()` output against the confirmed ground-truth `.ly`.
- `test_lead_sheet_fixture_compiles_cleanly` — reuses the `shutil.which("lilypond")` skip-if guard and the `_compile_and_check_no_warnings` helper (or an equivalent local copy) to run the real `lilypond` binary and assert a clean log, not just exit code 0.
- `test_cli_convert_lead_sheet_fixture_end_to_end` — drives the fixture through the actual CLI entry point (`dottednotes convert fixture.brf --category "Lead Sheet"`), complementing the existing inline-string CLI test (`test_cli.py::test_cli_convert_lead_sheet_category_routes_to_lead_sheet_parser`) with a real file and ground truth.

**Definition of Done:**
- [x] Fixture `.brf` composed and added to `tests/fixtures/`, with a `tests/fixtures/README.md` entry.
- [x] Ground-truth `.ly` output confirmed by the developer.
- [ ] `tests/test_lead_sheet_integration.py` written with the four tests above, all passing (compile test skips gracefully if `lilypond` isn't installed, per existing convention).

---

### [x] S8b-10: Compose a combined test fixture for breve/bowing/pedal/chord-tie/glissando/mute + real-compile integration tests

**Why:** S8b-1 through S8b-4 and S8b-6 (breve, bowing, sustain pedal, chord ties, glissando/mute) each have unit- and parser-level tests only — string-equality checks on `to_lilypond()` output. None of them are exercised together in one real, hand-authored `.brf` the way `fengyang_flower_drum.brf` anchors earlier sprints, and none are run through the real `lilypond` binary and checked for a clean compile log (the `_compile_and_check_no_warnings` pattern already established in `test_lilypond_formatter.py` and `test_vocal.py`). A feature can pass every existing test and still emit LilyPond that's syntactically wrong in combination with another feature (e.g. a glissando spanning a pedal marking, or a chord tie on a bowed chord) — nothing today would catch that. Lead-sheet chord symbols (S8b-5) are covered by their own fixture instead (S8b-9) since that format can't host these staff-based features. S8b-8 (strophic/multi-verse) is also excluded from this fixture's scope since it's still in progress as of this writing; fold it in (or add a further fixture) once it lands.

**Fixture requirements** (developer-authored, single or small set of `.brf` files, added to `tests/fixtures/` with an entry in `tests/fixtures/README.md` per the existing table format):
1. **Breve** (S8b-1): at least one breve note and one breve rest.
2. **Bowing** (S8b-2): both up-bow and down-bow marks, including at least one doubled (carried) bowing sign across 3+ notes, on a string instrument part.
3. **Sustain pedal** (S8b-3): a pedal-down/release pair, plus one pedal "change" (release+depress on the same note) on a piano part.
4. **Chord ties + doubled intervals** (S8b-4): at least one tied chord pair, one doubled chord-tie carry across 3+ chords, and one doubled-interval (octave or other) carry — including a case where a chord tie occurs *inside* an active interval-doubling carry (mirrors `test_chord_tie_does_not_interrupt_interval_doubling_carry`).
5. **Glissando + mute/open** (S8b-6): a glissando between two notes, and a stopped/open pair on a wind or string part — ideally the same instrument used for bowing, since `⠣⠃` is instrument-family-dependent (bow vs. mute) and a combined fixture should confirm both readings resolve correctly from real context rather than an isolated synthetic snippet.
6. Multi-staff/multi-instrument (at least piano + one bowed string + one wind), so bowing, mute, and pedal each land on the instrument family they're valid for.
7. Developer provides (or confirms, if drafted first) the hand-authored ground-truth `.ly` output, same as `fengyang_flower_drum.brf` — this is what makes it a real integration fixture rather than another synthetic snippet.

**Planned integration tests** (new file, e.g. `tests/test_sprint8b_integration.py`), to be written once the fixture text and ground truth are confirmed:
- `test_sprint8b_fixture_parses_without_warnings` — parses the fixture end to end, asserts no beat-count/validation warnings are raised.
- `test_sprint8b_fixture_matches_ground_truth_ly` — compares generated `to_lilypond()` output against the confirmed ground-truth `.ly` (same pattern as `test_children_s_piece` / `fengyang_flower_drum` ground-truth tests).
- `test_sprint8b_fixture_compiles_cleanly` — reuses the `shutil.which("lilypond")` skip-if guard and the `_compile_and_check_no_warnings` helper (or an equivalent local copy) to run the real `lilypond` binary and assert a clean log, not just exit code 0.
- `test_sprint8b_fixture_renders_expected_markup` — asserts the compiled `.ly` text contains each feature's expected LilyPond token at least once (`\breve`, `\downbow`/`\upbow`, `\sustainOn`/`\sustainOff`, chord tie `~` inside `<...>`, `\glissando`, `\stopped`/`\open`) so a future regression that silently drops one feature while the others still compile is caught.

**Definition of Done:**
- [x] Fixture `.brf` file(s) composed and added to `tests/fixtures/`, with a `tests/fixtures/README.md` entry.
- [x] Ground-truth `.ly` output confirmed by the developer.
- [x] `tests/test_sprint8b_integration.py` written with the four tests above, all passing (compile test skips gracefully if `lilypond` isn't installed, per existing convention).

---

### [x] S8b-11: Compose a strophic/multi-verse vocal test fixture + real-compile integration tests

**Why:** S8b-8 (strophic songs and multi-verse vocal formats) only has synthetic inline-string tests today — `test_parse_strophic_multiverse_lyrics_and_refrain` and `test_parse_strophic_with_word_number_verse_prefixes` in `test_vocal.py` construct minimal hand-built BRF strings and assert on `staff.verses`/`staff.verse_prefixes` and substring checks against `to_lilypond()` output. Neither is a real hand-authored `.brf` run through the real `lilypond` binary and checked for a clean compile log (the `_compile_and_check_no_warnings` pattern already established in `test_lilypond_formatter.py`, `test_vocal.py`'s own `vocal_test.brf` tests, and `test_lead_sheet_integration.py`). `vocal_test.brf` (the existing S7b-9 fixture) is single-verse and doesn't exercise multiple verses, verse-number prefixes, or refrain replication at all. S8b-10's own ticket text excluded strophic/multi-verse from its fixture's scope pending S8b-8 landing (3146a03) — it's landed now, so it's time to fold it in with its own fixture, the same way S8b-9 did for lead sheets.

**Fixture requirements** (developer-authored `.brf`, added to `tests/fixtures/` with an entry in `tests/fixtures/README.md` per the existing table format):
1. At least 2 verses of lyrics on the same melody, each with a verse-number prefix. The parser accepts two prefix styles — bracketed (`⠶⠼⠁⠶`, per `test_parse_strophic_multiverse_lyrics_and_refrain`) and plain (`⠼⠁`, per `test_parse_strophic_with_word_number_verse_prefixes`). Pick one as the fixture's primary style (testing both in one fixture would be artificial) and note which in the README entry.
2. A refrain: a system with an unprefixed lyric line following the verse systems, which must replicate across every verse's stanza (`staff.verses[n]` ends with the same refrain syllables for every verse) — the behavior already covered by the existing unit test, but not yet by a real fixture.
3. At least one syllabic slur (the "flo --" hyphenation-continuation case already exercised in `vocal_test.brf`), so this fixture isn't narrower in coverage than the single-verse fixture it's meant to complement.
4. An accompaniment part (e.g. piano, as in `vocal_test.brf`), so the fixture confirms verse/refrain stacking coexists correctly with a non-lyric staff, not just a solo vocal line.
5. Developer provides (or confirms, if drafted first) the hand-authored ground-truth `.ly` output, same as `vocal_test.ly`.

**Planned integration tests** (new file, e.g. `tests/test_strophic_integration.py`, or alongside the existing strophic unit tests in `test_vocal.py` — developer's call), to be written once the fixture text and ground truth are confirmed:
- `test_strophic_fixture_parses_without_warnings` — parses the fixture end to end, asserts no beat-count/validation warnings are raised.
- `test_strophic_fixture_verses_and_refrain_match_expected` — asserts `staff.verses`, `staff.verse_prefixes`, and refrain replication against the confirmed values (mirrors the assertions in `test_parse_strophic_multiverse_lyrics_and_refrain`, but against the real fixture instead of an inline string).
- `test_strophic_fixture_matches_ground_truth_ly` — compares generated `to_lilypond()` output against the confirmed ground-truth `.ly`, including `\set stanza = "N. "` markup and one `\new Lyrics \lyricsto` block per verse.
- `test_strophic_fixture_compiles_cleanly` — reuses the `shutil.which("lilypond")` skip-if guard and the `_compile_and_check_no_warnings` helper (or an equivalent local copy) to run the real `lilypond` binary and assert a clean log, not just exit code 0.

**Definition of Done:**
- [x] Fixture `.brf` composed and added to `tests/fixtures/`, with a `tests/fixtures/README.md` entry.
- [x] Ground-truth `.ly` output confirmed by the developer.
- [x] Integration tests written with the four tests above, all passing (compile test skips gracefully if `lilypond` isn't installed, per existing convention).

---

### [x] S8b-12: Fix octave resolution for unmarked notes to follow BANA Sec. 3.2.2's melodic-interval rule (found via S8b-10)

**Why:** While composing the S8b-10 fixture, an unmarked chord base note (`⠺`/B, following a `⠹`/C base note with no intervening octave mark) resolved to the wrong octave — B4 instead of B3 — producing a wrong pitch and, in one case, an "unterminated tie" warning on real `lilypond` compile. Tracing this in `braille_parser.py` shows the parser's octave handling for unmarked notes is a simple sticky counter: `_current_octave` is set only by explicit octave-mark cells (`_handle_octave_mark`) and otherwise reused as-is for whatever note letter comes next (see `test_octave_persists_without_mark`, which names and asserts exactly this behavior: `⠐⠹⠱` → C4, D4, "octave persists"). That happens to be correct for ascending/small stepwise motion within an octave, but it is not the actual BANA rule, and it silently produces wrong pitches whenever sticking to the same octave number would put the new note a fourth or more away from the previous one in the wrong direction — exactly the C4→B case here, where the intended reading (no mark needed) is the *nearest* B, a 2nd below (B3), not a major 7th above (B4).

The real rule, confirmed against the manual (`Music_Braille_Code_2015.pdf`, **Sec. 3.2.2, "Need Determined by Melodic Interval"**):
> (a) the octave is not marked for the second of two consecutive notes if the interval is less than a fourth, (b) the octave is always marked in a skip greater than a fifth, and (c) the octave is only marked in a skip of a fourth or fifth when the second note is in a different octave from the first.

In other words: an omitted mark is itself information — it asserts the interval is less than a fourth, so the correct octave is whichever one satisfies that, not "whatever octave we were last sitting at." The same bug affects chord base notes identically (confirmed on a second, adjacent chord in the same fixture measure); it happened not to produce a compile warning there only because the chord's other tones still matched the next chord's tones, masking it — meaning the wrong pitch can pass silently with no warning at all, not just when it happens to break a tie.

Sprint 9b's `BANAValidator` (S9b-3) independently flags the same category of issue as a warning for the composer to fix in their own `.brf` source (`Missing octave mark` / `Redundant octave mark` corrections). That is a complementary, not competing, mechanism: S9b-3 is aimed at helping a composer improve their *source* braille, while this ticket is about the parser producing the *correct pitch* even when the source is ambiguous or the composer hasn't gone back to add the mark yet. Since the parser now resolves unmarked notes correctly per the rule below, `BANAValidator._validate_octave_marks` no longer needs (or is able) to detect a "missing mark, interval of 6th+" or "missing mark, interval of 4th/5th crossing octaves" situation from the resolved pitches — those corrections are removed from `validator.py`; only "redundant explicit mark" corrections remain meaningful, since the parser always trusts an explicit mark at face value rather than second-guessing it.

**Steps:**
1. Implement a nearest-octave resolution for unmarked notes per Sec. 3.2.2(a): given the previous *sounding* note's absolute pitch and the new note's letter (no mark present), choose the candidate octave (current, current − 1, or current + 1) that puts the melodic interval below a fourth.
2. Handle the boundary case in Sec. 3.2.2(b)/(c): a skip of a fourth or fifth is only valid without a mark if it stays within the *same* octave as the previous note. Since there are only 7 diatonic letters, the signed difference between the new and previous note's letters fully determines which of (a)/(b)/(c) applies — there is no leftover "can't resolve" case that needs a raise/warn fallback.
3. Apply the fix at both call sites that currently read `_current_octave` directly for note construction (plain single notes and chord base notes) — confirm the "previous sounding note" used for the interval calculation is correct in both the piano-hand-switching case (`_octave_by_hand`) and the interval-doubling-carry case (`_interval_octave_override`), not just the simple single-voice case.
4. In-accord voices need their own handling: BANA reads octave continuity from the primary (first-written) voice, not whichever voice was written last, so `_finalize_measure` must restore the primary voice's ending octave once an in-accord group closes (confirmed against `Children_s_Piece.ly`'s real, hand-verified octaves, cross-checked via `lilypond`'s own `\displayLilyMusic`/MIDI output). Additionally, the first note of a *new* in-accord voice (voice 2, 3, ...) is not "consecutive" with the previous voice's last note in Sec. 3.2.2's sense, so it must not go through the melodic-interval computation at all — it simply keeps whatever octave number was last set.
5. Revisit `test_octave_persists_without_mark` — it will still pass under a correct implementation (C→D is under a fourth either way), but its name/comment currently reads as documentation of "always sticky," which is misleading; update the comment to reflect the real rule.
6. Add unit tests for the case that surfaced this bug: an unmarked note whose letter, kept at the same octave, would be a fourth or more away in the wrong direction (descending C→B and the symmetric ascending B→C case), for both plain notes and chord base notes.
7. Re-run the full suite to confirm no existing fixture/ground-truth `.ly` regresses — several existing fixtures likely have unmarked passages that happen to work under the old sticky logic and must still resolve to the same pitches under the corrected one. (`children_s_piece.brf`'s hand-authored ground truth, `instrumental_techniques_test.brf`, and the in-accord unit tests in `test_parser.py` all had genuinely wrong resolved octaves under the old sticky logic — confirmed correct under the fix by cross-checking `Children_s_Piece.ly` against real `lilypond` output, not just re-asserting whatever the parser happened to produce.)

**Definition of Done:**
- [x] Unmarked notes resolve to the nearest octave per BANA Sec. 3.2.2, not a sticky persisted value, for both plain notes and chord base notes.
- [x] In-accord voices resolve octave continuity from the primary (first-written) voice, not whichever voice was written last.
- [x] New unit tests cover the descending- and ascending-across-an-octave-boundary cases that motivated this ticket.
- [x] Full existing test suite still passes; `test_octave_persists_without_mark`'s comment updated to describe the real rule rather than "always sticky."

---

### [ ] S8b-13: Fix duplicated `\set stanza` directive in strophic/multi-verse lyrics output (found via S8b-11)

**Why:** While composing the S8b-11 strophic fixture, `strophic_song_test.ly`'s rendered `\new Lyrics` blocks came out as
`\new Lyrics \lyricsto "vocals_soprano" { \set stanza = "1. " \set stanza = "1. " Ho -- ly A -- men }` —
the `\set stanza = "1. "` directive is emitted **twice**. This isn't cosmetic: LilyPond accepts the duplicate silently (the second `\set` just re-applies the same value), so it doesn't break compilation, but it's dead/wrong markup that would confuse anyone hand-editing the `.ly` output, and it means the existing test suite has a real coverage gap around this exact case.

Root cause: the stanza prefix gets added to the lyrics **twice**, in two different places, that don't know about each other:
1. `EnsembleParser`'s stanza-prefix handling (`ensemble_parser.py`, around `extract_stanza_prefix` / the `remaining_syllables[0] = (f"\\set stanza = \"{prefix_val} \" {first_syl}", has_hyphen)` line) bakes the `\set stanza = "N. "` text directly into the *first syllable string* of `staff.verses[v_idx][0]` at parse time. This is confirmed intentional and covered by existing tests — `test_parse_strophic_multiverse_lyrics_and_refrain` and `test_parse_strophic_with_word_number_verse_prefixes` in `test_vocal.py` both assert `staff.verses[0] == ['\\set stanza = "1. " Ho --', ...]` directly.
2. `Score.to_lilypond()` (three call sites: the single-staff lyrics branch, the single-instrument-family-run branch, and the multi-staff-group branch) and `OrchestraScore.to_lilypond()` (one call site) **each independently** recompute `prefix_str = f"\\set stanza = \"{staff.verse_prefixes[v_idx]} \" "` from `staff.verse_prefixes` and prepend it again when joining `lyrics_content = prefix_str + " ".join(v)`.

Since `staff.verse_prefixes` is only ever populated by `EnsembleParser` at the same time as the syllable-level bake-in (both set together, right before `staff.verses = mapped_verses`), the render-time `prefix_str` addition is *always* redundant whenever it fires — there's no case where verse_prefixes is set but the first syllable *doesn't* already carry the `\set stanza` text.

This also explains why no existing test caught it: `test_vocal.py`'s `to_lilypond()` assertions (lines testing `test_parse_strophic_multiverse_lyrics_and_refrain` / `test_parse_strophic_with_word_number_verse_prefixes`) use loose `'\\set stanza = "1. " Ho -- ly ...' in ly_output` substring checks, which still pass even when that exact substring is preceded by a second, duplicate `\set stanza = "1. "` — a substring check can't detect an extra copy before it.

**Steps:**
1. Remove the redundant render-time `prefix_str` computation/prepending in all four call sites (`score.py`'s three, `orchestra_score.py`'s one), relying solely on the syllable text `EnsembleParser` already produced in `staff.verses`/`staff.lyrics`.
2. Double check the `verses = staff.verses if staff.verses else [staff.lyrics]` fallback path (a staff with plain, non-strophic lyrics and no `verse_prefixes`): confirm it still renders with no `\set stanza` at all (unaffected, since `verse_prefixes` is empty there and the guard already skips `prefix_str`) — should not need any change, but verify with a test.
3. Confirm `staff.verse_prefixes` isn't relied on anywhere else for something other than this now-removed render-time computation (e.g. reverse-direction `to_braille()` in Sprint 9 or the BRF writer) before deleting any of its call sites — if it's still needed elsewhere, only remove the four redundant `prefix_str` blocks, not the field itself.
4. Update `test_vocal.py`'s loose substring assertions (`'\\set stanza = "1. " Ho -- ly \\set stanza = "Refrain. " A -- men' in ly_output` and similar) to assert the directive appears **exactly once** per verse — e.g. `ly_output.count('\\set stanza = "1. "') == 1` — so this exact regression can't silently reappear.
5. Update `tests/test_strophic_integration.py::test_strophic_fixture_matches_ground_truth_ly`'s ground truth (`strophic_song_test.ly`) to drop the duplicate, and re-verify the fixture still compiles cleanly with the real `lilypond` binary.
6. Re-run the full suite to confirm no other `.ly` ground-truth fixture with verse/stanza lyrics (there aren't others as of this writing besides `strophic_song_test.ly` and the inline `test_vocal.py` cases) regresses.

**Definition of Done:**
- [ ] `\set stanza = "N. "` (and `"Refrain. "`) appears exactly once per verse in rendered LilyPond output, never doubled.
- [ ] `test_vocal.py`'s strophic assertions catch a doubled directive (not just loose substring containment).
- [ ] `strophic_song_test.ly` ground truth updated and re-verified against a real `lilypond` compile.
- [ ] Full existing test suite still passes.

---

# Sprint 9: Reverse Direction — LilyPond to BRF

Estimated time: 1.5–2 weeks.

**Research basis for this sprint:** Before starting this sprint, review the BANA Music Braille Code 2015 manual (specifically sections on page layout, spacing, and indicators) and the LilyPond Notation Reference (especially for notes, durations, and chords).

---

### [x] S9-1: Add to_braille() method to all domain model classes

**Why:** Currently, the internal domain model classes (Note, Rest, Chord, Measure, Staff, Score, etc.) only know how to render themselves to LilyPond via `to_lilypond()`. To enable the reverse translation path, these classes must implement `to_braille() -> str` using the dot-pattern tables in `src/dottednotes/bana_symbols.py`.

**Steps:**
1. Define the base `to_braille() -> str` method interface in `BrailleSymbol` (in `src/dottednotes/models/base.py`).
2. Implement `to_braille()` on core musical elements:
   - `Note`: output the pitch name + duration modifier, prepended by octave marks, accidentals, dynamics, articulations, ornaments, and grace note indicators, and appended by ties or slurs.
   - `Rest`: output the rest sign corresponding to the duration.
   - `Duration`: handle dots (augmentation dots) and triplet markings.
3. Implement `to_braille()` on structural and meta-elements:
   - `KeySignature`
   - `TimeSignature`
   - `Clef`
   - `TextMarking`
4. Implement `to_braille()` on composite elements:
   - `Chord`: output the primary note followed by interval indicators.
   - `InAccord`: output the voice parts separated by BANA in-accord signs.
   - `Measure`: output the sequence of notes/rests/chords, ending with the appropriate bar line symbol.
   - `MeasureRepeat`: output the whole-measure repeat sign (`⠍⠄`).
5. Implement `to_braille()` on score elements:
   - `Staff`: render measures separated by measure spaces.
   - `Score` / `OrchestraScore`: coordinate staves and metadata.
6. Create `tests/test_to_braille.py` and write unit tests for every class's `to_braille()` output.

**Definition of Done:**
- [x] Every domain model class implements `to_braille() -> str` returning correct BANA Unicode braille.
- [x] Unit tests in `tests/test_to_braille.py` assert on note durations, octave marks, accidentals, key/time signatures, chords, and simple measures.
- [x] All unit tests pass successfully.

**Senior note:** Keep `to_braille()` focused strictly on representing the object's own musical value. Do not hardcode line wrapping, page layouts, or part prefixing inside `Note.to_braille()` or `Measure.to_braille()`. Those layout concerns belong in `BrailleRenderer` (S9-2).

---

### [x] S9-2: Implement BrailleRenderer

**Why:** Converting a `Score` to a formatted braille document requires coordination of layout rules, measure spacing, page numbering, and part indicators (e.g. hand signs for piano parts, or abbreviated instrument names for ensemble scores).

**Steps:**
1. Create `src/dottednotes/renderers/braille_renderer.py` with the `BrailleRenderer` class.
2. Implement `render(self, score: Score) -> str` to format single-staff and multi-staff scores.
3. Handle part indicators:
   - For piano scores, output the right hand (`⠨⠜`) or left hand (`⠸⠜`) prefix at the start of systems.
   - For ensemble scores, output BANA-compliant instrument abbreviations.
4. Support measure spacing (a single space `⠀` separating measures) and system boundaries.
5. Create `tests/test_braille_renderer.py` and test formatting of both single-staff and multi-staff scores.

**Definition of Done:**
- [x] `BrailleRenderer` coordinates the translation and layout formatting of complete scores.
- [x] Part prefixes and measure spacing are output correctly according to BANA rules.
- [x] Unit tests verify formatting structure for piano and ensemble scores.

**Senior note:** Ensure `BrailleRenderer` only outputs Unicode braille characters (U+2800 to U+28FF) and spaces. Any conversion to ASCII braille for file writing should be handled at the file writing layer, not here.

---

### [x] S9-3: Implement resilient LilyPond parser for arbitrary scores

**Why:** To translate arbitrary LilyPond files (such as those from Mutopia) back to the internal domain model, we need a resilient LilyPond parser. This parser must extract supported musical elements (pitch, duration, chords, slurs, ties, dynamics, articulations, vocal lyrics, multiple voices, staves, headers) and ignore unrecognized markup, stem overrides, beam markers, and layout code without throwing errors.

**Steps:**
1. Create `src/dottednotes/parser/lilypond_parser.py` containing `LilypondParser`.
2. Implement a lexical tokenizer that parses LilyPond syntax into tokens:
   - Skip all single-line (`%`) and multi-line (`%{ ... %}`) comments.
   - Parse identifiers, command words (starting with `\`), strings (`"..."`), braces (`{ }`), angle brackets (`< >`, `<< >>`), numbers, and Scheme calls (starting with `#`).
3. Implement structured extraction for supported blocks:
   - **Headers**: Parse key-value definitions within `\header { ... }` blocks (extract `title`, `composer`, etc.).
   - **Variables**: Store variable names mapped to their musical token streams to resolve them when referenced in scores.
   - **Staves/Voices**: Parse `\new Staff` and `\new Voice` configurations, including parallel construct systems `<< ... >>` representing multi-staff/multi-part scores.
   - **Vocal music**: Support vocal lyrics declarations in `\new Lyrics \lyricsto "voice" { ... }` or `\addlyrics { ... }` blocks, mapping lyric syllables to their corresponding notes.
4. Implement a music parser that processes token streams (handling relative pitch context `\relative` as well as absolute pitch):
   - Parse note pitches (e.g., `c'4`, `d''8.`, `ees`, `fis`) with accidentals and octave indicators.
   - Parse rests (`r4`, `r8`) and multi-measure rests (`R2*52`), mapping them to `Rest` or appropriate spacer structures.
   - Parse chords (`<c e g>4`) containing multiple notes.
   - Extract attached details: dynamics (`\p`, `\f`), articulations (`-.`, `->`), slurs (`(`, `)`), and ties (`~`).
5. Implement the resilience/ignoring strategy:
   - Silently skip formatting overrides (e.g. `\override Staff.TimeSignature.stencil = ##f`).
   - Silently skip stem overrides (`\stemUp`, `\stemDown`, `\stemNeutral`) and beam markers (`[`, `]`).
   - Skip unrecognized noteside markup and text annotations (e.g. `^\markup { ... }` or text scripts `^"dolce"`).
   - Ignore layout blocks (`\layout { ... }`), midi blocks (`\midi { ... }`), paper blocks (`\paper { ... }`), and custom Scheme functions/macros.
6. Create `tests/test_lilypond_parser.py` and write unit and integration tests:
   - Test snippets of notes, chords, and lyrics.
   - Parse full DottedNotes-generated LilyPond files.
   - Parse real Mutopia fixtures (such as `tests/fixtures/vocal_test.ly` and `tests/fixtures/Children_s_Piece.ly`), asserting that all supported content (headers, notes, lyrics, chords, etc.) is successfully extracted while unsupported commands are skipped cleanly.

**Definition of Done:**
- [x] `LilypondParser` successfully extracts supported elements (vocal lyrics, slurs, ties, chords, voices, staves, headers) from arbitrary LilyPond files into a musically correct `Score` domain model.
- [x] The parser silently skips all unrecognized commands, formatting overrides, custom layouts, and Scheme code.
- [x] Raises `LilyPondParseError` only on syntactically malformed LilyPond (e.g., unmatched braces, unclosed string literals).
- [x] Unit and integration tests cover various test cases, including parsing vocal scores and piano scores from fixtures.

**Senior note:** Do not attempt to write a general compilation engine. Focus on structural block parsing and a robust fallback: if a command or block is not recognized, scan ahead to skip its parameters/scopes safely by balancing braces, brackets, and strings.

---

### [x] S9-4: Implement BRF file writer with BANA line length and pagination

**Why:** Braille files (.brf) require strict layout constraints, typically 38-40 characters per line and 25 lines per page, with right-aligned page numbering. We must break lines only at safe boundaries (e.g., measure spaces) and output page-break indicators.

**Steps:**
1. Implement page formatting and line wrapping in `BRFWriter` (in `src/dottednotes/renderers/braille_renderer.py` or a new writer file).
2. Allow setting line width (default 40) and page height (default 25).
3. Implement line-wrapping logic: wrap at measure spaces where possible. If a single measure exceeds the line length, break it using BANA continuation rules.
4. Implement pagination, outputting BANA page headers/footers with page numbers.
5. Implement conversion from Unicode braille to ASCII braille (since BRF files are traditionally ASCII-encoded).
6. Write tests in `tests/test_brf_writer.py` verifying page boundaries, line limits, and ASCII translation.

**Definition of Done:**
- [x] BRF writer formats text into clean pages matching BANA dimension constraints.
- [x] Text wraps cleanly without breaking individual note symbols.
- [x] Output is written in ASCII braille format.
- [x] Unit tests pass.

---

### [x] S9-5: Round-trip integration test

**Why:** The best way to ensure the reverse path works flawlessly is an end-to-end round-trip test: read a BRF, parse it, output to LilyPond, parse it back, render it back to BRF, and verify that the output matches the input.

**Steps:**
1. Create `tests/test_roundtrip.py`.
2. Load existing fixtures (`fengyang_flower_drum.brf`, `children_s_piece.brf`, etc.).
3. Convert: BRF → Internal Model → LilyPond → Internal Model → BRF.
4. Compare the resulting BRF content against the original. If there are minor formatting differences (e.g. spacing), verify the musical content is identical.
5. Run the round-trip check on all test fixtures.

**Definition of Done:**
- [x] Integration tests verify the complete round-trip flow for all standard BRF fixtures.
- [x] The generated BRF is musically equivalent to the original.
- [x] All tests pass.

---

# Sprint 9b: BANA Validator (between Sprint 9 and Sprint 10)

Estimated time: 1.5–2 weeks.

**Research basis for this sprint:** Verify BANA guidelines regarding octave rules (when marks are required or omitted), repeated articulations, measure repetitions, and line lengths.

---

### [x] S9b-1: Implement BANAValidator class with rule registry

**Why:** To ensure scores conform to BANA music notation rules, we need a centralized validation system that can run modular checks against the internal domain model and report errors/warnings.

**Steps:**
1. Create `src/dottednotes/validation/validator.py` with the `BANAValidator` class.
2. Implement a rule registry where validation rules can be registered, enabled, or disabled.
3. Define the validation run method returning a `ValidationResult`.
4. Write tests for rule registration and validation execution.

**Definition of Done:**
- [x] `BANAValidator` class and registry are implemented.
- [x] Rules can be registered and toggled.
- [x] Unit tests pass.

---

### [x] S9b-2: Implement articulation series shorthand rule

**Why:** BANA rules (Section 14) allow repeated identical articulations (such as a string of staccatos) to be written using a shorthand sign instead of repeating it on every single note. We need to validate if shorthands are correctly used.

**Steps:**
1. Create a validation rule that checks for 4 or more identical articulations in consecutive notes.
2. If the shorthand is missing, suggest a correction warning.
3. Write unit tests for the articulation shorthand rule.

**Definition of Done:**
- [x] Missing articulation shorthands are detected and reported.
- [x] Unit tests pass.

---

### [x] S9b-3: Implement octave mark validation and auto-insertion

**Why:** BANA has complex rules for when octave marks are required (e.g. measure starts, leaps of seconds/thirds/fifths/etc. depending on direction). Checking these is critical to prevent pitch misreadings.

**Steps:**
1. Implement BANA rules for octave marks based on leap sizes.
2. Flag missing or redundant octave marks.
3. Implement correction suggestions to auto-insert or auto-remove octave marks.
4. Write tests verifying correct warnings for various leaps.

**Definition of Done:**
- [x] Octave leap rules are validated and reported.
- [x] Redundant and missing octave marks are flagged.
- [x] Unit tests pass.

---

### [x] S9b-4: Implement line length checking and automatic line breaking

**Why:** Rendered braille lines should never overflow BANA physical page margins (usually 40 columns).

**Steps:**
1. Implement a rule checking if any line exceeds 40 characters (or the configured limit).
2. Report the position and length of the violation.
3. Propose line-break corrections.
4. Write tests verifying line-length validations.

**Definition of Done:**
- [x] Line overflow issues are flagged.
- [x] Unit tests pass.

---

### [x] S9b-5: Implement Correction dataclass and ValidationResult

**Why:** We need structured feedback for validation findings rather than generic strings to allow programmatic correction and UI displays.

**Steps:**
1. In `src/dottednotes/validation/validator.py`, implement `Correction` and `ValidationResult` dataclasses.
2. Include fields for rule ID, severity, message, line/measure reference, and before/after suggestions.
3. Update validator and rules to return these objects.
4. Write tests verifying the fields.

**Definition of Done:**
- [x] `Correction` and `ValidationResult` are implemented and used by the validator.
- [x] Unit tests pass.

---

### [x] S9b-6: Add --report flag to CLI that outputs plain text correction list

**Why:** Command-line users (especially blind composers using VoiceOver) need a highly readable, plain-text report of validation errors and corrections.

**Steps:**
1. Add the `--report` option to the `convert` subcommand in `src/dottednotes/cli.py`.
2. If `--report` is active, validate the score.
3. Print warnings and corrections in a clean, line-by-line format to `stderr` (e.g. `Measure 4: Missing octave mark on note D`).
4. Write tests in `tests/test_cli.py` verifying the `--report` output.

**Definition of Done:**
- [x] The CLI supports `--report`.
- [x] Output is plain-text, accessible, and contains all corrections.
- [x] Tests pass.

---

### [x] S9b-7: Add validation step to web UI with corrections displayed after upload

**Why:** Prepare backend support and APIs so that when files are uploaded in the future web UI, validation results are returned and can be displayed.

**Steps:**
1. Implement a backend helper or endpoint serializer returning JSON validation results.
2. Write tests verifying the JSON format.

**Definition of Done:**
- [x] JSON serialization of validation results is implemented and tested.

---

### [x] S9b-8: Integration test: input your Fengyang score with known rule violations, verify corrections match expected BANA output

**Why:** End-to-end integration tests using real compositions ensure the validator is reliable under real-world conditions.

**Steps:**
1. Create a variant of the Fengyang test fixture with intentional BANA violations.
2. Run the validator and assert the corrections match the expected output.

**Definition of Done:**
- [x] Integration test passes.

---

### [x] S9b-9: Document all implemented BANA rules in docs/bana_reference.md

**Why:** Clear documentation ensures developers and users understand which BANA rules are being checked.

**Steps:**
1. Update `docs/bana_reference.md` to list all validator rules, citing the BANA manual sections and providing examples.

**Definition of Done:**
- [x] `docs/bana_reference.md` is updated and complete.

---

### [x] S9b-10: Implement BrailleRenderer class with compression_level parameter

**Why:** Users should be able to control whether output braille is fully formatted, minimally formatted, or uncompressed.

**Steps:**
1. Update `BrailleRenderer` to accept a `compression_level` parameter.
2. Implement compression levels: `none`, `minimal`, and `full`.
3. Write unit tests checking that output changes based on the compression level.

**Definition of Done:**
- [x] `compression_level` is supported.
- [x] Unit tests pass.

---

### [x] S9b-11: Implement measure repeat detection using musical_equals()

**Why:** In compressed mode, identical consecutive measures should be rendered using the BANA measure repeat sign (`⠍⠄`) to save space.

**Steps:**
1. Implement measure repeat detection during rendering.
2. If consecutive measures are musically identical, replace the subsequent ones with a `MeasureRepeat` model.
3. Write unit tests.

**Definition of Done:**
- [x] Consecutive identical measures are replaced by the measure repeat sign in compressed output.
- [x] Unit tests pass.

---

### [x] S9b-12: Implement section repeat detection using sliding window comparison

**Why:** Larger repeated sections of music can be compressed using BANA section/part repeat signs.

**Steps:**
1. Implement a sliding window comparison algorithm to find repeating sequences of measures.
2. Replace repeated sequences with BANA repeat indications.
3. Write tests verifying correct detection and representation.

**Definition of Done:**
- [x] Section repeats are detected and compressed correctly.
- [x] Unit tests pass.

---

### [x] S9b-13: Implement articulation series shorthand detection at voice level

**Why:** Automatically compress repeated articulations into shorthand signs during rendering.

**Steps:**
1. Add a rendering pass that replaces sequences of 4+ identical articulations with BANA shorthand signs.
2. Write unit tests.

**Definition of Done:**
- [x] Repeated articulations are compressed into BANA shorthands.
- [x] Unit tests pass.

---

### [x] S9b-14: Integration test: expanded Internal Model → compressed braille → verify against hand-formatted BANA output

**Why:** Verify that the complete compression pipeline matches expected output from a hand-formatted BANA score.

**Steps:**
1. Run a complex score through the compression pipeline and assert the output matches hand-formatted BANA reference data.

**Definition of Done:**
- [x] Integration test passes.

---

### [x] S9b-15: Add musical_equals() to Note, Rest, Chord, and Measure classes

**Why:** To detect duplicates for compression, we need a way to compare objects for musical equivalence, ignoring non-musical attributes.

**Steps:**
1. Implement `musical_equals(self, other)` on `Note`, `Rest`, `Chord`, and `Measure`.
2. Write unit tests.

**Definition of Done:**
- [x] `musical_equals()` is implemented and verified on the core model classes.
- [x] Unit tests pass.

**Senior note:** Place this ticket before the repeat detection tickets in execution, as they depend on it.

---

### [x] S9b-16: Implement compression_level parameter with full, minimal, and none modes

**Why:** Expose the compression level option via the command line interface so users can configure formatting.

**Steps:**
1. Add the `--compression` option to the CLI (`cli.py`).
2. Wire the flag to the renderer.
3. Write tests verifying CLI parameter handling.

**Definition of Done:**
- [x] CLI supports `--compression none|minimal|full`.
- [x] CLI tests pass.

---

# Sprint 9c: BANA Formatting Rule Library

Estimated time: 1–1.5 weeks.

---

### [x] S9c-1: Compile complete list of BANA mandatory formatting rules from the Technical Manual

**Why:** To ensure full BANA compliance, we need a complete reference of mandatory rules from the manual.

**Steps:**
1. Gather all mandatory formatting rules from the BANA manual.
2. Document them in `docs/bana_reference.md` under a "Mandatory Formatting Rules" section.

**Definition of Done:**
- [x] Mandatory formatting rules are documented.

---

### [x] S9c-2: Compile complete list of BANA optional shorthand conventions

**Why:** Document all optional shorthands for completeness.

**Steps:**
1. Identify and document optional shorthands from the manual in `docs/bana_reference.md`.

**Definition of Done:**
- [x] Optional shorthands are documented.

---

### [x] S9c-3: Implement each rule as a discrete, testable method on BANAValidator

**Why:** Modular implementation makes the validator easy to test, maintain, and expand.

**Steps:**
1. Translate compiled rules into separate methods on `BANAValidator`.
2. Add tests verifying each method.

**Definition of Done:**
- [x] All compiled rules are implemented as modular methods.
- [x] Unit tests pass.

---

### [x] S9c-4: Document every rule in docs/bana_reference.md with manual citation and example

**Why:** Help users map validation errors to BANA manual guidelines.

**Steps:**
1. Update `docs/bana_reference.md` with rule names, description, citations, and examples.

**Definition of Done:**
- [x] Rule library is fully documented.

---

### [x] S9c-5: Build a rule registry so rules can be enabled/disabled individually — useful for different BANA editions

**Why:** Different BANA editions have slight differences in rules.

**Steps:**
1. Support loading validation profiles (e.g., standard, strict).
2. Write tests verifying profile loading and rule filtering.

**Definition of Done:**
- [x] Validator supports rule registry configuration profiles.
- [x] Unit tests pass.

---



# Sprint 10: MusicXML Bridge

Estimated time: 1–1.5 weeks.

---

### [x] S10-1: Integrate music21 for MusicXML parsing

**Why:** We need to parse MusicXML files using a reliable library without external binary dependencies. Integrating `music21` into our project will allow us to parse MusicXML files into an in-memory stream object structure that we can easily inspect and convert.

**Steps:**
1. Add `music21` to dependencies in `pyproject.toml` (e.g. `music21 = "^9.1.0"`).
2. Implement a helper/wrapper function/class in `src/dottednotes/parser/musicxml_parser.py` to load a MusicXML file or string via `music21.converter.parse()`.
3. Set up appropriate error handling to catch `music21` exceptions and translate them into a screen-reader friendly `DottedNotesError`.
4. Write basic unit tests to ensure that `music21` can parse a sample MusicXML string and retrieve basic elements (such as parts and notes) in our environment.

**Definition of Done:**
- [x] `music21` is successfully added to project dependencies.
- [x] MusicXML converter wrapper is implemented in `dottednotes/parser/musicxml_parser.py`.
- [x] Parser errors are wrapped in a clean, screen-reader friendly `DottedNotesError`.
- [x] Unit tests pass.

---

### [x] S10-2: Implement MusicXML to Internal Model translation

**Why:** To import MusicXML, we need to convert the hierarchical object structure returned by `music21` (such as `Score`, `Part`, `Measure`, `Note`, `Chord`, `Rest`, `KeySignature`, `TimeSignature`, `Clef`, etc.) into our own internal domain model `Score`.

**Steps:**
1. Create a translator class/function in `src/dottednotes/parser/musicxml_parser.py` (e.g. `MusicXMLTranslator`).
2. Map `music21.stream.Score` and `music21.stream.Part` to `dottednotes.models.Score` and `dottednotes.models.Staff`.
3. Map `music21.stream.Measure` to `dottednotes.models.Measure`.
4. Map individual `music21` note/chord/rest elements to `dottednotes` `Note`, `Chord`, and `Rest` models. This includes pitch mapping (accidentals, octaves), duration mapping (dots, triplet/tuplet ratios), expressive marks (articulations, dynamics, slurs, ties, ornaments), and fingering signs.
5. Map structural markings: clef, key signature, time signature, and text markings (tempo/expression).
6. Connect this translator to the CLI command `dottednotes convert` when the input file has a `.musicxml`, `.xml`, or `.mxl` extension.
7. Write unit tests in `tests/test_musicxml_parser.py` validating correct model construction for pitches, rhythms, dynamics, articulations, and polyphony.

**Definition of Done:**
- [x] `MusicXMLTranslator` successfully maps main musical elements from `music21` to the `DottedNotes` model.
- [x] CLI detects MusicXML file extensions and routes them to the MusicXML parser.
- [x] Unit tests cover various note types, accidentals, durations, tuplets, and expressions.
- [x] Unit tests pass.

---

### [x] S10-3: Implement Internal Model to MusicXML translation

**Why:** To support exporting to MusicXML, we must convert our internal `Score` model back to a `music21.stream.Score` representation and write it out as a MusicXML file.

**Steps:**
1. Implement a translator in `src/dottednotes/renderers/musicxml_renderer.py` (e.g. `MusicXMLRenderer` or a `to_musicxml` method on `Score`) that maps `Score`, `Staff`, `Measure`, `Note`, `Chord`, `Rest`, and structural elements to their corresponding `music21` classes.
2. Map accidentals, durations, tuplets, dynamic levels, articulations, ties, and slurs back to `music21` equivalents.
3. Export the resulting `music21.stream.Score` to a MusicXML byte/string output using `score_stream.write('musicxml')`.
4. Integrate the MusicXML exporter into `cli.py` such that if the output file path ends in `.musicxml` or `.mxl`, it renders and writes a MusicXML file.
5. Write tests in `tests/test_musicxml_exporter.py` validating that internal models are correctly exported.

**Definition of Done:**
- [x] Export translator maps the internal `Score` structure to a `music21` stream structure.
- [x] CLI supports exporting to `.musicxml` / `.mxl` files.
- [x] Unit tests verify basic note export, key/time signatures, and dynamics.
- [x] Unit tests pass.

---

### [x] S10-4: Integration test: import MuseScore MusicXML, export as BRF

**Why:** We want to make sure that MusicXML files exported by common editors like MuseScore can be successfully imported by DottedNotes and exported as beautifully formatted, validated braille music files.

**Steps:**
1. Add a sample MusicXML file (generated from MuseScore, containing a mixture of melody, chords, tuplets, dynamics, and articulations) to `tests/fixtures/`.
2. Implement an integration test in `tests/test_musicxml_integration.py` that reads this MusicXML file, runs it through the DottedNotes pipeline, exports the result as a `.brf` file, and validates the output.
3. Ensure that BANA validation is run during the import-export process and reports any issues.

**Definition of Done:**
- [x] A MuseScore-generated MusicXML fixture is added.
- [x] Integration test parses the fixture and exports correct BANA-compliant BRF.
- [x] Integration tests pass.

---

### [x] S10-5: Integration test: import BRF, export as MusicXML for MuseScore

**Why:** The reverse path (importing BRF and exporting as MusicXML) must be verified so that blind composers can share their braille music compositions with sighted musicians using standard notation software.

**Steps:**
1. In `tests/test_musicxml_integration.py`, add a test that reads a standard BRF fixture (e.g. `g_major_scale.brf` or `children_s_piece.brf`).
2. Parse the BRF using the existing `BrailleParser`, convert the resulting model to MusicXML using `music21`, and write the file.
3. Verify that the output XML file can be parsed by `music21` (or another validating parser) and has correct notes, pitches, measures, and layout details.

**Definition of Done:**
- [x] Integration test converts BRF to MusicXML.
- [x] The generated MusicXML is validated to contain correct pitch, rhythm, and structure matching the source BRF.
- [x] Integration tests pass.

---

# Sprint 10b: MusicXML Import Hardening (after Sprint 10)

Estimated time: 1.5–2 weeks.

**Why this sprint exists:** A code audit of `src/dottednotes/parser/musicxml_parser.py`
(the `MusicXMLTranslator` built in S10-2) found eight cases where real-world
MusicXML input is silently mishandled — not rejected with an error, just
imported wrong or dropped, which is worse for a blind composer who can't
visually spot-check the result against the source file. Two of the eight
were confirmed empirically against `music21` 10.5.0 (this repo's `.venv`),
not just read off the source; the rest are grounded in a direct reading of
`musicxml_parser.py`. Three of the eight (fermatas, breath marks, first/second
endings) are blocked on Sprint 10c landing the BANA model/braille support for
those signs first, since there's nowhere in the internal model to import them
into yet.

---

### [x] S10b-1: Import multi-voice single-staff writing as `InAccord`

**Why:** `InAccord` (`models/in_accord.py`, BANA Chapter 11) is imported into
`musicxml_parser.py` (line 12) but never instantiated anywhere in the file.
`translate_measure` reads `m21_measure.notesAndRests` directly, and that does
not descend into nested `music21.stream.Voice` sub-streams. **Confirmed
empirically:** a `Measure` containing two `Voice` children (the normal
`music21` representation of MusicXML's `<voice>` numbering — the standard way
piano/keyboard music encodes two independent rhythmic lines in one staff) has
`len(m.notesAndRests) == 0`. This isn't misordering — the entire measure
silently imports as empty. This is the highest-severity gap of the eight,
since polyphonic single-staff writing (e.g. hymn/piano textures) is common,
not a corner case.

**Steps:**
1. In `translate_measure`, check `m21_measure.voices` before falling back to
   flat `notesAndRests`; when voices are present, translate each one
   separately using the existing per-element translation logic (factor the
   note/chord/rest-and-tuplet loop out of `translate_measure` so it can run
   once per voice).
2. Wrap the resulting per-voice note lists in
   `InAccord(parts=[...], in_accord_type='full_measure')`.
3. Order voices per BANA 11's documented convention (already in
   `models/in_accord.py`'s docstring): highest voice first for treble/alto
   clef, lowest voice first for bass/tenor clef. `music21` voice numbering
   (`Voice.id`) doesn't reliably encode pitch order, so derive the order from
   the voices' actual pitch content, not just numbering.
4. Add a two-voice piano MusicXML fixture and a test asserting the resulting
   `Measure` contains an `InAccord` with both voices' notes present, in the
   correct order — not an empty measure.

**Definition of Done:**
- [x] Multi-voice measures import as `InAccord` instead of importing empty.
- [x] Voice ordering matches BANA 11's clef-dependent convention.
- [x] New tests pass; existing single-voice tests still pass.

---

### [x] S10b-2: Normalize instrument names so transposition lookup actually fires

**Why:** `get_transposition()` (`models/transposition.py:52`) only matches
strings shaped exactly `"<instrument> in <key>"` against a 6-entry table
(horn/F, english horn/F, clarinet/Bb, clarinet/A, trumpet/Bb, trumpet/C).
`translate_part` (musicxml_parser.py:68-70) sets `staff.name` straight from
`music21`'s `part.partName`/`part.id` with no normalization. Real-world
MusicXML part names from notation software ("Bb Clarinet", "Horn in F 1",
"French Horn") won't match, so imported orchestral scores silently keep
written pitch unmarked instead of wrapping it in `\transpose` for concert
pitch — with no error, just wrong output.

**Steps:**
1. Prefer `music21`'s own structured transposition data
   (`part.getInstrument().transposition`, an `Interval` object, present for
   nearly any MusicXML exported by real notation software) over string-
   matching the part name — this sidesteps naming variance entirely.
2. Where `music21` doesn't supply transposition data, normalize common part-
   name variants (numbering suffixes like "Horn in F 1", "Bb"/"B-flat"
   spelling, common abbreviations) toward the `"<instrument> in <key>"` form
   `get_transposition()` expects, or extend `get_transposition()` to accept
   an `Interval` directly instead of a name string.
3. `_TRANSPOSITIONS` in `models/transposition.py` currently only has 6
   entries; if this work surfaces instruments/keys not in that table, do not
   guess the interval — flag it to the developer for confirmation before
   adding it (per CLAUDE.md's rule on transposition intervals).
4. Add a test importing a transposing-instrument MusicXML fixture (e.g.
   Clarinet in Bb exported from real notation software) and assert the
   output gets the same `\transpose` wrapping as the equivalent BRF/ensemble
   input does today.

**Definition of Done:**
- [x] Transposing instruments imported from MusicXML get correct `\transpose`
      wrapping regardless of exact part-name spelling.
- [x] Any newly-added transposition intervals are developer-confirmed.
- [x] New tests pass.

---

### [x] S10b-3: Import lead-sheet chord symbols, and stop mis-importing them as played chords

**Why:** DottedNotes has `ChordSymbol`/`ChordNamesTrack` models built
specifically for BANA §23/§27 lead-sheet chord symbols, but
`musicxml_parser.py` never looks for `music21.harmony.ChordSymbol` elements.
**Confirmed empirically**, this is worse than a missing feature:
`music21.harmony.ChordSymbol` is a subclass of `music21.chord.Chord`
(`isinstance(ChordSymbol('Cmaj7'), music21.chord.Chord)` is `True`), and a
`ChordSymbol` placed inline in a measure shows up in `notesAndRests`
alongside the real notes. `translate_measure`'s
`elif isinstance(el, music21.chord.Chord):` branch (line 259) has no
exclusion for it, so today a chord symbol in the source MusicXML gets
imported as a real, sounding 4-note chord (root/3rd/5th/7th — confirmed
`ChordSymbol('Cmaj7').pitches` gives `['C3','E3','G3','B3']`) competing for
the same beat as the actual melody note, not as an annotation. This will
visibly corrupt the measure's rhythm and pitch content, not just drop
formatting.

**Steps:**
1. Exclude `music21.harmony.ChordSymbol` from the
   `isinstance(el, music21.chord.Chord)` branch in `translate_measure`
   (check `music21.harmony.ChordSymbol` first and route separately).
2. Collect chord-symbol elements per measure/offset and translate them into
   `ChordSymbol`/`ChordNamesTrack` entries aligned to the rhythm, per BANA
   §23/§27 — reuse the alignment logic `lead_sheet_parser.py` already has for
   the BRF-side lead-sheet parallel where practical.
3. Add a lead-sheet MusicXML fixture (chord symbols over a melody line) and
   a test asserting correct `ChordSymbol` import and rhythm alignment, and a
   regression test confirming a chord symbol no longer produces a phantom
   played chord in the `Measure`.

**Definition of Done:**
- [x] Chord symbols import as `ChordSymbol`/`ChordNamesTrack` entries.
- [x] A `ChordSymbol` in the source XML no longer imports as a played chord.
- [x] New tests pass.

---

### [x] S10b-4: Import fermatas

**Why:** `translate_note_obj`'s expression-mapping loop
(musicxml_parser.py:448-461) handles Trill/Mordent/InvertedMordent/Turn/
InvertedTurn but has no case for `music21.expressions.Fermata` — a fermata
in the source MusicXML is silently dropped, with no warning.

**Blocked on:** S10c-1 (there's no model field to import a fermata into
yet — this ticket only wires the `music21` → DottedNotes mapping once that
exists).

**Steps:**
1. Add a case in the expression loop mapping `music21.expressions.Fermata` to
   whatever model S10c-1 lands (confirmed: a `music21.expressions.Fermata`
   instance carries `.shape` — `'normal'`/`'angled'`/`'square'`/etc. — and
   `.type` — `'upright'`/`'inverted'`, i.e. above/below the staff, which BANA
   Table 22(B) does *not* distinguish with a separate sign, so `.type` can be
   ignored for the braille side but may matter for `to_lilypond()`).
2. Add a test importing a MusicXML fixture with a fermata over a note.

**Definition of Done:**
- [x] Fermatas import instead of silently disappearing.
- [x] New tests pass.

---

### [x] S10b-5: Import first/second endings (voltas)

**Why:** `translate_measure` only reads `m21_measure.rightBarline`/
`leftBarline` for simple repeat bar lines (lines 191-203);
`music21.spanner.RepeatBracket` — voltas / alternate endings — is never
inspected, so multi-ending sections lose their ending numbers on import.

**Blocked on:** S10c-3 (needs the `Measure`-level ending-number field that
ticket adds).

**Steps:**
1. For each measure, check spanner sites for `RepeatBracket` and record which
   ending number(s) apply. **Confirmed:** `RepeatBracket.numberRange` already
   gives this as a list (e.g. `[1, 2]` for a combined "1,2" bracket), which
   maps directly onto BANA 17.1.1(b)'s combined/ranged-ending handling.
2. Add a test importing a MusicXML fixture with a first/second ending pair,
   asserting correct ending numbers land on the right measures.

**Definition of Done:**
- [x] Voltas import with correct ending numbers per measure.
- [x] New tests pass.

---

### [x] S10b-6: Import breath marks and caesuras

**Why:** No reference to `music21.articulations.BreathMark` or
`music21.articulations.Caesura` (confirmed those are the correct classes —
both live in `music21.articulations`, not `music21.expressions`) anywhere in
`musicxml_parser.py`; both are silently dropped on import.

**Blocked on:** S10c-2 (needs the model field this ticket adds).

**Steps:**
1. Map `music21.articulations.BreathMark` and `music21.articulations.Caesura`
   to whatever model S10c-2 lands. Note BANA gives breath/break marks two
   distinct signs (Table 22(B), "(a)" and "(b)") with no stated rule
   distinguishing when to use which in the portion of the manual reviewed for
   this ticket — confirm with the developer which print glyph(s) map to which
   braille sign before wiring this, rather than guessing.
2. Add a test importing a MusicXML fixture with a breath mark and a caesura.

**Definition of Done:**
- [x] Breath marks and caesuras import instead of silently disappearing.
- [x] New tests pass.

---

### [x] S10b-7: ~~Consolidate consecutive full-measure rests into multi-measure rests~~ -- superseded, see below

**Correction (found during implementation):** this ticket's original premise
was wrong. `translate_measure` does always set `multi_measure_count=1` on
import, but that's *correct*, not a bug -- every parser in this codebase
(BRF's `braille_parser.py`, the reverse `lilypond_parser.py`, and now
MusicXML) represents a run of full-measure rests as N separate one-measure
`Measure`/`Rest` objects, never as a single pre-merged `Rest`. Consolidation
into `R1*N` happens as a render-time lookahead pass already present in
`Staff.to_lilypond()` (`models/staff.py`), which runs over `staff.measures`
regardless of which parser produced them -- confirmed empirically: a
MusicXML import of 3 consecutive whole-measure rests already renders as
`R1*3`, no code change needed. So there is nothing to fix on the MusicXML
*import* side, and this ticket does not belong in an import-hardening sprint.

**A real, separate gap does exist, just not here:** `BrailleRenderer`
(`renderers/braille_renderer.py`) and `Rest.to_braille()` (`models/note.py`)
have no equivalent consolidation pass at all -- `Rest.to_braille()` never
branches on `multi_measure_count`, so BANA's compact multi-measure-rest sign
(Table 18: `⠍⠍` for 2 measures, `⠍⠍⠍` for 3, `⠼<digits>⠍` for 4+ -- the same
cells `braille_parser.py`'s `MULTI_MEASURE_REST` token already parses on the
way in) is never produced on the way out. This affects every source (BRF
round-trip, LilyPond import, MusicXML import) equally -- it isn't
MusicXML-specific, and fixing it means teaching `BrailleRenderer` a new
compression pass (alongside `_compress_articulations`/
`_compress_measure_repeats`) plus deciding how a merged run interacts with
per-measure line-packing and measure-number prefixing in `_render_solo`/
`_render_piano`/`_render_ensemble`, which is real design work, not a
one-line fix. Filed as **S11c-7** in the BRF-reformatting/robustness backlog
below rather than folded into this sprint.

**Definition of Done:**
- [x] Confirmed no MusicXML-import-side fix is needed (LilyPond output
      already correct via the existing `Staff.to_lilypond()` pass).
- [x] The real gap (BrailleRenderer never emits the compact BANA sign) is
      filed as its own correctly-scoped ticket (S11c-7) instead.

---

### [x] S10b-8: Verify and, if needed, fix ottava (8va/15ma) pitch handling on import

**Why:** No reference to `music21.spanner.Ottava` anywhere in
`musicxml_parser.py`. BANA's default (nonfacsimile) convention for 8va/15ma
is unambiguous — Par. 3.3: "the words '8va,' '15ma,' 'loco,' and similar
expressions are represented by transcribing the pitches in the octave in
which they are to be performed without noting the expressions" — i.e. no
special braille sign at all, just the real sounding octave. The open
question is whether the *pitch data DottedNotes reads from `music21`* is
already the sounding pitch or the as-notated (pre-shift) pitch — this was
not fully resolved during the code audit. A quick empirical check found
`Ottava.transposing` defaults to `True` and `music21` exposes explicit
`performTransposition()`/`undoTransposition()` methods, which suggests the
stored `Note.pitch` is *not* automatically the sounding pitch and may need
transposition applied before import — but this needs to be confirmed against
a real ottava-bearing fixture, not assumed.

**Steps:**
1. Build a small MusicXML fixture with an 8va passage (or find one) and trace
   exactly what pitch `translate_note_obj` currently receives for a note
   under the bracket, compared to the sounding pitch a musician would
   actually read off the page.
2. If the stored pitch is the pre-shift/notated pitch, apply the ottava's
   octave shift during import so the internal model always holds the
   sounding pitch, per BANA 3.3 — no special sign, no model changes needed
   beyond getting the octave right.
3. Add a regression test locking in the correct behavior either way.

**Definition of Done:**
- [x] Ottava-bracketed passages import at the correct sounding octave.
- [x] New tests pass.

---

# Sprint 10c: BANA Transcription for Fermatas, Breath Marks, and First/Second Endings

Estimated time: 1.5–2 weeks.

**Why this sprint exists:** Fermatas, breath/break marks, and first/second
endings (voltas) currently have **no representation anywhere in DottedNotes**
— not in `bana_symbols.py`, not in any model class, not in
`braille_renderer.py`, not in `docs/bana_reference.md` (confirmed by
grepping the whole tree). This sprint adds them from scratch: model support,
the BANA braille cells, `to_braille()` placement per BANA's rules, and
`to_lilypond()` output — and is a prerequisite for S10b-4/5/6, which only
wire MusicXML *import* into whatever model these tickets create.

All dot patterns below are **derived**, not developer-confirmed: they were
decoded mechanically from the BANA Music Braille Code 2015 manual's own ASCII
transcriptions in Tables 17 and 22(B), cross-referenced bit-for-bit against
this repo's existing `ASCII_TO_DOTS` table
(`src/dottednotes/parser/input_pipeline.py`) — the method CLAUDE.md
prescribes — not guessed from memory. Per CLAUDE.md, treat them as a starting
point for implementation, not a substitute for developer confirmation against
a real fixture before shipping.

---

### [ ] S10c-1: Add fermata sign support (model + `to_braille()` + `to_lilypond()`)

**Why:** BANA Music Braille Code 2015, Table 22(B) (Par. 22.2, "Symbols That
Follow the Note in Braille") defines seven fermata variants. Par. 22.2's
placement rule: "Any of the ... various fermata markings, given in Table
22(B), follows the affected note. If a value dot, a fingering, or an
interval is given for the note, that sign precedes the ... fermata."

**BANA dot patterns (Table 22(B), derived from `ASCII_TO_DOTS`, not yet
developer-confirmed):**
| Variant | BANA ASCII | Braille |
|---|---|---|
| over or under a note | `<l` | ⠣⠇ (dots 1-2-6, 1-2-3) |
| between notes | `"<l` | ⠐⠣⠇ (dot 5 prefix) |
| above/below a bar line | `_<l` | ⠸⠣⠇ (dots 4-5-6 prefix) |
| above/below a sectional double bar | `<k'<l` | ⠣⠅⠄⠣⠇ |
| above/below a final double bar | `<k<l` | ⠣⠅⠣⠇ |
| squared shape | `;<l` | ⠰⠣⠇ (dots 5-6 prefix) |
| tent-shaped | `^<l` | ⠘⠣⠇ (dots 4-5 prefix) |

Note BANA does **not** distinguish "over" vs. "under" (above/below the
staff) with different signs — one cell pair covers both, which conveniently
matches `music21.expressions.Fermata.type` (upright/inverted) being
irrelevant to the braille output; only `.shape` (normal/angled/square) picks
a different braille variant.

**Steps:**
1. Add the seven cells above to `bana_symbols.py`, following the file's
   existing citation/confidence-flagging convention (see e.g. the triplet
   sign's "developer-confirmed" comment for the format to match).
2. Add fermata support to the domain model. The over/under-note and squared/
   tent-shaped variants are Note-attached (scope the first pass to these);
   the bar-line/double-bar variants attach to the measure boundary instead
   and may be worth splitting into a follow-up ticket rather than
   overloading this one — flag this trade-off to the developer rather than
   deciding it unilaterally.
3. Implement `to_braille()` placement per Par. 22.2: after the note, after
   any value dot/fingering/interval sign, before the breath/break mark if
   both are present on the same note (Par. 22.2's ordering: value dot,
   fingering, interval, *then* breath/break mark or fermata). Wire this into
   the BANAValidator's existing sign-ordering rule (S9b) so a misordered
   fermata gets flagged like other sign-order violations.
4. Implement `to_lilypond()` — fetch LilyPond Notation Reference's
   "Expressive marks" section before writing this (CLAUDE.md's standing
   rule); `\fermata` is the expected postfix articulation but verify exact
   syntax and how shape variants (square/angled) are expressed, if at all,
   against the Notation Reference rather than assuming.
5. Unit tests for the model, `to_braille()` placement (including the
   value-dot/fingering/interval ordering interaction), and `to_lilypond()`.

**Definition of Done:**
- [ ] Fermata cells added to `bana_symbols.py` with confidence flags.
- [ ] Model support for at least the over/under-note variant.
- [ ] `to_braille()` places the sign correctly per Par. 22.2's ordering rule.
- [ ] `to_lilypond()` verified against the real LilyPond Notation Reference.
- [ ] BANAValidator's sign-order rule covers fermatas.
- [ ] Unit tests pass.

---

### [ ] S10c-2: Add breath/break mark sign support (model + `to_braille()` + `to_lilypond()`)

**Why:** BANA Music Braille Code 2015, Table 22(B) (Par. 22.2) gives two
breath/break mark signs, subject to the same "follows the note, after any
value dot/fingering/interval" placement rule as fermatas above.

**BANA dot patterns (derived from `ASCII_TO_DOTS`, not yet
developer-confirmed):**
| Variant | BANA ASCII | Braille |
|---|---|---|
| breath or break mark (a) | `>1` | ⠨⠂ (dots 3-4-5, dot 2) |
| breath or break mark (b) | `,/` | ⠠⠌ (dot 6, dots 3-4) |

The manual doesn't state, in the sections reviewed for this ticket, which
print glyph (comma-shaped breath mark vs. tick/caesura-style break, etc.)
maps to (a) vs. (b) — **do not guess this mapping; confirm with the
developer before implementing**, per CLAUDE.md.

**Steps:**
1. Get the (a)/(b) print-glyph mapping confirmed by the developer first.
2. Add both cells to `bana_symbols.py` with confidence flags.
3. Add model support — likely Note-attached, same shape as S10c-1's
   over/under-note fermata field.
4. Implement `to_braille()` placement per Par. 22.2 (same ordering rule as
   fermatas — value dot/fingering/interval, then breath/break mark).
5. Implement `to_lilypond()` — fetch the Notation Reference's "Expressive
   marks" section first; `\breathe` is the expected LilyPond construct
   (inserted as a standalone event between notes, not attached to one), but
   verify against the Notation Reference rather than assuming, since its
   placement model differs from postfix articulations like `\fermata`.
6. Unit tests for the model, `to_braille()` placement, and `to_lilypond()`.

**Definition of Done:**
- [ ] (a)/(b) glyph mapping confirmed by the developer.
- [ ] Breath/break mark cells added to `bana_symbols.py` with confidence flags.
- [ ] Model, `to_braille()`, and `to_lilypond()` support implemented.
- [ ] Unit tests pass.

---

### [ ] S10c-3: Add first/second ending (volta) support (model + `to_braille()` + `to_lilypond()`)

**Why:** BANA Music Braille Code 2015, Chapter 17 "Print Repeats" (Table 17),
Par. 17.1.1 "Voltas": "The sign for a volta (alternate ending) is placed
without intervening space before the first sign connected with the measure
in which it occurs. The first note after the sign requires a special octave
mark. If the sign following the volta sign contains a dot 1, 2, or 3, the
volta sign must be followed by a dot 3 as a separator," plus: (a) multiple
voltas may share a line if there's room; (b) combined print endings ("1,2")
get each numeral its own numeric indicator unless following a hyphen, and a
hyphen showing a numeral range (e.g. "1-3") is followed in braille; (c) the
print bracket above the measure(s) is not itself brailled — only the
numeral(s).

**BANA dot pattern (Table 17):** Prima volta (1st ending) = `#1`, Seconda
volta (2nd ending) = `#2`. Decoded: `#` is `NUMBER_SIGN` (⠼, dots 3-4-5-6,
already defined in `bana_symbols.py`), and `1`/`2` are `LOWER_DIGIT_CELLS`'
existing entries (⠂ dot 2, ⠆ dots 2-3 — both already marked
**confirmed** elsewhere in `bana_symbols.py` for measure-number digits). So
first/second endings reuse two already-confirmed cells (⠼⠂ and ⠼⠆); what's
*not* yet confirmed is that this specific usage (numeral immediately after
the number sign, meaning "ending number" rather than "measure number") is
correct — flag that distinction to the developer rather than assuming the
existing confirmation carries over.

**Steps:**
1. Add a `Measure`-level ending-number field (e.g. `ending_numbers:
   list[int] | None`, alongside the existing `bar_line_type` field this
   mirrors), able to hold a combined/ranged set of numbers per Par.
   17.1.1(b).
2. Implement `to_braille()` placement per Par. 17.1.1: immediately before the
   first sign of the measure (no space, no dot-3 separator unless the
   following sign has a dot 1/2/3), forcing a special octave mark on the
   first note of the measure (reuse the existing octave-mark-reset machinery
   the BANAValidator/`Note.to_braille()` already has for other "requires
   fresh octave mark" triggers, per CLAUDE.md's note on that logic), and
   correct handling of combined/ranged numbers per 17.1.1(b)-(c).
3. Implement `to_lilypond()` — fetch the Notation Reference's "Repeats"
   section first; `\repeat volta N { ... } \alternative { {...} {...} }` is
   the expected construct, but verify exact syntax against the Notation
   Reference rather than assuming, especially for how it interacts with
   `\relative` pitch tracking (per this project's standing rule to verify
   `\relative` claims against the real binary, given the `<< \\ >>` bug found
   earlier this project — an `\alternative` block has its own pitch-chaining
   behavior that shouldn't be assumed by analogy).
4. Unit tests: model, `to_braille()` (including a combined "1,2" and a
   ranged "1-3" ending), and `to_lilypond()`.

**Definition of Done:**
- [ ] `Measure` carries ending-number data.
- [ ] Volta cells reuse the existing confirmed `NUMBER_SIGN`/
      `LOWER_DIGIT_CELLS` constants; the ending-number *usage* is flagged for
      developer confirmation.
- [ ] `to_braille()` implements Par. 17.1.1's placement, octave-mark, and
      combined/ranged-numeral rules.
- [ ] `to_lilypond()` verified against the real LilyPond Notation Reference
      and, if `\relative` is involved, the real `lilypond` binary.
- [ ] Unit tests pass.

**Follow-up completed:** `to_lilypond()`'s real `\repeat volta N { ... }
\alternative { \volta k {...} ... }` generation, initially deferred to a
`% ending N` comment pending `\relative`-across-`\alternative` verification,
was implemented as a follow-up once that verification was done (compiled
`\repeat volta`/`\alternative`/`\volta k` through the real `lilypond` 2.24.4
binary and dumped `\displayLilyMusic`: all three are no-ops for `\relative`
pitch tracking, pure sequential chaining, same as `<< \\ >>`). Lives in
`Staff.to_lilypond()` (`_find_volta_groups()`/`_render_volta_group()`), not
`Measure.to_lilypond()`, since the structure wraps a whole measure range.
Doing this also surfaced and fixed a real bug: MusicXML import/export had
`forward_repeat` on the wrong measure relative to this codebase's own
tested convention (see the "Fix MusicXML forward_repeat attachment..."
commit).

---

### [ ] S10c-4: Wire fermatas, breath marks, and voltas through MusicXML import and export

**Why:** S10c-1/2/3 add the model/braille/LilyPond support; this ticket
closes the loop by unblocking S10b-4/5/6 (MusicXML → model import) and
adding the matching model → MusicXML export path in
`renderers/musicxml_renderer.py`, so these signs survive a full BRF ↔
MusicXML round trip, not just BRF ↔ LilyPond.

**Steps:**
1. Complete S10b-4, S10b-5, and S10b-6 now that the model fields they need
   exist.
2. Add the reverse mapping in `musicxml_renderer.py`: model fermata/breath-
   mark/ending data → `music21.expressions.Fermata` /
   `music21.articulations.BreathMark`/`Caesura` / `music21.spanner.
   RepeatBracket`.
3. Extend `tests/test_musicxml_integration.py` with a round-trip test (BRF
   with a fermata/breath mark/volta → model → MusicXML → model) asserting
   the sign survives the round trip.

**Definition of Done:**
- [ ] S10b-4, S10b-5, S10b-6 complete.
- [ ] Export path implemented in `musicxml_renderer.py`.
- [ ] Round-trip test passes.

---

### [ ] S10c-5: ~~BANAValidator~~ docs and test coverage for all three signs -- BANAValidator wiring found infeasible without BRF tokenizer support

**Correction (found during implementation):** step 1's premise doesn't
hold. `BANAValidator._validate_sign_order` (`validation/validator.py`)
validates `Note.parsed_tokens` — the `BrailleToken`s the BRF
tokenizer/parser produced for that note — not the model's `to_braille()`
output. Fermatas, breath marks, and voltas are only wired up on the
MusicXML import path (S10b-4/5/6); `tokenizer.py`/`braille_parser.py` don't
recognize any of these three cell families at all, so a MusicXML-imported
note's `Note.fermata`/`.breath_mark` never has a corresponding
`parsed_tokens` entry to validate the order of. Extending the rule would
mean adding real BRF-side tokenization/parsing for three new cell
families first (checking for collisions with the existing heavily-overloaded
cell space, per this project's usual caution) — unscoped work belonging to
its own ticket, not a one-step addition here. Step 2 (volta placement) has
the same problem: `Measure.ending_numbers` is a data field with no record
of *where* in a source file a volta sign appeared, so there's nothing
position-based to validate against once it's already in the model.

Steps 3 and 4 (docs, full test pass) are unaffected and completed as
written — see `docs/bana_reference.md`'s new "Fermatas, Breath Marks, and
First/Second Endings (Sprint 10c)" section, which also documents this same
BRF-import gap in its own "Known scope gap" subsection so it doesn't have
to be rediscovered.

**Definition of Done:**
- [x] `docs/bana_reference.md` updated with citations for all three signs.
- [x] BANAValidator sign-order wiring confirmed infeasible without BRF
      tokenizer support; gap documented in both TICKETS.md and
      `docs/bana_reference.md` rather than silently skipped.
- [x] `pytest tests/` passes (936 tests as of this ticket).

---

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

**Sprint 11c: BRF Reformatting & Malformed Input Robustness (future sprint)**
- [ ] S11c-1: Add test cases and validator rules for malformed .brf music files, such as having measure numbers or notes in the left margins when the score is an ensemble score.
- [x] S11c-2: Implement BANA Page Layout and Formatting Rules for Braille Export
- [ ] S11c-7: Teach `BrailleRenderer`/`Rest.to_braille()` to emit BANA's compact multi-measure-rest sign (Table 18) for a run of consecutive full-measure rests, instead of one whole-rest cell per measure -- found while working S10b-7; affects BRF round-trip, LilyPond import, and MusicXML import equally, not source-specific. Needs a design decision on how a merged run interacts with `_render_solo`/`_render_piano`/`_render_ensemble`'s per-measure line-packing and measure-number prefixing, alongside the existing `_compress_articulations`/`_compress_measure_repeats` passes.

**Sprint 12: OMR Import via Audiveris (shelved 2026-07-19 -- see tickets)**
- [Shelved] S12-1: Integrate Audiveris as a subprocess PDF -> MusicXML import step (CLI + web backend)
- [Shelved] S12-2: Surface an OMR/MusicXML quality report in the web UI, alongside the existing BANA and LilyPond compile reports

---

### [x] S11c-2: Implement BANA Page Layout and Formatting Rules for Braille Export

**Why:** To ensure that exported braille scores are fully compliant with standard BANA page layout and formatting guidelines, making them easy and natural for blind musicians to read using physical embossers or refreshable braille displays.

**BANA Page Layout and Formatting Rules Compilation & Citations:**
1. **Title Centering (MBC 2015, Part IV, Section 31.1 / Section 32.1)**
   - The composition title must be centered as a literary heading on the first page of music. It must be centered within the page line width (default 40 cells) and have at least 3 blank cells on each side.
2. **Key and Time Signature Placement (MBC 2015, Part I, Section 21 & Part IV, Section 31.5)**
   - Key and time signatures must be written as a combined unit without any intervening spaces.
   - In solo instrument formatting, the signature unit should be placed on a separate line indented by 8 spaces (starting in cell 9) directly below the title. If the signatures and initial tempo/expression markings are centered, they must have at least 3 blank cells on each side.
3. **No Intervening Blank Lines (MBC 2015, Part IV, Section 32.2.1)**
   - There must be no blank lines between the title/signature header line and the first line of the music.
4. **Running Heads on Subsequent Pages (MBC 2015, Part IV, Section 32.1)**
   - Centered running heads (abbreviated titles) are required on the first line of all braille pages following the first page of music.
   - The running head must be centered and have at least 3 blank cells of separation from the print page numbers on the left and braille page numbers on the right.
5. **Blank Line Preceding Headings (MBC 2015, Part IV, Section 32.2)**
   - A blank line must precede the initial music heading of a composition, movement, or part, unless it starts at the top of a page immediately following a running head.
6. **Spacing Between Parallels (MBC 2015, Part IV, Section 32.3)**
   - Consecutive parallels must be separated by at least 1 blank line (for solo music) or 2 blank lines (for keyboard/organ music parallels).
7. **Line Indentation and Run-overs (MBC 2015, Part I, Section 1.3 & Part II, Section 26.1 & Part III, Section 29.1)**
   - In solo/bar-over-bar formats, main music lines start in cell 1, and run-over lines must be indented to cell 3.
   - In vocal formats (line-by-line), lyrics lines start in cell 1, music lines are indented to cell 3 (indented by 2 spaces), and run-over lines of both are indented to cell 5 (indented by 4 spaces).

**Definition of Done:**
- [x] Braille export format strictly centers titles with at least 3 blank cells on each side.
- [x] Key and time signatures are combined as a single unit without spaces.
- [x] For solo formatting, signature lines are indented by 8 spaces (starting in cell 9) on the line below the title.
- [x] No blank line is present between the signature/header line and the first music line.
- [x] Multi-page exports include centered running heads on line 1 of page 2 onwards, padded by at least 3 blank cells from page numbers.
- [x] Consecutive parallels are separated by exactly 1 blank line for solo scores and 2 blank lines for keyboard scores.
- [x] Run-over lines are properly indented (to cell 3 for solo/keyboard, cell 5 for vocal).
- [x] All unit and integration tests pass.

---

### [x] S11c-3: Implement Measure Numbers in Braille Music and UI Integration

**Why:** The user wants to easily locate and reference measures in both braille music and LilyPond. Emitting measure numbers helps blind musicians keep track of score positions. Adding a checkbox in the web UI lets users toggle this option dynamically.

**Steps:**
1. Update `src/dottednotes/static/index.html` to include a checkbox "Include Measure Numbers" in the settings grid. Add corresponding styling in `src/dottednotes/static/style.css` if needed.
2. Update the `/api/convert` endpoint in `src/dottednotes/web.py` to accept a `measure_numbers: bool = Form(False)` field and pass it to both `to_lilypond` and `to_braille`.
3. Update `Score.to_braille` in `src/dottednotes/models/score.py` to accept `measure_numbers` and pass it to `BrailleRenderer`.
4. Update CLI (`src/dottednotes/cli.py`) to pass the `--measure-numbers` flag to `to_braille`.
5. Update `BrailleRenderer` in `src/dottednotes/renderers/braille_renderer.py` to format measure numbers per BANA rules:
   - For **solo and solo piano** formats: format the measure numbers using literary digits **without** the number sign (e.g. `BJ` for measure 20), followed by a space.
   - For **ensemble** formats: format the measure numbers using literary digits **with** the number sign (e.g. `#BJ` / `⠼⠃⠚`), aligned vertically in the heading line above each measure's start in the top staff.
6. Write comprehensive unit and integration tests verifying the measure number formatting for all layouts (solo, piano, ensemble) and the UI/API checkbox integration.

**Definition of Done:**
- [x] UI has a checkbox for measure numbers.
- [x] Backend endpoint `/api/convert` accepts `measure_numbers` form parameter.
- [x] For solo/piano format, measure numbers are printed in the left margin without number sign, followed by a space.
- [x] For ensemble format, measure numbers are printed above each measure's start, preceded by the number sign.
- [x] Omitted or disabled measure numbers do not print numbers at all.
- [x] Existing tests and new tests all pass.

---

### [x] S11c-4: Support .brl (Unicode) and .brf (ASCII) Braille Export

**Why:** The user wants to support both `.brf` (ASCII Braille text) and `.brl` (Unicode Braille dots) file formats. Currently, DottedNotes writes Unicode braille to `.brf` files, which is incorrect as `.brf` files should contain standard ASCII braille. Adding `.brl` provides proper support for modern screen readers and braille displays attached to computers.

**Steps:**
1. Update `src/dottednotes/static/index.html` to add options for both `.brf` (ASCII) and `.brl` (Unicode) braille.
2. Update `src/dottednotes/static/app.js` to enable setting overrides/controls for both formats.
3. Update `BRFWriter` in `src/dottednotes/renderers/brf_writer.py` to support `compression_level` and write raw Unicode braille for `.brl`.
4. Update FastAPI backend `web.py` to route `target_format` of `brf` and `brl` to the paginated `BRFWriter`.
5. Update `cli.py` to write ASCII or Unicode braille based on output file extension (`.brf` vs `.brl`).
6. Write tests verifying the formats.

**Definition of Done:**
- [x] UI dropdown has "Braille Music (.brf)" and "Braille Music (.brl)".
- [x] Web backend routes both formats correctly.
- [x] `.brf` files contain only ASCII braille characters.
- [x] `.brl` files contain raw Unicode braille characters.
- [x] CLI correctly differentiates formats by extension.
- [x] Existing tests and new tests all pass.

---

### [x] S11c-5: Accessible UI Empty-State Handlers for Result Reports

**Why:** The results UI has three main report blocks (BANA violations table, Generated downloads, and LilyPond compilation report) which render in an ambiguous/hidden state before a file is parsed. We want these sections to transition cleanly through four explicit states: (1) No file uploaded yet, (2) Awaiting translation / in progress, (3) Translation complete but nothing to report, (4) Content present. The messages must be fully accessible and announced to screen readers.

**Steps:**
1. Update `TICKETS.md` (this ticket).
2. Add `.badge.neutral` style to `src/dottednotes/static/style.css`. Remove `.hidden` class from parent `#result-section` and `#validation-section` classes in `index.html` to keep cards persistently rendered.
3. Add status wrappers with `aria-live="polite"` to `index.html` for downloads, compile log, and validation reports.
4. Implement `updateSectionState` helper in `app.js` and hook it into DOM initialization, file select, form submit, conversion success, and conversion failure lifecycles.
5. Verify screen reader landmarks, semantic accessibility markup, and visual states.

**Definition of Done:**
- [x] BANA report, downloads, and compilation logs transition correctly through all 4 states.
- [x] No file structures (tables, lists, pre blocks) render when empty or not applicable.
- [x] State messages have appropriate `aria-live` regions or semantic markup.
- [x] All 880+ existing test cases pass.

---

### [x] S11c-6: Fix Braille Formatting Bugs in Ensemble and Piano Layouts

**Why:** Several formatting discrepancies and layout bugs have been identified when transcribing `fengyang_flower_drum.ly` and `children_s_piece.ly` to braille (`.brl`/`.brf`). Addressing these ensures strict compliance with BANA braille music formatting rules.

**Steps:**
1. **Remove unnecessary blank lines between ensemble parallel systems:**
   - In `src/dottednotes/renderers/braille_renderer.py`, locate `_render_ensemble()`.
   - Remove the code block that appends a blank line when `idx > 0`. (The "blank line" separation in BANA 33.4.6/34.4.6 refers to the sparse heading line containing the measure/rehearsal numbers, so an additional empty line is incorrect).

2. **Fix literary braille double-capital capitalization rule:**
   - In `src/dottednotes/renderers/braille_renderer.py`, update `encode_literary_braille()` to check if a word (or the entire text, if single word) is in all caps (such as "II").
   - If a word is in all caps (consists of 2 or more uppercase letters), prefix it with a double capital sign (`⠠⠠`) instead of prefixing each character individually with a single capital sign (`⠠`).

3. **Position measure numbers correctly for subsequent measures in ensemble heading lines:**
   - In `_render_ensemble()`, adjust the column calculation for measure numbers.
   - When placing measure numbers, ensure that the second measure's number `#B` is indented one cell beyond the music of measure 2 on the next line (the staff lines below it), rather than being placed right next to the number of the first measure.

4. **Correct multi-measure rests in LilypondParser:**
   - In `src/dottednotes/parser/lilypond_parser.py`, when parsing a Rest that has a `multi_measure_count > 1` (e.g. `R1*45`), expand it into `multi_measure_count` separate `Measure` objects containing single-measure rests.
   - This ensures the subsequent measures are positioned at the correct measure numbers (e.g. Flute starts at Measure 46 instead of Measure 1/2).

5. **Format Violin I and Violin II abbreviations correctly:**
   - In `src/dottednotes/renderers/braille_renderer.py`, ensure the instrument abbreviations (like `v1` and `v2`) are rendered as lowercase letter `v` + lower-cell digits (e.g., `⠧⠂` for `v1`, `⠧⠆` for `v2`) rather than upper-cell digits with number signs (e.g., `v#A`).
   - Create a helper `abbrev_to_brl(abbrev: str)` that maps letters to their standard braille cells and digits to their lower-cell equivalents (as defined in `ASCII_TO_DOTS` mapping). Use it in both the instrument list and the system lines prefix.

6. **Separate tempo and key/time signatures with a space:**
   - In `braille_renderer.py`, update `_render_solo()`, `_render_piano()`, and `_render_ensemble()` to ensure that the tempo/expression marking (if present) is separated from the combined key/time signature unit by a single space.

7. **Ensure identical indent for left and right hand parts in piano layout:**
   - In `src/dottednotes/renderers/brf_writer.py`, avoid prepending the form feed character `\f` directly to the first music line of a new page, which shifts the right hand line's column index.
   - Instead, place the form feed `\f` on its own line (or end each page with `\f\n`) so it doesn't affect the text alignment of the next page's first line.

8. **Remove unnecessary blank lines between parallels in piano layout:**
   - In `src/dottednotes/renderers/braille_renderer.py`, locate `_render_piano()`.
   - Remove the lines appending two blank lines when `idx > 0`.

**Definition of Done:**
- [x] Ensemble scores do not have separate blank lines between parallel systems (the measure number line is the only separator).
- [x] Capitalized words (e.g., "II") are prefixed with double capital sign `⠠⠠` rather than repeating `⠠` for each letter.
- [x] Ensemble measure numbers are aligned 1 cell past the start of their corresponding measure's music.
- [x] LilyPond multi-measure rests (e.g., `R1*45`) expand into individual measure rest objects, and the subsequent measures are numbered correctly.
- [x] Violin I/II abbreviations format as `⠧⠂` / `⠧⠆` (lowercase v + lower-cell digit) in both headers and prefixes.
- [x] Tempo is separated from key/time signatures by one space.
- [x] Left and right hand lines in piano layout align perfectly at the same indentation cell even across page boundaries.
- [x] Consecutive piano parallel systems are not separated by blank lines.
- [x] All unit and integration tests pass.

---

### [Shelved] S12-1: Integrate Audiveris as a subprocess PDF -> MusicXML import step

**Why shelved:** Audiveris is a JVM-based OMR engine with a much heavier runtime footprint than anything else this project shells out to (see the original ticket's point 2) -- running it in the hosted web UI would require upgrading Render past the Starter plan. Shelved 2026-07-19 to avoid that cost for now, not because the design is wrong. Revisit if/when a higher-tier plan is worth it, or if a lighter-weight OMR engine becomes viable (oemer was evaluated as an alternative the same day and rejected too -- no native PDF support, weak grand-staff/piano handling, no lyrics OCR, no confidence signal -- see chat history/session notes rather than a second shelved ticket here).

<details>
<summary>Original ticket text</summary>

**Why:** Blind composers currently can't transcribe a score that only exists as a printed/scanned PDF -- they need a sighted collaborator to re-enter it by hand first. Audiveris (an open-source, actively maintained OMR engine) can recognize a PDF and export MusicXML, which this project's existing `musicxml_parser.py`/`load_musicxml()` already consumes unmodified, so this is an *import*-side addition, not a new transcription target. Audiveris was chosen over PlayScore 2 specifically because it has a real headless CLI (`-batch -export`), is free with no restriction on the output, and fits the subprocess pattern this codebase already uses for `lilypond` (`cli.py`'s `_compile_with_lilypond()` / `web.py`'s `compile_with_lilypond()`).

Two things must not get lost in implementation:
1. **Accuracy is the real risk, not the subprocess call.** Audiveris' own published error rate is ~3.9% of symbols on clean, digitally-typeset scores -- and that's the *best* case; scans, dense/orchestral writing, and unusual notation are worse. Unlike a sighted user, a blind composer cannot visually proofread the recognized MusicXML against the original PDF page. **S12-2 (the OMR quality report) is what makes this safe to ship and should land in the same release as this ticket, not be deferred as a follow-up "nice to have."**
2. **This is a much heavier runtime dependency than `lilypond`.** Audiveris needs a JVM (the official distribution bundles its own JRE) and pulls in Tesseract OCR via bundled libraries for lyrics/text recognition (which still needs separately downloaded language-data files). `web.py`'s `MAX_UPLOAD_SIZE` comment already documents that Render Starter's 512MB is tight for the existing pure-Python pipeline alone -- running a JVM-based OMR engine needs its own explicit memory/CPU budget decision for the hosted web UI before this ships there, not just for local CLI use.

**Steps:**
1. Document how to install the `audiveris` CLI locally (README), matching how `lilypond` is documented today. Decide how/whether it's added to `Dockerfile` (currently `python:3.11-slim-bookworm` + `apt-get install lilypond`) given its far larger footprint -- likely a separate build stage or a documented "not available on the hosted demo" limitation rather than assuming it fits the same image.
2. Add `AudiverisError(DottedNotesError)` to `exceptions.py`, mirroring `LilyPondCompileError`'s shape (`message`, optional `stderr`).
3. Add a bridge helper (new `src/dottednotes/parser/audiveris_bridge.py`, parallel to how `musicxml_parser.py`/`lilypond_parser.py` are organized): `convert_pdf_to_musicxml(pdf_path: Path, output_dir: Path) -> Path`.
   - Check `shutil.which("audiveris")` (or a configurable path/env var); raise `AudiverisError` with an actionable message if missing.
   - Run `audiveris -batch -export -output <output_dir> <pdf_path>` via `subprocess.run(capture_output=True, timeout=...)`; raise `AudiverisError(stderr=...)` on non-zero exit or timeout -- mirror `_compile_with_lilypond()`'s exact error-handling shape in `cli.py`.
   - Locate the resulting `.mxl`/`.musicxml` file(s) in `output_dir`. Audiveris exports one MusicXML file per "movement" it detects -- decide explicitly how a multi-movement PDF is handled (e.g. convert each separately and let the user pick, or require single-movement input for now) rather than silently taking "the first file."
4. Wire `.pdf` as a new recognized input extension in `cli.py`'s `_run_convert()` (`is_pdf_input = input_path.suffix.lower() == ".pdf"`), calling the bridge helper first and handing its MusicXML output to the existing, unmodified `load_musicxml()` -- no changes needed inside `musicxml_parser.py` itself.
5. Wire the same detection into `web.py`'s `/api/convert` (a new `input_type = "pdf"` alongside the existing `"braille"`/`"musicxml"`/`"lilypond"` values), calling the bridge helper before the existing `load_musicxml()` call.
6. Update `static/index.html`'s upload-subtext/file-instructions to mention `.pdf`, and add a clear, prominent warning in the UI copy itself (not just README docs) that PDF import uses automated OMR and is not guaranteed accurate. This minimal warning must ship with this ticket even if S12-2's full report isn't ready yet.
7. Add test fixtures covering both a clean digitally-typeset PDF *and* a lower-quality scanned PDF -- testing only the pristine case would hide the exact failure mode (unverifiable misreads) that matters most for this feature.
8. Write tests: unit tests for `AudiverisError` handling (missing binary, non-zero exit, timeout) against a mocked/stubbed subprocess call, plus a real end-to-end conversion test gated on `shutil.which("audiveris")` (mirroring how LilyPond-compile tests are skipped in CI when the binary isn't installed).

**Definition of Done:**
- [ ] `dottednotes convert score.pdf output.brl` (and other target formats) works end to end when Audiveris is installed, producing the same output shape as an equivalent `.musicxml` input would.
- [ ] A missing or failing Audiveris binary produces a plain-text `AudiverisError` message (CLI) / structured error response (web) -- never a raw traceback or silently wrong output.
- [ ] Web UI accepts `.pdf` uploads, respects `MAX_UPLOAD_SIZE`, and visibly warns that PDF import is unverified OMR output before the user downloads anything.
- [ ] Multi-movement PDF handling is an explicit, documented decision, not a silent "first file wins."
- [ ] New tests (mocked-subprocess unit tests + a real-Audiveris-gated integration test) pass; existing test suite has no regressions.
- [ ] README/Dockerfile document the new dependency and its resource cost.

</details>

---

### [Shelved] S12-2: Surface an OMR/MusicXML quality report in the web UI

**Why shelved:** Depends entirely on S12-1 landing first; shelved alongside it 2026-07-19 for the same hosting-cost reason. Revisit together with S12-1.

<details>
<summary>Original ticket text</summary>

**Why:** Per S12-1's accuracy caveat: OMR misreads are the one place in this entire pipeline a blind composer cannot independently verify against the source, since they can't visually compare the recognized MusicXML/braille back to the original PDF page. The web UI already has a working precedent for exactly this kind of post-conversion trust signal: the "BANA Formatting Rule Report" (`validation_report`, backed by `BANAValidator`) and the LilyPond compile status/log (`compile_success`/`compile_error`) in `web.py`'s `/api/convert` response, rendered by `showResults()`/`updateSectionState()` in `static/app.js` and the `#validation-section`/`#result-section` markup in `static/index.html`. This ticket adds a third report of the same shape, specific to OMR-derived input, so a blind composer gets a clear signal of which measures an OMR engine itself was unsure about and should have a sighted collaborator double-check.

**Steps:**
1. Investigate what confidence/quality signals Audiveris actually exposes in batch/CLI mode (its own `.omr` project file, sheet-level log/warning output, or per-symbol confidence data) -- confirm this against Audiveris' own documentation/source before assuming a specific shape exists. Don't guess this the way this project never guesses BANA dot patterns without checking the primary source first.
2. Design an `OMRFinding`/`OMRReport` shape analogous to `validation.validator.Correction` (`measure_number`, `severity`, `message`, and likely a `confidence` field) -- reuse `Correction`'s exact JSON shape if it fits well enough, so the frontend can mostly reuse `showResults()`'s existing per-row table rendering rather than duplicating it.
3. Parse Audiveris' quality/confidence output (per step 1) into a list of these findings, run right after S12-1's bridge step, before handing off to `load_musicxml()`.
4. Thread this through `cli.py` (e.g. extending the existing `--report` flag to also cover PDF input) and `web.py`'s `/api/convert` response as a new `omr_report` field (list of finding dicts), plus an `omr_success`/`omr_error` pair for when Audiveris fails outright (mirroring `compile_success`/`compile_error`'s existing shape).
5. Add a third report section to `static/index.html` (an `#omr-section` card, "OMR Recognition Quality Report", following `#validation-section`'s existing markup pattern) and wire it into `app.js`'s `showResults()`/`updateSectionState()`, reusing the existing per-row table rendering rather than duplicating it.
6. Make the UI copy explicit that this report reflects the OMR engine's own confidence signal, not a correctness guarantee -- an empty/clean report must not read to the user as "verified correct."
7. Write tests: unit tests for the Audiveris-output-to-`OMRFinding`-list parsing (against recorded/fixture Audiveris output, not a live subprocess call), and a web/API test asserting the new response field's shape and the three report sections' independent state transitions (mirroring S11c-5's empty/present state-transition tests for the existing reports).

**Definition of Done:**
- [ ] Web UI shows a third "OMR Recognition Quality Report" section after a `.pdf` conversion, in the same accessible style (ARIA live regions, table, explicit state transitions) as the existing BANA and LilyPond compile reports.
- [ ] The report is driven by Audiveris' own confidence/warning data, verified against its actual documented output format, not inferred/guessed.
- [ ] The report section is empty/not-applicable for non-PDF input types, matching how the compile report is already "not_applicable" for non-LilyPond targets.
- [ ] UI copy makes clear this is an automated confidence signal, not a correctness guarantee.
- [ ] New tests pass; existing test suite has no regressions.

</details>

---

# Sprint 10d: MusicXML Import Hardening, Round 2

Estimated time: 2–3 weeks.

**Why this sprint exists:** DottedNotes currently has no solo instruments
besides piano tested against real-world input, so a real OMR-sourced
MusicXML solo flute piece (Gerhard Roberto, *Capriccio No. 2*,
`tests/fixtures/gerhard_roberto_capriccio2_for_flute.xml`) was used as a
stress test, alongside the (unofficial but widely used) MusicXML Test Suite
at `~/workspace/musicxmlTestSuite` (150 files, covering nearly every
MusicXML tag/attribute in isolation). Converting the flute piece all the
way to `.brf` surfaced a real crash (S10d-0, already fixed below) and a
serious validator-consistency bug (S10d-1); running all 150 test-suite
files through `load_musicxml()` + `BrailleRenderer` surfaced 7 further
crashes and ~20 distinct "succeeded but silently wrong or dropped content"
patterns. This sprint catalogs the ones judged worth a dedicated ticket,
each already grounded in a specific repro file and, where one exists, a
BANA Music Braille Code 2015 citation -- confirm any dot patterns quoted
below against `bana_symbols.py`/the manual directly before implementing,
per this file's standing rule; none of these have been developer-confirmed
yet.

**Already fixed while surveying (not a ticket, just for traceability):** a
`Tuplet`/`InAccord`-voice/`AlternatingTremolo` whose last item is a bare
`Rest` was propagated as the "previous note" for the next item's octave-
interval comparison, crashing with `AttributeError: 'Rest' object has no
attribute 'octave'` the first time real music hit it (confirmed: measure 7
of the flute piece, a triplet ending in a rest). Fixed via a shared
`_last_real_note()` helper in `models/measure.py` that skips rests and
recurses into nested tuplets instead of falling back to whatever the last
raw item happened to be.

---

### [ ] S10d-1: BANAValidator's octave-mark rule floods false positives on any multi-measure-per-line output

**Why:** `--report` flagged "Missing octave mark" on essentially every
measure of the flute piece (229 corrections, out of ~165 measures) --- and
the same false-positive flood reproduces on an existing, unmodified BRF
fixture too (`fengyang_flower_drum.brf`: 97 false positives), so this is
not a MusicXML-specific bug. `validation/validator.py`'s
`_validate_octave_marks()` (line ~281) treats *every measure boundary* as
an octave-mark reset point:
```python
elif last_measure_number is not None and m_num != last_measure_number:
    # BANA resets octave tracking at every measure boundary, not
    # just line starts -- Note.to_braille() (the actual renderer)
    # already forces an octave mark whenever is_measure_start is
    # True, regardless of interval size. This mirrors that rule.
    is_reset = True
```
That comment describes the renderer's behavior *before* this project's own
"Fix missing line-start octave marks and word signs in braille output"
commit. `BrailleRenderer._render_solo` (and the piano/ensemble equivalents)
now only force `is_measure_start=True` for a measure that starts a new
*physical braille line* -- mid-line measures don't get it unless
`octave_mark_every_measure` is on -- matching BANA 3.2.1 ("The octave is
always marked for the first note of a braille line..."), not "every
measure." The validator's copy of this rule was never updated to match,
so it now disagrees with the renderer it's supposed to be checking.

**The hard part:** "is this measure boundary also a line boundary" is a
*render-time* decision (depends on `line_width`, compression, hand/
ensemble layout) that the validator currently has no access to -- it
operates on the parsed `Score` alone. Fixing this properly likely means
either (a) having `BANAValidator` accept the actual rendered line-break
positions from a `BrailleRenderer` pass and check against those, or (b) if
line breaks turn out to be reproducible from the score alone under the
same settings the caller intends to render with, threading that same
`line_width`/settings through to the validator so it can compute the same
packing decision independently. Don't guess which -- read
`BrailleRenderer._render_solo`/`_render_ensemble`'s packing loops first to
see whether (b) is actually feasible without duplicating significant
layout logic before choosing.

**Update:** Fixed via `raw_brl_text` re-tokenizing rather than a
`BrailleRenderer` pass -- `BANAValidator._build_measure_line_map()`
(`validation/validator.py`) tokenizes the already-available `raw_brl_text`
(literal source text for BRF/BRL input; a fresh `score.to_braille()` render
for MusicXML/LilyPond input, see S10d-2's update) and segments it into
measures on BAR_LINE boundaries *and* physical-line changes (this parser's
grammar treats every new line as an implicit measure boundary too, even
with no bar-line cell written). `_validate_octave_marks`'s reset check now
asks "does this measure's mapped line differ from the previous measure's
mapped line" instead of "did the measure number change" -- matching
`BrailleRenderer`'s real, line-start-only BANA 3.2.1 behavior. When no line
map is available (`validate()` called without `raw_brl_text`, or a
multi-staff/piano/ensemble score -- deliberately out of scope for now, see
below), falls back to the original `parsed_tokens`-based comparison.
False-positive count on `fengyang_flower_drum.brf` confirmed dropped from
97 to 0 (all 97 were from the "every measure" bug, none were genuine).
Regression tests updated in `tests/test_validation.py`
(`test_validation_octave_marks_reset_points`,
`test_validation_octave_marks_new_measure_same_line` -- the latter's core
assertion inverted, since a same-line second measure correctly gets *no*
forced-mark correction now). Full suite (1008 tests) passes with no
regressions.

**Deliberately out of scope:** the line map is only built for single-staff
(solo) scores (`len(score.staves) == 1`) -- a multi-staff rendering (piano
bar-over-bar, ensemble parallels per BANA §33) interleaves several staves'
tokens per physical line, which this per-staff sequential BAR_LINE/line-
change walk can't disambiguate without much more work. Multi-staff scores
keep using the old `parsed_tokens`-based fallback (still correct for
BRF-sourced multi-staff input, e.g. `fengyang_flower_drum.brf`'s 6-staff
ensemble verified above; still says "Line 1" for a MusicXML/LilyPond-
sourced multi-staff score, unchanged from before this fix).

**Residual limitation found, not fixed here (needs its own ticket):**
`_validate_octave_marks`'s "has_mark" check (`curr_note.has_octave_mark or
any(t.category == OCTAVE_MARK for t in curr_note.parsed_tokens)`) is always
`False` for MusicXML/LilyPond-imported notes, regardless of what the
renderer actually emits -- neither field is ever populated for those input
types (both are BRF-parser-only bookkeeping). This means every genuine
reset point (first note of piece/line, after a numeric indicator) on a
MusicXML/LilyPond-sourced score is *still* reported as "missing octave
mark" even when the rendered output plainly has one (confirmed by hand
against `gerhard_roberto_capriccio2_for_flute.xml`'s real rendered braille,
which does include a `⠰`-family mark at these positions). This is a
pre-existing gap (not introduced or worsened by this fix -- `has_mark` was
already computed this same way before), just newly visible now that the
flood of *other* false positives is gone. Attempted a fix by re-tokenizing
`raw_brl_text` to check for a real preceding `OCTAVE_MARK` token per
measure, using the same segment-count-from-the-end trick as the line map;
abandoned it because a title line (common for MusicXML-sourced scores,
rare for hand-typed BRF) tokenizes as if it were partly real music content
-- the generic `BrailleTokenizer` has no concept of "this line is literary
text, not music," so title characters collide with NOTE/OCTAVE_MARK/BAR_LINE
dot patterns unpredictably, and on the real flute fixture this produced
fewer total segments (154) than real measures (166), meaning the
last-N-segments alignment trick silently misattributes measures. Fixing
this properly likely needs either a real per-note braille-position map
computed by `BrailleRenderer` itself at render time (a render-time
mechanism the validator consumes, rather than reverse-engineering position
from re-tokenized text), or an explicit tokenizer mode that skips a known
title/signature preamble structurally instead of by category. Left
unimplemented pending a scope decision -- flag to developer.

**Definition of Done:**
- [ ] `_validate_octave_marks` agrees with `BrailleRenderer`'s actual,
  current line-start-only rule (BANA 3.2.1) instead of a stale "every
  measure" assumption. (Implemented for single-staff scores -- see Update
  above -- awaiting developer sign-off; multi-staff deliberately deferred.)
- [ ] False-positive count on `fengyang_flower_drum.brf` and the flute
  fixture drops to (hand-verified) genuine issues only. (True for
  `fengyang_flower_drum.brf`. NOT true for the flute fixture -- see
  "Residual limitation" above; its `has_mark` false positives are
  unaffected by this ticket's fix.)
- [ ] New tests pass; existing `test_validation.py` suite has no
  regressions. (Confirmed -- full suite, 1008 tests, passes.)

---

### [ ] S10d-2: BANAValidator reports "Line 1" for every correction on MusicXML/LilyPond-imported scores

**Why:** Every line-number field in `--report`'s output comes from
`Note.parsed_tokens[0].line`, falling back to `1` when `parsed_tokens` is
empty (`validator.py`, at least 8 call sites, e.g. line 267:
`line_num = curr_note.parsed_tokens[0].line if curr_note.parsed_tokens else 1`).
`parsed_tokens` is populated *only* by `braille_parser.py`'s tokenizer --
confirmed empty for every `Note` produced by `musicxml_parser.py` (and,
presumably, `lilypond_parser.py`, not separately checked here). Confirmed:
all 229 corrections for the flute piece say "Line 1", regardless of which
of the piece's ~40 physical braille lines the issue is actually on -- for
a blind composer relying on `--report` to navigate back to a specific
line, this makes the report state "somewhere in this piece" instead of
pointing anywhere useful.

**Update:** Solved alongside S10d-1 via one shared mechanism, per this
ticket's own suggestion. Two parts:
1. `cli.py`'s `_run_convert()` and `web.py`'s `/api/convert` now pass a
   real `raw_brl_text` to the validator for MusicXML/LilyPond input too --
   previously `text` (CLI) / `raw_brl_text` (web) was the empty string for
   these input types, so line-length (S9b-4) and page-layout (S11c-2)
   rules silently never ran at all, on top of the "Line 1" problem. Both
   now do `report_text = text if text else score.to_braille()` (CLI) /
   `report_text = raw_brl_text if raw_brl_text else score.to_braille()`
   (web) before calling `validator.validate()` -- BRF/BRL input keeps
   validating the user's literal source text unchanged (correct semantics
   there: checking what the user actually wrote).
2. `BANAValidator._build_measure_line_map()` (see S10d-1's Update) gives
   real per-measure line numbers from that text, for single-staff scores.
   `--report` on the flute fixture now shows distinct, correct line
   numbers (`Line 1` through the piece's real ~155 physical lines) instead
   of `Line 1` for all 229 corrections.

**Remaining gap:** unchanged for multi-staff MusicXML/LilyPond-sourced
scores (line map isn't built there, see S10d-1's "deliberately out of
scope") -- those still report `Line 1` for everything. No MusicXML/
LilyPond multi-staff test fixture existed to confirm this either way before
or after; flagging as a known gap rather than guessing it's fine.

**Definition of Done:**
- [ ] `--report` on a MusicXML- or LilyPond-imported score reports a
  genuinely useful line reference, not a constant "Line 1". (True for
  single-staff/solo scores -- see Update above -- awaiting developer
  sign-off. Still "Line 1" for multi-staff MusicXML/LilyPond scores, see
  Remaining gap.)
- [ ] New tests pass; existing test suite has no regressions. (Confirmed
  -- full suite, 1008 tests, passes.)

---

### [ ] S10d-3: `load_musicxml()` lets internal translation errors surface as raw tracebacks

**Why:** `load_musicxml()` (`musicxml_parser.py`) only wraps
`music21.converter.parse(source)` in `try/except DottedNotesError` --
`MusicXMLTranslator().translate(m21_score)` (the much larger, more
failure-prone step) runs unguarded. Confirmed: the test suite's own
deliberately-malformed-input file,
`33e-Spanners-OctaveShifts-InvalidSize.xml` (an octave-shift/ottava
spanner with a garbage size attribute), raises a raw
`music21.exceptions21.SpannerException: Cannot get shift magnitude from
'a'` all the way up through `cli.py`'s `main()` -- a full Python
traceback, not the plain-text `Error: ...` line this project's own Key
Design Decision 7 promises ("Error messages: Always plain text, always
meaningful ... never silent failures"). Any other not-yet-cataloged
internal error during translation (several of which surfaced during this
same survey -- see S10d-4 through S10d-8) will do the same thing today.

**Steps:**
1. Wrap the `MusicXMLTranslator().translate(m21_score)` call in
   `load_musicxml()` in the same style as the existing
   `music21.converter.parse` guard, catching broad `Exception` and
   re-raising as `DottedNotesError` with the original message -- mirroring
   how `cli.py`'s `main()` already expects to catch exactly one error
   type cleanly.
2. Decide whether some internal exceptions (e.g. ones this sprint's other
   tickets turn into a specific, named `DottedNotesError` subclass) should
   be allowed to pass through this wrapper unchanged rather than being
   re-wrapped generically -- likely yes, so a caller can still distinguish
   "unsupported tuplet ratio" from "malformed spanner data" if that ever
   matters.
3. Add a regression test using `33e-Spanners-OctaveShifts-InvalidSize.xml`
   (or a minimal hand-built equivalent) asserting `load_musicxml()` raises
   `DottedNotesError` with a plain-text message, not a raw
   `SpannerException`.

**Definition of Done:**
- [ ] No internal `music21`/DottedNotes exception during MusicXML
  translation reaches the CLI as a raw traceback.
- [ ] New tests pass; existing test suite has no regressions.

---

### [ ] S10d-4: Tuplet ratios beyond 3-in-the-time-of-2 (BANA 8.5, irregular groups)

**Why:** Confirmed the single most commonly-hit missing feature across
real and varied scores: the flute piece alone uses 5:4 and 7:4 ratios in 4
different measures, and just the sampled MusicXML test-suite files add
4:2, 4:1, 7:3, 6:2, 4:3, 17:3, 7:5, and 6:4 (`23a`/`23b`/`23c`/`23e`).
Currently (as of this session's warn-instead-of-silently-guess fix)
`map_duration()` warns and falls back to a nearest-power-of-2
approximation, which keeps the piece converting but never actually
transcribes the irregular group correctly. BANA Music Braille Code 2015
Par. 8.5 (referenced already in `tuplet.py`'s docstring as "out of scope")
defines the irregular-group sign(s) for ratios other than 3:2 --- fetch
and read Par. 8.5 directly (this repo's cached copy, if still present in
whatever scratchpad this ticket was written from, or re-download) before
implementing; don't guess the dot pattern the way this project never
guesses BANA cells from memory.

**Update:** Fetched BANA 2015 Par. 8.4/8.5/Table 8 directly (PDF text-
extracted locally, cross-checked ASCII patterns against `ASCII_TO_DOTS`).
Par. 8.5: "The three-cell sign (or four-cell if the number is greater than
nine), consisting of dots 456 followed by a lower-cell numeral (without a
numeric indicator) and a dot 3, is used to indicate an irregular group
consisting of any number of notes OTHER THAN THREE." Confirms two things
not obvious from the ticket's own framing: (1) the sign encodes only the
note COUNT, not the full N:M ratio -- the "time of M" half is left for the
reader to infer from context, exactly like the existing 3:2 single-cell
sign never spells out "2" either; (2) the single-cell sign is tied to
"three notes", not to a strictly-2 denominator, so `is_triplet` was
relaxed from `actual==3 and normal==2` to just `actual==3` (real fixture
data never contradicts this -- every `actual==3` case found pairs with
`normal==2` -- but the model itself should not assume it).

Implemented generally rather than hand-listing 5:4/7:4:
`Duration` gained `tuplet_ratio: Optional[tuple[int, int]] = None`
(`models/duration.py`), used by `duration_in_ticks()` for an exact scale
of any ratio, with the existing `is_triplet` 2/3 shortcut kept unchanged
as a fallback for callers (`braille_parser.py`'s BRF -> Score direction)
that never set it. `musicxml_parser.py`'s tuplet grouping in
`_translate_note_stream` now groups ANY ratio into a `Tuplet` (previously
only exactly (3, 2)), threading the group's real `(actual, normal)` ratio
into `Tuplet(..., ratio=...)` (which was, even for the classic case,
previously never actually passed through -- always relying on the
dataclass default). `map_duration`'s old "unsupported ratio, approximating"
warning (which claimed "only 3-in-the-time-of-2 is supported", no longer
true) is replaced by a narrower one that fires only when no exact written
value can be found for the note's true duration.

`Tuplet.to_braille()` (`models/tuplet.py`) now branches on `ratio[0]`:
exactly 3 keeps the existing single-cell sign (`⠆`) unchanged; anything
else renders Par. 8.5's sign (dots 456 + `LOWER_DIGIT_CELLS` numeral,
inverted from `bana_symbols.py` -- reused, not a new digit table -- + dot
3 terminator), correctly widening to two cells for counts above nine
(verified with an 11-note group). `to_relative_lilypond` already used
`self.ratio` for `\tuplet {num}/{den}` generically (no change needed
there); verified `\tuplet 5/4` and `\tuplet 7/4` compile cleanly with the
real `lilypond` binary (`lilypond` 2.24, zero warnings, PDF produced).

Verified against the real flute piece's actual 5:4 tuplets (measures 55,
73, 150): correct grouping, correct `⠸⠢⠄...` braille prefix, correct
`\tuplet 5/4 { ... }` LilyPond -- decoded by hand, not just "no crash".
Also re-ran the MusicXML Test Suite's `23a`/`23b`/`23e` tuplet files: every
per-ratio "unsupported tuplet ratio" warning is gone.

**Known, deliberately unfixed limitation:** `TICKS_PER_QUARTER = 24`
(`models/duration.py`) is only evenly divisible by ratio denominators that
divide 24 (2, 3, 4, 6, 8, 12...) -- 5:4 and 7:4 specifically (named in
this ticket's own Definition of Done) do NOT divide evenly, so
`_validate_measure_beat_count`'s resolved beat count for a measure
containing one is still an approximation, and `map_duration` still emits
its (now more accurately worded) "could not find an exact written value"
warning for them. This is a real, structural limit of the internal tick
resolution, not a bug in this ticket's grouping/rendering logic -- the
actual transcribed BANA sign and LilyPond ratio are both exactly correct
regardless (verified above), only the internal beat-count diagnostic is
imprecise for these two ratios. Fixing it for arbitrary ratios is
unbounded (any prime tuplet count needs its own factor in the tick
resolution's LCM -- the test suite alone has ratios up to 120:7); fixing
it even just for 5 and 7 specifically means raising `TICKS_PER_QUARTER`
project-wide, which is a much larger, higher-risk change than this ticket
scoped for -- confirmed at least 15 existing tests hardcode absolute tick
values tied to the current constant (`test_models.py`, `test_parser.py`),
plus untouched call sites in `musicxml_renderer.py`, `staff.py`,
`tremolo.py`, `validator.py` that were not audited for other hidden
assumptions. Flagging as a separate, dedicated ticket rather than
expanding this one's blast radius silently.

**Definition of Done:**
- [ ] At least 5:4 and 7:4 (the ratios confirmed in real repro material)
  transcribe with an exact duration and a BANA-verified sign, not an
  approximation. (The BANA sign and LilyPond ratio are exact and verified
  -- see Update above. The internal *duration/beat-count* for 5:4 and 7:4
  specifically remains an approximation due to `TICKS_PER_QUARTER`'s
  resolution -- see Known limitation. Awaiting developer sign-off on
  whether this partial result meets the ticket's intent.)
- [ ] The existing "unsupported ratio" warning either narrows to whatever
  ratios remain genuinely unsupported, or is removed if this ticket
  covers arbitrary ratios generally. (Narrowed -- now only fires when no
  exact written value is found, which is a tick-resolution limit, not a
  ratio-support limit; no ratio is rejected/unsupported anymore.)
- [ ] New tests pass; existing test suite has no regressions. (Confirmed
  -- full suite, 1034 tests, passes.)

---

### [ ] S10d-5: Chord grouping breaks when a non-note element interrupts consecutive `<chord/>` notes

**Why:** MusicXML allows `<direction>` (and other) elements to appear
between the first note of a chord and its `<chord/>`-tagged continuation
notes -- confirmed via the test suite's own
`21f-Chord-ElementInBetween.xml` (a `<segno/>` and a dynamics `<p/>`
direction sit between the first and second notes of a 3-note chord).
DottedNotes' chord-grouping in `_translate_note_stream`
(`musicxml_parser.py`) apparently treats the interruption as "end of
chord", splitting a single 3-note chord into `Note(A)` + `Chord([F])` +
`Chord([D])` -- three separate items, each counted as its own beat instead
of one simultaneous beat. Confirmed via direct inspection: the measure's
resolved beat count comes out to 6.0 instead of the correct 4.0.

**Update:** Confirmed via direct inspection that music21 itself, not
DottedNotes' own stream-iteration loop, is where the grouping actually
breaks: `m21_measure.notesAndRests` for this fixture already comes back as
three separate objects (`Note A4`, `Chord F#4` (one note), `Chord D4` (one
note)) at three separate, wrongly-advanced offsets (0.0, 1.0, 2.0) --
`_translate_note_stream`'s own loop never gets a chance to see them as one
event, there is nothing to "skip over" there. Fixed one level up instead:
added `_merge_interrupted_chord_continuations()` (`musicxml_parser.py`),
run against `m21_measure` (and each `Voice` sub-stream) before
`notesAndRests` is extracted. It detects the unambiguous signal that this
happened -- a single-note `music21.chord.Chord` (real, uninterrupted
`<chord/>` grouping never produces a one-note Chord; that shape is only
possible when the grouping already failed) -- and repairs it by
`stream.remove()`-ing the anchor and its orphaned continuations, then
`stream.insert()`-ing one properly merged multi-note Chord back at the
anchor's original offset (using remove+insert rather than constructing a
detached replacement object, since a detached Chord's `measureNumber` isn't
derivable at all -- confirmed empirically). `_translate_note_stream` itself
needed no changes. Verified: the fixture now imports as a single 3-note
Chord, 0 beat-count warnings (was 1, "expected 4.0 counted 6.0"). Also
checked the surrounding basic-chord test-suite files
(`21a-Chord-Basic.xml`, `21e-Chords-PickupMeasures.xml`) for regressions --
both have pre-existing, unrelated beat-count warnings confirmed identical
before and after this change (not caused or masked by it).

Regression test added in `tests/test_musicxml_parser.py`
(`test_musicxml_chord_with_interrupting_direction_element_imports_as_one_chord`),
using the raw XML directly (not an in-memory `music21.stream`
construction), since the bug is specifically in how music21's own
MusicXML importer resolves offsets around an interrupting element --
building the stream by hand in Python wouldn't reproduce it.

**Definition of Done:**
- [ ] A chord followed by a non-note element mid-sequence still imports
  as one `Chord`, not several. (Implemented -- see Update above -- awaiting
  developer sign-off.)
- [ ] New tests pass; existing test suite has no regressions. (Confirmed
  -- full suite, 1021 tests, passes.)

---

### [ ] S10d-6: `<backup>` that doesn't fully rewind to measure start isn't mapped to BANA's part-measure in-accord

**Why:** MusicXML's `<backup>` element can rewind by less than the full
duration already consumed (a legitimate way to stagger two voices' entry
points within one measure) -- confirmed via the test suite's own
`03b-Rhythm-Backup.xml`: voice 1 plays 2 quarter notes (2 beats), a
`<backup duration="2">` rewinds only 1 beat (not the full 2), then voice 2
plays 2 more quarter notes starting from that offset point, not from the
measure start. `InAccord` already models exactly this distinction
(`in_accord_type='part_measure'`, BANA Par. 11.1.2, vs. `'full_measure'`,
Par. 11.1.1 -- see `models/in_accord.py`'s docstring), but S10b-1's voice
import always uses `'full_measure'`, so a partially-offset backup like
this one gets combined as if both voices started together, misrepresenting
the actual rhythm.

**Update:** Fetched BANA 2015 Par. 11.1-11.1.3 directly (PDF text-extracted
locally, cross-checked Table 11's ASCII-braille signs against
`ASCII_TO_DOTS` in `parser/input_pipeline.py` -- confirmed the existing
`in_accord.py` separator dict, `⠣⠜`/`⠐⠂`/`⠨⠅`, is already correct, so no
new dot patterns were needed here). Par. 11.1.2's actual prescription: "it
is advisable to divide the measure into convenient sections, each section
being treated as an isolated unit. The measure-division sign stands
between the sections... The part-measure in-accord sign joins the parts
of the resulting section." So a partial-overlap case is NOT "one ordinary
item + one full_measure in-accord" (the ticket's own guessed alternative)
-- it is however many temporal sections the voices' actual overlap
pattern requires, each either a single voice's notes (no in-accord needed)
or a `part_measure` in-accord of whichever voices are simultaneously
active in that section specifically.

Implemented as `_voices_span_measure_in_lockstep()` (a cheap guard: if
every voice covers the identical `[start, end)` range, nothing changed,
keep the existing single full-measure in-accord path untouched -- zero
regression risk for the overwhelmingly common case) and
`_split_voices_into_sections()` (`musicxml_parser.py`): computes each
voice's offset range, collects every voice-start/voice-end as a
breakpoint, and for each breakpoint-to-breakpoint window determines which
voices are active, merging adjacent windows with an identical active-voice
set into one section. `translate_measure` adds each section's single
voice directly (no in-accord) or wraps multiple active voices as
`InAccord(parts=..., in_accord_type='part_measure')`, matching exactly the
section-then-in-accord-or-flat shape `braille_parser.py`'s own
`_finalize_measure` already builds for the reverse (BRF -> Score)
direction (confirmed by reading it -- this is not a new shape invented for
MusicXML, it reuses the codebase's own established convention). Verified
on `03b-Rhythm-Backup.xml`: 3 sections now (voice 1 alone / both voices as
a part-measure in-accord / voice 2 alone), resolved beat count improved
from an under-counted 2.0 (the old full-measure path silently dropped
voice 2's actual timing) to 3.0 -- still short of the nominal 4.0 because
this fixture's own last beat genuinely has no content in either voice
(confirmed against the raw XML: voice 1 spans offset 0-4, voice 2 spans
2-6, out of an 8-tick/4-beat measure -- nothing to do with this fix).

**Known limitation, not attempted:** a note that straddles a section
boundary (e.g. a half note starting before an overlap begins and ending
after it ends) is not split into tied fragments -- `_split_voices_into_sections`
only cuts at offsets that are already real note/rest boundaries. Not
reachable by `03b-Rhythm-Backup.xml` (all quarter notes, cleanly aligned);
flagging as a gap for whatever future fixture exercises it, rather than
guessing at a tie-insertion scheme now.

**Residual limitation found, not fixed here (needs its own ticket):**
confirmed, independent of MusicXML, that `Measure.to_braille()` /
`_render_note_list_to_braille()` never actually emits the measure-division
sign (`⠨⠅`) between adjacent sections at all -- round-tripping
`tests/test_parser.py`'s own existing `_PART_MEASURE_ACCORD` fixture
(`⠐⠝⠐⠂⠫⠻⠨⠅⠳⠪⠀`, parsed then re-rendered via `Score.to_braille()`) drops
the division sign entirely and runs section 2's single voice straight
into section 1's in-accord with no separator, an ambiguous/wrong braille
result. This is a pre-existing gap in the *renderer*, not something this
ticket's parser-side fix introduces: `braille_parser.py` already builds
the same section-then-in-accord-or-flat `Measure.notes` shape this ticket
now also builds for MusicXML import, and neither path can currently
re-render its own section boundaries correctly, because nothing in
`Measure.notes` records where one section ends and the next begins once
a single-voice section's notes are flattened directly into the list.
Fixing it properly likely needs a lightweight sentinel model class (e.g.
`MeasureDivision`, alongside `MeasureRepeat`) inserted between sections by
both `braille_parser.py` and this ticket's new MusicXML code, with
`_render_note_list_to_braille` taught to render it as `⠨⠅` and skip it for
beat-tracking/`curr_prev`/`curr_measure_start` purposes. Left unimplemented
here since it is a materially larger, separate change (touches the model,
parser, and renderer, not just the MusicXML importer this ticket scoped
to) -- flagging for a dedicated ticket rather than expanding this one's
scope silently.

**Steps:**
1. In `translate_measure`'s voice-handling branch (`musicxml_parser.py`),
   detect when a `<backup>` (surfaced via `music21`'s voice/offset
   handling -- confirm exactly how `music21` exposes partial backups
   before writing the detection) doesn't rewind to the measure's start
   offset, and reflect that as a `part_measure` in-accord (or an ordinary
   sequential item followed by a `full_measure` in-accord for the
   overlapping remainder, depending on what Par. 11.1.2 actually
   prescribes for a partial-overlap case -- read it directly rather than
   assuming a shape).
2. Add a regression test using `03b-Rhythm-Backup.xml` (or a minimal
   equivalent) asserting the resulting BRF matches BANA Par. 11.1.2's
   part-measure in-accord convention, and that the resolved beat count is
   correct (4.0, not 2.0).

**Definition of Done:**
- [ ] A partially-rewound `<backup>` imports as a part-measure in-accord
  (or whatever the manual actually prescribes), not a naive full-measure
  combination. (Implemented -- see Update above -- awaiting developer
  sign-off. Beat count improves 2.0 -> 3.0, not all the way to 4.0, because
  this specific fixture is itself missing its last beat -- see Update.)
- [ ] New tests pass; existing test suite has no regressions. (Confirmed
  -- full suite, 1023 tests, passes. Note: the *rendered BRF* still will
  not show the measure-division sign correctly -- see the Residual
  limitation above; this ticket fixed the internal Score model, not the
  renderer.)

---

### [ ] S10d-7: Non-traditional/microtonal key signatures (`<key-step>`/`<key-alter>`) not imported at all

**Why:** MusicXML supports two key-signature encodings: `<fifths>` (the
common case, already supported) and a list of `<key-step>`/`<key-alter>`
pairs for a "non-traditional" key (e.g. an octatonic or custom scale) --
confirmed via the test suite's `13c-KeySignatures-NonTraditional.xml` and
`13d-KeySignatures-Microtones.xml`, both of which crash with
`TypeError: '<=' not supported between instances of 'int' and 'NoneType'`
because `translate_measure` only reads `keys[0].sharps`, which is `None`
for this encoding. BANA Par. 6.5.1 ("Unusual Key Signatures") already
documents the transcription convention: "music parenthesis, hand or clef
sign, accidental, octave mark, note(s), closing music parenthesis" -- this
is a real, named BANA concept, not an out-of-scope curiosity.

**Update:** Fetched BANA 2015 Par. 6.5.1/Table 1/Table 6 directly (PDF
text-extracted locally). Confirmed the "music parenthesis" sign is NOT the
same cell as `CHORD_PAREN_CELL` (chord symbols, Table 23, `⠶`) -- Table 1
lists a separate, general-purpose "Music parentheses" sign, `,'` in ASCII,
decoding to `⠠⠄` (dots 6 then dot 3), used unchanged for both the opening
and closing parenthesis. Decoded Example 6.5.1-1's worked example
cell-by-cell against `ASCII_TO_DOTS`/existing tables and found its "hand
or clef sign" component decodes to exactly `models/clef.py`'s own
`ClefType.TREBLE` cell (`⠜⠌⠇`) -- a non-coincidental match confirming that
piece. Table 6 also directly gives the quarter/three-quarter step
accidental cells needed for the microtonal fixture (`13d-KeySignatures-
Microtones.xml`'s alter values of +/-0.5 and +/-1.5).

Implemented in `models/key_signature.py`: `KeySignature` gained
`non_traditional_pitches: Optional[list[tuple[str, float, Optional[int]]]]`
(step, alter, octave-or-None), with `sharps_or_flats` now `Optional[int]`
and a `__post_init__` requiring exactly one of the two. `to_braille()`
renders Par. 6.5.1's construction per altered pitch (parenthesis + treble
clef + accidental + octave mark + note + parenthesis), reusing the
existing `NOTE_CELLS`/`_OCTAVE_TO_BRL` tables rather than new ones.
`to_lilypond()` raises a clean `DottedNotesError` for this variant --
LilyPond's own non-standard/microtonal key-signature and note-naming
syntax was not researched (out of scope for the time this ticket
justified), so this correctly refuses to guess rather than emit unverified
LilyPond, per this project's standing rule.

**Deliberately NOT implemented, flagged rather than guessed:** (1) BANA's
exact convention for chaining MULTIPLE altered pitches within one
signature (Example 6.5.1-2, "Unusual combined key signatures") could not
be confidently decoded cell-by-cell from the manual's extracted text alone
without its accompanying print image -- each altered pitch currently gets
its own complete parenthesis-wrapped construction instead, a defensible
but unverified reading; ask a BANA transcriber or consult the print
image before trusting this for a real combined signature. (2) which clef
to assume inside the construction when the source doesn't specify one for
it specifically -- always assumes treble (neither worked example in the
manual covers a non-treble case). (3) `Measure.key_signature` is a plain
`int` used pervasively for the ordinary sharps/flats case (measure-level
key-change tracking, `Staff`'s header line, etc.) -- there is no slot in
that plumbing for a non-traditional signature, and changing that field's
type everywhere it is used is a materially larger, separate change than
this ticket justified. `translate_measure` (`musicxml_parser.py`) detects
`keys[0].sharps is None`, builds nothing at the Measure/Staff-int level
(keeps `key_val` unchanged from before this measure, so the rest of the
piece is unaffected), and emits a clear warning instead -- fixing the
crash without silently corrupting the ordinary display path. Confirmed
against the real repro fixtures that the notes exercised there carry no
explicit MusicXML accidental of their own and are plain, unaltered
pitches (not one of the signature's altered pitch classes), so this
specific repro data has no actual pitch-correctness risk from the
omission -- flagged in the warning text regardless, since a real piece's
notes might not be so lucky.

**Definition of Done:**
- [ ] Non-traditional key signatures import without crashing and produce
  BANA-Par.-6.5.1-shaped output. (Import no longer crashes -- confirmed on
  both real fixtures. The `KeySignature` model itself produces BANA-Par.-
  6.5.1-shaped braille when constructed directly -- see Update above --
  but is not yet wired into the actual imported Staff/Measure display; see
  "Deliberately NOT implemented" item 3. Awaiting developer sign-off on
  whether this partial result meets the ticket's intent, and on the
  combined-signature chaining question in item 1.)
- [ ] New tests pass; existing test suite has no regressions. (Confirmed
  -- full suite, 1040 tests, passes.)

---

### [ ] S10d-8: Key signatures beyond ±7 sharps/flats crash instead of using BANA's numeral-prefixed form

**Why:** `KeySignature`'s `sharps_or_flats` is hard-limited to −7…+7;
confirmed via the test suite's own `13aa-KeySignatures-Extreme.xml`
(fifths values down to −11), which raises
`ValueError: sharps_or_flats must be in –7 … +7, got -11`. BANA Par. 6.5
already documents the correct convention for 4+ accidentals: "the number
including the numeric indicator precedes a single flat or sharp sign" --
i.e. BANA's key-signature notation is not inherently capped at 7; the cap
is specific to DottedNotes' current model, not to BANA itself. (Low
practical priority -- an 11-accidental key signature is a theoretical/
enharmonic-respelling curiosity, not something a real solo instrumental
piece is likely to need -- but a clean, documented limit or a real
extension is better than a raw `ValueError`.)

**Update:** Fetched BANA 2015 Par. 6.5 directly (PDF text-extracted
locally): "When it consists of four or more accidentals, the number
including the numeric indicator precedes a single flat or sharp sign" --
no cap is stated anywhere for how large that number can get, confirming
the ±7 limit is purely this project's own model artifact, not a BANA one.
Chose the "extend it" branch over the "clean error" branch accordingly.

`key_signature.py`'s old `_KEY_TO_BRL`/`KEY_TO_LILYPOND` were both flat
lookup tables hardcoded to -7..7 -- confirmed they did NOT generalize.
Replaced the out-of-range check with a computed fallback instead of
enumerating more table entries: `_tonic_letter_and_accidental()` derives
the tonic's letter and sharp/flat count from circle-of-fifths semitone
arithmetic (verified by first reproducing all 15 of `KEY_TO_LILYPOND`'s
existing -7..7 entries exactly via the same formula before trusting it
past that range), and `_numeral_prefixed_braille()` spells the count using
the *same* `LITERARY_DIGITS` letter alphabet BANA measure numbers already
use (`bana_symbols.py`, inverted), rather than a second, separate digit
table. `KEY_TO_LILYPOND`/`_KEY_TO_BRL` themselves are untouched and stay
the fast path for -7..7 (an existing test asserts that dict is exactly
that range, so it was left alone rather than folded into the generalized
form). `KeySignature.__post_init__`'s `ValueError` was removed entirely --
`sharps_or_flats` is now unbounded in either direction.

Verified against `13aa-KeySignatures-Extreme.xml` (fifths=-11): imports
cleanly, `\key aeses \major`, braille signature line includes `⠼⠁⠁⠣`
(numeral sign + "11" + flat sign) -- checked by decoding the actual
rendered output, not just absence of a crash. Also hand-verified +8 sharps
(G# major, needing a double-sharp on F -- `gis`) since the fixture itself
only exercises the flat side.

Existing tests `test_key_signature_sharps_out_of_range_raises` and
`test_key_signature_flats_out_of_range_raises` in `test_models.py`
asserted the old capped behavior and were removed (they tested a
limitation this ticket deliberately lifted, not a bug); replaced with
tests asserting the extended range now works, plus a MusicXML-level
regression test in `test_musicxml_parser.py` using the real repro shape.

**Definition of Done:**
- [ ] A key signature beyond ±7 either transcribes correctly (BANA Par.
  6.5) or fails with a clean, plain-text `DottedNotesError` -- never a raw
  `ValueError` traceback. (Implemented as the "transcribes correctly"
  branch -- see Update above -- awaiting developer sign-off.)
- [ ] New tests pass; existing test suite has no regressions. (Confirmed
  -- full suite, 1028 tests, passes.)

---

### [ ] S10d-9: Note values finer than 64th and augmentation dots beyond 2 crash instead of using BANA's value signs

**Why:** `Duration.dots` is limited to 0-2 and `VALID_DURATIONS` tops out
at 64th notes; confirmed via the test suite's
`03d-Rhythm-DottedDurations-Factors.xml` (a note with 4 `<dot/>` tags,
`ValueError: Invalid dot count: 4`) and `03ab-Rhythm-Durations.xml`
(`ValueError: denominator must be a power of 2 in [1, 2, 4, 8, 16, 32], got
64`, i.e. a 128th-note-equivalent duration). BANA Par. 2.3 ("Dotted
Notes") states plainly: "When a note has more than one dot, the same
number of dot 3s are given in the braille" -- no cap at 2 is stated there.
Par. 2.4/2.4.1 go further and explicitly cover 128th and 256th notes,
via a "larger/smaller value" sign (`^<1`/`,<1`) used to disambiguate
otherwise-ambiguous note values -- both finer values and 3+ dots are
real, documented BANA constructs, not out-of-scope extremes. (Rare in
practice for solo instrumental writing, but real repro data exists in
this survey, and the current behavior is a raw crash rather than a
graceful limit.)

**Steps:**
1. Fetch and read BANA Par. 2.3/2.4/2.4.1 directly, confirming the exact
   dot-tripling convention for 3+ dots and the value-sign cells/placement
   rule for 128th/256th notes, before touching `bana_symbols.py` or
   `models/duration.py`.
2. Extend `Duration` to allow more than 2 dots and note values below 64
   (128, 256), and extend `duration_in_ticks()`'s dot-scaling formula
   (currently hardcoded for exactly 0/1/2) to a general case.
3. Implement the larger/smaller value-sign placement logic in whichever
   render path needs it (likely `Note.to_braille()`, checking the
   previous/next note's value the same way existing ambiguity-resolution
   code already does elsewhere in this parser).
4. At minimum, even before implementing the full value-sign mechanism,
   replace the raw `ValueError` with a clean `DottedNotesError` so a
   score using these values fails gracefully rather than with a
   traceback, if the fuller implementation is deferred further.
5. Add tests using both test-suite fixtures.

**Definition of Done:**
- [ ] Notes with 3+ dots or finer-than-64th values either transcribe
  correctly per BANA Par. 2.3/2.4, or fail with a clean plain-text error
  -- never a raw `ValueError` traceback.
- [ ] New tests pass; existing test suite has no regressions.

---

### [ ] S10d-10: Missing lead-sheet chord-symbol mapping for "augmented-seventh" (and similar combination kinds)

**Why:** Confirmed via the test suite's `71f-AllChordTypes.xml`: MusicXML
chord kind `augmented-seventh` isn't in
`_CHORD_KIND_TO_MODEL_FIELDS` (`musicxml_parser.py`), raising
`DottedNotesError: Unrecognized MusicXML chord kind 'augmented-seventh'`
-- already a clean error, not a crash, so this is a small/easy gap rather
than a robustness issue. BANA Table 23 doesn't need a new sign for this:
it's the existing "Plus" sign (augmented) combined with the existing
"Italic 7" sign (seventh) already used elsewhere in the same dict (see
e.g. `'dominant-seventh': {'extensions': [(7, None)]}` and how
`is_augmented`/`is_diminished` combine with `extensions` for other kinds)
-- this ticket is "add the missing dict entry using primitives that
already exist," not new BANA research.

**Update:** `'augmented-seventh': {'is_augmented': True, 'extensions':
[(7, None)]}` has been added (confirmed a clean combination of existing
primitives) with a regression test. Cross-checking the rest of
`71f-AllChordTypes.xml`'s kinds against `music21`'s own `chordKind`
normalization (not the raw MusicXML `<kind>` string -- confirmed these
differ, e.g. raw `half-diminished` normalizes to `chordKind ==
'half-diminished-seventh'`, already mapped) turned up three more this
fixture uses that are still genuinely unmapped: `other`, `pedal`, `power`.
Unlike `augmented-seventh`, none of these are a simple combination of
existing `ChordSymbol` fields -- there is no field today for "root +
fifth, no third" (`power`), "sustained bass note, no chord quality at
all" (`pedal`), or an arbitrary/custom quality with only a display-text
override (`other`, MusicXML's `<kind text="...">`). Left open pending
real BANA Sec. 23 research (Table 23's sign list doesn't show an obvious
existing sign for any of the three) rather than guessing a mapping.

**Steps (remaining):**
1. Fetch and read BANA Sec. 23 directly for whether/how a power chord,
   a pedal-point symbol, or an arbitrary/custom chord quality are
   transcribed at all -- don't assume a sign exists.
2. If a convention exists, add whatever new `ChordSymbol` field(s) it
   needs and the corresponding `_CHORD_KIND_TO_MODEL_FIELDS` entries.
3. If no BANA convention exists for one or more of these, document that
   explicitly (a clean, specific `DottedNotesError` message already
   covers the "unsupported" case -- no code change needed for that part).
4. Add tests for whichever of the three get a real mapping.

**Definition of Done:**
- [ ] `augmented-seventh` (and any other simple existing-primitive
  combinations) added; regression test passing. (Implemented -- see
  Update above -- awaiting developer sign-off.)
- [ ] `other`/`pedal`/`power` either get a real, BANA-verified mapping, or
  are explicitly documented as having no BANA counterpart.
- [ ] New tests pass; existing test suite has no regressions.

---

### [ ] S10d-11: Unpitched percussion notes (`<unpitched>`) are silently dropped entirely (scope decision needed)

**Why:** Confirmed via the test suite's `73a-Percussion.xml`: a Timpani
staff (pitched percussion, written with real `<pitch>` elements) imports
correctly, but Cymbals and Triangle staves (using `<unpitched>` instead of
`<pitch>`) import as completely empty measures -- not even converted to
rests, just absent, with the resolved beat count coming out to 0.0.
BANA Chapter 34 ("Percussion") documents the transcription convention in
detail (Par. 34.2 "Typical Braille Transcription", 34.2.1 "Note Names",
34.2.2 "Octave Marks", 34.2.3 "Interval Signs and In-Accords", 34.7 "Drum
Kit Transcriptions"), so this is a real, well-documented gap, not a
guess -- but per this project's current stated scope (solo instrumental,
not yet ensemble/orchestral percussion), this is lower priority than the
other tickets in this sprint unless a percussion piece becomes a near-term
target. Flagging for a scope decision rather than assuming it should be
built now.

**Steps (if greenlit):**
1. Fetch and read BANA Chapter 34 directly (Par. 34.2.1/34.2.2/34.2.3 in
   particular) before implementing anything -- unpitched percussion note
   naming/octave conventions differ from pitched instruments and
   shouldn't be guessed from the pitched-note code path.
2. Decide on a model representation for an unpitched note (a distinct
   field on `Note`, or a new lightweight model -- BANA's own note-naming
   convention from step 1 should inform which fits better).
3. Import `<unpitched>` elements in `_translate_note_stream`
   (`musicxml_parser.py`) instead of silently skipping them.
4. Implement `to_braille()` per BANA 34.2, and `to_lilypond()` (LilyPond's
   percussion-staff/note-name syntax, verified against the Notation
   Reference, not guessed).
5. Add a test using `73a-Percussion.xml` asserting Cymbals/Triangle
   measures import with real content, not empty.

**Definition of Done:**
- [ ] Explicit scope decision recorded (build now vs. defer) before any
  code changes.
- [ ] If built: unpitched percussion notes import and transcribe per BANA
  Chapter 34, verified tests pass, existing test suite has no
  regressions.



