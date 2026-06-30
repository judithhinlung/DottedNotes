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

Active development — Sprint 0 (project setup and input pipeline) is complete.
The full planned sprint schedule is in [TICKETS.md](TICKETS.md).

## Workflow

```
composer writes in braille → .brf file
→ dottednotes convert piece.brf piece.ly
→ lilypond piece.ly → piece.pdf + piece.midi
```

## Installation

Requires Python 3.9 or later.

```bash
git clone https://github.com/judithhinlung/DottedNotes.git
cd DottedNotes
pip install -e ".[dev]"
```

To also compile LilyPond output to PDF and MIDI, install LilyPond separately:
[lilypond.org](https://lilypond.org/download.html)

## Usage

```bash
# Convert a braille music file to LilyPond
dottednotes convert piece.brf piece.ly

# Convert and compile to PDF + MIDI (requires lilypond installed)
dottednotes convert piece.brf piece.ly --compile

# Verbose output — lists all symbols parsed and any skipped
dottednotes convert piece.brf piece.ly --verbose

# Show version
dottednotes --version
```

Both `.brf` (ASCII braille) and `.brl` (Unicode braille) input files are supported.
The tool detects the encoding automatically.

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
