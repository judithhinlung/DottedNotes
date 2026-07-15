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

## Bar Lines

The regular bar line is a blank braille cell (no dots, U+2800).  All special bar
line types begin with ⠣ (dots 1,2,6 = U+2823), which is also the flat accidental
cell.  The tokenizer uses lookahead to distinguish bar line sequences from a flat
sign preceding a note.

| Symbol | Unicode       | Dots                          | Type                 | LilyPond         |
|--------|---------------|-------------------------------|----------------------|------------------|
| ⠀      | U+2800        | (none)                        | Regular bar line     | (space)          |
| ⠣⠅⠄   | U+2823 U+2805 U+2804 | 1,2,6 + 1,3 + 3        | Double bar (section) | `\bar "||"`      |
| ⠣⠅     | U+2823 U+2805 | 1,2,6 + 1,3                   | Double bar (final)   | `\bar "|."`      |
| ⠣⠶     | U+2823 U+2836 | 1,2,6 + 2,3,5,6               | Forward repeat       | `\bar ".|:"`     |
| ⠣⠆     | U+2823 U+2806 | 1,2,6 + 2,3                   | End repeat           | `\bar ":|."`     |

Note: the 3-cell sequence ⠣⠅⠄ must be checked before ⠣⠅ because the 2-cell
sequence is a prefix of the 3-cell one.

---

## BANA Formatting, Validation & Compression Rules (Sprint 9c)

DottedNotes enforces standard BANA formatting rules via its validation library (`BANAValidator`) and supports variable compression settings during Braille rendering.

### Mandatory Formatting Rules

#### 1. Line Length / Column Limit (MBC 2015 Part I, Section 1)
* **Rule ID**: `S9b-4`
* **Description**: A line of braille music must not exceed the standard column limit (default 40 cells).
* **Citation**: MBC 2015 Part I, Section 1.2.
* **Example**: A line containing 45 cells will trigger a warning, proposing a break location at the last space before the 40th cell.

#### 2. Octave Marks & Register Tracking (MBC 2015 Part I, Section 3)
* **Rule ID**: `S9b-3`
* **Description**: In BANA Music Braille, register/octave markings are kept to a minimum using contextual interval calculation:
  * **The First Note** of any voice, segment, or piece must always have an octave mark.
  * **Intervals Less than a Fourth** (seconds and thirds) are never marked, even if they cross into a neighboring octave.
  * **Intervals Greater than a Fifth** (sixths, sevenths, and larger leaps) are always marked, even if they remain in the same octave.
  * **Intervals of a Fourth or Fifth** are marked only if the register changes (i.e. the two notes are in different octaves).
  * **Reset Points** where register tracking resets and an octave mark is **always required**:
    - The first note of a voice/piece.
    - The first note of every measure (BANA resets octave tracking at every measure
      boundary, not just line starts — this naturally covers double bar lines and every
      other bar-line type too, since they all end a measure).
    - The first note starting a new line of braille music.
    - The first note immediately succeeding any numeric indicator (e.g. measure numbers at line-start or multi-measure rests).
* **Citation**: MBC 2015 Part I, Section 3.1–3.4.

#### 3. Sign Ordering Guidelines (MBC 2015 Appendix A)
* **Rule ID**: `S9b-sign-order`
* **Description**: Pre-note and post-note modifier signs must follow a strict sequential ordering around the note cell (order index 0 to 12):
  1. **Pedal Down** (`⠣⠉` / index 0)
  2. **Slur Bracket Open** (`⠰⠃` / index 1)
  3. **Dynamics** (e.g. `⠜⠋⠄` / index 2)
  4. **Articulations** (e.g. `⠦` / index 3)
  5. **Ornaments** (e.g. `⠘⠗` / index 4)
  6. **Accidentals** (e.g. `⠩` / index 5)
  7. **Octave Marks** (e.g. `⠐` / index 6)
  8. **Note Cell** (index 7)
  9. **Intervals** (e.g. `⠼` / index 8)
  10. **Tremolos** (index 9)
  11. **Fingerings** (e.g. `⠂` / index 10)
  12. **Ties / Slurs** (e.g. `⠉` / index 11)
  13. **Pedal Up** (`⠡⠉` / index 12)
* **Citation**: MBC 2015 Appendix A, Section A.1.

#### 4. Measure Beat-Count Mismatch (MBC 2015 Part I, Section 2)
* **Rule ID**: `S9c-beat-count`
* **Description**: The sum of note, rest, and chord durations within a measure must equal the expected beats defined by the time signature.
* **Citation**: MBC 2015 Part I, Section 2.1.
* **Example**: In 4/4 time, a measure containing only a single half note (2 beats) will trigger a warning: "Measure 1: expected 4.0 beats but counted 2.0."

#### 5. Slur & Tie Matching (MBC 2015 Part I, Section 13)
* **Rule ID**: `S9c-slur-matching`
* **Description**: All opened slurs, ties, and slur brackets must be resolved and closed within the voice. Closed slurs or brackets without a matching open mark are also flagged.
* **Citation**: MBC 2015 Part I, Section 13.1.
* **Example**: A voice that starts a slur on note C4 but ends the staff/voice without a closing slur will trigger a warning.

---

### Optional Shorthands & Conventions

#### 1. Articulation Carry Shorthand (MBC 2015 Part I, Section 14)
* **Rule ID**: `S9b-2`
* **Description**: To save space, runs of 4 or more notes with the same articulation (e.g. staccato `⠦`) should use shorthand carry:
  * **First Note**: Starts carry by doubling the sign (e.g. `⠦⠦`).
  * **Middle Notes**: Articulation is completely omitted.
  * **Last Note**: Written as a plain, single occurrence of the sign (e.g. `⠦`).
* **Citation**: MBC 2015 Part I, Section 14.1.
* **Example**: `⠦⠹⠦⠹⠦⠹⠦⠹` (4 staccato C4s) triggers a warning to use articulation carry shorthand (rendered as `⠦⠦⠹ ⠹ ⠹ ⠦⠹` under minimal/full compression).

#### 2. Redundant / Cautionary Accidental (MBC 2015 Part I, Section 5)
* **Rule ID**: `S9c-redundant-accidental`
* **Description**: Explicit accidentals in braille should not be written if they match the key signature or the active accidental for that pitch class and octave in the current measure.
* **Citation**: MBC 2015 Part I, Section 5.1.
* **Example**: In a piece with a G major key signature (F sharp), writing an explicit sharp accidental `⠩` before an F note is redundant.

#### 3. Measure Repeat Recommendation (MBC 2015 Part I, Section 18)
* **Rule ID**: `S9c-measure-repeat`
* **Description**: Suggest using the measure repeat sign `⠶` (dots 2,3,5,6) when two or more consecutive measures are musically identical.
* **Citation**: MBC 2015 Part I, Section 18.1.
* **Example**: If measure 2 is identical to measure 1, a warning suggests using the measure repeat sign `⠶`.

