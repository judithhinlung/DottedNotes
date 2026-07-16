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
| strophic_song_test.brf | (untitled exercise) | Judith Lung | Solo voice with chords and refrain (BANA Secs. 35/36) | Developer-authored |
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
- `strophic_song_test.brf` is the integration fixture for the BANA Secs.
  35.1/35.7/35.7.2/36 solo-vocal strophic-song format
  (`parse_strophic_song()`, `--category "Strophic Song"`): a single voice
  with lyrics, chord symbols, and melody. Verse 1 ("Fly away oh my
  friend," / "Please go quickly.") is given in full with chords and
  melody in repeating (lyric, chord, melody) groups, followed by a
  refrain ("Go far away, please go far away.") introduced by the literal
  word "REFRAIN" (BANA 35.7.2) with its own chord line. Verse 2
  ("Everyone has gone to sleep," / "Tarry no more.") is a lyrics-only
  overflow block marked by a verse-number literary parenthesis
  (`"<#b">`, BANA 35.7) that reuses verse 1's melody and ends in a bare
  "REFRAIN" line reusing the already-parsed refrain lyrics rather than
  restating them. Paired with `strophic_song_test.ly`
  as its ground truth (tests/test_strophic_integration.py).
- `dichterliebe01.musicxml` is a MusicXML file containing the first song of Schumann's *Dichterliebe*, sourced from the MusicXML example set and used for testing MusicXML import/parsing integration.
