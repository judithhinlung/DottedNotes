# Test Fixtures

This directory holds `.brf` braille music files used as test inputs.

| File | Title | Composer | Instrumentation | Source |
|------|-------|----------|-----------------|--------|
| fengyang_flower_drum.brf | Fengyang Flower Drum (凤阳花鼓) | Traditional Chinese folk song, arr. Judith Lung | Flute and strings | Developer-authored |
| children_s_piece.brf | Children's Piece | Judith Lung | Piano | Developer-authored composition exercise |
| Bartok_Bella_Romanian_Folk_Dances_for_Orchestra.brl | Romanian Folk Dances | Béla Bartók | Orchestra | Auto-transcribed by Sao Mai Braille software |
| Beethoven_Ludwig_Van_String_Quartet_No_1-1.brf | String Quartet No. 1 in F, Movement 1 | Ludwig van Beethoven | String quartet | MusicXML from braillemuse.net, transcribed via their system |
| Faure_Gabriel_Morceau_de_Concours.brf | Morceau de Concours | Gabriel Fauré | Flute and piano | IMSLP (PDF → MusicXML via PlayScore2, transcribed via braillemuse.net) |
| lead_sheet_test.brf | (untitled exercise) | Judith Lung | Melody + chord symbols (BANA Sec. 27 lead sheet) | Developer-authored, S8b-9 |
| instrumental_techniques_test.brf | (untitled exercise) | Judith Lung | Flute, Violin, Piano (2 staves) | Developer-authored, S8b-10 |
| strophic_song_test.brf | (untitled exercise) | Judith Lung | Voice and piano, 2 verses + refrain | Developer-authored, S8b-11 |
| dichterliebe01.musicxml | Dichterliebe, Op. 48, No. 1 (Im wunderschönen Monat Mai) | Robert Schumann | Voice and piano | [MusicXML Example Set](https://www.musicxml.com/music-in-musicxml/example-set/) |

## Notes

- `fengyang_flower_drum.brf` is the primary integration test fixture.
  The developer arranged it and knows the expected LilyPond output exactly.
  It is the most reliable ground-truth test case in the suite.
- `children_s_piece.brf` is a short developer-authored piece useful for testing
  simple single-voice piano notation.
- The Bartók, Beethoven, and Fauré files are orchestral/ensemble scores from
  public-domain editions. The Bartók file was auto-transcribed with Sao Mai
  Braille software; the Beethoven and Fauré files were sourced via IMSLP and
  transcribed via braillemuse.net. They are useful for testing multi-staff
  and multi-voice parsing.
- `lead_sheet_test.brf` is the S8b-9 integration fixture for BANA Sec. 27
  lead sheets (`parse_lead_sheet()`, `--category "Lead Sheet"`): an
  instrumental header (time signature only), a one-beat pickup measure
  (margin-numbered 0) with no chord symbol of its own, and chord symbols
  covering maj7, dominant 7th, minor, sus4, and diminished, each aligned to
  the first cell of the melody note it accompanies. Paired with
  `lead_sheet_test.ly` as its confirmed ground truth
  (tests/test_lead_sheet_integration.py).
- `instrumental_techniques_test.brf` is the S8b-10 integration fixture combining
  the breve (S8b-1), bowing (S8b-2), sustain pedal (S8b-3), chord ties and
  doubled intervals (S8b-4), and glissando/wind mute (S8b-6) features in one
  hand-authored, multi-staff (Flute, Violin, Piano RH/LH) score, so they're
  exercised together and compiled with the real `lilypond` binary rather than
  only in isolated unit tests. Piano-RH measure 3 combines a doubled
  chord-tie carry (BANA Sec. 10.2.2) with an active doubled-interval carry
  (Sec. 10.2.1) at the same time. Paired with `instrumental_techniques_test.ly`
  as its confirmed ground truth (tests/test_sprint8b_integration.py).
- `strophic_song_test.brf` is the S8b-11 integration fixture for strophic/
  multi-verse vocal formats (S8b-8): a Soprano + Piano score with 2 verses
  ("Ho -- ly" / "Glo -- ry") sharing one melody, using the bracketed
  verse-number prefix style (`⠶⠼⠁⠶`/`⠶⠼⠃⠶`), followed by a separate
  unprefixed refrain system ("A -- men") that replicates across both
  verses. The verse melody's first two notes carry a syllabic slur (the
  "Ho --" hyphenation-continuation case, the same convention as
  `vocal_test.brf`'s "flo -- wers"). Paired with `strophic_song_test.ly`
  as its ground truth (tests/test_strophic_integration.py).
- `dichterliebe01.musicxml` is a MusicXML file containing the first song of Schumann's *Dichterliebe*, sourced from the MusicXML example set and used for testing MusicXML import/parsing integration.
