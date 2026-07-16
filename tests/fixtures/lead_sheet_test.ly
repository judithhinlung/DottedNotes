\version "2.24.0"

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
  <<
    \new ChordNames {
      \set chordChanges = ##t
      \chordmode { s4 c2:maj7 c4:maj7 c4:maj7 c2:7 c4:7 c4:7 d4:m d4:m d8:m d8:m d8:m d8:m c2.:sus4 c4:sus4 a2:m7 a4:m7 a4:m7 a2:m a4:m a4:m d4/f d4/f d4/f d4/f d2.:dim }
    }
    \new Staff {
    \relative c' {
      \time 4/4
      \partial 4
      \clef treble
      c4 |
      b'2 a4-. g4-. |
      bes2 a4-. g4-. |
      a4 f4 e8( f8) d8( e8) |
      f2. d4 |
      e2 c4-. b4-. |
      a2 b4-. c4-. |
      d4 e4 f4 g4 |
      gis2. \bar "|."
    }
    }
  >>
  \layout { }
  \midi { }
}
