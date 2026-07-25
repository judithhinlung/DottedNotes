\version "2.26.0"

#(set-global-staff-size 20.0)

\paper {
  #(set-paper-size "letter")
  top-margin = 20.0\mm
  bottom-margin = 20.0\mm
  left-margin = 20.0\mm
  right-margin = 20.0\mm
  system-system-spacing = #'((basic-distance . 12.0)
                             (minimum-distance . 8.0)
                             (padding . 2.0)
                             (stretchability . 60))
}

\score {
  \relative c' {
      \mark \markup { "Mystery Melody for Violin" }
      \key e \minor
      \time 6/8
      \clef treble
      \tempo "allegro moderato"
      \set Staff.instrumentName = "Violin I"
      \set Staff.midiInstrument = "violin"

      % 1
      e8 g8 d'8 fis,8 a8 d8 |
      % 2
      g,8 b8 e,8 g4 fis8 |
      % 3
      e8 g8 d'8 fis,8 a8 d8 |
      % 4
      b8 d8 g,8 b4 a8 |
      % 5
      g8 b8 d8 a4 c8 |
      % 6
      b8 c8 e,8 g4 f8 |
      % 7
      e8 g8 d'8 fis,8 a8 d8 |
      % 8
      b8 d8 g,8 b4 a8 |
      % 9
      gis4. b4. \bar "|."
  }
  \layout { }
  \midi { }
}
