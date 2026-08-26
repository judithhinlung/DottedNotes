\version "2.26.0"

#(set-global-staff-size 14.1)

\paper {
  #(set-paper-size "letter")
  top-margin = 12.0\mm
  bottom-margin = 12.0\mm
  left-margin = 12.0\mm
  right-margin = 12.0\mm
  system-system-spacing = #'((basic-distance . 18.0)
                             (minimum-distance . 14.0)
                             (padding . 5.0)
                             (stretchability . 60))
}

pianoRightHandMusic = \relative c'' {
    \key d \major
    \time 3/4
    \tempo 4 = 100
    % 1-28
    R2.*28 |
    % 29
    r2 a'4
    %30
    b2\f a8( g8) |
    % 31
    d2 b'4 |
    % 32
    c2 a8( g8) |
    % 33
    fis4 d4 b'8( c8) |
    % 34
    d4 b4 d4 |
    % 35
    fis4 g4 d4 |
    % 36
    e4.( d8) c8( b8) |
    % 37
    a2 a,4 |
    % 38
    b2\mf a8( g8) |
    % 39
    d2 b'4 |
    % 40
    c2 a8( g8) |
    % 41
    fis4 d4 b'8( c8) |
    % 42
    d4 b4 d4 |
    % 43
    e4 c4 b4 |
    % 44
    a2 b8( c8) |
    % 45
     d2. \bar "|." |
}

pianoLeftHandMusic = \relative c' {
    \key d \major
    \time 3/4
    % 1-25
    R2.*25 |
    % 26
d4\p a'4 d4 |
    % 27
    d,4 a'2 |
    % 28
    d,4 a'4 d4 |
    % 29
    d,4 a'4 a,4 |
    % 30
    g4\f d'4 g4 |
    %31
    b,4 d4 g4 |
    %32
    a,4 e'4 a4 |
    %33
    d,4 a4 d4 |
    % 34
    b4 fis4 b4 |
    % 35
    c,4 g'4 c4 |
    % 36
    a,4 e'4 a4 |
    % 37
    d,4 a'4 d4 |
    % 38
    g,,4\mf d'4 g4 |
    % 39
    b,4 d4 g4 |
    % 40
    a,4 e4 a4 |
    % 41
    d,,4 a'4 d4 |
    % 42
    b4 fis4 b4 |
    % 43
    c,4 g'4 c4 |
    % 44
    d,4 a'4 d4 |
    % 45
    fis,4 a4 d'4 \bar "|." |
}

violinOneMusic = \relative c'' {
    \key d \major
    \time 3/4
    % 1-22
    R2.*22 |
    % 23
    aes'2:16->\< g4:16 |
    % 24
    bes2:16-> aes4:16 |
    % 25
    cis2:16->\> d4:16 |
    % 26
    d2.~ |
    % 27
    d2.~ |
    % 28
    d2.~ |
    % 29
    d2.~ |
    % 30
    d2.~ |
    % 31
    d2.~ |
    % 32
    d2. |
    % 33
    d2.~ |
    % 34
    d2.~ |
    % 35
    d2.~ |
    % 36
    d2.~ |
    % 37
    d2. |
    % 38
    d,2.\mp~ |
    % 39
    d2. |
    % 40
    e2. |
    % 41
    d2. |
    % 42
    fis2. |
    % 43
    e2. |
    % 44
    d2. |
    % 45
    d2. \bar "|." |
}

violinTwoMusic = \relative c' {
    \key d \major
    \time 3/4
    % 1-11
    R2.*11 |
    % 12
    d4\mf fis4 a4 |
    % 13
    bes8( a8~) a8 fis8-. bes8( a8~) |
    % 14
    a8 fis8-. bes8( a8) r4 |
    % 15
    aes4 a4 bes4 |
    % 16
    bes8( d8~) d8 bes8-. aes8( a8) |
    % 17
    bes8( a8~) a4 r4 |
    % 18
    aes8 a8 bes8 fis8 a8 d,8 |
    % 19
    a'8 bes8 c8 g8 bes8 d,8 |
    % 20
    bes'4 c4 cis4 |
    % 21
    cis8( d8~) d8 cis8-. cis8( d8~) |
    % 22
    d8 cis8-. cis8( d8) r4 |
    % 23
    d2.:16->\< |
    % 24
    d2.:16-. |
    % 25
    g2:16->\> fis4:16 |
    % 26-37
    R2.*12 |
    % 38
    b2.\mp |
    % 39
    b2. |
    % 40
    c2. |
    % 41
    a2. |
    % 42
    b2. |
    % 43
    g2. |
    % 44
    g2. |
    %45
    fis2. \bar "|." |
    }

violaMusic = \relative c' {
    \key d \major
    \time 3/4
    % 1-11
    R2.*11 |
    % 12
    d4\mf fis4 a4 |
    % 13
    bes8( a8~) a8 fis8-. bes8( a8~) |
    % 14
    a8 fis8-. bes8( a8) r4 |
    % 15
    aes4 a4 bes4 |
    % 16
    bes8( d8~) d8 bes8-. aes8( a8) |
    % 17
    bes8( a8~) a4 r4 |
    % 18
    aes8 a8 bes8 fis8 a8 d,8 |
    % 19
    a'8 bes8 c8 g8 bes8 d,8 |
    % 20
    bes'4 c4 cis4 |
    % 21
    cis8( d8~) d8 cis8-. cis8( d8~) |
    % 22
    d8 cis8-. cis8( d8) r4 |
    % 23
    c,2.->\< |
    % 24
    cis2.-> |
    % 25
    d2.->\> |
    % 26-37
    R2.*12 |
    % 38
g,2.\mp |
    % 39
g2. |
    % 40
    e2. |
    % 41
    d'2. | |
    % 42
    e2. |
    % 43
    c2. |
    % 44
    a2. |
    %45
    d2. \bar "|." |
}

violoncelloMusic = \relative c {
    \key d \major
    \time 3/4
    % 1
    d4\p fis4 a4 |
    % 2
    bes8( a8~) a8 fis8-. bes8( a8~) |
%3
a8 fis8-. bes8( a8) r4 |
    % 4
    aes4 a4 bes4 |
    % 5
    bes8( d8~) d8 bes8-. aes8( a8) |
    % 6
    bes8( a8~) a4 r4 |
    % 7
    aes8 a8 bes8 fis8 a8 d,8 |
    % 8 
    a'8 bes8 c8 g8 bes8 d,8 |
    % 9
    bes'4 c4 cis4 |
    % 10
    cis8( d8~) d8 cis8-. cis8( d8~) |
    % 11
    d8 cis8-. cis8( d8) r4 |
    % 12
    d,2.\mf |
    % 13
    ees2. |
    % 14
    d2. |
    % 15
    cis2. |
    % 16
    ees2 d4~ |
    % 17
    d2 r4 |
    % 18
    ees2. |
    % 19
    d2. |
    % 20
    c2. |
    % 21
    ees2. |
    % 22
    c2. |
    % 23
    d2.->\< |
    % 24
    e2.-> |
    % 25
    d2.->\> |
    % 26-37
    R2.*12 |
    % 38
    d2.\mp~ |
    % 39
    d2. |
    % 40
    c2. |
    % 41
    d2. |
    % 42
    c2. |
    % 43
    e2. |
    % 44
    d2. |
    % 45
    d2. \bar "|." |
}

doubleBassMusic = \relative c, {
    \key d \major
    \time 3/4
    \mark \markup { "pizz" }
    % 1
    d2.\p |
    % 2
    d'2.~ |
    % 3
    d4 fis,4 r4 |
    % 4
    d2. |
    % 5
    g2 f4~ |
    % 6
    f4 fis4 r4 |
    % 7
    f4. d4. |
    % 8
    fis4. d4. |
    % 9
    g4 a4 bes4 |
    % 10
    bes4 g4 bes4 |
    % 11
    g4 fis4 r4 |
    % 12
    \mark \markup { "arco" }
    d2.~ |
    % 13
  d2.~ |
    % 14
    d2.~ |
    % 15
    d2.~
    %16
    d2.~
    % 17
    d2 r4 |
    % 18
    fis2.~ |
    % 19
    fis2. |
    % 20
g2.~ |
% 21
g2. |
% 22
fis2 r4 |
% 23
d2.->\< |
% 24
e2.-> |
% 25
d2.->\> |
% 26-37
    
    r2.*12
    % 38
    g2.\mp~ |
    % 39
    g2. |
    % 40
    a2. |
    % 41
    g2. |
    % 42
    e2. |
    % 43
    a2. |
    % 44
    g2. |
    % 45
    fis2. \bar "|." |
    }


\score {
  <<
\new PianoStaff <<
    \new Staff \with {
      instrumentName = "Piano right hand"
      shortInstrumentName = "pr"
    } {
      \clef treble
      \set Staff.instrumentName = "Piano right hand"
      \set Staff.midiInstrument = "acoustic grand"
      \pianoRightHandMusic
    }
    \new Staff \with {
      instrumentName = "Piano left hand"
      shortInstrumentName = "pl"
    } {
      \clef treble
      \set Staff.instrumentName = "Piano left hand"
      \set Staff.midiInstrument = "acoustic grand"
      \pianoLeftHandMusic
    }
>>
\new StaffGroup <<
    \new Staff \with {
      instrumentName = "Violin I"
      shortInstrumentName = "v1"
    } {
      \clef treble
      \set Staff.instrumentName = "Violin I"
      \set Staff.midiInstrument = "violin"
      \violinOneMusic
    }
    \new Staff \with {
      instrumentName = "Violin II"
      shortInstrumentName = "v2"
    } {
      \clef treble
      \set Staff.instrumentName = "Violin II"
      \set Staff.midiInstrument = "violin"
      \violinTwoMusic
    }
    \new Staff \with {
      instrumentName = "Viola"
      shortInstrumentName = "vl"
    } {
      \clef alto
      \set Staff.instrumentName = "Viola"
      \set Staff.midiInstrument = "viola"
      \violaMusic
    }
    \new Staff \with {
      instrumentName = "Violoncello"
      shortInstrumentName = "vc"
    } {
      \clef bass
      \set Staff.instrumentName = "Violoncello"
      \set Staff.midiInstrument = "cello"
      \violoncelloMusic
    }
    \new Staff \with {
      instrumentName = "Double bass"
      shortInstrumentName = "db"
    } {
      \clef bass
      \set Staff.instrumentName = "Double bass"
      \set Staff.midiInstrument = "contrabass"
      \doubleBassMusic
    }
>>
  >>

  \layout { }
  \midi { }
}
