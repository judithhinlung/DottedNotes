\version "2.24.0"

#(set-global-staff-size 16.0)

\paper {
  #(set-paper-size "letter")
  top-margin = 15.0\mm
  bottom-margin = 15.0\mm
  left-margin = 15.0\mm
  right-margin = 15.0\mm
  system-system-spacing = #'((basic-distance . 16.0)
                             (minimum-distance . 12.0)
                             (padding . 4.0)
                             (stretchability . 60))
}

fluteMusic = \relative c'' {
    \time 8/4
    e4\p d4 c4 d4 e4 f4 g4 f4 |
    f4\stopped g4 a4 b4 c4\open b4 a4 g4 |
    f4 e4 d4 g4 f4 e4 d4 c4 |
    c\breve |
}

violinMusic = \relative c' {
    \time 8/4
    c\breve\upbow\p |
    \mark \markup { "gliss" } d4\downbow-.\glissando e4-.\downbow f4-.\downbow g4-.\downbow a4-.\downbow g4-.\downbow f4\upbow e4\upbow-. |
    R\breve |
    c\breve\downbow |
}

pianoRightHandMusic = \relative c' {
    \time 8/4
    <c e g>4~\p <c e g>4 <b d f>4~ <b d f f>4 c4 d4 e4 d4 |
    R\breve |
    <d g b>4~ <c e g>4~ <c e g>4~ <b e g>4 <d g b>4 <c e g>4 <b d f>4~ <a d f>4 |
    c\breve |
}

pianoLeftHandMusic = \relative c' {
    \time 8/4
    <c, e g>\breve~\p\sustainOn |
    <c e g>\breve\sustainOff\sustainOn |
    <d f g b>2~ <d g b>2~\sustainOff\sustainOn <e g b>2 <f a c>2~\sustainOn |
    <c e g c>\breve~\sustainOff |
}


\score {
  <<
  \new Staff \with {
    instrumentName = "Flute"
    shortInstrumentName = "fl"
  } {
    \clef treble
    \set Staff.instrumentName = "Flute"
    \set Staff.midiInstrument = "flute"
    \fluteMusic
  }
  \new Staff \with {
    instrumentName = "Violin"
  } {
    \clef treble
    \set Staff.instrumentName = "Violin"
    \set Staff.midiInstrument = "violin"
    \violinMusic
  }
\new PianoStaff <<
    \new Staff \with {
      instrumentName = "Piano Right Hand"
    } {
      \clef treble
      \set Staff.instrumentName = "Piano Right Hand"
      \set Staff.midiInstrument = "acoustic grand"
      \pianoRightHandMusic
    }
    \new Staff \with {
      instrumentName = "Piano Left Hand"
    } {
      \set Staff.instrumentName = "Piano Left Hand"
      \set Staff.midiInstrument = "acoustic grand"
      \pianoLeftHandMusic
    }
>>
  >>

  \layout { }
  \midi { }
}
