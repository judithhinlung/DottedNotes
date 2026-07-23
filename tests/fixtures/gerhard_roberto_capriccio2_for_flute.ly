\version "2.24.4"
% automatically converted by musicxml2ly from tests/fixtures/gerhard_roberto_capriccio2_for_flute.xml
\pointAndClickOff

%% additional definitions required by the score:
fz = #(make-dynamic-script "fz")

\header {
    encodingsoftware =  "PlayScore 2"
    encodingdate =  "2026-07-22"
    }

\layout {
    \context { \Score
        skipBars = ##t
        autoBeaming = ##f
        }
    }
PartPOneVoiceOne =  \relative d''' {
    \clef "treble" \time 4/4 | % 1
    \key c \major r4 \stemDown d2 ( ~ _\f \stemDown d8. [ \stemDown cis16
    ] | % 2
    \stemDown b8 [ _\> \stemDown f8 ~ ] \stemDown f2. ) | % 3
    \grace { \stemUp es16 ( [ \stemUp f16 ] } \stemDown es8 ) [ -\!
    \stemDown c8 ~ ] \stemDown c2. | % 4
    \stemUp bes2. \stemUp as4 | % 5
    \grace { \stemUp fis16 ( [ \stemUp a16 \stemUp e'16 ] } \stemDown g2.
    ) ^- _\p \stemDown a4 ( | % 6
    \grace { \stemUp e,16 [ \stemUp a16 \stemUp fis'16 ] } \stemDown gis2.
    ) ^- \grace { \stemUp e,16 [ \stemUp a16 \stemUp fis'16 ] }
    \stemDown gis4 ^- | % 7
    \stemDown bes,2 ( ~ _. \times 2/3 {
        \stemDown bes8 [ \stemDown bes'8 ) ^. \stemDown c,8 ^. ] }
    \times 2/3  {
        \stemDown es8 -1 ( [ \stemDown f8 ) \stemDown b8 ^. ] }
    | % 8
    \stemDown cis,4 ^\trill \times 2/3 {
        \stemDown cis8 ^. [ \stemDown b8 ^. \stemDown f'8 ^. ] }
    \stemUp es,4 ^\trill \times 2/3 {
        \stemUp es8 _. [ \stemUp c8 _. \stemUp bes'8 _. ] }
    | % 9
    \stemUp as4. :64 _\< \stemUp as16. [ s32 r8 \stemUp as8 :16 ] -\!
    _\< \stemUp as16 ( r16 \stemDown ges'8 ^. -\! | \barNumberCheck #10
    des'1 ) ~ ^\trill -\markup { \flat } _\fz | % 11
    \times 2/3  {
        \stemDown des8 ^. [ \stemDown b8 ^. \stemDown a8 ^. ] }
    \times 2/3  {
        \stemDown fis8 ( [ \stemDown e'8 ) ^. \stemDown bes,8 ( ] }
    \times 2/3  {
        \stemDown as'8 ) ^. [ \stemDown g,8 ( \stemDown c'8 ) ^. ] }
    \times 2/3  {
        \stemDown es,8 ( [ \stemDown f,8 ) \stemDown b'8 ^. ] }
    | % 12
    \stemDown cis,2. ^- _\> r4 | % 13
    \times 2/3  {
        \stemDown bes8 ( [ -\! \stemDown as'8 ) ( ^. \stemDown g,8 ] }
    \times 2/3  {
        \stemDown c'8 ) ^. [ \stemDown es,8 ( \stemDown f,8 ) ( ^. ] }
    \stemDown b'2 ^- | % 14
    r4 \times 2/3 {
        \stemDown as,8 ) ^. [ _\p \stemDown g8 ( \stemDown c'8 ) ^. ] }
    \times 2/3  {
        \stemDown es,8 ( [ \stemDown f,8 ) \stemDown b'8 ^. ] }
    \stemDown cis,4 ~ ^- | % 15
    \stemDown cis4 r4 \times 2/3 {
        \stemDown es8 ( [ \stemDown f,8 ) ^. \stemDown b'8 ^. ] }
    \stemDown cis,4 ~ ^- | % 16
    \stemDown cis4 r4 \times 2/3 {
        \stemUp cis8 [ \stemUp d,8 ( \stemUp f8 ) ] }
    \times 2/3  {
        \stemDown c''8 ( \stemDown es,4 ~ }
    | % 17
    \stemDown es4 ) r4 \times 2/3 {
        \stemDown es8 -1 ( [ _\pp \stemDown f,8 \stemDown b'8 ) ^. ] }
    \times 2/3  {
        \stemUp cis,8 _! [ \stemUp d,8 ( \stemUp f8 ) _. ] }
    | % 18
    \times 2/3  {
        \stemDown c''8 ( \stemDown es,4 ~ }
    \times 2/3  {
        \stemDown es4 ) r8 _\mf }
    \stemUp d,8 -3 ( [ \stemUp f8 ] \times 2/3 {
        \stemDown c'8 [ \stemDown es8 \stemDown cis'8 ) ] }
    | % 19
    b1 _\f | \barNumberCheck #20
    \grace { \stemUp a16 ( [ \stemUp b16 ] } \stemDown a8 ) [ \stemDown
    fis8 ~ ] \stemDown fis2. | % 21
    \grace { \stemUp e16 ( [ \stemUp fis16 ] } \stemDown e8 ) [
    \stemDown bes8 ~ ] \stemDown bes4 \grace { \stemUp as16 ( [ \stemUp
        bes16 ] } \stemUp as8 [ _\p \stemUp g8 ) ] r4 ^\fermata | % 22
    r8 \stemDown g'8 ( \stemUp as,8 [ \stemUp bes8 ) _. ] \times 2/3 {
        \stemUp as16 ( [ \stemUp bes16 -3 \stemUp as16 }
    \stemUp bes8 ) ] r4 | % 23
    r8 \stemDown g'8 ( \stemUp as,8 [ \stemUp bes8 ) _. ] \times 2/3 {
        \stemUp e,16 ( [ \stemUp fis16 \stemUp e16 }
    \stemUp fis8 ) _. ] r4 | % 24
    r8 \stemDown g'8 ( \stemUp as,8 [ \stemUp bes8 ] \stemUp e,8 ) _.
    \stemDown fis'8 ( [ \stemDown a,8 \stemDown b8 ] | % 25
    \stemUp cis,8 ) _. \stemDown es''8 ( [ _\f \stemDown c8 \stemDown f,8
    ] \stemDown d8 [ \stemDown g8 ] \stemDown e8 ) r8 | % 26
    r8 \stemDown g8 ( _\p \stemDown e8 [ \stemDown a,8 ) ] \times 2/3 {
        \stemUp fis16 ( [ \stemUp gis16 -3 \stemUp fis16 }
    \stemUp gis8 ) ] r4 | % 27
    r8 \stemDown a''8 ( _\fz \stemDown fis,8 [ \stemDown gis8 ) ^. ]
    \times 2/3 {
        \stemDown bes,16 ( [ \stemDown c16 \stemDown bes16 }
    \stemDown c8 ) ] r4 | % 28
    r8 \stemDown c'8 ( \stemDown es,8 ) [ \stemDown f8 ] \stemDown b,8
    ^. \stemDown cis'8 ( [ \stemDown d,8 \stemDown g8 ] | % 29
    \stemUp as,8 ) _. \stemDown bes'8 ( [ \stemDown e,8 \stemDown fis8 )
    ^. ] \stemDown a,8 ( [ _\> \stemDown b8 \stemDown cis8 \stemDown dis8
    ] -\! | \barNumberCheck #30
    \stemDown c8 ) _\p r8 \stemDown f'4 -1 _\fz \stemDown d2 ~ ^\trill | % 31
    \stemDown d4 ~ \stemDown d16 [ r16 r16 \stemDown cis16 ] \times 2/3
    {
        \stemDown b8 ( [ \stemDown f8 ) \stemDown es8 ] }
    \times 2/3  {
        \stemDown c8 ( [ \stemDown bes8 ) \stemDown as8 ^! ] }
    | % 32
    \stemDown fis16 ( [ \stemDown a16 \stemDown e'16 \stemDown g16 ]
    \stemDown as4 \stemDown as'4. \stemDown g8 | % 33
    \stemDown f8 [ \stemDown b,8 \stemDown a8 \stemDown fis8 ] \stemDown
    e8 \stemDown d4 \stemDown c8 | % 34
    es,1 ) ( | % 35
    \acciaccatura { \stemUp d8 ) ( } \stemDown bes'8 ) ( [ _\p \stemDown
    des'8 ~ ] \stemDown des2. ) | % 36
    \time 2/2  r8 _\pp \stemDown as8 ^. _\p \grace { \stemUp f16 ( [
        \stemUp as16 ] } \stemDown g8 ) ^. [ \stemDown f8 ^. ] \stemDown
    as8 ( _- [ \stemDown g8 ) ^. ] \stemDown b8 ^. [ \stemDown a8 ^. ] | % 37
    \stemDown fis8 ^. [ \stemDown e8 ^. ] \grace { \stemUp d16 ( [
        \stemUp e16 ] } \stemDown d8 ) ^. [ \stemDown c8 ^. ] \stemDown
    e8 ( [ \stemDown dis8 ) ^. ] r4 | % 38
    r8 \stemDown e8 \grace { \stemUp d8 ( [ \stemUp e8 ] } \stemDown d8
    ) ^. [ \stemDown c8 ^. ] \stemDown e8 ( [ \stemDown dis8 ) ^. ] _\<
    \stemDown ais8 ^. [ \stemDown cis8 ^. ] -\! | % 39
    \stemDown d'2 ^- _\mf _\> r8 \acciaccatura { \stemUp d,8 } \stemDown
    e8 ^. [ -\! \stemDown cis8 ^. \stemDown e8 ^. ] | \barNumberCheck
    #40
    \stemDown bes'8 ( [ \stemDown c,8 ) ^. ] \stemDown es8 ^. [
    \stemDown f,8 ( ^. ] \times 2/3 {
        \stemUp g16 [ \stemUp a16 \stemUp g16 ) }
    \stemUp fis8 ~ ] \stemUp fis8 r8 | % 41
    r8 \stemUp f8 _. \times 2/3 {
        \stemUp g16 ( [ \stemUp a16 \stemUp g16 }
    \stemUp fis8 ) _. ] \stemUp b8 _. [ \stemUp gis8 _. ] \stemUp cis,8
    _. [ \stemUp bes'8 _. ] | % 42
    \stemDown es8 ^. [ \stemDown c8 ^. ] \times 2/3 {
        \stemDown d16 ( [ \stemDown es16 \stemDown d16 }
    \stemDown c8 ) ] \stemDown d8 ( [ _\< \stemDown e8 ~ ^- ] \stemDown
    e4 ) \bar "|."
    r8 \acciaccatura { \stemUp fis,8 ( } \stemDown c'8 ) ^. _\fz -\! s2.
    | % 44
    \stemDown fis'4 ( \stemDown e4 \stemDown d4 ^\ff \stemDown c4 )
    \repeat volta 2 {
        | % 45
        r8 \times 2/3 {
            \stemDown a16 ( [ \stemDown b16 \stemDown a16 }
        \stemDown f8 ~ ] \stemDown f8 ) [ \times 2/3 {
            \acciaccatura { \stemUp f,8*3/2 ( } \stemDown g8 ) ( ^. ]
            \stemUp as4 ) _- }
        \stemUp b4 _- | % 46
        \stemDown fis'4 ( \stemDown g4 ) \stemDown f4 \stemDown es4 | % 47
        \stemDown c2 ( r8 \acciaccatura { \stemUp bes8 ) } \stemDown c8
        ^. \stemDown e8 ^. [ \stemDown d8 ] _\> | % 48
        \stemDown c8 ( [ \stemDown d8 ~ ] \stemDown d4 ~ \stemUp d8 ) _.
        [ _\p -\! \stemUp c8 _. \stemUp bes8 _. \stemUp e,8 _. ] | % 49
        \times 2/3  {
            \stemUp d16 ( [ \stemUp e16 \stemUp d16 }
        \stemUp cis8 ~ ] \stemUp cis2 ) ( \times 2/3 {
            r8 \stemUp e8 -3 _. [ \stemUp g8 ) _. ] }
        | \barNumberCheck #50
        \times 2/3  {
            \stemUp c8 ( [ \stemUp bes8 ) \stemUp d,8 _. ] }
        \times 2/3  {
            \stemUp f8 _. [ \stemUp gis8 _. \stemUp b8 _. ] }
        \times 2/3  {
            \stemUp dis8 ( [ \stemUp cis8 ) \stemUp fis,8 _. ] }
        \times 2/3  {
            \stemDown a8 ^. [ \stemDown c8 ^. \stemDown es8 ^. ] }
        | % 51
        \stemDown as8 ( [ \stemDown ges8 ) \stemDown b,8 ^. ] \stemDown
        cis8 ^. [ \stemDown e8 ^. s4. | % 52
        \stemDown g8 ^. ] \stemDown b8 ( [ \stemDown a8 ) \stemDown d,8
        ^. ] \stemDown f8 ^. [ \stemDown c'8 ^. \stemDown es8 ^. ]
        \stemDown as8 ^- _\fz | % 53
        \time 4/4  \stemDown e8 ( [ \stemDown g,8 ~ ] \stemDown g4 ~
        \times 2/3 {
            \stemDown g8 ) [ \stemDown d8 ^. \stemDown f8 ^. ] }
        \times 2/3  {
            \stemDown bes8 ( [ \stemDown cis8 ) ( \stemDown b8 _- ] }
        | % 54
        \stemDown a8 [ \stemDown bes,8 ~ ] \times 2/3 {
            \stemDown bes8 ) [ \stemDown g'8 ^. \stemDown e8 ^. ] }
        \stemUp des8 ( [ \stemUp es,8 ~ ] \times 2/3 {
            \stemUp es8 ) [ \stemUp d'8 _. \stemUp a8 _. ] }
        | % 55
        \times 4/5  {
            \stemDown as16 ( [ \stemDown g16 \stemDown bes16 \stemDown
            f'16 \stemDown c'16 ] }
        \stemDown b2. ~ ^\trill | % 56
        \stemDown b8 ) _. [ \acciaccatura { \stemUp g8 ( } \stemDown as8
        ) ^. \stemDown as8 ^. \stemDown as8 ^. ] \stemDown as8 ^. [ _\>
        \stemDown as8 ^. \stemDown as8 ^. \acciaccatura { \stemUp g8 ( }
        \stemDown as8 ) ^. ] | % 57
        \stemDown as2 r2 | % 58
        \acciaccatura { \stemUp d,,8 ( } \stemDown cis'2. ) ( -\!
        \stemDown b4 ) ( _\pp | % 59
        \stemDown cis2. ) ( _\< \stemDown f4 _\mf -\! _\> |
        \barNumberCheck #60
        \stemDown es2 ) r4 r16 \stemUp c,16 ( [ -\! \stemUp es16 \stemUp
        d16 ) ] | % 61
        cis'1 ~ _\> | % 62
        \stemDown cis4 -\! r4 r2 | % 63
        \acciaccatura { \stemUp d,8 ( } \stemDown cis'2. ) ( \stemDown b4
        ) ( | % 64
        \stemDown cis2. ) ^- \acciaccatura { \stemUp f,8 ( } \stemDown
        es'4 ) ^- | % 65
        \grace { \stemUp d,32 ( } cis'1 ) ( | % 66
        \stemDown c2 ~ _\> \stemDown c8 ) -\! r8 r4 | % 67
        \times 2/3  {
            r8 _\pp \stemDown g'8 ( [ \stemDown as8 ] }
        \times 2/3  {
            \stemDown g8 [ \stemDown as'8 \stemDown g,8 ] }
        \times 2/3  {
            \stemDown bes8 [ \stemDown g8 \stemDown as'8 ] }
        \times 2/3  {
            \stemDown g,8 [ \stemDown bes8 \stemDown g8 ] }
        | % 68
        \times 2/3  {
            \stemDown as'8 \stemDown g,4 ~ }
        \times 2/3  {
            \stemDown g4 ) ( r8 }
        \stemDown g8 [ \stemDown as8 ) ] \times 2/3 {
            \stemDown g8 [ \stemDown bes8 \stemDown e8 ] }
        | % 69
        \stemDown fis,2 \times 2/3 {
            r8 \stemDown a8 -3 ( [ \stemDown bes8 ] }
        \times 2/3  {
            \stemDown g8 [ \stemDown as8 \stemDown g'8 ) ^. ] }
        | \barNumberCheck #70
        \stemDown e,2 ( ~ \times 2/3 {
            \stemDown e8 [ \stemDown fis8 \ottava #1 \stemDown a'8 ] }
        \times 2/3  {
            \stemDown c,8 [ \stemDown es8 \stemDown f8 ) ^. ] }
        \ottava #0 | % 71
        \times 2/3  {
            \stemDown es,8 ( [ \stemDown f8 \stemDown b8 ] }
        \times 2/3  {
            \stemDown cis8 ) ^. [ \stemDown d,8 ( \stemDown es8 ] }
        \times 2/3  {
            \stemDown f8 ) ^. [ \stemDown cis8 ( \stemDown d8 ] }
        \times 2/3  {
            \stemDown cis8 [ \stemDown d8 \stemDown es8 ) ^. ] }
        | % 72
        \stemUp d,16 ( [ \stemUp es16 \stemUp cis'16 \stemUp d16 ]
        \stemDown es16 [ \stemDown cis'16 ) ^. ] \stemUp es,,16 ( [
        \stemUp cis'16 ] \stemDown d16 [ \stemDown es16 ) ^. ] \stemDown
        cis16 ( [ \stemDown d16 ] \stemDown es16 [ \stemDown d16
        \stemDown es16 ) ^. ] r16 | % 73
        \time 3/4  r4 r8 \stemUp c,16 ( [ _\mf _\< \stemUp es16 ] \times
        4/5 {
            \stemUp f16 [ \stemUp b16 \stemUp cis16 \stemUp d16 ) -\!
            \stemUp d16 ( ] }
        | % 74
        \stemDown d'2 ~ _\f \stemDown d16 [ \stemDown b16 \stemDown cis8
        ~ ] | % 75
        \stemDown cis2*3/2 ~ | % 76
        \stemDown cis16 [ \stemDown b16 \stemDown dis8 ~ ] \stemDown dis4..
        \stemDown b16 ) | % 77
        \stemDown c4. \stemDown f4. ~ | % 78
        \stemDown f2 _\> _\! r4 | % 79
        \times 2/3  {
            r8 _\p \stemDown d,8 ( [ \stemDown f8 ] }
        \times 2/3  {
            \stemDown c8 [ \stemDown es8 \stemDown cis'8 ] }
        \stemDown b4 ~ | \barNumberCheck #80
        \stemDown b8 [ \stemDown g8 ] \stemDown as8 [ \stemDown bes8 ~ ]
        \stemDown bes4 ~ | % 81
        \times 2/3  {
            \stemDown bes8 ) ( [ \stemDown e,8 \stemDown fis8 ] }
        \stemDown a2 ~ | % 82
        \stemDown a8 ) r8 r4 r4 | % 83
        \times 2/3  {
            r8 \stemDown a8 ( [ \stemDown fis8 ] }
        \times 2/3  {
            \stemDown e8 [ \stemDown a8 \stemDown fis8 ] }
        \stemDown bes8 [ \stemDown a8 ~ ] | % 84
        \stemDown a2. ) ( | % 85
        \times 2/3  {
            r8 \stemDown e8 -3 [ \stemDown fis8 ) ] }
        \times 2/3  {
            \stemDown a8 [ \stemDown bes8 \stemDown as8 ] }
        \stemDown g4 ~ | % 86
        \stemDown g4 \stemDown d8 ^- [ \stemDown f8 ~ ] \stemDown f4 ~ | % 87
        \stemDown f8 ( r8 \times 2/3 {
            r8 \stemUp c,8 -3 _. [ \stemUp es8 ) _. ] }
        \times 2/3  {
            \stemUp cis'8 ( [ \stemUp b8 \stemUp a8 ) ] }
        | % 88
        \stemUp fis8. ( [ \stemUp bes16 ) ] \stemDown as16 ( [ \stemDown
        g'16 ) ^. \stemDown e8 ( ~ ] \stemDown e16 [ \stemDown a16
        \stemDown fis16 \stemDown as,16 ] | % 89
        \stemDown bes8. [ \stemDown c'16 ) ^. ] \stemDown e,16 [
        \stemDown f,16 ^. \stemDown b8 ( ~ ] \stemDown b16 _. [
        \stemDown cis'16 ) ^. \stemDown d,16 ^. \stemDown b16 ^. ] |
        \barNumberCheck #90
        \stemDown cis16 [ \stemDown c'16 \stemDown es,16 ^. \stemDown c16
        ^. ] \stemUp f,32 ( [ \stemUp d32 \stemUp es32 \stemUp f32
        \stemUp b32 \stemUp cis32 \stemUp e32 \stemUp fis32 ) ]
        \stemDown fis'4 ~ | % 91
        \stemDown fis2 \acciaccatura { \stemUp b,,8 ( } \stemDown gis'4
        ) ^- | % 92
        \time 2/2  \stemDown e'4 ^- \acciaccatura { \stemUp cis,8 ( }
        \stemDown g'4 ) ^- \acciaccatura { \stemUp c,8 ( } \stemDown es'4
        ) ( ^- s4 | % 93
        \acciaccatura { \stemUp a,,8 } \stemDown f'4 ) ^- \acciaccatura
        { \stemUp d,8 } \stemDown b''4 ~ ^- \stemDown b8 [ \stemDown e,16
        -3 ^. \stemDown e16 ^. \stemDown cis16 ^. \stemDown cis16 ^. ]
        s8 | % 94
        \grace { \stemUp e,8 [ \stemUp g8 ] } \stemUp f4 \stemDown g''16
        ^. [ \stemDown g16 ^. \stemDown bes,16 ^. \stemDown bes16 ^.
        \stemDown c,16 ^. \stemDown c16 ^. ] \stemDown fis8 ( ^. \stemUp
        gis,4 ) _- | % 95
        \times 2/3  {
            \stemDown a'16 ^. [ \stemDown a16 ^. \stemDown d,16 ^. }
        \times 2/3  {
            \stemDown d16 ^. \stemDown es,16 ^. \stemDown es16 ^. ] }
        \stemDown f'8 ^. \stemDown b,4 ( ^- \stemDown cis8 ) \stemUp e,4
        _- | % 96
        \acciaccatura { \stemUp f8 ( } es2.*4/3 ) ~ ^\trill | % 97
        \stemUp es16 [ \stemUp cis16 ( \stemUp e16 \stemUp b'16 ]
        \stemDown d16 [ \stemDown a'16 \stemDown c16 ) \stemDown a,16 (
        ] \stemDown c16 [ \stemDown g'16 \stemDown bes16 \stemDown gis'16
        ] s4 | % 98
        \stemDown fis4.. :32 _\< s32. \stemDown fis16 ) -\! r16
        \stemDown d8 :16 ^. [ \stemDown es8 :16 ^. ] \stemDown f,8 :16
        ^. s64 | % 99
        \stemDown e'8 :16 ^. [ \stemDown fis,8 :16 ^. \stemDown gis8 :16
        ^. ] \stemDown ais,8 ^. [ \stemDown g'8 :16 ^. \stemDown a8 :16
        ^. ] \times 2/3 {
            \stemDown c8 :16 ^. [ \stemDown e,8 :16 ^. \stemDown g8 :16
            ^. ] }
        | \barNumberCheck #100
        \stemDown a,8 ^. [ \stemDown fis'8 :16 ^. \stemDown gis8 :16 ^.
        ] \stemDown bes,8 :16 ^_ [ \stemDown c8 :16 ^. \stemDown es8 ^.
        ] \times 2/3 {
            \stemUp f,8 _. [ \stemUp b8 :16 _. \stemUp cis8 :16 _. ] }
        \bar "|."
        \time 4/4  \stemUp d,2. ( ~ ^\trill _\> \times 4/7 {
            \stemDown d16 [ -\! \stemDown es16 \stemDown f16 \stemDown b16
            \stemDown cis16 \stemDown e16 \stemDown a16 ] }
        | % 102
        \stemDown c2 ~ _\p \times 2/3 {
            \stemDown c8. ) [ \stemDown d,,16 \stemDown b'16 \stemDown
            g'16 ] }
        \stemDown bes4 ( | % 103
        \stemDown as2 ~ ^- \times 2/3 {
            \stemDown as8. ) [ \stemDown d,,16 \stemDown b'16 (
            \stemDown e16 ] }
        \times 2/3  {
            \stemDown fis8. ) ^- [ \stemDown e,16 \stemDown c'16 (
            \stemDown d16 ] }
        | % 104
        \stemDown f2 ~ ^- \times 2/3 {
            \stemDown f8. ) [ _\p \stemDown g,16 \stemDown bes16 (
            \stemDown cis16 ] }
        \times 2/3  {
            \stemUp fis,8. [ \stemUp g16 \stemUp bes16 \stemUp cis16 ] }
        | % 105
        \stemUp as2 ~ \stemUp as8. ) [ \stemUp g16 ( \stemUp bes16
        \stemUp c16 ] \stemUp fis,8 | % 106
        \stemUp a2 \stemUp b2 ) \bar "|."
        r2 \times 2/3 {
            r8 \stemUp g8 ( [ _\p \stemUp fis8 ] }
        \times 2/3  {
            \stemDown e'8 [ \stemDown bes'8 \stemDown as8 ] }
        | % 108
        \stemDown f2. ) ^. _\< \stemDown es4 ( | % 109
        \stemDown f'2 _\f -\! \stemDown es8 \stemDown des4 \stemDown ces8
        | \barNumberCheck #110
        \stemDown d2 ~ _\> \stemDown d8 [ \stemDown a,8 ] \stemDown c'4
        ~ -\! | % 111
        \stemDown c8 ) ( r8 r4 \times 2/3 {
            r8 \stemUp d,,8 _. [ _\p \stemUp a'8 ) _. ] }
        \times 2/3  {
            \stemUp c8 ( [ \stemUp des8 ) \stemUp es,8 ( ] }
        | % 112
        \stemDown a8 [ \stemDown b8 \stemDown d8 ] s8*5 | % 113
        \stemDown e4 ) ^. \stemDown e8 ^. [ \stemDown e8 ~ ] \stemDown e4*2
        ~ | % 114
        \stemDown e8 ( r8 r4 \times 2/3 {
            r8 \stemUp es,8 [ \stemUp a8 ) ] }
        \times 2/3  {
            \stemDown b8 [ \stemDown d8 \stemDown e8 ] }
        | % 115
        \stemUp fis,8 _. [ \stemUp fis8 _. ] \stemUp fis8 _. [ \stemUp
        fis8 ~ _- ] \stemUp fis2 _\> | % 116
        r8 \stemDown as''8 ^. [ _\fz -\! \times 2/3 {
            \stemDown f8 ^. ] \stemDown bes,4 ~ ^- }
        \times 2/3  {
            \stemDown bes8 [ \stemDown g8 ^. \stemDown c,8 ^. ] }
        \times 2/3  {
            \stemUp a8 ( [ \stemUp d,8 ) _. \stemUp b'8 _. ] }
        | % 117
        \stemDown cis8 ^. [ _\> \stemDown cis8 ^. ] \stemDown cis8 ^. [
        \stemDown cis8 ~ ] _\p -\! \stemDown cis8 [ \grace { \stemUp d,32
            ( } \stemDown dis'8 ) ] \stemDown dis8 ^. [ \stemDown dis8
        ^. ] | % 118
        \stemDown g,32 ( [ _\f \stemDown bes32 \stemDown f'32 \stemDown
        as32 \stemDown ges8 ~ ] \stemDown ges4 ~ \stemDown ges8 ) [
        \acciaccatura { \stemUp ges8 ( } \stemDown e'8 ) ~ ^- ]
        \stemDown e4 _\> | % 119
        \stemDown f,,32 ( [ -\! \stemDown as32 \stemDown d32 \stemDown
        fis32 \stemDown e8 ~ ] \stemDown e4 ~ \stemDown e8 ) [ \stemDown
        dis'8 ~ ] _\> \stemDown dis4 | \barNumberCheck #120
        \stemDown d,,32 [ -\! \stemDown b'32 ( \stemDown a'32 \stemDown
        es32 \stemDown des8 ~ ] \stemDown des4 ~ \stemDown des8 ) [
        \acciaccatura { \stemUp des8 } \stemDown c'8 ~ ] \stemDown c4 _-
        _\> -\! | % 121
        \stemDown cis,,32 ( [ \stemDown d32 \stemDown e32 \stemDown bes'32
        \stemDown c32 \stemDown es32 \stemDown fis32 \stemDown a32 ]
        \stemDown b8 ) ^. [ \stemDown b8 ^. ] \stemDown b8 ^. \stemDown
        b4. ^- | % 122
        r32 \stemDown a32 ( [ \stemDown b32 \stemDown f'32 \stemDown g8
        ) ^. ] \stemDown g8 ^. [ \stemDown g8 ^. ] \stemDown g8 ^.
        \stemDown g4. ~ ^- | % 123
        \times 2/3  {
            \stemDown g8 [ \stemDown as,8 ^. \stemDown des8 ^. ] }
        \times 2/3  {
            \stemDown d,8 ^. [ \stemDown e'8 ( \stemDown bes8 ) ^. ] }
        \times 2/3  {
            \stemDown c,8 [ \stemDown es'8 ( \stemDown fis,8 ) ^. ] }
        \times 2/3  {
            \stemDown a,8 [ \stemDown b'8 ( \stemDown f8 ) ^. ] }
        | % 124
        \times 2/3  {
            \stemUp g,8 ( [ \stemUp as8 \stemUp des8 ] }
        \times 2/3  {
            \stemUp bes8 [ \stemUp es,8 \stemUp c8 ] }
        \times 2/3  {
            \stemUp d8 \stemUp e4 ~ }
        \stemUp e4 ) _\> _\! \bar "|."
        \acciaccatura { \stemUp d8 ( } \stemDown cis'2. ) ( _\pp
        \stemDown b4 ) | % 126
        \stemUp c,32 ( \stemDown dis'8. -2 ) ( _\< \stemDown f4 ^- _\mf
        -\! s32*17 | % 127
        \stemDown es2. ) _\> r16 \stemUp c,16 ( _. [ -\! \stemUp es16
        \stemUp d16 ] | % 128
        cis'1 ~ _\> | % 129
        \stemDown cis4 ) -\! r4 r2 | \barNumberCheck #130
        \grace { \stemUp c,64 ( } \stemDown cis'2. ) ( \stemDown b4 ) | % 131
        \acciaccatura { \stemUp c,8 ( } \stemDown cis'2. ) \acciaccatura
        { \stemUp f,8 ( } \stemDown es'4 ) ^- | % 132
        \acciaccatura { \stemUp d,8 ( } cis'1 | % 133
        \stemDown c2 ~ _\> \stemDown c8 ) -\! r8 r4 | % 134
        R1 | % 135
        \times 2/3  {
            \stemDown d'8 ( [ \stemDown f8 ) \stemDown c8 ^. ] }
        \times 2/3  {
            \acciaccatura { \stemUp es8*3/2 ( } \stemDown des8 ) ^. [
            \stemDown b8 ^. \stemDown a8 ^. ] }
        \times 2/3  {
            \stemDown fis8 ( [ _\sf \stemDown e8 ) \stemDown bes8 ] }
        \times 2/3  {
            \stemUp as8 _. [ \stemUp g8 _. \stemUp e8 _. ] }
        | % 136
        \stemDown a'8 [ _\p \stemDown fis,8 ] \times 2/3 {
            \stemDown as'8 ( [ \stemDown bes,8 ) \stemDown bes'8 ( ] }
        \stemDown c,8 ) r8 \times 2/3 {
            r8 \stemDown a'8 [ \stemDown fis,8 ] }
        | % 137
        \times 2/3  {
            \stemDown as'8 [ \stemDown bes,8 \stemDown bes'8 ( ] }
        \times 2/3  {
            \stemDown c,8 ) ^. [ \stemDown fis,8 \stemDown as'8 ( ] }
        \times 2/3  {
            \stemDown bes,8 [ \stemDown as'8 ) ( \stemDown c,8 ] }
        \times 2/3  {
            \stemDown bes'8 ) ( ^. [ \stemDown fis,8 \stemDown a'8 ) ] }
        | % 138
        \times 2/3  {
            \stemDown bes,8 ( [ \stemDown as'8 ) ( \stemDown c,8 ] }
        \stemDown bes'8 ) r8 r2 | % 139
        \times 2/3  {
            r8 \stemDown bes8 ( [ _\f \stemDown g8 ] }
        \times 2/3  {
            \stemDown cis8 [ \stemDown e8 \stemDown dis8 ] }
        \times 2/3  {
            \stemDown c8 [ \stemDown a8 \stemDown fis8 ] }
        \times 2/3  {
            \stemDown f8 [ \stemDown d8 \stemDown as'8 ) ] }
        | \barNumberCheck #140
        \acciaccatura { \stemUp b8 } \stemDown a'2. ~ \stemDown a8. [
        \stemDown gis16 ] | % 141
        \stemDown fis8 ( [ \stemDown c8 ~ ] \stemDown c2. ) | % 142
        \grace { \stemUp bes16 ( [ \stemUp c16 ] } \stemDown bes8 ) [
        \stemDown g8 ~ ] \stemDown g2. | % 143
        \stemDown f2. ( \stemDown es4 ~ | % 144
        \stemDown es2 ) r2 | % 145
        \grace { \stemUp c,16 ( [ \stemUp e16 \stemUp b'16 ] } \stemDown
        d2. ) _\p \grace { \stemUp c,16 ( [ \stemUp e16 \stemUp b'16 ] }
        \stemDown d4 ) ^- | % 146
        \grace { \stemUp a16 ( [ \stemUp c16 \stemUp g'16 ] } \stemDown
        bes2. ) ^- \grace { \stemUp a,16 ( [ \stemUp c16 \stemUp g'16 ]
            } \stemDown bes4 ) ^- | % 147
        \grace { \stemUp g,16 ( [ \stemUp bes16 -2 \stemUp e16 \stemUp f16
            ] } \stemDown gis2. ) \grace { \stemUp g,16 ( [ \stemUp bes16
            \stemUp f'16 ] } \stemDown gis4 ) ^- | % 148
        \grace { \stemUp as,16 ( [ \stemUp bes16 -3 \stemUp e16 \stemUp
            f16 ] } \stemDown e'2. ) ^- \grace { \stemUp as,,16 ( [
            \stemUp bes16 \stemUp f'16 ] } \stemDown e'4 ) ^- | % 149
        \times 2/3  {
            \stemDown fis,16 ( [ \stemDown gis16 \stemDown e16 }
        \stemDown cis8 ~ ] \stemDown cis2 ) \grace { \stemUp b16 ( [
            \stemUp eis16 ] } \stemDown <c' d>4 ) ^- | \barNumberCheck
        #150
        \times 4/5  {
            \stemDown d,,16 [ \stemDown f16 ( \stemDown c'16 \stemDown
            es16 \stemDown cis'16 ] }
        \stemDown b2 ~ \times 2/3 {
            \stemDown b8 ) [ \stemDown cis,,8 ( \stemDown b'8 ] }
        s4 \stemUp fis'8 ) [ \stemUp cis,8 ( \stemUp b'8 ] s4. | % 152
        g1 ) ~ ^\trill | % 153
        \stemDown g8 [ _\fz \stemDown f8 ^. r8 \stemDown b'8 ^. ]
        \stemDown a,8 ^. [ \stemDown fis'8 ^. \stemDown e,8 ^. ]
        \stemDown d'8 ^. | % 154
        \times 2/3  {
            \stemDown f'2. ~ ^\trill \ottava #0 \ottava #0 \ottava #0
            \stemDown f4 \stemDown es8 ^. \stemDown c8 ( [ \stemDown
            bes'8 ) ^. \stemDown e,,8 ( ] }
        | % 155
        \times 2/3  {
            \stemDown d'8 ) ^. [ \stemDown cis,8 ^. \stemDown fis'8 ^. ]
            }
        \times 2/3  {
            \stemDown a,8 ( [ \stemDown b,8 ) \stemDown f''8 ^. ] }
        \stemDown g,2 ^- | % 156
        \times 2/3  {
            \stemDown d8 ( [ \stemDown cis8 ) \stemDown fis'8 ^. ] }
        \times 2/3  {
            \stemDown a,8 ( [ \stemDown b,8 ) \stemDown f''8 ^. ] }
        \stemDown g,2 ^- _\> _\! | % 157
        \times 2/3  {
            \stemDown bes,8 ( [ \stemDown as'8 ) ( ^. \stemDown g,8 ] }
        \times 2/3  {
            \stemDown c'8 ) ^. [ \stemDown es,8 ( \stemDown f,8 ] }
        \stemDown b'2 ) | % 158
        \times 2/3  {
            \stemDown as,8 ( [ \stemDown g8 ) \stemDown c'8 ^. ] }
        \times 2/3  {
            \stemDown es,8 ( [ \stemDown f,8 ) \stemDown b'8 ^. ] }
        \stemDown cis,2 ^- _\> | % 159
        r4 \times 2/3 {
            \stemUp cis8 ( [ -\! \stemUp d,8 \stemUp f8 ) _. ] }
        \times 2/3  {
            \stemDown c''8 ( \stemDown es,4 ~ }
        \stemDown es4 ) | \barNumberCheck #160
        r4 \stemDown es8 ( ^. [ _\p \stemDown f,8 \stemDown b'8 ) ^. ]
        \stemUp cis,8 ( [ \stemUp d,8 \stemUp f8 ) _. ] | % 161
        \stemDown e'4 r4 r4 _\ppp \times 2/3 {
            \stemDown es8 ( [ \stemDown f,8 \stemDown b'8 ) ^. ] }
        | % 162
        \stemDown cis,2. ^- \grace { \stemUp cis16 ( [ \stemUp es16 ] }
        \stemDown d4 ) ^- | % 163
        \numericTimeSignature\time 2/2  \stemUp g,4. ( ~ ^\trill
        \stemDown g16 [ \stemDown as16 ) \stemDown bes16 ( \stemDown e16
        \stemDown fis16 \stemDown a16 ) ] s4 | % 164
        \stemDown b8 ^. \stemDown b4. :64 ^. \stemDown b2 :32 s1 | % 166
        <g,, b>1 \bar "|."
        }
    }

PartPOneVoiceTwo =  \relative a'' {
    \clef "treble" \time 4/4 | % 1
    \key c \major s1*35 | % 36
    \time 2/2  s1*7 \bar "|."
    s1*2 \repeat volta 2 {
        s1*8 | % 53
        \time 4/4  s1*20 | % 73
        \time 3/4  s4*57 | % 92
        \time 2/2  s1*9 \bar "|."
        \time 4/4  s1*6 \bar "|."
        s1*18 \bar "|."
        s1*26 | % 151
        \stemDown a8 \stemDown fis4 ( s4 \stemDown e8 ) \stemDown b4 (
        s1*11 | % 163
        \numericTimeSignature\time 2/2  s1 | % 164
        s4 _\sf r4 s2 _\ff | % 165
        \stemDown b'8 ^. _\< \stemDown b8 ^. [ -\! \stemDown b8 ^.
        \stemDown b8 ^. ] \stemDown b8 ^. [ \stemDown b8 ^. \stemDown b8
        ^. \stemDown b8 ^. ] | % 166
        \acciaccatura { \stemUp b8 } \stemDown b'8 ) ^! r8 _\f r4 r2
        \bar "|."
        }
    }


% The score definition
\score {
    <<
        
        \new Staff
        <<
            \set Staff.instrumentName = "Part 1"
            
            \context Staff << 
                \mergeDifferentlyDottedOn\mergeDifferentlyHeadedOn
                \context Voice = "PartPOneVoiceOne" {  \voiceOne \PartPOneVoiceOne }
                \context Voice = "PartPOneVoiceTwo" {  \voiceTwo \PartPOneVoiceTwo }
                >>
            >>
        
        >>
    \layout {}
    % To create MIDI output, uncomment the following line:
    %  \midi {\tempo 4 = 100 }
    }

