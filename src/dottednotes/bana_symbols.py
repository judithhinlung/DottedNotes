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
    SLUR = auto()
    ORNAMENT = auto()
    BAR_LINE = auto()
    REPEAT = auto()
    INTERVAL = auto()
    CHORD_INDICATOR = auto()
    IN_ACCORD = auto()
    MEASURE_NUMBER = auto()
    HAND_SIGN = auto()
    WORD_SIGN = auto()
    AUGMENTATION_DOT = auto()
    TRIPLET_INDICATOR = auto()
    MULTI_MEASURE_REST = auto()
    FINGERING = auto()
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
    '⠭': 8,  # dots 1,3,4,6  — eighth rest, unambiguous (confirmed by developer,
             # S5b-8, from Fengyang_Flower_Drum.brf Violin I mm. 21-22)
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

# ---------------------------------------------------------------------------
# Measure repeat sign (S5b-2, BANA Music Braille Code 2015, Table 18 / Pars.
# 18.1-18.4, ASCII '7' — dots 2,3,5,6 — confirmed by developer).
#
# A bare cell means "repeat the immediately preceding measure or part of a
# measure" (Par. 18.1). It is context-sensitive, same as several other cells
# in this module:
#   - Preceded by the bar-line prefix ⠣, it forms ⠣⠶ (forward_repeat, a
#     BAR_LINE_SEQUENCES entry) instead — that 2-cell lookahead already runs
#     before a bare ⠶ would be classified, so there is no tokenizer conflict.
#   - The same cell is LOWER_DIGIT_CELLS['⠶'] = 7, but that table is only
#     consulted by the separate §33.2 instrument-list parser
#     (parser/instrument_list.py), never by BrailleTokenizer, so there is no
#     runtime ambiguity either.
# ---------------------------------------------------------------------------

MEASURE_REPEAT_CELL: str = '⠶'  # dots 2,3,5,6 = U+2836

# ---------------------------------------------------------------------------
# Articulation cells
# All articulations are 2-cell sequences whose second cell is ⠦ (dots 2,3,6),
# except staccato (single cell ⠦) and swell (⠤⠄).
#
# Several first cells (⠐, ⠸, ⠨, ⠘, ⠠) are also OCTAVE_MARKS; the tokenizer
# must check 2-cell articulation pairs before classifying isolated octave marks.
#
# Only articulations with LilyPond equivalents are listed here.
# Reversed accent and arpeggios are handled in later sprints.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Word sign and end word sign
# The word sign (⠜, dots 3,4,5) is the prefix for all dynamic markings.
# It is also the clef prefix; the tokenizer checks clef sequences first.
# The end word sign (⠄, dot 3) terminates a dynamic sequence when the
# following cell would otherwise be ambiguous (i.e. starts with dots 1, 2, or 3).
# ---------------------------------------------------------------------------

WORD_SIGN: str = '⠜'    # dots 3,4,5 = U+281C
END_WORD_SIGN: str = '⠄' # dot 3     = U+2804

# ---------------------------------------------------------------------------
# Instrument abbreviations (S5b-1, BANA Music Braille Code 2015, Sec. 33.2,
# Table 29). Fetched directly from the BANA PDF per CLAUDE.md's
# "fetch before implementing" rule (Music_Braille_Code_2015.pdf pp. 27-28).
#
# In the §33.2 instrument-list header and inline part labels, an abbreviation
# is written as WORD_SIGN (⠜, reused here as the "abbreviation lead-in", same
# cell as the dynamics/clef prefix — disambiguated by the two-column header
# structure, not by cell content) + lowercase letters + optional numbering
# (§33.2.2) + END_WORD_SIGN (⠄, dot 3, same cell used elsewhere as a dynamic
# terminator) closing the abbreviation.
#
# Table 29(A), English. Keys match the instrument name exactly as it decodes
# from a BANA-conformant §33.2 header (only the first letter of each newly
# capitalized word is uppercase — see Example 33.2.1-1/33.2.2-1 in the
# manual). Values are the literal lowercase ASCII-braille abbreviation text.
# ---------------------------------------------------------------------------

TABLE_29_ENGLISH: dict[str, str] = {
    'Piccolo': 'pc',
    'Flute': 'fl',
    'Oboe': 'o',
    'English horn': 'eh',
    'Clarinet': 'cl',
    'Bass clarinet': 'bcl',
    'Bassoon': 'b',
    'Double bassoon': 'bb',
    'Horn': 'hn',
    'Trumpet': 'tp',
    'Trombone': 'tb',
    'Tuba': 'tu',
    'Kettledrums': 'dr',
    'Cymbals': 'cym',
    'Triangle': 'tri',
    'Snare drum': 'sdr',
    'Bass drum': 'bdr',
    'Harp right hand': 'hr',
    'Harp left hand': 'hl',
    'Piano right hand': 'pr',
    'Piano left hand': 'pl',
    'Violin I': 'v1',
    'Violin II': 'v2',
    'Viola': 'vl',
    'Violoncello': 'vc',
    'Double bass': 'db',
}

# ---------------------------------------------------------------------------
# Lower-cell digits (§33.2.2's numbering-digit sign, and the same cells
# already confirmed elsewhere in this table for other purposes — e.g. '⠲'
# as a time-signature denominator digit, '⠆' as TRIPLET_INDICATOR/ASCII '2').
# Each cell is literary digit-shifted-down-one-row, i.e. identical to
# ASCII_TO_DOTS['1'..'9','0'] (input_pipeline.py) — the same "lower digit"
# scheme documented under TIME_SIGNATURE_CELLS above.
#
# Only 1 and 2 are exercised by a real fixture so far (Fengyang's
# Violin I / Violin II). 3-9/0 are mechanically derived from the same
# verified ASCII_TO_DOTS shift, not independently developer-confirmed —
# treat with the same caution as any un-exercised entry until a fixture
# using them turns up.
# ---------------------------------------------------------------------------

LOWER_DIGIT_CELLS: dict[str, int] = {
    '⠂': 1,  # dot 2         — ASCII '1'  — confirmed (Fengyang Violin I)
    '⠆': 2,  # dots 2,3      — ASCII '2'  — confirmed (Fengyang Violin II)
    '⠒': 3,  # dots 2,5      — ASCII '3'  — derived, not yet exercised
    '⠲': 4,  # dots 2,5,6    — ASCII '4'  — derived, not yet exercised
    '⠢': 5,  # dots 2,6      — ASCII '5'  — derived, not yet exercised
    '⠖': 6,  # dots 2,3,5    — ASCII '6'  — derived, not yet exercised
    '⠶': 7,  # dots 2,3,5,6  — ASCII '7'  — derived, not yet exercised
    '⠦': 8,  # dots 2,3,6    — ASCII '8'  — derived, not yet exercised
    '⠔': 9,  # dots 3,5      — ASCII '9'  — derived, not yet exercised
    '⠴': 0,  # dots 3,5,6    — ASCII '0'  — derived, not yet exercised
}

# ---------------------------------------------------------------------------
# Single-cell triplet sign (S5-8, BANA Music Braille Code 2015, Sec. 8.4)
# Dots 2-3 (ASCII '2' in ASCII_TO_DOTS), developer-confirmed. Precedes a
# triplet of any note value (3 notes in the time of 2). Doubled for four or
# more successive triplets of the same value; see BrailleParser's triplet
# state handling for the single-vs-doubled semantics.
# ---------------------------------------------------------------------------

TRIPLET_INDICATOR: str = '⠆'  # dots 2,3 = U+2806

# ---------------------------------------------------------------------------
# Dynamic cells
# All dynamic markings are multi-cell sequences beginning with the word sign.
# Dynamic letters use standard braille letter values:
#   p = dots 1,2,3,4 (⠏)   f = dots 1,2,4 (⠋)   m = dots 1,3,4 (⠍)
#   s = dots 2,3,4   (⠎)   z = dots 1,3,5,6 (⠵)
#   c = dots 1,4     (⠉)   d = dots 1,4,5   (⠙)
# Hairpin end letters use the "lower" shift (dots shifted down 3 positions):
#   lower c = dots 2,5 (⠒)   lower d = dots 2,5,6 (⠲)
#
# Keys are ordered longest-first so the tokenizer can use a greedy search.
# Longer sequences must be checked before their shorter prefixes.
# ---------------------------------------------------------------------------

DYNAMIC_CELLS: dict[str, str] = {
    # 4-cell sequences (word sign + 3 letters)
    '⠜⠏⠏⠏': 'ppp',               # word sign + p + p + p
    '⠜⠋⠋⠋': 'fff',               # word sign + f + f + f
    '⠜⠎⠋⠵': 'sfz',               # word sign + s + f + z
    # 3-cell sequences (word sign + 2 letters)
    '⠜⠏⠏':  'pp',                # word sign + p + p
    '⠜⠍⠏':  'mp',                # word sign + m + p
    '⠜⠍⠋':  'mf',                # word sign + m + f
    '⠜⠋⠋':  'ff',                # word sign + f + f
    '⠜⠎⠋':  'sf',                # word sign + s + f
    '⠜⠋⠏':  'fp',                # word sign + f + p
    # 2-cell sequences (word sign + 1 letter)
    '⠜⠏':   'p',                 # word sign + p
    '⠜⠋':   'f',                 # word sign + f
    '⠜⠉':   'crescendo_start',   # word sign + c (dots 1,4)
    '⠜⠙':   'decrescendo_start', # word sign + d (dots 1,4,5)
    '⠜⠒':   'crescendo_end',     # word sign + lower c (dots 2,5) — follows last note
    '⠜⠲':   'decrescendo_end',   # word sign + lower d (dots 2,5,6) — follows last note
}

# ---------------------------------------------------------------------------
# Slur and tie cells
# Ties and slurs use single braille cells or 2-cell sequences.
# Several first cells (⠈, ⠰, ⠘) are also OCTAVE_MARKS; the tokenizer checks
# 2-cell slur pairs before falling through to single-cell octave classification.
# ---------------------------------------------------------------------------

SLUR_CELLS: dict[str, str] = {
    '⠈⠉': 'tie',               # dots 4 + dots 1,4 — placed after tied note
    '⠉':  'slur',              # dots 1,4 — between notes (simple) or doubled for carry
    '⠰⠃': 'slur_bracket_open', # dots 5,6 + dots 1,2 — before first bracketed note
    '⠘⠆': 'slur_bracket_close', # dots 4,5 + dots 2,3 — after last bracketed note
}

# ---------------------------------------------------------------------------
# Articulation cells
ARTICULATION_CELLS: dict[str, str] = {
    '⠦':   'staccato',           # dots 2,3,6           (single cell)
    '⠠⠦': 'staccatissimo',      # dots 6 + dots 2,3,6
    '⠐⠦': 'mezzo_staccato',     # dots 5 + dots 2,3,6
    '⠸⠦': 'tenuto',             # dots 4,5,6 + dots 2,3,6
    '⠨⠦': 'accent',             # dots 4,6 + dots 2,3,6
    '⠘⠦': 'expressive_accent',  # dots 4,5 + dots 2,3,6
    '⠤⠄': 'swell',              # dots 3,6 + dot 3
}

# ---------------------------------------------------------------------------
# Ornament cells
# Verified by developer against BANA Braille Music Technical Manual, Section 15.
#
# PLACEMENT: most ornament signs precede the note they modify.
# BANA order (left to right): ornament → accidental → octave mark → note cell.
# Exception: glissando (⠈⠁, two cells: dot 4 then dot 1) follows the first note.
# The parser attaches it to the preceding note, not the following one.
#
# TRILL ON INTERVALS: when a trill modifies an interval sign (Sprint 5b),
# the trill sign is placed before the interval sign. TODO: implement in S5b.
#
# INFLECTED ORNAMENTS: trills and mordents with accidentals (indicating the
# auxiliary note's pitch) use complex LilyPond \pitchedTrill / \markup output.
# TODO: implement in a future sprint.
#
# Keys are ordered longest-first within each grouping so the tokenizer can
# use a single greedy 3→2→1 cell check.
# ---------------------------------------------------------------------------

ORNAMENT_CELLS: dict[str, str] = {
    # --- 3-cell sequences (check before their 2-cell prefixes) ---
    '⠐⠖⠇': 'lower_mordent',           # dots 5, 2,3,5, 1,2,3  → \mordent
    '⠰⠖⠇': 'extended_lower_mordent',  # dots 5,6, 2,3,5, 1,2,3 → \downmordent
    # --- 2-cell sequences ---
    '⠐⠖': 'upper_mordent',            # dots 5, 2,3,5  → \prall
    '⠰⠖': 'extended_upper_mordent',   # dots 5,6, 2,3,5 → \upmordent
    '⠲⠇': 'inverted_turn',            # dots 2,5,6, 1,2,3 → \reverseturn
    '⠈⠁': 'glissando',                # dot 4, dot 1 — FOLLOWS first note → \glissando
    # --- 1-cell sequences ---
    '⠖': 'trill',                     # dots 2,3,5 → \trill (or span marks for series)
    '⠲': 'turn',                      # dots 2,5,6 → \turn
}

# Grace note / appoggiatura indicator cells.
# Kept separate from ORNAMENT_CELLS because they initiate a two-step parse:
# indicator → consume the following note cell as the grace note, then attach
# to the next real note.
#
# Short appoggiatura (with slash through stem):
#   Sign: dots 2,6 (⠢ = U+2822)
#   LilyPond: \grace { note }
# Long appoggiatura (without slash through stem):
#   Sign: dots 5, 2,6 (two cells: ⠐⠢ = U+2810 + U+2822)
#   LilyPond: \appoggiatura { note }
#
# Note: ACCIACCATURA_INDICATOR is named from the ticket spec; it maps to the
# LONG grace note (no slash) rendered via \appoggiatura, not \acciaccatura.
GRACE_NOTE_INDICATOR: str = '⠢'      # dots 2,6  (U+2822) — short grace (with slash)
ACCIACCATURA_INDICATOR: str = '⠐⠢'  # dots 5 + dots 2,6  — long grace (no slash)

# ---------------------------------------------------------------------------
# Literary braille header markers
# In BANA braille music, header text markings (tempo, expression) that appear
# before the key/time signatures use standard literary braille with a capital
# letter indicator.  The capital indicator (⠠, dots 6) signals that the cell
# immediately following it should be read as an uppercase letter; all subsequent
# cells are read as lowercase literary braille until the literary period (⠲)
# terminates the marking.
#
# Note: ⠠ (dots 6) also appears as the braille music octave-7 mark in
# OCTAVE_MARKS.  The tokenizer resolves the ambiguity by treating ⠠ as a
# capital indicator whenever it is NOT followed by ⠦ (the staccatissimo
# second cell).  Octave 7 is beyond the range of almost all real music and
# is effectively unused in practice.
# ---------------------------------------------------------------------------

CAPITAL_INDICATOR: str = '⠠'   # dots 6 (U+2820) — literary capital letter indicator
LITERARY_PERIOD: str = '⠲'     # dots 2,5,6 (U+2832) — literary period, terminates header text

# ---------------------------------------------------------------------------
# Interval cells
# In braille music a chord is written as a note followed by one or more
# interval signs.  Each interval sign encodes the diatonic distance from
# the written note to the additional chord note.
#
# Direction depends on clef:
#   Treble / alto clef: written note is the HIGHEST; intervals go DOWNWARD.
#   Bass / tenor clef:  written note is the LOWEST;  intervals go UPWARD.
#
# Dot patterns (verified against BANA manual):
#   2nd  — dots 3,4         U+280C  ⠌
#   3rd  — dots 3,4,6       U+282C  ⠬
#   4th  — dots 3,4,5,6     U+283C  ⠼  (same cell as NUMBER_SIGN — context-sensitive)
#   5th  — dots 3,5         U+2814  ⠔
#   6th  — dots 3,5,6       U+2834  ⠴
#   7th  — dots 2,5         U+2812  ⠒
#   8th  — dots 3,6         U+2824  ⠤  (same cell prefix as SWELL — 2-cell ⠤⠄ takes priority)
#
# The 4th-interval cell (⠼) is ambiguous with the NUMBER_SIGN.  The tokenizer
# resolves this by context: ⠼ at a measure boundary starts a key/time signature;
# ⠼ mid-measure (after a note has been seen) is a 4th interval.
# ---------------------------------------------------------------------------

INTERVAL_CELLS: dict[str, int] = {
    '⠌': 2,   # dots 3,4         — 2nd
    '⠬': 3,   # dots 3,4,6       — 3rd
    '⠼': 4,   # dots 3,4,5,6     — 4th  (NUMBER_SIGN cell; context-disambiguated)
    '⠔': 5,   # dots 3,5         — 5th
    '⠴': 6,   # dots 3,5,6       — 6th
    '⠒': 7,   # dots 2,5         — 7th
    '⠤': 8,   # dots 3,6         — 8th (octave)
}

# ---------------------------------------------------------------------------
# In-accord cells
# In-accord is BANA's term for two or more independent rhythmic lines written
# within the same measure, separated by one of these signs.
#
# Source: BANA Music Braille Code 2015, Chapter 11 (pages 87–91), Table 11.
#
# Dot patterns verified from Table 11 ASCII representations via ASCII_TO_DOTS
# (developer to confirm against BANA manual before first use in a real file):
#
#   Full-measure in-accord: ASCII `<>` — dots 1,2,6 + dots 3,4,5 → U+2823 U+281C
#   Part-measure in-accord: ASCII `"1` — dot 5     + dot 2       → U+2810 U+2802
#   Measure division:       ASCII `.k` — dots 4,6   + dots 1,3    → U+2828 U+2805
#
# Scope note: S5-2 implements full-measure in-accord only (BANA 11.1.1).
# Part-measure and measure-division are recognized by the tokenizer but emit a
# "not yet supported" warning from the parser.  See S5-3 for full support.
# ---------------------------------------------------------------------------

IN_ACCORD_CELLS: dict[str, str] = {
    '⠣⠜': 'full_measure',    # dots 1,2,6 + dots 3,4,5  — full-measure in-accord
    '⠐⠂': 'part_measure',    # dot 5      + dot 2        — part-measure in-accord
    '⠨⠅': 'measure_division', # dots 4,6   + dots 1,3    — measure division sign
}

# ---------------------------------------------------------------------------
# Hand signs
# Piano BANA scores mark each physical staff line (right hand / left hand)
# with a 2-cell sign at the start of every line, so the parser can route each
# line's measures to the correct staff without relying on indentation.
#
# Source: developer-confirmed directly (not derived from the BANA manual),
# cross-checked mechanically against every one of the 45 measure lines in
# tests/fixtures/children_s_piece.brf with zero exceptions.
#
#   Right hand: ASCII `.>` — dots 4,6   + dots 3,4,5 → U+2828 U+281C
#   Left hand:  ASCII `_>` — dots 4,5,6 + dots 3,4,5 → U+2838 U+281C
#
# Overlap warning: both signs' first cell is also an OCTAVE_MARKS entry
# elsewhere (⠨=octave 5, ⠸=octave 3), and both share their second cell (⠜)
# with _CLEF_PREFIX in tokenizer.py. ⠨ additionally collides with the first
# cell of IN_ACCORD_CELLS['⠨⠅'] (measure_division). All are disambiguated by
# exact 2-character dict-key lookup, the same mechanism already used for
# IN_ACCORD_CELLS vs. bare octave marks.
#
# Disambiguator: a dot-3 cell (END_WORD_SIGN, ⠄) immediately follows the hand
# sign in the source whenever the very next real content cell contains dot 1,
# 2, or 3 — verified with zero exceptions across the fixture. The tokenizer
# does not predict this; it simply consumes a trailing END_WORD_SIGN after a
# hand sign if present, emitting no token for it.
# ---------------------------------------------------------------------------

HAND_SIGN_CELLS: dict[str, str] = {
    '⠨⠜': 'right',   # dots 4,6   + dots 3,4,5 — right-hand staff
    '⠸⠜': 'left',    # dots 4,5,6 + dots 3,4,5 — left-hand staff
}

# ---------------------------------------------------------------------------
# Literary braille digits — used for measure numbers at the start of each line.
#
# In BANA music braille, measure numbers appear at the left margin of each
# system.  They use the standard literary braille letter-digit convention:
# the same braille cells as letters A–J represent digits 1–0 respectively,
# but WITHOUT a number-sign prefix (⠼).
#
# Dot patterns verified from the fengyang_flower_drum.brf fixture file:
#   A (dot 1)        = 1   → line starts with measure 1
#   D (dots 1,4,5)   = 4   → line starts with measure 4
#   F (dots 1,2,4)   = 6   → line starts with measure 6
#   AJ (dots1 + dots2,4,5) = 10 → line starts with measure 10
#
# IMPORTANT: digits 4–9 and 0 overlap with the 8th-note cell patterns in
# NOTE_CELLS (C–B eighth notes).  Digit 3 (⠉, dots 1,4) overlaps with the
# slur cell.  Position state (at_line_start) is the primary disambiguator:
# these cells are measure-number digits ONLY when at the start of a line,
# and ONLY when followed by another digit or a blank cell (⠀).
# ---------------------------------------------------------------------------

LITERARY_DIGITS: dict[str, int] = {
    '⠁': 1,   # dot 1        (A)
    '⠃': 2,   # dots 1,2     (B)
    '⠉': 3,   # dots 1,4     (C) — also the slur cell mid-line
    '⠙': 4,   # dots 1,4,5   (D) — also C-eighth note mid-line
    '⠑': 5,   # dots 1,5     (E) — also D-eighth note mid-line
    '⠋': 6,   # dots 1,2,4   (F) — also E-eighth note mid-line
    '⠛': 7,   # dots 1,2,4,5 (G) — also F-eighth note mid-line
    '⠓': 8,   # dots 1,2,5   (H) — also G-eighth note mid-line
    '⠊': 9,   # dots 2,4     (I) — also A-eighth note mid-line
    '⠚': 0,   # dots 2,4,5   (J) — also B-eighth note mid-line
}

# ---------------------------------------------------------------------------
# Fingering notation (BANA Section 15 & Table 15)
# ---------------------------------------------------------------------------

FINGERING_CELLS: dict[str, int] = {
    '⠁': 1,  # dot 1
    '⠃': 2,  # dots 1,2
    '⠇': 3,  # dots 1,2,3
    '⠂': 4,  # dot 2
    '⠅': 5,  # dots 1,3
}

FINGERING_CHANGE_CELL: str = '⠉'  # dots 1,4

OMISSION_FIRST_FINGERING_CELL: str = '⠠'  # dot 6
OMISSION_SECOND_FINGERING_CELL: str = '⠄' # dot 3

