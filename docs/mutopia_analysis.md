# Mutopia Project LilyPond Formatting Analysis

This artifact documents the statistical and structural patterns extracted from public-domain LilyPond scores in the Mutopia Project. These evidence-based defaults are used directly in the `LilyPondFormatter` layout templates (Sprint 7b).

## Terms of Use & Scraper Compliance
Mutopia Project scores are distributed under open Creative Commons and Public Domain licenses. Under their guidelines, bulk downloading is permitted. To prevent server impact, this analysis was performed by calling raw file endpoints on their official GitHub mirror archive with a polite rate-limit (200ms delay between downloads) and using a local cache (`.mutopia_cache/`, gitignored) to avoid redundant requests.

## Corpus Distribution

A total of **48** representative `.ly` scores were analyzed, stratified across the four target instrumentation categories:

| Instrumentation Category | Score Count | Purpose / Mapping |
|-------------------------|-------------|-------------------|
| Solo Piano | 12 | Curates layout defaults for solo piano scores |
| Art Song | 12 | Curates layout defaults for art song scores |
| Chamber | 12 | Curates layout defaults for chamber scores |
| Orchestral | 12 | Curates layout defaults for orchestral scores |
| **Total** | **48** | |

## Header Field Analysis

The following table displays the frequency of variable definitions inside the `\header {}` blocks across the analyzed corpus. This drives our choice of supported headers:

| Header Variable | Frequency | Percentage | Recommended Support |
|-----------------|-----------|------------|---------------------|
| `title` | 11 | 22.9% | Core (Sprint 7) |
| `composer` | 11 | 22.9% | Core (Sprint 7) |
| `copyright` | 9 | 18.8% | Optional |
| `opus` | 6 | 12.5% | Optional |
| `instrument` | 6 | 12.5% | Optional |
| `style` | 5 | 10.4% | Optional |
| `source` | 5 | 10.4% | Optional |
| `maintainer` | 5 | 10.4% | Optional |
| `piece` | 5 | 10.4% | Optional |
| `poet` | 4 | 8.3% | Optional |
| `instrumentHeader` | 4 | 8.3% | Optional |
| `mutopiatitle` | 2 | 4.2% | Optional |

### Header Recommendations
- **Core Fields**: `title` and `composer` must always be supported.
- **Extended Fields**: `copyright`, `mutopiainstrument`, `mutopiapoet`, and `tagline` are highly frequent and should be supported to yield complete scores.
- **Escaping**: Since header values are user-supplied strings, all generated LilyPond strings must escape double quotes (`"` -> `\"`).

## Paper & Page Layout Settings

### Paper Sizes
LilyPond files in Mutopia overwhelmingly use standard paper size variables. Where specified:
- `paper-height` and `paper-width` (frequently used to define standard dimensions or customized layouts)
- In modern LilyPond, paper size is set via `#(set-default-paper-size "letter")` or `"a4"`.

### Spacing and Margins (Average Values)
The analyzed margins and system-system spacing vary significantly by instrumentation category to accommodate different densities of music:

| Category | Average Staff Size (pt) | Default Margin | System Spacing Rule |
|----------|------------------------|----------------|---------------------|
| Solo Piano | 20.0 | 20 mm | Tight (10-12pt baseline) |
| Art Song | 20.0 | 18 mm | Moderate (12-14pt baseline) |
| Chamber | 22.2 | 15 mm | Compact (14-16pt baseline) |
| Orchestral | 21.0 | 12 mm | Very Compact (16-18pt system distance) |

## Rehearsal Mark Styles

Rehearsal marks are formatted in LilyPond with `\mark` or `\mark \default`. Frequencies across the corpus:
- **No marks found**: 38 scores (mostly solo piano and simple songs)
- **Default marks (`\mark \default`)**: 10 occurrences (LilyPond automatically increments numbers/letters)
- **Explicit letter marks (`\mark "A"`)**: 0 occurrences
- **Explicit numeric marks (`\mark "1"`)**: 0 occurrences

### Recommendation
DottedNotes should support standard sequential marks using `\mark \default` (which translates BANA's standard rehearsal numbers/letters to LilyPond's automatic formatter) and preserve explicit text labels if specified.

## Representative Curated Files (For S7b-4 Templates)
The following files are curated as high-quality formatting anchors for the four layout templates:

### 1. Solo Piano Template Anchor
- **Piece**: Beethoven's Sonata No. 20 (Op. 49 No. 2)
- **Path**: `ftp/BeethovenLv/Op49/Sonate-20/Sonate-20.ly`
- **Key features**: Clean 2-staff layout, standard piano brackets, global staff size 20pt, title, composer, opus, and copyright tags.

### 2. Art Song Template Anchor
- **Piece**: Schubert's An die Musik (D547)
- **Path**: `ftp/SchubertF/D547/an-die-musik/an-die-musik.ly`
- **Key features**: Voice + Piano 3-staff layout, lyrics aligned under voice, global staff size 18pt.

### 3. Chamber Template Anchor
- **Piece**: Mozart's String Quartet No. 14 in G major (KV387)
- **Path**: `ftp/MozartWA/KV387/kv387-1/kv387-1.ly`
- **Key features**: 4 staves grouped in a `StaffGroup`, instrument names (Violin I/II, Viola, Cello), staff size 16pt.

### 4. Orchestral Template Anchor
- **Piece**: Mozart's Symphony No. 40 in G minor (KV550)
- **Path**: `ftp/MozartWA/KV550/kv550-1/kv550-1.ly`
- **Key features**: Full multi-family layout (winds, brass, strings), instrument name abbreviations, global staff size 14.1pt for density.

---
## Detailed Analysis List
The full raw parameters are available in [docs/mutopia_analysis.json](file:///Users/Judith/workspace/DottedNotes/docs/mutopia_analysis.json). Below is a summary of the analyzed scores:

| Path | Category | Staff Size | Paper Settings |
|------|----------|------------|----------------|
| [violino-2.ly](https://github.com/MutopiaProject/MutopiaProject/blob/master/ftp/BachJS/BWV1047/brandenburg_2/brandenburg_2-lys/violino-2.ly) | Solo Piano | Default (20 pt) | `Default` |
| [Bass.ly](https://github.com/MutopiaProject/MutopiaProject/blob/master/ftp/BeethovenLv/O55/BeethovenSymphony3/BeethovenSymphony3-lys/Bass.ly) | Orchestral | Default (20 pt) | `Default` |
| [Mvt4_conFuoco.ly](https://github.com/MutopiaProject/MutopiaProject/blob/master/ftp/DvorakA/O95/Sym9/Sym9-lys/Mvt4_conFuoco.ly) | Orchestral | Default (20 pt) | `indent, short-indent, ragged-last-bottom, page-limit-inter-system-space, system-separator-markup` |
| [DvorakSYMPH7M2_musique-Corno_G_III_IV.ly](https://github.com/MutopiaProject/MutopiaProject/blob/master/ftp/DvorakA/O70/DvorakSYMPH7/DvorakSYMPH7-lys/DvorakSYMPH7M2/DvorakSYMPH7M2_musique-Corno_G_III_IV.ly) | Art Song | Default (20 pt) | `Default` |
| [DvorakSYMPH7_part_Oboe_I.ly](https://github.com/MutopiaProject/MutopiaProject/blob/master/ftp/DvorakA/O70/DvorakSYMPH7/DvorakSYMPH7-lys/DvorakSYMPH7_part_Oboe_I.ly) | Chamber | Default (20 pt) | `Default` |
| [Basse_3.ly](https://github.com/MutopiaProject/MutopiaProject/blob/master/ftp/GossecFJ/Gossec-Symphonie-sib/Gossec-Symphonie-sib-lys/Basse_3.ly) | Art Song | Default (20 pt) | `Default` |
| [DvorakSYMPH7M1_musique-Violino_I.ly](https://github.com/MutopiaProject/MutopiaProject/blob/master/ftp/DvorakA/O70/DvorakSYMPH7/DvorakSYMPH7-lys/DvorakSYMPH7M1/DvorakSYMPH7M1_musique-Violino_I.ly) | Orchestral | Default (20 pt) | `Default` |
| [oboeone.ly](https://github.com/MutopiaProject/MutopiaProject/blob/master/ftp/BachJS/BWV1046/Brandenburg1-1/Brandenburg1-1-lys/oboeone.ly) | Solo Piano | Default (20 pt) | `Default` |
| [corni.ly](https://github.com/MutopiaProject/MutopiaProject/blob/master/ftp/BeethovenLv/O92/Symphony7_1/Symphony7_1-lys/corni.ly) | Orchestral | Default (20 pt) | `Default` |
| [clarinetti.ly](https://github.com/MutopiaProject/MutopiaProject/blob/master/ftp/BeethovenLv/O92/Symphony7_2/Symphony7_2-lys/clarinetti.ly) | Orchestral | Default (20 pt) | `Default` |
| [Variables.ly](https://github.com/MutopiaProject/MutopiaProject/blob/master/ftp/DvorakA/O70/DvorakSYMPH7/DvorakSYMPH7-lys/Common/Variables.ly) | Solo Piano | Default (20 pt) | `Default` |
| [header.ly](https://github.com/MutopiaProject/MutopiaProject/blob/master/ftp/MozartWA/KV620/magicflute-00-overture/magicflute-00-overture-lys/header.ly) | Orchestral | Default (20 pt) | `Default` |
| [DvorakSYMPH7M2_Staves.ly](https://github.com/MutopiaProject/MutopiaProject/blob/master/ftp/DvorakA/O70/DvorakSYMPH7/DvorakSYMPH7-lys/DvorakSYMPH7M2/DvorakSYMPH7M2_Staves.ly) | Orchestral | Default (20 pt) | `Default` |
| [DvorakSYMPH7M2_musique-Oboe_G_I_II.ly](https://github.com/MutopiaProject/MutopiaProject/blob/master/ftp/DvorakA/O70/DvorakSYMPH7/DvorakSYMPH7-lys/DvorakSYMPH7M2/DvorakSYMPH7M2_musique-Oboe_G_I_II.ly) | Art Song | Default (20 pt) | `Default` |
| [DvorakSYMPH7M4_musique-Oboe_G_I_II.ly](https://github.com/MutopiaProject/MutopiaProject/blob/master/ftp/DvorakA/O70/DvorakSYMPH7/DvorakSYMPH7-lys/DvorakSYMPH7M4/DvorakSYMPH7M4_musique-Oboe_G_I_II.ly) | Art Song | Default (20 pt) | `Default` |
| [DvorakSYMPH7M1_musique-Timpani.ly](https://github.com/MutopiaProject/MutopiaProject/blob/master/ftp/DvorakA/O70/DvorakSYMPH7/DvorakSYMPH7-lys/DvorakSYMPH7M1/DvorakSYMPH7M1_musique-Timpani.ly) | Orchestral | Default (20 pt) | `Default` |
| [Hautbois1_2.ly](https://github.com/MutopiaProject/MutopiaProject/blob/master/ftp/GossecFJ/Gossec-Symphonie-mib/Gossec-Symphonie-mib-lys/Hautbois1_2.ly) | Solo Piano | Default (20 pt) | `Default` |
| [Basse_1.ly](https://github.com/MutopiaProject/MutopiaProject/blob/master/ftp/GossecFJ/Gossec-Symphonie-mib/Gossec-Symphonie-mib-lys/Basse_1.ly) | Art Song | Default (20 pt) | `Default` |
| [DvorakSYMPH7M4_musique-Oboe_I_II.ly](https://github.com/MutopiaProject/MutopiaProject/blob/master/ftp/DvorakA/O70/DvorakSYMPH7/DvorakSYMPH7-lys/DvorakSYMPH7M4/DvorakSYMPH7M4_musique-Oboe_I_II.ly) | Art Song | Default (20 pt) | `Default` |
| [Properties.ly](https://github.com/MutopiaProject/MutopiaProject/blob/master/ftp/DvorakA/O70/DvorakSYMPH7/DvorakSYMPH7-lys/Common/Properties.ly) | Art Song | Default (20 pt) | `Default` |
| [Basso.ly](https://github.com/MutopiaProject/MutopiaProject/blob/master/ftp/PorporaN/Semiramide_riconosciuta/Semiramide_riconosciuta-lys/Sinfonia-1/Basso.ly) | Orchestral | Default (20 pt) | `Default` |
| [tromba.ly](https://github.com/MutopiaProject/MutopiaProject/blob/master/ftp/BachJS/BWV1047/brandenburg_2/brandenburg_2-lys/tromba.ly) | Orchestral | Default (20 pt) | `Default` |
| [DvorakSYMPH7M1_musique-Flauto_G_I_II.ly](https://github.com/MutopiaProject/MutopiaProject/blob/master/ftp/DvorakA/O70/DvorakSYMPH7/DvorakSYMPH7-lys/DvorakSYMPH7M1/DvorakSYMPH7M1_musique-Flauto_G_I_II.ly) | Art Song | Default (20 pt) | `Default` |
| [beethoven-s5.2-va.ly](https://github.com/MutopiaProject/MutopiaProject/blob/master/ftp/BeethovenLv/O67/Symphony5_2/Symphony5_2-lys/beethoven-s5.2-va.ly) | Orchestral | 21.0 pt | `print-page-number, tagline` |
| [violinoone.ly](https://github.com/MutopiaProject/MutopiaProject/blob/master/ftp/BachJS/BWV1046/Brandenburg1-1/Brandenburg1-1-lys/violinoone.ly) | Solo Piano | Default (20 pt) | `Default` |
| [Violon1_2.ly](https://github.com/MutopiaProject/MutopiaProject/blob/master/ftp/GossecFJ/Gossec-Symphonie-sib/Gossec-Symphonie-sib-lys/Violon1_2.ly) | Art Song | Default (20 pt) | `Default` |
| [DvorakSYMPH7M1_musique-Corno_G_III_IV.ly](https://github.com/MutopiaProject/MutopiaProject/blob/master/ftp/DvorakA/O70/DvorakSYMPH7/DvorakSYMPH7-lys/DvorakSYMPH7M1/DvorakSYMPH7M1_musique-Corno_G_III_IV.ly) | Art Song | Default (20 pt) | `Default` |
| [Version.ly](https://github.com/MutopiaProject/MutopiaProject/blob/master/ftp/DvorakA/O70/DvorakSYMPH7/DvorakSYMPH7-lys/Common/Version.ly) | Solo Piano | Default (20 pt) | `Default` |
| [Symphony25_2.ly](https://github.com/MutopiaProject/MutopiaProject/blob/master/ftp/MozartWA/KV183/Symphony25_2/Symphony25_2-lys/Symphony25_2.ly) | Orchestral | Default (20 pt) | `after-title-space, top-margin, bottom-margin, left-margin, paper-width` |
| [fagotto.ly](https://github.com/MutopiaProject/MutopiaProject/blob/master/ftp/BachJS/BWV1046/Brandenburg1-1/Brandenburg1-1-lys/fagotto.ly) | Solo Piano | Default (20 pt) | `Default` |
| [oboethree.ly](https://github.com/MutopiaProject/MutopiaProject/blob/master/ftp/BachJS/BWV1046/Brandenburg1-1/Brandenburg1-1-lys/oboethree.ly) | Solo Piano | Default (20 pt) | `Default` |
| [Basson1.ly](https://github.com/MutopiaProject/MutopiaProject/blob/master/ftp/MehulEN/Symphonie-1/Symphonie-1-lys/Basson1.ly) | Chamber | 20.0 pt | `top-margin, bottom-margin, before-title-space, after-title-space, oddHeaderMarkup, evenHeaderMarkup, oddFooterMarkup, ragged-last-bottom` |
| [DvorakSYMPH7M4_musique-Flauto_I_II.ly](https://github.com/MutopiaProject/MutopiaProject/blob/master/ftp/DvorakA/O70/DvorakSYMPH7/DvorakSYMPH7-lys/DvorakSYMPH7M4/DvorakSYMPH7M4_musique-Flauto_I_II.ly) | Art Song | Default (20 pt) | `Default` |
| [DvorakSYMPH7M3_musique-Clarinetto_G_I_II.ly](https://github.com/MutopiaProject/MutopiaProject/blob/master/ftp/DvorakA/O70/DvorakSYMPH7/DvorakSYMPH7-lys/DvorakSYMPH7M3/DvorakSYMPH7M3_musique-Clarinetto_G_I_II.ly) | Art Song | Default (20 pt) | `Default` |
| [oboi.ly](https://github.com/MutopiaProject/MutopiaProject/blob/master/ftp/MozartWA/KV620/magicflute-00-overture/magicflute-00-overture-lys/oboi.ly) | Solo Piano | Default (20 pt) | `Default` |
| [cornotwo.ly](https://github.com/MutopiaProject/MutopiaProject/blob/master/ftp/BachJS/BWV1046/Brandenburg1-1/Brandenburg1-1-lys/cornotwo.ly) | Solo Piano | Default (20 pt) | `Default` |
| [DvorakSYMPH7M3_Tempi.ly](https://github.com/MutopiaProject/MutopiaProject/blob/master/ftp/DvorakA/O70/DvorakSYMPH7/DvorakSYMPH7-lys/DvorakSYMPH7M3/DvorakSYMPH7M3_Tempi.ly) | Solo Piano | Default (20 pt) | `Default` |
| [DvorakSYMPH7_part_Fagotto_I.ly](https://github.com/MutopiaProject/MutopiaProject/blob/master/ftp/DvorakA/O70/DvorakSYMPH7/DvorakSYMPH7-lys/DvorakSYMPH7_part_Fagotto_I.ly) | Chamber | Default (20 pt) | `Default` |
| [Hautbois2.ly](https://github.com/MutopiaProject/MutopiaProject/blob/master/ftp/GossecFJ/Gossec-Symphonie-mib/Gossec-Symphonie-mib-lys/Hautbois2.ly) | Chamber | 24.0 pt | `top-margin, bottom-margin, obsolete-before-title-space, obsolete-between-system-padding, oddFooterMarkup, first-page-number, ragged-last-bottom` |
| [Timbales.ly](https://github.com/MutopiaProject/MutopiaProject/blob/master/ftp/MehulEN/Symphonie-1/Symphonie-1-lys/Timbales.ly) | Chamber | 20.0 pt | `top-margin, bottom-margin, before-title-space, after-title-space, oddHeaderMarkup, evenHeaderMarkup, oddFooterMarkup, ragged-last-bottom, first-page-number` |
| ... and 8 more scores | | | |