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

### [ ] S1-3: Implement Note class

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
- [ ] `Note` class exists and inherits from `BrailleSymbol`
- [ ] `to_lilypond()` produces correct output for all 7 natural note names
- [ ] `to_lilypond()` includes octave marks for all octaves 1–7
- [ ] `to_lilypond()` includes accidental when present
- [ ] `to_lilypond()` appends articulation strings when present
- [ ] Invalid note names raise `ValueError`
- [ ] All unit tests pass

---

### [ ] S1-4: Implement Rest class

**Why:** Rests are as important as notes.
A piece with missing rests will have incorrect rhythmic structure.

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
- [ ] `Rest` class exists with `duration` and `is_full_measure` fields
- [ ] `to_lilypond()` produces `r` prefix for regular rests
- [ ] `to_lilypond()` produces `R` prefix for full-measure rests
- [ ] Dotted rests produce correct output
- [ ] All unit tests pass

---

### [ ] S1-5: Implement Accidental class

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
- [ ] `Accidental` class with `AccidentalType` enum exists
- [ ] `to_lilypond()` returns correct suffix for all five types
- [ ] Natural accidental returns empty string (correct LilyPond behavior)
- [ ] All unit tests pass

---

### [ ] S1-6: Implement Articulation class

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
- [ ] `Articulation` class with `ArticulationType` enum exists
- [ ] `to_lilypond()` returns correct LilyPond string for all types
- [ ] All unit tests pass

---

### [ ] S1-7: Implement Dynamic class

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
- [ ] `Dynamic` class with `DynamicLevel` enum exists
- [ ] `to_lilypond()` returns correct LilyPond string for all levels
- [ ] Hairpin dynamics (crescendo/decrescendo) produce correct output
- [ ] All unit tests pass

---

### [ ] S1-8: Write Sprint 1 integration test

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
- [ ] Integration test passes
- [ ] All Sprint 1 unit tests pass (no regressions)
- [ ] `models/` directory has >80% test coverage
- [ ] `pytest tests/` runs clean with no warnings

---

# Sprint 2: Braille Parser — Notes and Rhythm

Goal: Parse a simple single-voice braille melody from a .brf file
and produce correct Note objects with correct pitches and durations.
Estimated time: 1.5–2 weeks.

---

### [ ] S2-1: Implement BrailleTokenizer

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
- [ ] `BrailleTokenizer` class exists
- [ ] Tokenizer produces correct token types for note cells
- [ ] Tokenizer produces correct token types for bar lines
- [ ] Unknown symbols produce UNKNOWN tokens, not exceptions
- [ ] Token includes position information for error reporting
- [ ] Unit tests pass

---

### [ ] S2-2: Implement BrailleParser skeleton

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
- [ ] `BrailleParser` class exists and imports without errors
- [ ] `parse()` method exists and returns a `Score`
- [ ] Parser state (octave, duration, key, time) is initialized correctly
- [ ] Unit test passes

---

### [ ] S2-3: Implement octave mark recognition and tracking

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
- [ ] Octave mark tokens are recognized and consumed by the parser
- [ ] `_current_octave` state is updated on each octave mark
- [ ] Notes following an octave mark use the correct octave
- [ ] Notes without a preceding octave mark use the last known octave
- [ ] Unit tests pass

---

### [ ] S2-4: Implement note value ambiguity resolution

**Why:** This is the hardest problem in the entire project.
In braille music, the dot pattern for a whole note is identical to
a 16th note, and a half note is identical to an 8th note.
The parser must determine the intended duration from rhythmic context.

**Steps:**
1. Research the BANA rules for note value disambiguation:
   - In 4/4 time, if you have seen only quarter-note-equivalent values
     so far in the measure, a new ambiguous cell is more likely the
     longer value
   - The "value indicator" sign in BANA explicitly marks when the
     short (16th/8th) interpretation is intended
2. Implement `_resolve_note_value(ambiguous_value, context)` method:
```python
def _resolve_note_value(self, ambiguous_value: int) -> int:
    """
    Resolve ambiguous braille note value to actual duration.
    ambiguous_value is either 1 (whole/16th) or 2 (half/8th).
    Returns the resolved duration value (1, 2, 8, or 16).
    """
    # Check if a value indicator was seen before this note
    if self._short_value_indicator_active:
        self._short_value_indicator_active = False
        return ambiguous_value * 8  # 1→8 (eighth) or 2→16 (16th)
    # Default: use the long value interpretation
    return ambiguous_value  # 1→1 (whole) or 2→2 (half)
```
3. Track `_short_value_indicator_active` state in the parser
4. Track `_beats_used_in_measure` to validate against time signature
5. Write tests with known BRF input and expected duration output

**Definition of Done:**
- [ ] `_resolve_note_value()` exists and handles both ambiguous values
- [ ] Short value indicator is recognized and consumed
- [ ] Default resolution (long value) is used when no indicator present
- [ ] Beat-counting validation catches rhythmically incorrect measures
- [ ] Unit tests cover: whole note, 16th note (with indicator),
      half note, 8th note (with indicator)

**Senior note:** If you are unsure about a specific BANA rule for
disambiguation, do not guess — write a test that documents your
uncertainty with a comment, and move on. It is better to have an
honest TODO than a silent wrong answer.

---

### [ ] S2-5: Implement bar line recognition

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
- [ ] All four bar line types are recognized
- [ ] Bar line tokens trigger measure finalization
- [ ] Beat count validation runs and produces a warning on mismatch
- [ ] Warning is plain text and screen-reader friendly
- [ ] Unit tests pass

---

### [ ] S2-6: Sprint 2 integration test — parse a simple melody

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
- [ ] Integration test passes end-to-end
- [ ] Correct number of measures parsed
- [ ] First note has correct pitch, octave, and duration
- [ ] No exceptions raised during parsing
- [ ] `pytest tests/` passes with no regressions

---

### [ ] S2-7: Integration test — render parsed melody to LilyPond

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
- [ ] `score.to_lilypond()` returns a valid string
- [ ] LilyPond output contains required header elements
- [ ] If lilypond binary is available, output compiles without errors
- [ ] Test is skipped gracefully if lilypond is not installed
      (do not fail CI just because lilypond is not in the CI environment)

---

# Sprint 3: Key Signatures, Time Signatures, Clefs

Estimated time: 3–4 days.

### [ ] S3-1: Implement KeySignature class
### [ ] S3-2: Implement TimeSignature class
### [ ] S3-3: Implement Clef class
### [ ] S3-4: Add key and time signature parsing to BrailleParser
### [ ] S3-5: Integration test with non-C-major key

*Detailed steps to be written when Sprint 2 is complete.*
*Senior note: Write the detailed tickets for the next sprint
at the end of the current sprint, when you have learned
what the actual complexity looks like.*

---

# Sprint 4: Articulations and Dynamics

Estimated time: 3–4 days.

### [ ] S4-1: Add articulation parsing to BrailleParser
### [ ] S4-2: Add dynamic parsing to BrailleParser
### [ ] S4-3: Implement slur and tie parsing
### [ ] S4-4: Integration test using Fengyang Flower Drum .brf

*Detailed steps to be written when Sprint 3 is complete.*

---

# Sprint 5: Chords and Multiple Voices

Estimated time: 1.5–2 weeks.

### [ ] S5-1: Implement Chord class
### [ ] S5-2: Implement in-accord parsing
### [ ] S5-3: Implement Voice class and multi-voice measure parsing
### [ ] S5-4: Implement Staff class with voice assembly
### [ ] S5-5: Integration test: two-voice piano piece

*Detailed steps to be written when Sprint 4 is complete.*

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

# Sprint 10: MusicXML Bridge

Estimated time: 1–1.5 weeks.

### [ ] S10-1: Integrate music21 for MusicXML parsing
### [ ] S10-2: Implement MusicXML to Internal Model translation
### [ ] S10-3: Implement Internal Model to MusicXML translation
### [ ] S10-4: Integration test: import MuseScore MusicXML, export as BRF
### [ ] S10-5: Integration test: import BRF, export as MusicXML for MuseScore

*Detailed steps to be written when Sprint 9 is complete.*
