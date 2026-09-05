\version "2.26.0"

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
    \key f \major
    \time 4/4
    f8\f g8 a4 a4 a4 |
    f16 f16 g8 a4 a4 a4 |
    bes8( a8) g4 r2 |
    bes8\p( a8) g4 r2 |
    a8\<( bes8) c2 c4 |
    f,8\>( g8) a4 a4 a4 |
    a8\p bes8 g4 r2 |
    g4 f4~ f2 |
}

pianoRightHandMusic = \relative c' {
    \key f \major
    \time 4/4
    r4 r8 <c' a f>8\f r8 <c a f>8 r8 <c a f>8 |
    r4 r8 <c a f>8\f r8 <c a f>8 r8 <c a f>8 |
    r2 r4 <c g e c>4 |
    r2 r4 <c' g e c>4\p |
    r4 r8 <c, a f>8\< r8 <c a f>8 r8 <c a f>8 |
    r4 r8 <c a f>8\> r8 <c a f>8 r8 <c a f>8 |
    r2 r4 <c g e>4\p |
    <c g e>4 <c a f>2. |
}

pianoLefthandMusic = \relative c {
    \key f \major
    \time 4/4
    r4 f8\f r8 f8 r8 f8 r8 |
    r4 f8\f r8 f8 r8 f8 r8 |
    r4 r8 c8( e8() g8) c4 |
    r4 r8 c,8\p( e8() g8) c4 |
    r4 f,,8\< r8 f8 r8 f8 r8 |
    r4 f8\> r8 f8 r8 f8 r8 |
    r4 r8 c'8\p e8 g8 c4 |
    c4 f,8 f8 a8 c8 f4 |
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
    \new Lyrics \lyricsto "vocals_soprano" { Let me run, run, run, After the sun, sun, sun, Let me, Find hope, Where the flowers bloom, And the leaves are green, Where I will, Find hope. }
  >>
\new PianoStaff <<
    \new Staff \with {
      instrumentName = "Piano Right Hand"
    } {
      \set Staff.instrumentName = "Piano Right Hand"
      \set Staff.midiInstrument = "acoustic grand"
      \pianoRightHandMusic
    }
    \new Staff \with {
      instrumentName = "Piano Left-Hand"
    } {
      \clef bass
      \set Staff.instrumentName = "Piano Left-Hand"
      \set Staff.midiInstrument = "acoustic grand"
      \pianoLefthandMusic
    }
>>
  >>

  \layout { }
  \midi { }
}
