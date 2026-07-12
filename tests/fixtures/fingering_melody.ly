\version "2.24.4"
pianoRightHand = \relative c' { \clef treble
\key c \major
\time 4/4 \tempo "allegro moderato"
%1
c4-1 d4-2 e4-3 f4-4 |
%2
g2.-5-4 a8-5( g8) |
%3
g4-\markup \center-column { "5" "4" } f4-4 e4-3 d4-2 |
%4
c2-1 c'2-5 \bar "|." |
}

pianoLeftHand = \relative c { \clef bass
\key c \major
\time 4/4
%1
c4-5 g'4-1 d4-4 g4-1 |
%2
c,4-5 e4-3 g4-1 f8-2( e8-3) |
%3
c4-5 d4-4 e4-3 f4-2 |
%4
<c-5 e-3 g-1>1 \bar "|." |
}

\score {
\new PianoStaff \with { instrumentName = "Piano" midiInstrument = "acoustic grand" } <<
\new Staff = "piano right hand" \pianoRightHand
\new Staff = "piano left hand" \pianoLeftHand >>
\layout { }
\midi { } }
