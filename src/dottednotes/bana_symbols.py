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
  Whole/16th  (base_duration=1): add dots 3 AND 6
  Half/8th    (base_duration=2): add dot 3 only
  Quarter/32nd(base_duration=4): add dot 6 only

Duration ambiguity
------------------
The same note cell represents two possible durations (e.g. C quarter and C
32nd use identical dot patterns). The parser resolves ambiguity using
rhythmic context and the BANA value indicator sign.
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


# ---------------------------------------------------------------------------
# Note cells
# Maps Unicode braille char → (note_name, base_duration)
#
# base_duration values (ambiguous pairs):
#   1 = whole note OR 16th note  (dots 3,6 added to pitch base)
#   2 = half note  OR 8th note   (dot 3 added to pitch base)
#   4 = quarter    OR 32nd note  (dot 6 added to pitch base)
#
# Ambiguity is resolved by the parser using rhythmic context.
# ---------------------------------------------------------------------------

NOTE_CELLS: dict[str, tuple[str, int] | None] = {
    '⠀': None,  # blank cell (space/padding)

    # --- Quarter / 32nd notes (dot 6 added to pitch base) ---
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

    # --- Half / 8th notes (dot 3 added to pitch base) ---
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
# Maps Unicode braille char → octave number (BANA octave 1–8)
#
# BANA octaves align with scientific pitch notation:
#   octave 4 = middle C octave (C4)
#   octave 5 = one-line octave (C5)
#
# Octave 1 (sub-contra) uses a two-cell mark ⠈⠈ and is handled in the
# parser rather than this table.
# ---------------------------------------------------------------------------

OCTAVE_MARKS: dict[str, int] = {
    '⠈': 2,  # dots 4          (contra octave)
    '⠘': 3,  # dots 4,5        (great octave)
    '⠸': 4,  # dots 4,5,6      (small octave, contains middle C)
    '⠐': 5,  # dots 5          (one-line octave)
    '⠨': 6,  # dots 4,6        (two-line octave)
    '⠰': 7,  # dots 5,6        (three-line octave)
    '⠠': 8,  # dots 6          (four-line octave)
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
#   base_duration 2 = half rest  OR 8th rest
#   base_duration 4 = quarter rest OR 32nd rest
# ---------------------------------------------------------------------------

REST_CELLS: dict[str, int] = {
    '⠍': 1,  # dots 1,3,4    — whole rest (or 16th rest)
    '⠥': 2,  # dots 1,3,6    — half rest  (or 8th rest)
    '⠧': 4,  # dots 1,2,3,6  — quarter rest (or 32nd rest)
}
