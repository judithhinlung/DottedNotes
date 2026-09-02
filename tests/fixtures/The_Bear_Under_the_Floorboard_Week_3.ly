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
    % 1-26
    R2.*26 |
    % 27
    r2 a'4 |
    % 28
    b2\f a8( g8) |
    % 29
    d2 b'4 |
    % 30
    c2 a8( g8) |
    % 31
    fis4 d4 b'8( c8) |
    % 32
    d4 b4 d4 |
    % 33
    fis4 g4 d4 |
    % 34
    e4.( d8) c8( b8) |
    % 35
    a2 a,4 |
    % 36
    b2\mf a8( g8) |
    % 37
    d2 b'4 |
    % 38
    c2 a8( g8) |
    % 39
    fis4 d4 b'8( c8) |
    % 40
    d4 b4 d4 |
    % 41
    e4 c4 b4 |
    % 42
    a2 b8( c8) |
    % 43
    d2. |
}

pianoLeftHandMusic = \relative c, {
    \key d \major
    \time 3/4
    % 1-25
    R2.*25 |
    % 26
    g'8\p g'8 b8 d8 g8 b8 |
    % 27
    g,,8 g'8 b8 d8 g8 b8 |
    % 28
    g,,8\f g'8 b8 d8 g8 b8 |
    % 29
    b,,8 d8 g8 b8 d8 g8 |
    % 30
    c,,8 e8 g8 c'8 e8 g8 |
    % 31
    d,8 fis8 a8 d8 fis8 a8 |
    % 32
    b,,8 dis8 fis8 b8 d8 fis8 |
    % 33
    c,8 e8 g8 c'8 e8 g8 |
    % 34
    a,,8 a'8 c8 e8 a4 |
    % 35
    d,,,8 d'8 fis8 a8 d4 |
    % 36
    g,,,8\mf g'8 b8 d8 g8 b8 |
    % 37
    b,,8 g'8 b8 d8 g8 b8 |
    % 38
    a,,8 c8 e8 a8 cis8 e8 |
    % 39
    d,8 fis8 a8 d8 fis8 a8 |
    % 40
    b,,8 dis8 fis8 b8 dis8 fis8 |
    % 41
    c,8 e8 g8 c'8 e8 g8 |
    % 42
    d,8 fis8 a8 d8 fis8 a8 |
    % 43
    fis,8 a8 d8 fis8 a8 d8 |
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
    d2.~\p |
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
    d2.~ |
    % 33
    d2.~ |
    % 34
    d2.~ |
    % 35
    d2. |
    % 36
    d,2.~\ppp |
    % 37
    d2. |
    % 38
    e2. |
    % 39
    d2. |
    % 40
    fis2. |
    % 41
    e2. |
    % 42
    d2. |
    % 43
    d2. |
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
    ees2:16->\< d4:16 |
    % 24
    e2:16-> d4:16 |
    % 25
    g2:16->\> fis4:8 |
    % 26-35
    R2.*10 |
    % 36
    b,2.~\ppp |
    % 37
    b2. |
    % 38
    c2. |
    % 39
    a2. |
    % 40
    b2. |
    % 41
    g2. |
    % 42
    g2. |
    % 43
    fis2. |
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
    c,2:16->\< bes4:16 |
    % 24
    aes2:16-> fis4:16 |
    % 25
    g2:16->\> g4:8 |
    % 26-35
    R2.*10 |
    % 36
    g2.~\ppp |
    % 37
    g2. |
    % 38
    e2. |
    % 39
    d'2. |
    % 40
    e2. |
    % 41
    c2. |
    % 42
    a2. |
    % 43
    d2. |
}

violoncelloMusic = \relative c {
    \key d \major
    \time 3/4
    % 1
    d4\p fis4 a4 |
    % 2
    bes8( a8~) a8 fis8-. bes8( a8~) |
    % 3-4
    R2.*2 |
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
    d,8-.\mf fis8-. a8-. d8-. a8-. fis8-. |
    % 13
    f8-. fis8-. a8-. d8-. a8-. fis8-. |
    % 14
    d8-. fis8-. a8-. d8-. a8-. fis8-. |
    % 15
    f4-. fis4-. g4-. |
    % 16
    g4-. bes4-. d4-. |
    % 17
    g8( fis8~) fis4 r4 |
    % 18
    d8 a8 fis8 a8 fis8 d8 |
    % 19
    d8 fis8 a8 d,8 g8 bes8 |
    % 20
    g4-. f4-. ees4-. |
    % 21
    cis4-. d4-. ees4-. |
    % 22
    d4-. d4-. r4 |
    % 23
    c,2:16->\< bes4 |
    % 24
    aes2-> g4 |
    % 25
    g2:16->\> g4:8 |
    % 26-35
    R2.*10 |
    % 36
    d''2.~\ppp |
    % 37
    d2. |
    % 38
    c2. |
    % 39
    d2. |
    % 40
    c2. |
    % 41
    e2. |
    % 42
    d2. |
    % 43
    d2. |
}

doubleBassMusic = \relative c, {
    \key d \major
    \time 3/4
    \mark \markup { "pizz" }
    % 1
    d4\p d'4 a4 |
    % 2
    fis4 a4 d4 |
    % 3
    a4 fis4 a4 |
    % 4
    f4 fis4 g4 |
    % 5
    g4 bes4 d4 |
    % 6
    g8( fis8~) fis4 r4 |
    % 7
    d,4 g8 a4 a8 |
    % 8
    fis4 fis8 g4 bes8 |
    % 9
    g4 a4 bes4 |
    % 10
    bes4 g4 bes4 |
    % 11
    g4 fis4 r4 |
    % 12
    \mark \markup { "arco" } d4-. r4 r4 |
    % 13
    a'4-. r4 r4 |
    % 14
    d4-. r4 r4 |
    % 15
    a4-. r4 r4 |
    % 16
    d,4-. r4 r4 |
    % 17
    a'4-. r4 r4 |
    % 18
    d,4. a'4. |
    % 19
    d,4. g4. |
    % 20
    cis2. |
    % 21
    e2. |
    % 22
    d2 r4 |
    % 23
    cis2.->\< |
    % 24
    aes2.-> |
    % 25
    g2.->\> |
    % 26-35
    R2.*10 |
    % 36
    g'2.~\ppp |
    % 37
    g2. |
    % 38
    a2. |
    % 39
    g2. |
    % 40
    e2. |
    % 41
    a2. |
    % 42
    g2. |
    % 43
    fis2. |
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
      \clef bass
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
