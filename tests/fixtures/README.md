# Test Fixtures

This directory holds `.brf` braille music files used as test inputs.

| File | Title | Composer | Instrumentation | Source |
|------|-------|----------|-----------------|--------|
| fengyang_flower_drum.brf | Fengyang Flower Drum (凤阳花鼓) | Traditional Chinese folk song, arr. Judith Lung | Flute and strings | Developer-authored |
| children_s_piece.brf | Children's Piece | Judith Lung | Piano | Developer-authored composition exercise |
| Bartok_Bella_Romanian_Folk_Dances_for_Orchestra.brl | Romanian Folk Dances | Béla Bartók | Orchestra | Auto-transcribed by Sao Mai Braille software |
| Beethoven_Ludwig_Van_String_Quartet_No_1-1.brf | String Quartet No. 1 in F, Movement 1 | Ludwig van Beethoven | String quartet | MusicXML from braillemuse.net, transcribed via their system |
| Faure_Gabriel_Morceau_de_Concours.brf | Morceau de Concours | Gabriel Fauré | Flute and piano | IMSLP (PDF → MusicXML via PlayScore2, transcribed via braillemuse.net) |
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
- `dichterliebe01.musicxml` is a MusicXML file containing the first song of Schumann's *Dichterliebe*, sourced from the MusicXML example set and used for testing MusicXML import/parsing integration.
