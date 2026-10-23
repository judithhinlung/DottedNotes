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
  \new Staff <<
    \new Voice = "vocals_right_hand" {
    \relative c {
      \key a \major
      \time 6/8
      \partial 8
      \clef bass
      a'8 |
      cis8 e8 a8 b8 a8 gis8 |
      gis8 fis8 f8 fis4 e8 |
      fis8 gis8 a8 gis8 a8 b8 |
      fis8 gis8 a8 gis4 \bar "|."
    }
    }
    \new Lyrics \lyricsto "vocals_right_hand" { Hello little song, Sing it loud and long. }
  >>
  \layout { }
  \midi { }
}
