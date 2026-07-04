"""
BANA Braille Music symbol table.

Each entry maps a Unicode braille character (U+2800-U+28FF) to its meaning.

Reference: New International Manual of Braille Music Notation (BANA, 1997)
and the 2015 BANA revision.

Note cell structure
-------------------
Each note cell encodes both pitch and duration in a single 6-dot braille cell.

Pitch is determined by the "base" dot pattern, derived from literary braille
letters d through j (dots 1,4,5 through dots 2,4,5):
  C → dots 1,4,5
  D → dots 1,5
  E → dots 1,2,4
  F → dots 1,2,4,5
  G → dots 1,2,5
  A → dots 2,4
  B → dots 2,4,5

Duration class is determined by dots 3 and 6:
  Whole/16th   (base_duration=1): add dots 3 AND 6
  Half/32nd    (base_duration=2): add dot 3 only
  Quarter/64th  (base_duration=4): add dot 6 only

Duration ambiguity
------------------
The same note cell represents two possible durations (e.g. C quarter and C
64th use identical dot patterns). The parser resolves ambiguity using
rhythmic context and the BANA value indicator sign.
"""

from __future__ import annotations

from enum import Enum, auto


class SymbolCategory(Enum):
    NOTE = auto()
    REST = auto()
    ACCIDENTAL = auto()
    OCTAVE_MARK = auto()
    KEY_SIGNATURE = auto()
    TIME_SIGNATURE = auto()
    CLEF = auto()
    ARTICULATION = auto()
    DYNAMIC = auto()
    ORNAMENT = auto()
    BAR_LINE = auto()
    REPEAT = auto()
    INTERVAL = auto()
    CHORD_INDICATOR = auto()
    IN_ACCORD = auto()
    UNKNOWN = auto()


# ---------------------------------------------------------------------------
# Note cells
# Maps Unicode braille char → (note_name, base_duration)
#
# base_duration values (ambiguous pairs):
#   1 = whole note OR 16th note  (dots 3,6 added to pitch base)
#   2 = half note  OR 32nd note  (dot 3 added to pitch base)
#   4 = quarter    OR 64th note  (dot 6 added to pitch base)
#
# Ambiguity is resolved by the parser using rhythmic context.
# ---------------------------------------------------------------------------

NOTE_CELLS: dict[str, tuple[str, int] | None] = {
    '⠀': None,  # blank cell — measure separator (no dots); classified as BAR_LINE, not NOTE

    # --- Eighth / 128th notes (pitch base only — no duration modifier dots) ---
    # In a 16th-note run, these cells represent run continuations (16th notes);
    # see BrailleParser._resolve_measure_durations() for run detection.
    '⠙': ('C', 8),  # dots 1,4,5
    '⠑': ('D', 8),  # dots 1,5
    '⠋': ('E', 8),  # dots 1,2,4
    '⠛': ('F', 8),  # dots 1,2,4,5
    '⠓': ('G', 8),  # dots 1,2,5
    '⠊': ('A', 8),  # dots 2,4
    '⠚': ('B', 8),  # dots 2,4,5

    # --- Quarter / 64th notes (dot 6 added to pitch base) ---
    '⠹': ('C', 4),  # dots 1,4,5,6
    '⠱': ('D', 4),  # dots 1,5,6
    '⠫': ('E', 4),  # dots 1,2,4,6
    '⠻': ('F', 4),  # dots 1,2,4,5,6
    '⠳': ('G', 4),  # dots 1,2,5,6
    '⠪': ('A', 4),  # dots 2,4,6
    '⠺': ('B', 4),  # dots 2,4,5,6

    # --- Whole / 16th notes (dots 3 and 6 added to pitch base) ---
    '⠽': ('C', 1),  # dots 1,3,4,5,6
    '⠵': ('D', 1),  # dots 1,3,5,6
    '⠯': ('E', 1),  # dots 1,2,3,4,6
    '⠿': ('F', 1),  # dots 1,2,3,4,5,6
    '⠷': ('G', 1),  # dots 1,2,3,5,6
    '⠮': ('A', 1),  # dots 2,3,4,6
    '⠾': ('B', 1),  # dots 2,3,4,5,6

    # --- Half / 32nd notes (dot 3 added to pitch base) ---
    '⠝': ('C', 2),  # dots 1,3,4,5
    '⠕': ('D', 2),  # dots 1,3,5
    '⠏': ('E', 2),  # dots 1,2,3,4
    '⠟': ('F', 2),  # dots 1,2,3,4,5
    '⠗': ('G', 2),  # dots 1,2,3,5
    '⠎': ('A', 2),  # dots 2,3,4
    '⠞': ('B', 2),  # dots 2,3,4,5
}

# ---------------------------------------------------------------------------
# Octave marks
# Maps Unicode braille char → octave number (scientific pitch notation)
#
# BANA one-line octave = octave 4 (C4 = middle C).
# Sub-contra (octave 0) uses a two-cell mark ⠈⠈ and is handled in the
# parser rather than this table.
# ---------------------------------------------------------------------------

OCTAVE_MARKS: dict[str, int] = {
    '⠈': 1,  # dots 4          (contra octave)
    '⠘': 2,  # dots 4,5        (great octave)
    '⠸': 3,  # dots 4,5,6      (small octave)
    '⠐': 4,  # dots 5          (one-line octave, middle C)
    '⠨': 5,  # dots 4,6        (two-line octave)
    '⠰': 6,  # dots 5,6        (three-line octave)
    '⠠': 7,  # dots 6          (four-line octave)
}

# ---------------------------------------------------------------------------
# Key signature cells
# Maps Unicode braille char → sharps_or_flats count
# (positive = sharps, negative = flats, 0 not listed — no cell for C major)
#
# POPULATE ONLY WITH VERIFIED VALUES from the BANA Braille Music Technical
# Manual, Chapter 6 (Key Signatures).  Do not guess dot patterns.
# The developer (a blind composer) should verify each entry against the manual
# before adding it.
# ---------------------------------------------------------------------------

KEY_SIGNATURE_CELLS: dict[str, int] = {
    # --- Sharps ---
    # 1–3 sharps: repeated sharp-sign cells (⠩ = dots 1,4,6 = U+2829).
    # Same cell as the accidental sharp; parser uses positional context to
    # distinguish key-signature use from mid-note accidental use (S3-4).
    '⠩': 1,                    # ⠩       G major / E minor   (1 sharp)
    '⠩⠩': 2,              # ⠩⠩     D major / B minor   (2 sharps)
    '⠩⠩⠩': 3,        # ⠩⠩⠩   A major / F♯ minor  (3 sharps)
    # 4–7 sharps: number sign (⠼ dots 3,4,5,6) + braille digit + sharp sign (⠩)
    # Braille digits: 4=⠙(1,4,5) 5=⠑(1,5) 6=⠋(1,2,4) 7=⠛(1,2,4,5)
    '⠼⠙⠩': 4,        # ⠼⠙⠩   E major  / C♯ minor (4 sharps)
    '⠼⠑⠩': 5,        # ⠼⠑⠩   B major  / G♯ minor (5 sharps)
    '⠼⠋⠩': 6,        # ⠼⠋⠩   F♯ major / D♯ minor (6 sharps)
    '⠼⠛⠩': 7,        # ⠼⠛⠩   C♯ major / A♯ minor (7 sharps)

    # --- Flats ---
    # 1–3 flats: repeated flat-sign cells (⠣ = dots 1,2,6 = U+2823).
    # ⠣ also starts multi-cell bar-line sequences; tokenizer uses longest-match
    # lookahead (⠣⠅, ⠣⠅⠄, ⠣⠶, ⠣⠆) before treating ⠣ as key/accidental.
    '⠣': -1,                   # ⠣       F major / D minor   (1 flat)
    '⠣⠣': -2,             # ⠣⠣     B♭ major / G minor  (2 flats)
    '⠣⠣⠣': -3,       # ⠣⠣⠣   E♭ major / C minor  (3 flats)
    # 4–7 flats: number sign (⠼) + braille digit + flat sign (⠣)
    '⠼⠙⠣': -4,       # ⠼⠙⠣   A♭ major / F minor  (4 flats)
    '⠼⠑⠣': -5,       # ⠼⠑⠣   D♭ major / B♭ minor (5 flats)
    '⠼⠋⠣': -6,       # ⠼⠋⠣   G♭ major / E♭ minor (6 flats)
    '⠼⠛⠣': -7,       # ⠼⠛⠣   C♭ major / A♭ minor (7 flats)
}

# ---------------------------------------------------------------------------
# Number sign
# Used as the prefix for both key-signature (4+ accidentals) and time-signature
# cells.  Same cell as literary-braille number indicator.
# ---------------------------------------------------------------------------

NUMBER_SIGN: str = '⠼'   # dots 3,4,5,6 = U+283C

# ---------------------------------------------------------------------------
# Time signature cells
# A BANA time signature is encoded as:
#   NUMBER_SIGN + upper-dot numerator cell(s) + lower-dot denominator cell
#
# Upper-dot numerator cells (same as standard braille digits after #):
#   1=⠁(1)  2=⠃(1,2)  3=⠉(1,4)  4=⠙(1,4,5)  5=⠑(1,5)
#   6=⠋(1,2,4)  7=⠛(1,2,4,5)  8=⠓(1,2,5)  9=⠊(2,4)
#
# Lower-dot denominator cells (each upper-dot digit shifted down by 1 row):
#   /2  = ⠆  (dots 2,3)     U+2806  — unverified
#   /4  = ⠲  (dots 2,5,6)   U+2832  — inferred from fengyang_flower_drum.brf
#   /8  = ⠦  (dots 2,3,6)   U+2826  — confirmed by developer
#   /16 = ⠂⠖ (dot 2 + dots 2,3,5)   — confirmed by developer (two cells)
#
# There is no separate separator cell: the shift to lower dots marks the
# transition from numerator to denominator.
#
# Keys are the full multi-character sequences (NUMBER_SIGN stripped) so
# the tokenizer can do a single table lookup after consuming ⠼.
# ---------------------------------------------------------------------------

TIME_SIGNATURE_CELLS: dict[str, tuple[int, int]] = {
    # Keys include the NUMBER_SIGN prefix (⠼) so the tokenizer can do a single
    # 3-char lookup after encountering ⠼, matching the same pattern used for
    # KEY_SIGNATURE_CELLS.  Verified entries noted below.
    '⠼⠙⠲': (4, 4),   # 4/4 common time  — inferred from fengyang_flower_drum.brf
    '⠼⠉⠲': (3, 4),   # 3/4 waltz time   — confirmed by developer
    '⠼⠋⠦': (6, 8),   # 6/8 compound     — confirmed by developer
    '⠼⠃⠆': (2, 2),   # 2/2 cut time     — confirmed by developer
    '⠼⠃⠲': (2, 4),   # 2/4             — confirmed by developer
}

# ---------------------------------------------------------------------------
# Clef cells
# Maps Unicode braille character(s) → clef type string ('treble', 'bass', etc.)
# Verify every cell against the BANA manual before entering it.
# The ClefType conversion from string to enum happens in the parser (S3-4),
# keeping this table free of any import dependency on models/clef.py.
# ---------------------------------------------------------------------------

CLEF_CELLS: dict[str, str] = {
    # Clef sequences all start with ⠜ (dots 3,4,5) and end with ⠇ (dots 1,2,3).
    # The middle cell(s) identify the clef type.  Tenor is a 4-cell sequence;
    # all others are 3-cell.  The tokenizer checks longest match first (S3-4).
    '⠜⠌⠇': 'treble',   # G clef: dots 3,4,5 + dots 3,4   + dots 1,2,3
    '⠜⠼⠇': 'bass',     # F clef: dots 3,4,5 + dots 3,4,5,6 + dots 1,2,3
    '⠜⠬⠇': 'alto',     # C clef (alto):  dots 3,4,5 + dots 3,4,6 + dots 1,2,3
    '⠜⠬⠐⠇': 'tenor',   # C clef (tenor): dots 3,4,5 + dots 3,4,6 + dots 5 + dots 1,2,3
}

# ---------------------------------------------------------------------------
# Accidental cells
# Maps Unicode braille char → accidental type string
# ---------------------------------------------------------------------------

ACCIDENTAL_CELLS: dict[str, str] = {
    '⠡': 'natural',       # dots 1,6
    '⠩': 'sharp',         # dots 1,4,6
    '⠣': 'flat',          # dots 1,2,6
}

# ---------------------------------------------------------------------------
# Rest cells
# Maps Unicode braille char → base_duration (same ambiguity scheme as notes)
#
# Rests follow the same three-way ambiguity as notes:
#   base_duration 1 = whole rest OR 16th rest
#   base_duration 2 = half rest  OR 32nd rest
#   base_duration 4 = quarter rest OR 64th rest
# ---------------------------------------------------------------------------

REST_CELLS: dict[str, int] = {
    '⠍': 1,  # dots 1,3,4    — whole rest (or 16th rest)
    '⠥': 2,  # dots 1,3,6    — half rest  (or 32nd rest)
    '⠧': 4,  # dots 1,2,3,6  — quarter rest (or 64th rest)
}

# ---------------------------------------------------------------------------
# Value indicator
# The BANA value indicator is a prefix cell that explicitly marks whether a
# note should be read as its long or short duration value.  In practice it
# appears to be extremely rare: the developer (a blind composer) has never
# encountered it in real music, and secondary BANA sources do not define its
# dot pattern.  Duration disambiguation is handled instead by the sequential
# context rules in BrailleParser._resolve_measure_durations().
#
# Leave as None until a verified cell is identified in an actual .brf file.
# ---------------------------------------------------------------------------

VALUE_INDICATOR_CELL: str | None = None

# ---------------------------------------------------------------------------
# Bar line / measure separator
# In BANA braille music, measures are separated by a blank braille cell
# (U+2800, no dots).  Special bar line types use multi-cell sequences,
# all starting with ⠣ (dots 1,2,6 = U+2823), which is also the flat
# accidental cell — the tokenizer uses lookahead to distinguish them.
# ---------------------------------------------------------------------------

BAR_LINE_CELLS: dict[str, str] = {
    '⠀': 'measure_separator',  # U+2800 — blank braille cell (no dots)
}

# Multi-cell bar line sequences (all begin with ⠣, dots 1,2,6 = U+2823).
# The 3-cell entry MUST be listed before the 2-cell ⠣⠅ entry so the
# tokenizer checks the longer match first.
BAR_LINE_SEQUENCES: dict[str, str] = {
    '⠣⠅⠄': 'section_double_bar',  # dots 1,2,6 + dots 1,3 + dot 3  (end of section)
    '⠣⠅':  'final_double_bar',    # dots 1,2,6 + dots 1,3           (end of piece)
    '⠣⠶':  'forward_repeat',      # dots 1,2,6 + dots 2,3,5,6
    '⠣⠆':  'end_repeat',          # dots 1,2,6 + dots 2,3
}
