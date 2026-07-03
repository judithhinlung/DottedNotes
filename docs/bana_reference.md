# BANA Braille Music Reference

This document is a human-readable reference for the braille music symbols used by
DottedNotes, as defined by the Braille Authority of North America (BANA).

## Source

*New International Manual of Braille Music Notation* (BANA, 1997)
and the 2015 BANA revision.

---

## Note Cell Structure

Each note cell encodes both pitch and duration in a single 6-dot braille cell.

**Pitch base patterns** (derived from literary braille letters d through j):

| Note | Base dots | Literary letter |
|------|-----------|-----------------|
| C    | 1, 4, 5   | d               |
| D    | 1, 5      | e               |
| E    | 1, 2, 4   | f               |
| F    | 1, 2, 4, 5| g               |
| G    | 1, 2, 5   | h               |
| A    | 2, 4      | i               |
| B    | 2, 4, 5   | j               |

**Duration class** is added to the pitch base using dots 3 and 6:

| Duration group       | Modifier        | base_duration |
|----------------------|-----------------|---------------|
| Eighth / 128th note  | no modifier     | 8             |
| Quarter / 64th note  | add dot 6 only  | 4             |
| Half / 32nd note     | add dot 3 only  | 2             |
| Whole / 16th note    | add dots 3, 6   | 1             |

### Duration ambiguity

Each note cell is ambiguous between two durations spaced a factor of 16
apart (e.g., whole and 16th notes share the same cell pattern).
The parser resolves this using sequential context rules (see
BrailleParser._resolve_measure_durations).  A formal "value indicator"
cell is mentioned in some BANA literature but does not appear in
real-world music; its dot pattern has not been verified and it is not
currently implemented.

### 16th-note runs

Three or more 16th notes in a group are notated as a run:
the **first** note uses the standard whole/16th-class cell (dots 3+6 added),
while each **subsequent** note in the group uses an 8th-note-class cell
(bare pitch base, no dots 3 or 6).  The parser detects this by:

1. Resolving the whole/16th group first (if count × 4 beats overflows the
   measure → they are 16th notes).
2. Any 8th-note-class cell that directly follows a 16th-note cell is a
   run continuation and is also resolved to a 16th note.
3. A cell from any other duration class ends the run; 8th-class cells
   after that point are genuine 8th notes.

---

## Note Cells — Eighth / 128th (no duration modifier)

| Symbol | Unicode  | Dots      | Note |
|--------|----------|-----------|------|
| ⠙      | U+2819   | 1, 4, 5   | C    |
| ⠑      | U+2811   | 1, 5      | D    |
| ⠋      | U+280B   | 1, 2, 4   | E    |
| ⠛      | U+281B   | 1, 2, 4, 5| F    |
| ⠓      | U+2813   | 1, 2, 5   | G    |
| ⠊      | U+280A   | 2, 4      | A    |
| ⠚      | U+281A   | 2, 4, 5   | B    |

## Note Cells — Quarter / 64th (dot 6 added)

| Symbol | Unicode  | Dots         | Note |
|--------|----------|--------------|------|
| ⠹      | U+2839   | 1, 4, 5, 6   | C    |
| ⠱      | U+2831   | 1, 5, 6      | D    |
| ⠫      | U+282B   | 1, 2, 4, 6   | E    |
| ⠻      | U+283B   | 1, 2, 4, 5, 6| F    |
| ⠳      | U+2833   | 1, 2, 5, 6   | G    |
| ⠪      | U+282A   | 2, 4, 6      | A    |
| ⠺      | U+283A   | 2, 4, 5, 6   | B    |

## Note Cells — Whole / 16th (dots 3 and 6 added)

| Symbol | Unicode  | Dots            | Note |
|--------|----------|-----------------|------|
| ⠽      | U+283D   | 1, 3, 4, 5, 6   | C    |
| ⠵      | U+2835   | 1, 3, 5, 6      | D    |
| ⠯      | U+282F   | 1, 2, 3, 4, 6   | E    |
| ⠿      | U+283F   | 1, 2, 3, 4, 5, 6| F    |
| ⠷      | U+2837   | 1, 2, 3, 5, 6   | G    |
| ⠮      | U+282E   | 2, 3, 4, 6      | A    |
| ⠾      | U+283E   | 2, 3, 4, 5, 6   | B    |

## Note Cells — Half / 32nd (dot 3 added)

| Symbol | Unicode  | Dots         | Note |
|--------|----------|--------------|------|
| ⠝      | U+281D   | 1, 3, 4, 5   | C    |
| ⠕      | U+2815   | 1, 3, 5      | D    |
| ⠏      | U+280F   | 1, 2, 3, 4   | E    |
| ⠟      | U+281F   | 1, 2, 3, 4, 5| F    |
| ⠗      | U+2817   | 1, 2, 3, 5   | G    |
| ⠎      | U+280E   | 2, 3, 4      | A    |
| ⠞      | U+281E   | 2, 3, 4, 5   | B    |

---

## Octave Marks

An octave mark precedes the note it applies to. BANA octaves correspond to
scientific pitch notation (octave 4 = middle C octave).

| Symbol | Unicode | Dots    | Octave | Name               |
|--------|---------|---------|--------|--------------------|
| ⠈⠈    | (two cells) | 4, 4 | 0     | Sub-contra         |
| ⠈      | U+2808  | 4       | 1      | Contra             |
| ⠘      | U+2818  | 4, 5    | 2      | Great              |
| ⠸      | U+2838  | 4, 5, 6 | 3      | Small              |
| ⠐      | U+2810  | 5       | 4      | One-line (middle C)|
| ⠨      | U+2828  | 4, 6    | 5      | Two-line           |
| ⠰      | U+2830  | 5, 6    | 6      | Three-line         |
| ⠠      | U+2820  | 6       | 7      | Four-line          |

Octave 0 (sub-contra) is a two-cell mark (⠈ followed by ⠈) and is handled
specially in the parser.

---

## Rests

Rests use the same duration ambiguity scheme as notes (base_duration 1/2/4).

| Symbol | Unicode | Dots       | Duration group |
|--------|---------|------------|----------------|
| ⠍      | U+280D  | 1, 3, 4    | whole / 16th   |
| ⠥      | U+2825  | 1, 3, 6    | half / 32nd    |
| ⠧      | U+2827  | 1, 2, 3, 6 | quarter / 64th |

---

## Accidentals

Accidentals precede the note they modify.

| Symbol | Unicode | Dots    | Meaning     |
|--------|---------|---------|-------------|
| ⠡      | U+2821  | 1, 6    | Natural     |
| ⠩      | U+2829  | 1, 4, 6 | Sharp       |
| ⠣      | U+2823  | 1, 2, 6 | Flat        |

Double sharp and double flat cells need verification against the full BANA
table before adding to the code.

---

## TODO (later sprints)

- Key signatures (BANA section 7) — Sprint 3
- Time signatures (BANA section 6) — Sprint 3
- Articulations (BANA section 14) — Sprint 4
- Dynamics (BANA section 16) — Sprint 4
- Ornaments (BANA section 15) — Sprint 6
- Chords and in-accord (BANA section 9) — Sprint 5
- Ties and slurs (BANA section 13) — Sprint 4
- Bar lines and repeat signs — Sprint 2
- Value indicator sign (duration disambiguation) — Sprint 2
