\version "2.24.0"

#(set-global-staff-size 18.0)

\paper {
  #(set-paper-size "letter")
  top-margin = 18.0\mm
  bottom-margin = 18.0\mm
  left-margin = 18.0\mm
  right-margin = 18.0\mm
  system-system-spacing = #'((basic-distance . 14.0)
                             (minimum-distance . 10.0)
                             (padding . 3.0)
                             (stretchability . 60))
}

sopranoMusic = \relative c' {
    \time 3/4
    c4( d4) e4 |
    g4( a4) b4 |
}

pianoMusic = \relative c' {
    \time 3/4
    c4 e4 g4 |
    g4 b4 d4 |
}


\score {
  <<
  \new Staff \with {
    instrumentName = "Soprano"
  } <<
    \new Voice = "vocals_soprano" {
      \clef treble
      \set Staff.instrumentName = "Soprano"
      \sopranoMusic
    }
    \new Lyrics \lyricsto "vocals_soprano" { \set stanza = "1. " Ho -- ly A -- men }
    \new Lyrics \lyricsto "vocals_soprano" { \set stanza = "2. " Glo -- ry A -- men }
  >>
  \new Staff \with {
    instrumentName = "Piano"
  } {
    \clef treble
    \set Staff.instrumentName = "Piano"
    \set Staff.midiInstrument = "acoustic grand"
    \pianoMusic
  }
  >>

  \layout { }
  \midi { }
}
