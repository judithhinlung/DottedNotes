# Development Guide

This document walks a human contributor through how DottedNotes fits
together and how to extend it. It complements `docs/bana_reference.md`
(the braille symbol table) and `docs/lilypond_conventions.md` (the output
formatting defaults) rather than repeating either — read this first for
the shape of the pipeline, then follow the links out to those two when you
need symbol- or formatting-level detail.

If you haven't read the project's `CLAUDE.md` yet, the short version of
its most important rule applies here too: never guess a BANA dot pattern
or LilyPond syntax detail. Cite the BANA Music Braille Code 2015 manual or
the LilyPond Notation Reference, or ask.

## The pipeline, in one sentence

A `.brf`/`.brl` file becomes Unicode braille, then a flat list of
classified tokens, then a tree of domain-model objects (notes, measures,
staves, a score), and each of those objects knows how to render itself as
LilyPond text. Every stage is a real, separately testable Python class:

1. `BRLInputPipeline` (`src/dottednotes/parser/input_pipeline.py`) —
   detects whether a file is ASCII braille (what a BrailleNotetaker
   actually exports) or already Unicode braille, and normalizes either
   one to Unicode braille (U+2800-U+28FF). Every real code path loads
   input through this class; nothing reads a `.brf` file directly.
2. `BrailleTokenizer` (`src/dottednotes/parser/tokenizer.py`) — walks the
   normalized Unicode text and produces a flat list of `BrailleToken`
   objects, each one classified into a `SymbolCategory` (NOTE, REST,
   OCTAVE_MARK, TIME_SIGNATURE, and so on, defined in
   `bana_symbols.py`). Most cells classify from a single character; a few
   BANA conventions need lookahead across two or three cells (documented
   in the tokenizer's own module docstring).
3. `BrailleParser` (`src/dottednotes/parser/braille_parser.py`) — walks
   the token list and builds up domain-model objects: `Note`, `Rest`,
   `Measure`, `Staff`, `Score`, and so on
   (`src/dottednotes/models/`). This is where BANA's context-dependent
   rules live — for example, resolving a note cell's ambiguous duration,
   or tracking which octave a run of notes without an explicit octave
   mark belongs to. `EnsembleParser`
   (`src/dottednotes/parser/ensemble_parser.py`) is the same idea for
   scores with an instrument-list header (BANA §33) instead of a single
   staff.
4. Every domain-model class renders itself. `Note.to_lilypond()`,
   `Measure.to_lilypond()`, `Score.to_lilypond()`, and so on each return
   the LilyPond text for that object — the model is the pivot point for
   translation, not a separate formatter walking the tree from outside.

## Worked example: one measure end to end

Here's a real, minimal input file — a 4/4 time signature followed by one
measure with a middle-C quarter note:

```
⠀⠀⠼⠙⠲
⠐⠹
```

Running `dottednotes convert` on this file with `--verbose` shows every
stage:

```
$ dottednotes convert example.brf --verbose
Detected encoding: unicode
Token: BAR_LINE ⠀
Token: BAR_LINE ⠀
Token: TIME_SIGNATURE ⠼⠙⠲
Token: OCTAVE_MARK ⠐
Token: NOTE ⠹
Token: BAR_LINE ⠀
Warning: Measure 1: expected 4.0 beats but counted 1.0. Check for notation ambiguity or missing/extra notes.
\version "2.26.0"
...
\score {
  \relative c' {
      \time 4/4
      \clef treble
      c4 |
  }
  \layout { }
  \midi { }
}
```

Tracing what produced each line:

- `BRLInputPipeline._detect_encoding` sees the first non-whitespace
  character is already in the U+2800-U+28FF range, so the file passes
  through unchanged (`"Detected encoding: unicode"`). A `.brf` exported
  from a BrailleNotetaker would instead be ASCII braille, and
  `_ascii_to_unicode` would convert every character via the
  `ASCII_TO_DOTS` table before tokenizing.
- `BrailleTokenizer` classifies `⠼⠙⠲` (three cells, looked up together)
  as `TIME_SIGNATURE` via `TIME_SIGNATURE_CELLS`, which maps it to
  `(4, 4)`. It classifies `⠐` as `OCTAVE_MARK` (`OCTAVE_MARKS['⠐'] == 4`,
  BANA's one-line octave, i.e. the octave containing middle C) and `⠹` as
  `NOTE` (`NOTE_CELLS['⠹'] == ('C', 4)` — pitch class C, `base_duration`
  4, meaning "quarter or 64th," resolved to quarter by context).
- `BrailleParser.parse()` sees `OCTAVE_MARK` and calls
  `_handle_octave_mark`, which sets `_current_octave = 4` and a
  "pending" flag. The following `NOTE` token then calls `_buffer_note`,
  which builds a `Note(note_name='C', octave=4, duration=Duration(value=4), ...)`
  and consumes the pending octave. The beat-count warning comes from the
  parser's own validation: a 4/4 measure with one quarter note is short
  three beats, which is expected here since this is a deliberately
  minimal example, not a bug.
- Rendering happens through `to_relative_lilypond`, not `to_lilypond()`
  directly. `Score.to_lilypond()` opens the block with `\relative c'`
  (reference pitch C4), and `Measure.to_lilypond()` then calls each
  item's `to_relative_lilypond(prev_midi)` in sequence, threading the
  previous pitch through so every note's octave marks (`'` / `,`) come
  out relative to the note before it, per LilyPond's own nearest-neighbor
  convention, rather than as absolute marks. For this example the note's
  absolute pitch (C4) equals the relative reference pitch, so no octave
  mark is needed at all: the measure body is just `c4`. `to_lilypond()`
  still exists on every model (see "Adding a new domain model class"
  below) — it's what gets called for cases where relative-pitch chaining
  doesn't apply, and it's the method every model is required to
  implement.

## Adding a new BANA symbol

1. Look up the symbol in the BANA Music Braille Code 2015 manual
   (linked from `CLAUDE.md`). Never guess a dot pattern from how it looks
   or from a search result — cite the manual, or ask the developer to
   confirm the dot pattern from her own BrailleNotetaker if the manual is
   ambiguous.
2. Add the cell to the relevant table in
   `src/dottednotes/bana_symbols.py` (e.g. `NOTE_CELLS`,
   `ARTICULATION_CELLS`, `ORNAMENT_CELLS` — there's one table per
   `SymbolCategory`, and most are simple `dict[str, ...]` literals keyed
   by the Unicode braille cell). If the symbol doesn't fit any existing
   category, add a new member to the `SymbolCategory` enum near the top
   of that file.
3. Teach `BrailleTokenizer` to classify the new cell into that category
   (`src/dottednotes/parser/tokenizer.py`). Single-cell symbols are
   usually a dictionary lookup already handled generically; multi-cell
   sequences need explicit lookahead logic — see the tokenizer's module
   docstring for the existing examples (bar-line prefixes, key
   signatures, clefs) and follow the same pattern.
4. Teach `BrailleParser` what to do when it encounters a token of that
   category (`src/dottednotes/parser/braille_parser.py`) — typically
   building or updating a domain-model object.
5. `bana_symbols.py` is the single authoritative source for dot patterns
   in this codebase — don't duplicate a dot-pattern table anywhere else.

## Adding a new domain model class

Every symbol that renders into LilyPond output is a domain-model class
in `src/dottednotes/models/`, following the `BrailleSymbol` base contract
(`models/base.py`): a `dots` field, a `category` field, a `raw_brl`
field, and a required `to_lilypond()` method (calling it on the base
class directly raises `NotImplementedError` — every subclass must
override it).

To add one end to end:

1. Create the class in a new or existing file under
   `src/dottednotes/models/`, subclassing or following the shape of
   `BrailleSymbol`. Implement `to_lilypond()` — fetch the relevant
   section of the LilyPond Notation Reference first (linked from
   `CLAUDE.md`) and verify the exact syntax before writing it; don't
   write LilyPond syntax from memory.
2. If the object can appear inside a `\relative` block, also implement
   `to_relative_lilypond(prev_midi)` returning `(lilypond_str,
   new_prev_midi)` — see "Worked example" above for why this is the
   method actually called when rendering measure contents, and look at
   `Note.to_relative_lilypond` or `Chord.to_relative_lilypond` for the
   pattern.
3. Export the new class from `src/dottednotes/models/__init__.py` (both
   the `from .yourmodule import ...` line and the `__all__` list).
4. Wire it into `BrailleParser` (or `EnsembleParser`, if it's
   ensemble-only) so a token of the corresponding category actually
   produces an instance of your new class.
5. Add unit tests to `tests/test_models.py` covering `to_lilypond()` (and
   `to_relative_lilypond()` if implemented) directly against the model
   class, independent of the parser.
6. Add or extend an integration-test fixture (see "Testing conventions"
   below) so the new symbol is also covered end to end, from raw braille
   input through to rendered LilyPond output.

## Testing conventions

- Every model class has direct unit tests against its `to_lilypond()`
  method in `tests/test_models.py` (plus dedicated files for larger
  subsystems, e.g. `test_fingering_model.py`).
- Tokenizing and solo-score parsing have their own unit tests in
  `tests/test_parser.py`; ensemble/instrument-list parsing has its own
  files (`test_ensemble_parser.py`, `test_ensemble_integration.py`).
- `tests/test_cli.py` drives `cli.py`'s `main()` directly via `sys.argv`
  and `capsys`, covering `convert`, `--compile`, `--verbose`,
  `--version`, and both plain-text error paths.
- Integration tests parse a real `.brf` fixture end to end and compare
  it against a hand-authored `.ly` ground truth, where one exists (see
  `tests/fixtures/README.md` for which fixtures have one and why).
- **Fixture gotcha (this has shipped as a real bug once — S7-2):** most
  real `.brf` fixtures are ASCII-encoded, since that's what a
  BrailleNotetaker actually exports, not Unicode braille. Always load a
  fixture through `BRLInputPipeline`, never a raw file read
  (`Path(...).read_text()` or similar) — a raw read skips ASCII-to-Unicode
  normalization, and the content will silently fail to tokenize instead
  of raising an obvious error.
- Run the suite with `pytest tests/` (add `--cov=dottednotes` for
  coverage). Formatting-pipeline tests that invoke the real `lilypond`
  binary are skipped automatically when it isn't installed, via
  `shutil.which("lilypond")`.

## Where to go next

- `docs/bana_reference.md` — the braille symbol table itself: dot
  patterns, duration ambiguity resolution, octave marks, and so on.
- `docs/lilypond_conventions.md` — where the output formatting defaults
  (paper size, staff size, margins per instrumentation category) come
  from, and the Mutopia corpus evidence behind each one.
- `CONTRIBUTING.md` — how to actually open a pull request, including this
  project's accessibility bar for any change touching CLI output or
  documentation, and dedicated guidance for blind and low-vision
  contributors.
