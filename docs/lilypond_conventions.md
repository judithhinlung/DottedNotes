# LilyPond Formatting Conventions

This document is a human-readable reference for the LilyPond output
formatting defaults used by DottedNotes's `LilyPondFormatter`
(`src/dottednotes/renderers/lilypond_formatter.py`), applied by
`Score.to_lilypond()` / `OrchestraScore.to_lilypond()`
(`src/dottednotes/models/score.py`, `orchestra_score.py`). It plays the
same role for the formatting layer that `docs/bana_reference.md` plays for
the braille symbol table: a companion to the code, not a substitute for
reading it, with every default traced back to the evidence that justified
it (Sprint 7b, S7b-1 through S7b-6).

## Source

*Mutopia Project* (mutopiaproject.org), analyzed via its GitHub mirror
archive — see `docs/mutopia_analysis.md` (raw data in
`docs/mutopia_analysis.json`) for the full corpus and methodology.
48 representative `.ly` scores, stratified across four instrumentation
categories (12 each): Solo Piano, Art Song, Chamber, Orchestral.

**Read this alongside `docs/mutopia_analysis.md` for the corpus-wide
statistics** (header field frequency, rehearsal-mark usage, per-category
staff-size mode/median). This document instead traces each *implemented*
default in `LilyPondFormatter.DEFAULTS` to the specific value the code
actually uses — which, category by category, is not the same thing as
the corpus-wide statistic (see "A note on which numbers are actually
cited" below).

---

## Instrumentation categories and their formatting templates (S7b-2, S7b-4)

`LilyPondFormatter.DEFAULTS` holds one `FormattingSettings` per category.
Each category's numbers are derived from a single **anchor piece** —
one high-quality, representative score from the corpus for that category
(`docs/mutopia_analysis.md`'s "Representative Curated Files" section) —
not a corpus-wide statistic.

| Category | Anchor piece | Source path (`source_citation`) |
|----------|-------------|----------------------------------|
| Solo Piano | Beethoven, Piano Sonata No. 20 (Op. 49 No. 2) | `ftp/BeethovenLv/Op49/Sonate-20/Sonate-20.ly` |
| Art Song | Schubert, *An die Musik* (D547) | `ftp/SchubertF/D547/an-die-musik/an-die-musik.ly` |
| Chamber | Mozart, String Quartet No. 14 in G major (KV387) | `ftp/MozartWA/KV387/kv387-1/kv387-1.ly` |
| Orchestral | Mozart, Symphony No. 40 in G minor (KV550) | `ftp/MozartWA/KV550/kv550-1/kv550-1.ly` |

### Per-category settings (`FormattingSettings` fields)

| Category | `staff_size` (pt) | `margin_mm` | `system_system_spacing_basic_distance` | `system_system_spacing_padding` | `short_instrument_names` |
|----------|-------------------:|------------:|----------------------------------------:|----------------------------------:|:-------------------------|
| Solo Piano | 20.0 | 20.0 | 12.0 | 2.0 | `False` |
| Art Song | 18.0 | 18.0 | 14.0 | 3.0 | `False` |
| Chamber | 16.0 | 15.0 | 16.0 | 4.0 | `True` |
| Orchestral | 14.1 | 12.0 | 18.0 | 5.0 | `True` |

Each row is the anchor piece's own settings, read directly from its
LilyPond source (staff size, margins, `\paper{}`/`\layout{}` spacing
where the anchor specified them explicitly; otherwise LilyPond's own
engraving default for that field, as observed in the anchor). The pattern
across the four rows is intentional and matches standard engraving
practice, not a coincidence of the specific anchors chosen: **larger
ensembles get smaller staves, tighter margins, and looser
system-to-system spacing** — more instruments need more staves to fit per
page, so each one must be smaller and packed closer together, while the
literal distance *between systems* (`basic_distance`/`padding`) grows to
keep dense multi-staff systems visually separated from their neighbors.

**`short_instrument_names`**: `False` for Solo Piano and Art Song (a
single instrument, or voice + piano, doesn't need an abbreviated name —
there's no second system to disambiguate against), `True` for Chamber and
Orchestral (repeated systems on later pages conventionally show
abbreviated names — "Vln. I" rather than "Violin I" — once the full name
has appeared on the first system; see `OrchestraScore._staff_with_block`,
which looks up the abbreviation in `TABLE_29_ENGLISH` only when this flag
is set).

### A note on which numbers are actually cited

`docs/mutopia_analysis.md`'s "Spacing and Margins" section reports each
category's staff-size **mode and median** across the corpus (an earlier
version of that table reported an arithmetic mean instead, which produced
numbers — e.g. Chamber "22.2pt" — that weren't the staff size of any
actual score; see that document for why mode/median replaced it). With
mode/median computed properly, **every category's value is 20.0pt** —
LilyPond's own built-in default — because the large majority of scores in
the corpus never override it at all. That's an even stronger reason than
"averages are skewed" not to use the raw corpus as this project's
category defaults: the corpus, honestly summarized, carries essentially
*no* per-category staff-size signal at all. `LilyPondFormatter.DEFAULTS`'s
`staff_size` values above (20.0 / 18.0 / 16.0 / 14.1pt) come from each
category's single curated anchor piece instead (S7b-4) — a score a human
confirmed is well-engraved for that category, which the corpus-wide
statistic, computed any honest way, cannot substitute for. If you're
auditing or changing a default, verify against the anchor piece's own
source file (`source_citation` above), not `docs/mutopia_analysis.md`'s
corpus-wide table.

### Category auto-detection (S7b-3)

`LilyPondFormatter.detect_category()` (no override) classifies a `Score`
using its staves, in this order:

1. No staves → `"Solo Piano"` (fallback).
2. More than 6 staves → `"Orchestral"`.
3. A vocal-family staff (name contains "voice", "vocal", "lyrics",
   "soprano", "alto", "tenor", "bass", or "lied") *and* a keyboard/harp
   staff both present → `"Art Song"`.
4. 3 or more staves (that didn't already match above) → `"Chamber"`.
5. Otherwise (1–2 staves) → `"Solo Piano"`.

These thresholds are a first-pass heuristic (S7b-3's own docstring calls
it out as such), not derived from a specific Mutopia statistic — the
corpus doesn't have a labeled "how many staves is orchestral" number to
cite. They're chosen to match the four template categories' own defining
characteristics (a single piano staff or two; voice-plus-accompaniment;
a handful of chamber parts; a full orchestral system), and are covered by
`tests/test_lilypond_formatter.py`'s `test_formatter_detects_*` tests
rather than by corpus evidence.

**Known gap:** there is currently no real fixture that exercises Art Song
detection (no vocal-staff support exists yet — see ticket S7b-9) or a
real >6-staff fixture that parses successfully for Orchestral detection
(the one candidate, `Bartok_Bella_Romanian_Folk_Dances_for_Orchestra.brl`,
doesn't parse — see `tests/test_ensemble_integration.py`'s documented
xfail). `tests/test_lilypond_formatter.py` and
`tests/test_lilypond_formatter.py`'s S7b-7 integration tests use
`category_override` to exercise Orchestral/Art Song formatting settings
on other, real, working scores instead.

---

## Page layout: `\paper{}` block (S7b-5)

`Score.to_lilypond()`/`OrchestraScore.to_lilypond()` emit, immediately
after `\version`:

```lilypond
#(set-global-staff-size {staff_size})

\paper {
  #(set-paper-size "{paper_size}")
  top-margin = {margin_mm}\mm
  bottom-margin = {margin_mm}\mm
  left-margin = {margin_mm}\mm
  right-margin = {margin_mm}\mm
  system-system-spacing = #'((basic-distance . {basic_distance})
                             (minimum-distance . {basic_distance - 4.0})
                             (padding . {padding})
                             (stretchability . 60))
}
```

- `staff_size`, `margin_mm`, `basic_distance`, `padding` come from the
  category's `FormattingSettings` (table above).
- `paper_size` is an explicit `to_lilypond(paper_size=...)` argument
  (`"letter"` if not passed) — every category uses the same margin value
  regardless of paper size; Mutopia's own scores don't vary margins by
  paper size either, and there was no evidence to derive a paper-size-
  specific margin rule from.
- All four margins (top/bottom/left/right) are set to the same
  `margin_mm` value. The corpus doesn't distinguish top/bottom from
  left/right margins in a way that survived into a citable default, so
  DottedNotes doesn't either.

**Two uncited constants — flagged honestly rather than assigned a false
citation:**
- `minimum-distance = basic_distance - 4.0`: a fixed 4.0pt offset from
  `basic_distance`. This is not a value read off any specific anchor
  piece; it's a reasonable-looking constant that hasn't been verified
  against the corpus. If you're changing `basic_distance` and this ratio
  matters to you, verify it against the anchor piece's own
  `system-system-spacing` setting first.
- `stretchability . 60`: hardcoded the same for all four categories, not
  varied per anchor piece. Same caveat as above.

---

## `\header{}` block (S7b-6)

`Score._header_lines()` (`models/score.py`) emits a `\header {}` block
containing whichever of `title`, `composer`, `copyright`, `tagline` are
set on the `Score` — each field is omitted individually when empty (a
title-only score doesn't get a blank `composer = ""` line), and the whole
block is omitted when none are set. String values are quote/backslash-
escaped (`Score._escape_header_field`) before interpolation.

Field selection is driven by `docs/mutopia_analysis.md`'s header-field
frequency table:

| Field | Corpus frequency | Support |
|-------|------------------:|---------|
| `title` | 22.9% | Implemented (S7-1) |
| `composer` | 22.9% | Implemented (S7-1) |
| `copyright` | 18.8% | Implemented (S7b-6) |
| `tagline` | not separately tracked in the frequency table; included per S7b-6's own scope (Mutopia-style tagline) | Implemented (S7b-6) |

Fields the corpus analysis found but that DottedNotes does **not**
support (`opus`, `instrument`, `style`, `source`, `maintainer`, `piece`,
`poet`, `instrumentHeader`, `mutopiatitle` — each under 15% frequency,
`docs/mutopia_analysis.md`'s table) were judged not worth the
`Score`/CLI surface area for their frequency. Add one only alongside a
`docs/mutopia_analysis.md` frequency high enough to justify it, or an
explicit product need (e.g. `poet` would matter once Art Song/lyrics
support, S7b-9, lands).

---

## Rehearsal marks

`docs/mutopia_analysis.md`'s corpus found 38/48 scores use no rehearsal
marks at all, and the 10 that do use `\mark \default` exclusively (no
explicit letter/number marks). **This is analysis only — DottedNotes does
not currently generate rehearsal marks at all.** Recorded here so the
recommendation (`\mark \default` if/when this is implemented) isn't lost
between the analysis and an eventual implementation ticket.

---

## TODO (later / follow-up work)

- `--format` CLI overrides for these settings (paper size, margins, staff
  size) — ticket S7b-10, not yet implemented.
- Vocal/Art Song real fixture and lyrics support — ticket S7b-9, not yet
  implemented; Art Song's row above is currently exercised only via
  `category_override` in tests, never real detection.
- `minimum-distance`/`stretchability` constants noted above as uncited —
  verify against anchor pieces' own settings if changing
  `basic_distance`/`padding`, rather than assuming the current offset
  scales correctly.
