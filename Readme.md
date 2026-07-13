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

All CLI output, error messages, and documentation must be screen-reader
friendly: plain text, no ASCII art, no progress bars, no visual-only feedback.

## License

GPL-2.0. See [LICENSE](LICENSE).
