# DottedNotes — Claude Code Project Context

This file gives Claude Code full context for the DottedNotes project.
At the start of each session, read this file first before doing anything else.
Tickets that are done are marked with [x]. Tickets still to do are marked with [ ].
Never mark a ticket done yourself — the developer will check it off.

---

## Project Overview

**Repository:** https://github.com/judithhinlung/DottedNotes
**Language:** Python (`>=3.9`, per `pyproject.toml`)
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
             BRF/BRL reverse (Sprint 9 — `Score.to_braille()` / `BrailleRenderer`,
             reachable from the CLI via a `.brf`/`.brl` output path, see CLI Design)
```

Sprint 9b layers a `BANAValidator` (`validation/validator.py`) and a
`compression_level` parameter on `BrailleRenderer` on top of the reverse
path above — see the Project structure entries below for both.

### Project structure
```
DottedNotes/
├── src/
│   └── dottednotes/
│       ├── __init__.py
│       ├── bana_symbols.py      # Authoritative BANA dot-pattern tables (all SymbolCategory cells)
│       ├── exceptions.py        # DottedNotesError, BrailleParseError, LilyPondCompileError
│       ├── cli.py               # CLI: `convert` subcommand, --compile/--verbose/--version/
│       │                         # --report/--compression (Sprint 9b)
│       ├── models/
│       │   ├── __init__.py      # Re-exports every model class below
│       │   ├── base.py          # BrailleSymbol base class
│       │   ├── note.py          # Note, Rest classes
│       │   ├── duration.py      # Duration class (incl. is_triplet)
│       │   ├── accidental.py    # Accidental, AccidentalType
│       │   ├── articulation.py  # Articulation, ArticulationType
│       │   ├── dynamic.py       # Dynamic, DynamicLevel
│       │   ├── ornament.py      # Ornament, OrnamentType, GraceNote
│       │   ├── fingering.py     # Fingering (basic/change/alternative)
│       │   ├── chord.py         # Chord class
│       │   ├── chord_symbol.py  # ChordSymbol (BANA Table 23 lead-sheet chord symbols)
│       │   ├── chord_names.py   # ChordNamesTrack (rhythm-aligned \chordmode entries)
│       │   ├── in_accord.py     # InAccord (multi-voice BANA "in accord")
│       │   ├── measure.py       # Measure class
│       │   ├── measure_repeat.py # MeasureRepeat (whole-measure repeat sign)
│       │   ├── tuplet.py        # Tuplet class
│       │   ├── clef.py          # Clef, ClefType
│       │   ├── key_signature.py # KeySignature
│       │   ├── time_signature.py # TimeSignature
│       │   ├── text_marking.py  # TextMarking (tempo/expression word-signs)
│       │   ├── instrument.py    # InstrumentInfo, InstrumentFamily, family lookup
│       │   ├── transposition.py # Transposing-instrument interval table (used by Score)
│       │   ├── staff.py         # Staff class
│       │   ├── score.py         # Score class (single/multi-staff to_lilypond())
│       │   └── orchestra_score.py # OrchestraScore (named-variable, \with{} staves)
│       ├── parser/
│       │   ├── __init__.py
│       │   ├── input_pipeline.py   # BRLInputPipeline: ASCII/Unicode braille detection + normalization
│       │   ├── tokenizer.py        # BrailleTokenizer, BrailleToken (line/position-tagged; each
│       │   │                       # parsed Note now keeps its own `parsed_tokens` slice, consumed
│       │   │                       # by the validator's sign-order rule, S9b — see Note below)
│       │   ├── braille_parser.py   # BrailleParser (main solo-score parser)
│       │   ├── chord_symbol_parser.py # parse_chord_symbol_line (BANA §23/Table 23)
│       │   ├── lead_sheet_parser.py   # parse_lead_sheet (BANA §27 two-line lead-sheet parallel)
│       │   ├── ensemble_parser.py  # EnsembleParser (BANA §33 instrument-list header + parallel systems)
│       │   └── instrument_list.py  # parse_instrument_list, resolve_abbreviation (Table 29)
│       ├── renderers/
│       │   ├── __init__.py
│       │   ├── lilypond_formatter.py  # LilyPondFormatter: per-category \paper{}/staff-size settings
│       │   └── braille_renderer.py    # BrailleRenderer (Sprint 9): Score -> BRF text, solo/piano/
│       │                               # ensemble layout + line packing. `compression_level` param
│       │                               # ("full"/"minimal"/"none", Sprint 9b) runs an articulation-
│       │                               # carry-shorthand pass and a measure-repeat-sign pass before
│       │                               # layout. Carry runs always terminate on a plain, unprefixed
│       │                               # sign (matching tremolo/triplet carry elsewhere in this
│       │                               # file), never a special termination cell -- reachable from
│       │                               # the CLI via a `.brf`/`.brl` output path (see CLI Design).
│       └── validation/
│           ├── __init__.py
│           └── validator.py   # BANAValidator (Sprint 9b): rule-based checker run against the
│                               # internal Score model (+ raw BRF text for line-length). Rules
│                               # implemented: octave-mark register tracking (S9b-3, resets at
│                               # first-note-of-voice, every measure start, every new source line,
│                               # and after a numeric indicator -- matching Note.to_braille()'s
│                               # real is_measure_start-based reset), missing articulation shorthand
│                               # (S9b-2), BANA sign ordering around a note, and line-length overflow
│                               # (S9b-4). Returns a `ValidationResult` of `Correction` dataclasses
│                               # (line/measure, message, severity, rule_id, optional proposed_fix);
│                               # `ValidationResult.to_json()` serializes for the future web-UI
│                               # validation step (S9b-7). Wired into the CLI via
│                               # `dottednotes convert --report` (see CLI Design).
├── tests/
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_parser.py
│   ├── test_ensemble_parser.py
│   ├── test_ensemble_integration.py
│   ├── test_chord_symbols.py     # BANA §23/27 chord symbols + lead-sheet alignment (S8b-5)
│   ├── test_fingering_model.py
│   ├── test_fingering_parser.py
│   ├── test_fingering_integration.py
│   ├── test_lilypond_formatter.py
│   ├── test_exceptions.py
│   ├── test_cli.py
│   ├── test_validation.py    # BANAValidator rules (Sprint 9b)
│   ├── test_compression.py   # musical_equals() + BrailleRenderer compression_level (Sprint 9b)
│   └── fixtures/                # .brf/.brl inputs, each paired with a hand-authored
│                                 # .ly ground truth where one exists (see fixtures/README.md)
├── docs/
│   ├── bana_reference.md        # BANA symbol table reference
│   ├── lilypond_conventions.md  # LilyPond formatting defaults reference, with citations
│   └── mutopia_analysis.md      # Raw Mutopia corpus analysis backing lilypond_conventions.md
├── examples/
├── LICENSE                      # GPL-2.0
├── README.md
├── pyproject.toml
├── CLAUDE.md                    # This file
├── TICKETS.md                   # Full sprint/ticket backlog
└── .github/
    └── workflows/
        └── ci.yml
```

---

## Key Design Decisions

1. **Voice numbers:** All voice numbers are per-part (1-4), never global.
2. **Encoding:** Normalize all input to Unicode braille (U+2800-U+28FF) internally
   regardless of whether the input file uses ASCII braille or Unicode braille
   (`BRLInputPipeline`, `parser/input_pipeline.py`) — every real caller uses this
   class, never a raw file read.
3. **Relative mode:** All LilyPond output uses `\relative` mode for readability.
4. **Concert pitch:** Default to concert pitch output; transposing instrument
   support added in Sprint 5b (`models/transposition.py`).
5. **Restricted LilyPond parser:** The LilyPond → BRF reverse direction (Sprint 9,
   implemented) only needs to parse LilyPond that DottedNotes itself
   generated, not arbitrary LilyPond written by humans. This keeps the reverse
   parser tractable.
6. **No external APIs at runtime:** `dottednotes convert` has no network
   dependencies. (Sprint 7b's one-time Mutopia corpus analysis, which derived
   the formatting defaults below, is an offline research script — not something
   the shipped CLI ever calls.)
7. **Error messages:** Always plain text, always meaningful, always
   screen-reader friendly, never silent failures — enforced by
   `exceptions.py`'s `DottedNotesError` hierarchy, which `cli.py`'s `main()`
   catches centrally to print one plain-text line and exit non-zero, never a
   Python traceback (Sprint 7, S7-3).
8. **Evidence-based formatting, not per-score guessing:** `LilyPondFormatter`
   (`renderers/lilypond_formatter.py`) picks `\paper{}`/staff-size settings
   from one of five templates (Solo Piano / Art Song / Chamber / Orchestral /
   Lead Sheet), each template's numbers taken from a single curated,
   well-engraved Mutopia score for that category — not invented, and not a
   raw corpus average (see `docs/lilypond_conventions.md` for why an average
   was actively misleading here). The exception is Lead Sheet, which has no
   Mutopia anchor (chord-symbol lead sheets aren't present in that corpus in
   `\chordmode`/`ChordNames` form) and reuses Solo Piano's numbers as a
   documented placeholder instead — see `docs/lilypond_conventions.md`.
   Category is auto-detected from staff count/family but can be
   overridden (`to_lilypond(category_override=...)`).
9. **Compression is a rendering-time pass, not a parser concept:** `BrailleRenderer`
   (`renderers/braille_renderer.py`) never mutates the `Score` it's given — `render()`
   deep-copies it first, then (when `compression_level != "none"`) runs an
   articulation-carry pass and a measure-repeat pass over the copy before laying
   out lines. `Note.musical_equals()` / `Chord.musical_equals()` / `Rest.musical_equals()`
   / `Measure.musical_equals()` (Sprint 9b, S9b-15) back the measure-repeat pass;
   `Articulation.explicit` (written-vs-carried bookkeeping) is a `compare=False`
   dataclass field precisely so it can't leak into that equality check.
10. **`.brf`/`.brl` output path switches `convert` to braille output:** `cli.py`'s
    `_run_convert()` checks the output path's suffix — `.brf`/`.brl` renders via
    `Score.to_braille(compression_level=args.compression)` instead of
    `to_lilypond()`. `--compile` is rejected with a plain-text error if combined
    with a `.brf`/`.brl` output path (compiling needs a `.ly` file). No output
    path (stdout) always defaults to LilyPond.
11. **Part-level score rendering and downloading:** Multi-staff scores can have individual parts (staves) rendered on-demand. To avoid parsing the input file twice, the parsed `Score` object is cached in memory on the backend (with fallback to re-parsing). We construct a temporary single-staff `Score` and run it through the renderers, which naturally output single-part formats without format-specific slicing logic. In the CLI, the `--part` and `--list-parts` options allow selecting a part and listing parts respectively.

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
accidental: Accidental | None = None
dynamics: list[Dynamic]
articulations: list[Articulation]
ornaments: list[Ornament]
grace_note: GraceNote | None = None
tie: bool = False
slur_start: bool = False
slur_end: bool = False
slur_bracket_open: bool = False
slur_bracket_close: bool = False
fingerings: list[Fingering]
has_octave_mark: bool = False        # Sprint 9b: did the source BRF write an octave mark
                                      # on this note (vs. inferred by parser state)?
articulation_format: str = "single"  # Sprint 9b: "single"/"start_carry"/"inside_carry"/
                                      # "stop_carry", set by BrailleRenderer's compression pass
parsed_tokens: list[BrailleToken]    # Sprint 9b: the BrailleTokens (with line/position) that
                                      # produced this note, used by BANAValidator's sign-order
                                      # and octave-mark rules — not populated for notes built
                                      # by hand outside the parser
after_numeric_indicator: bool = False # Sprint 9b: True if this is the first note after a
                                       # measure number / multi-measure rest (BANA octave reset)
def to_lilypond() -> str
def to_braille() -> str    # Sprint 9 — implemented
def musical_equals(other) -> bool   # Sprint 9b (S9b-15): equivalence for measure-repeat
                                     # detection, ignoring notation-only fields
```

`Articulation` also gained an `explicit: bool = field(default=True, compare=False)`
field in Sprint 9b, marking whether an articulation was written in the source BRF vs.
carried forward from parser state. `compare=False` keeps it out of `Articulation`'s
(and therefore `Note.musical_equals()`'s) equality check, since it's presentation-only
bookkeeping, not a musical attribute.

### Duration
```python
value: int                 # 1, 2, 4, 8, 16, 32, 64
dots: int                  # augmentation dots (0, 1, or 2)
is_triplet: bool = False   # 3-in-the-time-of-2 (BANA 8.4); no other tuplet ratios supported
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
# Basic conversion (writes .ly to the given path; omit output to print to stdout)
dottednotes convert input.brf output.ly

# Convert and compile to PDF + MIDI (requires lilypond binary installed)
dottednotes convert input.brf output.ly --compile

# Convert with a diagnostic trace on stderr: detected encoding, every
# tokenizer-level token (category + raw braille cell), and validation
# warnings (e.g. beat-count mismatches) in plain text, one per line.
# stdout still carries only the rendered .ly, so `... | lilypond -` stays safe.
dottednotes convert input.brf output.ly --verbose

# Print a BANA validation report (line/measure, message, rule ID) to stderr
# alongside the normal .ly conversion (Sprint 9b)
dottednotes convert input.brf output.ly --report

# Render back to compressed braille instead of LilyPond: a .brf/.brl output
# path switches `convert` to braille output (Sprint 9, CLI-wired in Sprint 9b)
dottednotes convert input.brf output.brf --compression minimal

# Show help
dottednotes --help
dottednotes convert --help

# Show version (from installed package metadata, not a source-tree file read)
dottednotes --version
```

Malformed input or a failed `lilypond` compile prints one plain-text
`Error: ...` line to stderr and exits non-zero — never a Python traceback
(`exceptions.py`, `cli.py`'s `main()`). A `--format` flag for overriding
individual formatting settings (paper size, margins, staff size) from the
command line is planned but not yet implemented (TICKETS.md S7b-10).

`convert` also accepts `--compression {none,minimal,full}` (Sprint 9b, default
`full`), controlling articulation-carry-shorthand and measure-repeat compression
in BRF output. It only has an effect when the output path ends in `.brf`/`.brl`
(see the extension-based dispatch in Key Design Decision 10 above) — it's a
no-op on `.ly` output. `--compile` and a `.brf`/`.brl` output path can't be
combined; combining them raises a plain-text `DottedNotesError`.

---

## Testing Strategy

- Unit tests for every model class `to_lilypond()` method (`test_models.py`,
  `test_fingering_model.py`, `test_exceptions.py`)
- Unit tests for encoding detection, normalization, tokenizing, and the solo
  parser (`test_parser.py`); ensemble/instrument-list parsing has its own
  files (`test_ensemble_parser.py`, `test_ensemble_integration.py`)
- CLI tests drive `cli.py`'s `main()` directly via `sys.argv` + `capsys`
  (`test_cli.py`) — covers `convert`, `--compile`, `--verbose`, `--version`,
  `--report`, `--compression` (including `.brf`/`.brl` output dispatch and the
  `--compile` + braille-output conflict), and both plain-text error paths
  (missing file, malformed input)
- Formatting-pipeline tests (`test_lilypond_formatter.py`) include real
  `lilypond`-binary compile checks per template category, skipped via
  `shutil.which("lilypond")` when the binary isn't installed — and check the
  compile *log* for warnings, not just the exit code (a clean exit code does
  not mean LilyPond was happy with the engraving)
- Integration tests: parse a real `.brf` fixture end to end and compare
  against a hand-authored `.ly` ground truth where one exists
- Round-trip tests (Sprint 9): BRF → Internal Model → BRF via
  `Score.to_braille()` / `BrailleRenderer`
- Validator tests (`test_validation.py`, Sprint 9b): each `BANAValidator` rule
  (octave marks, articulation shorthand, sign order, line length) against
  hand-built BRF snippets, plus `ValidationResult.to_json()`
- Compression tests (`test_compression.py`, Sprint 9b): `musical_equals()` on
  `Note`/`Rest`/`Chord`/`Measure`, and `BrailleRenderer(compression_level=...)`
  output differences across `"none"`/`"minimal"`/`"full"`
- Primary test fixture: `fengyang_flower_drum.brf` (developer's own
  composition, known correct output, per `tests/fixtures/README.md`) — other
  fixtures with a paired `.ly` ground truth include `children_s_piece.brf`,
  `fingering_melody.brf`, `g_major_scale.brf`, and `sprint_4_melody.brf`
- Most real `.brf` fixtures are ASCII-encoded (what a BrailleNotetaker
  actually exports), not Unicode braille — always load fixtures through
  `BRLInputPipeline`, never a raw file read, or ASCII content silently fails
  to tokenize (this exact bug shipped once; see TICKETS.md S7-2)
- Run tests with: `pytest tests/` (add `--cov=dottednotes` for coverage)

---

## Sprint Progress

See TICKETS.md for full ticket details and step-by-step instructions.

- [x] Sprint 0: Project Setup
- [x] Sprint 1: Core Symbol Layer
- [x] Sprint 2: Braille Parser — Notes and Rhythm
- [x] Sprint 3: Key Signatures, Time Signatures, Clefs
- [x] Sprint 4: Articulations, Dynamics, Ornaments, and Text
- [x] Sprint 5: Chords and Multiple Voices
- [x] Sprint 5b: Orchestral Score Support
- [x] Sprint 6: Fingering Notation
- [x] Sprint 7: Score Assembly and Full Pipeline
- [x] Sprint 7b: LilyPond Formatting Library
- [x] Sprint 8: Accessibility and Polish
- [x] Sprint 9: Reverse Direction — LilyPond to BRF
- [x] Sprint 9b: BANA Validator
- [x] Sprint 9c: BANA Formatting Rule Library
- [x] Sprint 10: MusicXML Bridge
- [ ] Sprint 10b: MusicXML Import Hardening
- [ ] Sprint 10c: BANA Transcription for Fermatas, Breath Marks, and First/Second Endings
- [ ] Sprint 10d: MusicXML Import Hardening, Round 2

---

## Known Issues / In-Progress Work

### Resolved (2026-07-17): `Children_s_Piece.ly` crash was a real parser bug, not a transcription error

An earlier version of this note concluded that `tests/fixtures/Children_s_Piece.ly`
(a hand-authored ground-truth fixture) contained transcription errors —
specifically spurious/missing octave marks like `fis'8` vs `f8` — because
parsing it made `LilypondParser` crash with `Octave 9 out of range`. That
diagnosis was wrong, and the fixture's transcription is correct as written.

The real bug was in how `LilypondParser`'s `<<` handling
(`src/dottednotes/parser/lilypond_parser.py`) and
`InAccord.to_relative_lilypond()` (`src/dottednotes/models/in_accord.py`)
resolved `\relative` pitches through `<< {voice1} \\ {voice2} >>`: both
reset each voice to a shared reference pitch and resumed afterward from
voice 1, which is self-consistent but does **not** match real LilyPond.
Verified against the actual `lilypond` binary's `\displayLilyMusic` output:
`\relative` pitch tracking treats `<<`, `\\`, and `>>` as complete no-ops —
it's pure sequential/textual chaining through the token stream. Voice 2
continues from voice 1's *last* note (not the pre-`<<` pitch, not voice 1's
first note); whatever follows `>>` continues from the *last* voice's last
note (not voice 1's). The old model's artificial per-voice reset compounded
into runaway octave drift over many real in-accord measures, eventually
exceeding `Note`'s valid octave range.

Both call sites now implement real sequential chaining. Regression tests
using real-lilypond-verified, non-degenerate probes are in
`tests/test_lilypond_parser.py` (search `chains_from_first_voices_last_note`
/ `uses_last_voice` / `chain_through_last_voice`) and
`tests/test_parser.py::test_in_accord_to_relative_lilypond_prev_midi_advances_through_last_voice`.
`tests/test_e2e_cli.py::test_convert_hand_authored_lilypond_round_trips_cleanly`
confirms `Children_s_Piece.ly` now converts cleanly end to end, producing
41 measures per staff matching its own `%1`–`%41` comment labels.

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

   10. The LilyPond Learning Manual is available at:
    https://lilypond.org/doc/v2.26/Documentation/learning/index.html
    
    The LilyPond Notation Reference is available at:
    https://lilypond.org/doc/v2.26/Documentation/notation/index.html
    
    Before implementing any to_lilypond() method or LilyPond 
    output feature, fetch the relevant section of the Notation 
    Reference first and verify the correct syntax before writing 
    any code. Never guess LilyPond syntax from memory.
    
    Quick section references for common lookups:
    - Note names and accidentals: Notation Reference → Pitches
    - Durations and rhythms: Notation Reference → Rhythms  
    - Articulations: Notation Reference → Expressive marks
    - Dynamics: Notation Reference → Expressive marks
    - Ornaments: Notation Reference → Expressive marks
    - Slurs and ties: Notation Reference → Expressive marks
    - Repeats: Notation Reference → Repeats
    - Chords: Notation Reference → Simultaneous notes
    - Multiple voices: Notation Reference → Simultaneous notes
    - Clefs: Notation Reference → Staff notation
    - Key signatures: Notation Reference → Pitches
    - Time signatures: Notation Reference → Rhythms
    - MIDI output: Notation Reference → MIDI output
    - Instrument names: Notation Reference → Staff notation