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
  <<
    \new ChordNames {
      \set chordChanges = ##t
      \chordmode { bes4 bes4 bes4 bes4 bes4 bes4 f4:7 f4:7 f4:7 bes4 bes2 ees8 bes8 bes8 bes8 bes8 bes8 bes8 bes8 bes2 }
    }
    \new Staff <<
      \new Voice = "vocals_right_hand" {
      \relative c' {
      \key bes \major
      \time 3/4
      \clef treble
      bes'4 a4 bes4 |
      bes4 c4 d4 |
      ees4( d4) c4 |
      c4 bes2 \bar "|."
      ees8 d8 c8 bes8 bes8 d8 |
      c8 bes8~ bes2 \bar "|."
      }
      }
      \new Lyrics \lyricsto "vocals_right_hand" { Fly away oh my friend, Ple -- ase go quickly. Go far away, please go far away. }
      \new Lyrics \lyricsto "vocals_right_hand" { \set stanza = "2. " Everyone has gone to sleep, Tar -- ry no more. Go far away, please go far away. }
    >>
  >>
  \layout { }
  \midi { }
}
