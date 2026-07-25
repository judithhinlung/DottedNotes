# DottedNotes

![CI](https://github.com/judithhinlung/DottedNotes/actions/workflows/ci.yml/badge.svg)

A Python tool that converts braille music notation (.brf/.brl) to LilyPond (.ly),
giving blind composers a direct path from their native notation to PDF scores and MIDI audio.

## Why DottedNotes exists

Blind musicians who compose in braille music notation have no direct path from
their native format to publication-quality scores or audio playback without
sighted assistance. Existing tools go the opposite direction — they convert
printed notation *to* braille, not the other way around.

DottedNotes closes that gap. A blind composer can write in braille on a
BrailleNotetaker or any braille editor, then run one command to produce a
LilyPond file that compiles to a PDF score and MIDI file — no sighted
intermediary required.

## Current status

Active development. The tool supports solo and ensemble scores (multiple parallel instruments, keyboard staves, and vocal scores with lyric alignment), key and time signatures, measure divisions, repeats, tuplets/triplets, and fingerings.
The full sprint schedule is in [TICKETS.md](TICKETS.md).

## Workflow

```
composer writes in braille → .brf file
→ dottednotes convert piece.brf piece.ly
→ lilypond piece.ly → piece.pdf + piece.midi
```

## Installation

### 1. Install DottedNotes

Requires Python 3.9 or later. It is highly recommended to install the package inside a virtual environment to avoid macOS code-signing issues and global permission conflicts (which can result in a `kill -9` or `Killed: 9` error in the terminal).

```bash
# Clone the repository
git clone https://github.com/judithhinlung/DottedNotes.git
cd DottedNotes

# Create a virtual environment
python3 -m venv .venv

# Activate the virtual environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
# .venv\Scripts\activate

# Install in development mode with dev dependencies
pip install -e ".[dev]"
```

### 2. Install LilyPond (Optional, required for --compile)

To compile the generated LilyPond `.ly` files to print-ready PDF scores and MIDI audio, you need to install the `lilypond` binary:

* **macOS**:
  Install via Homebrew:
  ```bash
  brew install lilypond
  ```
* **Linux (Debian/Ubuntu)**:
  Install via apt:
  ```bash
  sudo apt-get install lilypond
  ```
* **Windows / Other**:
  Download the installer or archive for your system from the [LilyPond download page](https://lilypond.org/download.html) and add the directory containing the `lilypond` executable to your system's `PATH`.

## Usage

All commands use the `convert` subcommand to process input files. Both `.brf` (ASCII braille) and `.brl` (Unicode braille) input files are supported. The tool automatically detects the file encoding.

```bash
# Convert a braille music file to LilyPond and output to stdout
dottednotes convert piece.brf

# Convert and write the output directly to a file
dottednotes convert piece.brf piece.ly

# Convert and compile to PDF + MIDI (requires lilypond to be installed on your PATH)
dottednotes convert piece.brf piece.ly --compile

# Verbose output — prints diagnostic info (detected encoding, tokens, validation warnings) to stderr
dottednotes convert piece.brf piece.ly --verbose

# Override the layout category (defaults to auto-detection from staves and instruments)
dottednotes convert piece.brf piece.ly --category "Chamber"

# Override specific formatting options using key=value pairs
dottednotes convert piece.brf piece.ly --format "paper_size=a4,margin_mm=12,staff_size=18"

# Print BANA validation report (corrections list) to stderr
dottednotes convert piece.brf --report

# Render back to compressed braille instead of LilyPond: a .brf/.brl output
# path switches to BRF output. --compression controls shorthand carrying and
# measure-repeat compression (full, minimal, none).
dottednotes convert piece.brf piece.brf --compression minimal

# Show measure numbers in braille output, keeping the source MusicXML/
# LilyPond file's own numbering (e.g. a pickup measure numbered 0) instead
# of renumbering sequentially from 1
dottednotes convert piece.musicxml piece.brf --measure-numbers --measure-numbering print_score

# List all available parts (staves) in a multi-staff score
dottednotes convert piece.musicxml --list-parts

# Convert only a specific part (by 1-based index or name)
dottednotes convert piece.musicxml piece.ly --part 2
dottednotes convert piece.musicxml piece.ly --part "Soprano"

# Convert a BANA Sec. 24 single-line-format instrumental solo, naming its
# instrument (the braille never states this itself)
dottednotes convert piece.brf piece.ly --single-line --instrument violin

# List every instrument name --instrument accepts
dottednotes --list-instruments

# Show version
dottednotes --version
```

### Customization Options

* **`--category <CategoryName>`**:
  Overrides the default layout template heuristics. The layout controls the default staff size, margins, and staff grouping.
  Supported categories:
  * `Solo Piano` (Default for single/double keyboard instrument scores; staff size 20.0 pt, margins 20 mm)
  * `Art Song` (Default for voice + keyboard scores; staff size 18.0 pt, margins 18 mm)
  * `Chamber` (Default for 3–6 staves; staff size 16.0 pt, margins 15 mm)
  * `Orchestral` (Default for >6 staves; staff size 14.1 pt, margins 12 mm)

  > [!NOTE]
  > Overriding a score's category to a non-vocal category (e.g. `Chamber` or `Solo Piano`) prevents the parser from extracting vocal lyrics from literary braille lines, suppressing lyric mapping and `\addlyrics` rendering.

* **`--format "key1=value1,key2=value2"`**:
  Applies specific, comma-separated layout/formatting overrides on top of the template defaults.
  Supported format keys:
  * `paper_size` (string, e.g. `a4`, `letter`)
  * `margin_mm` (float, margin size in millimeters)
  * `staff_size` (float, global staff size in points)
  * `basic_distance` (float, basic distance between systems)
  * `padding` (float, padding spacing between systems)

* **`--report`**:
  Runs the BANA validator on the parsed music score and prints a line-by-line list of correction warnings (such as sign order violations, missing octave marks under register rules, and shorthand recommendations) to `stderr`.

* **`--compression <Level>`**:
  Sets the level of braille shorthand/compression used when the `convert` output path
  ends in `.brf` or `.brl` (which renders back to braille instead of LilyPond). Has no
  effect on ordinary `.ly` output.
  Supported levels:
  * `full` (Default; enables all shorthand carrying and measure repeat compression)
  * `minimal` (Enables shorthand carrying and measure repeats, but disables long-span repeats if supported)
  * `none` (Disables all shorthand carrying and repeat compression, rendering notes and articulations explicitly)

* **`--measure-numbers`**:
  Shows measure numbers at all. Off by default. In `.brf`/`.brl` output this
  is the BANA margin number (solo/keyboard) or heading (ensemble) that
  marks where each system starts; in `.ly` output it's a `% N` comment on
  each measure's line instead, for navigating a validation warning back to
  its source line.

* **`--measure-numbering <Mode>`**:
  Only matters when `--measure-numbers` is on, and only for `.brf`/`.brl`
  output — controls *which* number gets shown, not whether one is shown.
  * `auto` (Default; numbers measures sequentially from 1, ignoring
    whatever measure numbers the source file has — a plain BRF's own
    margin numbers, or a MusicXML/LilyPond file's `<measure number="...">`,
    are all disregarded in favor of a clean 1, 2, 3, ... count)
  * `print_score` (Reads and keeps the source MusicXML/LilyPond file's own
    measure numbers instead of recalculating them — including an
    irregular pickup measure numbered 0, or a mid-piece renumbering that
    isn't strictly sequential. A LilyPond source currently has no way to
    carry that original numbering through the round trip, so `print_score`
    and `auto` behave the same there; MusicXML and BRF sources aren't
    affected by that limitation.)

* **`--octave-mark-every-measure`**:
  For `.brf`/`.brl` output, forces the octave mark on every measure's first
  note, not just measures that start a new braille line. Off by default.
  This is a reader/regional preference on top of BANA's required rules
  (which already force the mark at each line's first note, and after a
  word sign or numeric indicator) — turning it on never removes a mark
  that would already be shown, it only adds more. Has no effect on `.ly`
  output.

* **`--full-measure-repeat <Mode>`**:
  Controls whole-measure repeat-sign compression for `.brf`/`.brl` output,
  independent of `--compression`'s (unrelated) articulation-carry
  shorthand. Has no effect if `--compression` is `none` (that remains a
  hard override disabling all compression) or on `.ly` output.
  * `single-voice` (Default; compresses runs of identical measures, but
    never a measure containing in-accord/multi-voice content)
  * `off` (Disables repeat-sign compression entirely)
  * `multi-voice` (Also compresses in-accord-containing measures, when
    every voice matches)

* **`--min-repeated-measures <N>`**:
  Minimum number of consecutive musically-identical measures required
  before they're compressed into a repeat sign, for `.brf`/`.brl` output.
  Default `2` (the smallest possible repeat: one original plus one
  repetition). Has no effect if `--full-measure-repeat` is `off` or on
  `.ly` output.

* **`--include-clef-sign`**:
  For `.brf`/`.brl` output, includes the clef sign for a facsimile
  transcription (BANA Par. 4.1: clef signs are otherwise routinely omitted
  in braille music). Off by default. When on, the clef is stated once,
  right after the first measure's number — not glued onto the key/time
  signature line. Has no effect on `.ly` output.

* **`--list-parts`**:
  Prints a list of all available parts (staves) in the score and their indices, then exits.

* **`--part <IndexOrName>`**:
  Filters the score to include only the specified part before rendering. Accepts a 1-based index (e.g. `2`) or a case-insensitive part name (e.g. `Soprano`).

* **`--single-line`**:
  Parses `.brf`/`.brl` input as BANA Sec. 24 single-line format (an
  instrumental solo or single ensemble part) — its braille never states
  which instrument it's written for (Secs. 24.1–24.5 only cover segment/
  measure-number layout). Not valid with MusicXML/LilyPond input, which
  already carries its own instrument information.

* **`--instrument <Name>`**:
  Names the instrument for a `--single-line` conversion, from LilyPond's
  General MIDI instrument list (run `dottednotes --list-instruments` to
  see every option — e.g. `violin`, `flute`, `french horn`). Sets the
  output staff's name and `\set Staff.midiInstrument`. Optional: if
  omitted, the instrument is inferred from the piece's title (e.g. "for
  Violin"), falling back to piano when nothing recognizable is found. The
  same inference (with a confirm/override prompt) drives the web UI's
  post-translation instrument popup — see `web.py`'s
  `needs_instrument_selection`/`POST /api/jobs/{id}/instrument`, which
  also covers an extracted piano hand (`right hand`/`left hand` are
  parser placeholders, not real instrument names).

* **`--list-instruments`**:
  Prints every instrument name `--instrument` accepts, one per line, and
  exits. Works standalone, without `convert` or an input file (like
  `--version`).

> [!NOTE]
> DottedNotes transcribes braille input faithfully rather than
> auto-correcting it, so a few things are on the transcriber to get right
> in the source `.brf`/`.brl` file:
> - **Capitalization**: follow BANA's literary-braille capital-indicator
>   convention for instrument names, titles, and tempo/mood markings (e.g.
>   "Allegro moderato", not "allegro moderato") — DottedNotes reproduces
>   whatever capitalization the braille actually encodes, it doesn't infer
>   proper-noun or sentence casing on its own.
> - **Key signature mode**: braille key signatures encode a sharp/flat
>   count only, with no way to distinguish a major key from its relative
>   minor (e.g. E minor and G major share one sharp) — DottedNotes always
>   emits the major spelling; if the piece is actually in the relative
>   minor, edit the generated `\key` line by hand.

## Web UI

A hosted version is available at [www.dottednotes.net](https://www.dottednotes.net) —
no installation required. Upload a `.brf`, `.brl`, `.ly`, `.musicxml`, `.xml`, or `.mxl`
file, choose the options described below, and download the converted result (and, for
LilyPond output, the compiled PDF/MIDI if compilation succeeds).

The web UI's options mirror the CLI's `convert` flags one-to-one — the "What do these
options mean?" link on the page points back to this section.

* **Target Format**: LilyPond (`.ly`, `.pdf`, `.midi`), Braille Music (`.brf`),
  Braille Music (`.brl`), or MusicXML (`.musicxml`). Corresponds to `dottednotes convert`'s
  choice of output file extension.
* **Layout Category**: same as `--category` — Default (auto-detect), Solo Piano, Art Song,
  Chamber, Orchestral, or Lead Sheet.
* **Braille Compression**: same as `--compression` — Full Compression, Minimal
  Compression, or No Compression. Only affects Braille Music output.
* **BANA Validation Profile**: Standard or Strict (extra checks). Controls which rules the
  BANA Formatting Rule Report (below the downloads) checks for.
* **Include Measure Numbers**: same as `--measure-numbers`.
* **Measure Numbering**: same as `--measure-numbering` — Auto (renumber sequentially from
  1) or Print Score (keep the source file's own numbers). Only matters when Include
  Measure Numbers is on.
* **Include Page Numbers**: adds the piece title and a braille page number to every page
  of Braille Music output. On by default; turn off for a plain continuous stream with no
  page breaks.
* **Always Mark Octave at Start of Measure**: same as `--octave-mark-every-measure`.
* **Include Clef Sign (Facsimile)**: same as `--include-clef-sign`.
* **Full-Measure Repeat**: same as `--full-measure-repeat` — Single-Voice Only (default),
  Off, or Single- and Multi-Voice.
* **Minimum Repeated Measures**: same as `--min-repeated-measures`.
* **Advanced Formatting Overrides**: same as `--format`, entered as the same
  comma-separated `key=value` string (e.g. `paper_size=a4,margin_mm=12`).

For a multi-staff score, a **part selector** appears next to the downloads so you can
fetch a single part (staff) instead of the full score — equivalent to the CLI's
`--list-parts`/`--part`.

### Instrument selection dialog

If the uploaded file is a BANA Sec. 24 single-line-format `.brf`/`.brl` (an instrumental
solo or single ensemble part) — or an extracted piano hand from a keyboard score — the
result has no instrument name of its own: single-line braille never states which
instrument it's written for, and "right hand"/"left hand" are internal placeholders, not
real instrument names. In both cases the web UI pops up an **instrument selection
dialog** after translation, equivalent to the CLI's `--instrument` flag.

Before showing the dialog, DottedNotes makes a best-effort guess: it tries to infer the
instrument from the piece's title (e.g. a title containing "for Violin"), and falls back
to piano if nothing recognizable is found. That guess is pre-applied to the initial
output and pre-selected in the dialog — you can accept it as-is, pick a different
instrument from the list, or dismiss the dialog to keep the guessed/default instrument.

## Background

This project is written by a blind composer who uses a BrailleNotetaker to
compose and LilyPond for engraving and MIDI output. The developer previously
contributed to [Freedots](https://github.com/mlang/freedots), a project
that converted MusicXML to braille. DottedNotes works in the reverse direction
and is designed from the ground up for accessibility: all output is plain text,
all error messages are screen-reader friendly, and no sighted assistance is
required at any step.

## Running the tests

```bash
pytest tests/
pytest tests/ --cov=dottednotes --cov-report=term-missing
```

## Contributing

Contributions are welcome, especially from blind or low-vision developers and
musicians who use braille notation. Please open an issue before starting
significant work so we can coordinate.

See [docs/development.md](docs/development.md) for an architecture
walkthrough of the BRF/BRL → LilyPond pipeline, a worked example tracing
one measure through it end to end, and how to add a new BANA symbol or
domain model class. See [CONTRIBUTING.md](CONTRIBUTING.md) for issue/PR
conventions, dev environment setup, and dedicated guidance for blind and
low-vision contributors.

All CLI output, error messages, and documentation must be screen-reader
friendly: plain text, no ASCII art, no progress bars, no visual-only feedback.

## License

GPL-2.0. See [LICENSE](LICENSE).
