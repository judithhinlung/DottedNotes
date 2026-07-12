\version "2.24.0"

% ============================================================
% Fengyang Flower Drum Song
% 65 measures, 4/4, key of B-flat
% ============================================================

\header {
  title = "Fengyang Flower Drum Song"
  subtitle = "Variation for Flute and Strings"
}

% ------------------------------------------------------------
% Pizzicato / arco helpers (notation + MIDI)
% ------------------------------------------------------------
pizz = { \set Staff.midiInstrument = "pizzicato strings" }
arcoCello = { \set Staff.midiInstrument = "cello" }
arcoBass = { \set Staff.midiInstrument = "contrabass" }

% ------------------------------------------------------------
% Global settings shared by all parts (key, time, bar count)
% ------------------------------------------------------------
global = {
  \key ees \major
  \time 4/4
  \tempo 4 = 120
}

% ------------------------------------------------------------
% FLUTE
% ------------------------------------------------------------
fluteMusic = \relative c'' {
  \global

  %1
r1 * 45 |
%46
bes'8\f g8 f8 g8 bes4 r4 |
%47
g8 bes8 c8 ees8 bes4 r4 |
%48
bes8 bes4 ees8 c8 bes8 g4 |
%49
f8. bes16 g8-. f8-. ees4 r4 |
%50
ees8 ees4 c8 bes'4 bes8 g8 |
%51
f8. ees16 f8-. g8-. bes4 r4 |
%52
r1 |
%53
r1 |
%54
bes4\mf bes8 f8 ees8. f16 g8 bes8 | |
%55
f8 ees8 c8-. f8-. ees4 r4 |
%56
bes'4-.\f ees,8 ees8 ees8 c8 ees4-. |
%57
r1 |
%58
bes'4 ees,4 bes'4 ees,4 |
%59
bes'8-. bes8-. ees,8-. bes'8-. ees,8-. ees8-. c8-. f8-. | |
%60
ees8-. ees8-. ees8-. c8-. ees4-- ees4-- | |%61
%61
r1 * 2
%63
bes'4\f ees,4 bes'4 ees,4 |
%64
bes'8-. bes8-. ees,8-. bes'8-. ees,8-. ees8-. c8-. f8-. |
%65
ees8-. es8-. ees8-. c8-. ees4-- ees4-- \bar "|." |
}

% ------------------------------------------------------------
% VIOLIN I
% ------------------------------------------------------------
violinOneMusic = \relative c'' {
  \global
  %1
  r1 |
  %2
bes8-.\mp bes16 c16 bes4-. ees8-. ees16 f16 ees4-. |
%3
bes'8 bes16 c16 bes8-. g8-. f8 ees16 c16 bes8-. g8-. |
%4
f'16->\< g16 f16 ees16 c16-> bes16 g16 f16 ees16-> f16 g16 bes16 c16-> ees16 f16 g16 |
%5
bes2\> bes,2 |
%6
R1 * 15
%21
r2 r8 bes16\pp c16 ees16 c16 ees16 f16 |
%22
g4-. r4 r8 c,16 ees16 f16 ees16 f16 g16 |
%23
bes4-. r4 ees,16 f16 g16 bes16 c16 bes16 g16 bes16 |
%24
bes4-. r4 c16 bes16 f16 bes16 g16 bes16 g16 f16 |
%25
ees4-. r4 ees16 f16 g16 bes16 c16 bes16 g16 bes16 |
%26
g4-. 4 g16 f16 g16 bes16 ees16 c16 ees16 bes16 |
%27
bes4-. r4 ees,16 f16 g16 bes16 c16 bes16 f16 g16 |
%28
f4 f4 ees4 r4 |
%29
g8-. bes8-. f8-. bes8-. ees,8-. bes'8-. f8-. bes8-. |
%30
g8-. bes8-. f8-. bes8-. ees,4-. r4 |
%31
bes'8 bes16 bes16 bes8-. bes8-. bes4-. bes4-.
%32
bes8 bes16 bes16 bes8-. bes8-. bes4-. ees,4-.
%33
g4-. c,4-. g'4-. c,4-. |
%34
g'8-. g8-. c,8-. g'8-. c,8-. c8-. g8-. bes8-. |
%35
c8-. c8-. c8-. g8-. c4-- c4-- |
%36
bes8-.\mp bes16 c16 bes4-. ees8-. ees16 f16 ees4-. |
%37
bes'8-.\< bes16 c16 bes8-. g8-. f8-. ees16 c16 bes8-. g8-. |
%38
f8. ees16 f8-. g8-. bes4 r4 |
%39
f'8.\f ees16 c8-. ees8-. bes8-. c8-. bes8-. g8-. |
%40
f8. g16 ees'8-. g,8-. bes4 r4 |
%41
g8. bes16 ees8-. bes8 -.c4 r4 |
%42
c8-.\> bes8-. g8-. f8-. ees8-. c8-. bes8-. g8-. |
%43
bes8-. c8-. ees8-. f8-. c8-. ees8-. f8-. g8-. |
%44
f'16->\< g16 f16 ees16 c16-> bes16 g16 f16 ees16-> f16 g16 bes16 c16-> ees16 f16 g16 |
%45violin 
bes2\> bes,2 |
%46
r2 bes8\pp bes16 bes16 bes8-. bes8-. |
%47
r2 bes8 bes16 bes16 bes8-. bes8-. |
%48
bes8 bes16 bes16 bes8-. bes8-. bes8 bes16 bes16 g8-. g8-. |
%49
f8 f16 f16 f8-. f8-. g4-. r4 |
%50
r1 |
%51
g4-. bes4-. bes4-. bes4-. |
%52
r1 |
%53
bes4 f8 f16 f16 g4 r4 |
%54
bes4-. bes4-. bes4-. bes4-. |
%55
f4-. f4-. bes4-. r4 |
%56
bes2-.\mf g4-. bes4-. |%57
%57
r1 |
%58
bes4 ees,4 bes'4 ees,4 |
%59
bes'8-. bes8-. ees,8-. bes'8-. ees,8-. ees8-. c8-. f8-. |
%60
ees8-. ees8-. ees8-. c8-. ees4-- ees4-- | |
%61
bes'8-.\mp bes16 c16 bes4-. ees8-. ees16 f16 ees4-. |
%62
bes8-.\< bes16 c16 bes8-. g8-. f8 ees16 c16 bes8-. bes8-. |
%63
bes'4\f ees,4 bes'4 ees,4 |
%64
bes'8-. bes8-. ees,8-. bes'8-. ees,8-. ees8-. c8-. f8-. |
%65
ees8-. es8-. ees8-. c8-. ees4-- ees4-- \bar "|." |
}

% ------------------------------------------------------------
% VIOLIN II
% ------------------------------------------------------------
violinTwoMusic = \relative c'' {
  \global
%1
r1 |
%2
bes,8-.\mp bes16 c16 bes4-. ees8-. ees16 f16 ees4-. |
%3
bes'8-. bes16 c16 bes8-. g8-. f8 ees16 c16 bes8-. g8-. |
%4
f'16->\< g16 f16 ees16 c16-> bes16 g16 bes16 ees16-> f16 g16 bes16 c16-> ees16 f16 g16 |
%5
bes2\> bes,2 |
%6
r1 * 15 |
%21
bes8\mf g8 f8 g8 bes4 r4 |
%22
g8 bes8 c8 ees8 bes4 r4 |
%23
bes8 bes4 ees8 c8 bes8 g4 |
%24
f8. bes16 g8-. f8 -.ees4 r4 |
%25
ees8 ees4 c8 bes'4 bes8 g8 |
%26
f8. ees16 f8-. g8-. bes4 r4 |
%27
bes8 bes4 ees8 c8 bes8 g4 |
%28
f8. bes16 g8-. f8-. ees4 r4 |
%29
bes'4 bes8 f8 ees8. f16 g8-. bes8-. |
%30
f8 ees8 c8 f8 ees4-. ees4-. |
%31
bes'4 ees,8 ees8 ees8 c8 ees4-. |
%32
bes'4 ees,8 ees8 ees8 c8 ees4-. |
%33
bes'4-. ees,4-. bes'4-. ees,4-. |
%34
bes'8-. bes8-. ees,8-. bes'8-. ees,8-. ees8-. c8-. f8-. |
%35
ees8-. ees8-. ees8-. c8-. ees4-- ees4-- |

%36
bes8-.\mp bes16 c16 bes4-. ees8-. ees16 f16 ees4-. |
bes'8-.\< bes16 c16 bes8-. g8-. f8 ees16 c16 bes8-. g8-. |
%38
f'8. ees16 f8-. g8-. bes4 r4 |
%39
f8.\f ees16 c8 ees8 bes8-. c8-. bes8-. g8-. |
%40
f'8. g16 ees'8-. g,8-. bes4 r4 |
%41
ees,8. g16 c8 g8 g4 r4 |
%42
g8-.\> g8-. ees8-. d8-. c8-. bes8-. g8-. bes8-. |
%43
g4-. c4-. bes4-. ees4-. |
%44
c'16->\< ees16 c16 bes16 g16-> g16 f16 ees16 bes16-. c16 ees16 f16 g,16-> bes16 c16 ees16 |
%45
f2 \>bes2 |
%46
r2 g8\pp g16 g16 g8-. g8-. |
%47
r2 g8 g16 g16 f8-. g8-. |
%48
g8 g16 g16 g8-. g8-. g8 g16 g16 ees8-. ees8-. |
%49
c8 c16 c16 c8-. c8-. ees4-. r4 |
%50
r1 |
%51
ees4-. g4-. f4-. g4-. |%52
r1 |
%53
f4 bes,8 bes16 bes16 ees4 r4 |
%54
ees4-. ees4-. ees4-. ees4-. |
%55
bes4-. bes4-. ees4-. r4 |
%56
ees2-.\mf c4-. ees4-. |
%57
r1 |
%58
g4-. c,4-. g'4-. c,4-. |
%59
g'4-. c,4-. g'4-. c,4-. |
%60
f4-. bes,4-. g'4-. g4-. |
%61
bes,8-.\mp bes16 c16 bes4-. ees8-. ees16 f16 ees4-. |
%62
bes'8-.\< bes16 c16 bes8-. g8-. f8 ees16 c16 bes8-. bes8-. |
%63
bes'4\f ees,4 bes'4 ees,4 |
%64
bes'8-. bes8-. ees,8-. bes'8-. ees,8-. ees8-. c8-. f8-. ||
%65
ees8-. es8-. ees8-. c8-. ees4-- ees4-- \bar "|." |
}

% ------------------------------------------------------------
% VIOLA
% ------------------------------------------------------------
violaMusic = \relative c' {
  \global
%1
bes4-.\mp bes4-. bes4-. bes4-. |
%2
bes4-. bes4-. bes4-. bes4-. |
%3
bes2 ees,4-. ees4-. |
%4
g4 bes4 c4 g4 |
%5
ees'2 f2 |
%6
r1 * 15 |
%21
r1 * 15
%36
ees4\mp-. ees4-. ees4-. ees4-. |
%37
ees4-.\< ees4-. ees4-. ees4-. |%37
%38
ees4-. ees4-. f4-. f4-. |
%39
f4-.\f f4-. ees4-. ees4-. |
%40
f2.-. f4-. |
%41
ees2.-. c4-. |
%42
c4-. c4-. c4-. c4-. |
%43
c4-. c4-. c4-. c4-. |
%44
c8-.\< c8-. c8-. c8-. c8-. c8-. c8-. c8-. |
%45
bes2\> f'2 |
%46
r2 bes8\f g8 f8 g8 |
%47
bes4 r4 g8 bes8 c8 ees8 |
%48
bes4 r4 bes8 bes4 ees8 |
%49
c8 bes8 g4 f8. bes16 g8-. f8-. |
%50
r1 |
%51
r1 |
%52
bes8 bes4 ees8 c8 bes8 g4 |
%53
f8. bes16 g8-. f8-. ees4 r4 |
%54
ees4-.\mf f4-. g4-. bes4-. |
%55
c4-. bes4-. g4-. r4-. |
%56
r1 |
%57
bes4-.\f ees,8 ees8 ees8 c8 ees4-. |
%58
bes'4 ees,4 bes'4 ees,4 |
%59
bes'8-. bes8-. ees,8-. bes'8-. ees,8-. ees8-. c8-. f8-. |
%60
ees8-. ees8-. ees8-. c8-. ees4-- ees4-- |
%61
bes4-.\mp bes4-. bes4-. bes4-. |
%62
bes4-.\f bes4-. ees4-. ees4-. |
%63
bes'4 ees,4 bes'4 ees,4 |
%64
bes'8-. bes8-. ees,8-. bes'8-. ees,8-. ees8-. c8-. f8-. ||
%65
ees8-. es8-. ees8-. c8-. ees4-- ees4-- \bar "|." |
}

% ------------------------------------------------------------
% CELLO
% ------------------------------------------------------------
celloMusic = \relative c {
  \global
%1
ees4-.\mp ees4-. ees4-. ees4-. |
%2
ees4-. ees4-. ees4-. ees4-. |
%3
ees4-. ees4-. bes4-. bes4-. |
%4
g4-. bes4-. c4-. g4 |
%5
ees'2 f2 |
%6
bes8\mf g8 f8 g8 bes4 r4 |
%7
g8 bes8 c8 ees8 bes4 r4 |
%8
bes8 bes4 ees8 c8 bes8 g4 |
%9
f8. bes16 g8-. f8 -.ees4 r4 |
%10
ees8 ees4 c8 bes'4 bes8 g8 |
%11
f8. ees16 f8-. g8-. bes4 r4 |
%12
bes8 bes4 ees8 c8 bes8 g4 |
%13
f8. bes16 g8-. f8-. ees4 r4 |
%14
bes'4 bes8 f8 ees8. f16 g8-. bes8-. |
%15
f8 ees8 c8 f8 ees4-. ees4-. |
%16
bes'4\f ees,8 ees8 ees8 c8 ees4-. |
%17
bes'4 ees,8 ees8 ees8 c8 ees4-. |
%18
bes'4-. ees,4-. bes'4-. ees,4-. |
%19
bes'8-. bes8-. ees,8-. bes'8-. ees,8-. ees8-. c8-. f8-. |
%20
ees8-. ees8-. ees8-. c8-. ees4-- ees4-- |
%21
ees,4\pp-. bes'4-. ees4-. bes4-. |
%22
ees,4-. bes'4-. ees4-. bes4-. |
%23
ees,4-. bes'4-. ees4-. bes4-. |
%24
bes4-. f'4-. ees4-. ees,4-. |
%25
c4-. g'4-. c4-. g4-. |
%26
f4-. bes4-. ees,4-. bes'4-. |
%27
ees,4-. bes'4-. ees4-. bes4-. |
%28
f4-. bes4-. ees,4-. bes'4-. |
%29
bes4-. bes4-. g4-. g4-. |
%30
f4 f4 ees4 ees4 |
%31
bes'8 bes16 bes16 bes8-. bes8-. bes4-. bes4-. |
%32
bes8 bes16 bes16 bes8-. bes8-. bes4-. bes4-. |
%33
ees2-. c2-. |
%34
ees2-. c2-. |
%35
g2-. c2-. |
%36
bes4-.\mp bes4-. bes4-. bes4-. |
%37
bes4-.\< bes4-. bes4-. bes4-. |
%38
bes4-. bes4-. bes4-. bes4-. |
%39
c4-.\f c4-. bes4-. bes4-. |
%40
bes2.-. bes4-. |%41
%41
bes2.-. g4-. |
%42
c4-.\> ees4-. f4-. g4-. |
%43
c4-. bes4-. g4-. f4-. |
%44
c8-. ees8-. f8-. g8-. c8-. bes8-. g8-. f8-. |
%45
bes,2
 bes'2 |
%46
ees,,8-.\p g8 -.ees'8-. bes8-. g8-. bes8-. ees8-. bes8-. |
%47
ees,8-. g8-. ees'8-. bes8-. g8-. bes8-. ees8-. bes8-. |
%48
ees,8-. g8-. ees'8-. c8-. g8-. bes8-. ees8-. bes8-. |
%49
bes8-. bes'8-. f8-. bes8-. ees,4-. r4 |
%50
c8 ees8-. bes'8-. f8-. bes,8-. ees8-. bes'8-. ees,8-. |
%51
bes8.-. c16-. ees8-. f8-. g8-. bes8-. c8-. bes8-. |
%52
c,8-. ees8-. bes'8-. ees,8-. bes8-. ees8-. bes'8-. ees,8-. |

%53
bes8-. ees8-. bes'8-. ees,8-. ees4-. r4 |

%54
bes'4-.\mp bes4-. bes4 bes4-. |
%55
bes4-. bes4-. ees,4-. r4 |
%56
r1 |
%57
bes2-.\mf g4-. bes4-. |
%58
c4-. g4-. c,4-. g'4-. |
%59
c,4-. g'4-. c,4-. g'4-. |
%60
bes'4-. f4-. bes4-. bes4-. |
%61
ees,4-.\mp ees4-. ees4-. ees4-. |
%62
ees4-. ees4-. bes4-. bes4-. |
%63
bes'4\f ees,4 bes'4 ees,4 |
%64
bes'8-. bes8-. ees,8-. bes'8-. ees,8-. ees8-. c8-. f8-. ||
%65
ees8-. es8-. ees8-. c8-. ees4-- ees4-- \bar "|." |
}

% ------------------------------------------------------------
% DOUBLE BASS
% (sounds an octave lower than written - standard convention)
% ------------------------------------------------------------
bassMusic = \relative c {
  \global
%1
ees,4\mp-. ees4-. ees4-. ees4-. |
%2  
ees4-. ees4-. ees4-. ees4-. |
%3
ees4-. ees4-. bes'4-. bes4-. |
%4
g4-. bes4-. c4-. ees4-. |
%5
ees2 bes2 |
%6
\pizz ees,8-.\p ^\markup { \italic "pizz." } g8-. ees'8-. bes8-. g8-. bes8-. ees8-. bes8-. |
%7
ees,8-. g8-. ees'8-. bes8-. g8-. bes8-. ees8-. bes8-. |
%8
ees,8-. g8-. ees'8-. c8-. g8-. bes8-. ees8-. bes8-. |
%9
bes8-. bes'8-. f8-. bes8-. ees,4-. r4 |
%10
c,8-. ees8-. bes'8-. f8-. bes,8-. ees8-. bes'8-. ees,8-. |
%11
bes8.-. c16-. ees8-. f8-. g8-. bes8-. c8-. bes8-. |
%12
c,8-. ees8-. bes'8-. ees,8-. bes8-. ees8-. bes'8-. ees,8-. |
%13
bes8-. ees8-. bes'8-. ees,8-. ees4-. r4 |
%14
c4-. ees4-. bes'4-. ees,4-. |
%15
c4-. ees8-. bes'8-. ees,4-. r4 |
%16
\arcoBass ees2-.\mp ^\markup { \italic "arco" } ees4-. ees4-. |
%17
ees2-. ees4-. ees4-. |
%18
bes4-. c4-. ees4-. ees4-. |
%19
bes4-. c4-. ees4-. f4-. |
%20
c4-. bes4-. ees4-. ees4-. |
%21
ees4-.\pp bes'4-. ees4-. bes4-. |
%22
ees,4-. bes'4-. ees4-. bes4-. |
%23
ees,4-. bes'4-. ees4-. bes4-. |
%24
bes4-. f'4-. ees4-. ees,4-. |
%25
c4-. g'4-. c4-. g4-. |
%26
f4-. bes4-. ees,4-. bes'4-. |
%27
ees,4-. bes'4-. ees4-. bes4-. |
%28
f4-. bes4-. ees,4-. bes'4-. |
%29
ees,4-. ees4-. c4-. c4-. |
%30
bes4 bes4 ees4 ees4
%31
ees8 ees16 ees16 ees8-. ees8-. ees4-.-. ees4-.-. |
%32
ees8 ees16 ees16 ees8-. ees8-. ees4-. ees4-. |
%33
ees2-. c2-. |
%34
ees2-. c2-. |
%35
g2-. c2-. |
%36
ees4-.\mp ees4-. ees4-. ees4-. |
%37
ees4-.\< ees4-. ees4-. ees4-. |
%38
ees4-. ees4-. f4-. f4-. |
%39
f4-.\f f4-. ees4-. ees4-. |
%40
ees2.-. ees4-. |
%41
ees2.-. c4-. |
%42
c4-.\> ees4-. f4-. g4-. |
%43
c4-. bes4-. g4-. f4-. |
%44
c8-. ees8-. f8-. g8-. c8-. bes8-. g8-. f8-. |
%45
bes2 bes,2 |
%46
ees8-.\p g8-. ees'8-. bes8-. g8-. bes8-. ees8-. bes8-. |
%47
ees,8-. g8-. ees'8-. bes8-. g8-. bes8-. ees8-. bes8-. |
%48
ees,8-. g8-. ees'8-. c8-. g8-. bes8-. ees8-. bes8-. |
%49
bes8-. bes'8-. f8-. bes8-. ees,4-. r4 |
%50
c,8-. ees8-. bes'8-. f8-. bes,8-. ees8-. bes'8-. ees,8-. |
%51
bes8.-. c16-. ees8-. f8-. g8-. bes8-. c8-. bes8-. |
%52
c,8-. ees8-. bes'8-. ees,8-. bes8-. ees8-. bes'8-. ees,8-. |
%53
bes8-. ees8-. bes'8-. ees,8-. ees4-. r4 |
%54
bes'4-.\mp bes4-. bes4-. bes4-. |
%55
bes4-. bes4-. ees,4-. r4 |
%56
r1 |
%57
ees2-.\mf c4-. ees4-. |
%58
g4 c4 g4 c4 |
%59
g4 c4 g4 c4 |
%60
bes4-. f4-. ees4-. ees4-. |
%61
ees4-.\mp ees4-. ees4-. ees4-. |
%62
ees4-. ees4-. bes4-. bes4-. |
%63
bes'4\f ees,4 bes'4 ees,4 |
%64
bes'8-. bes8-. ees,8-. bes'8-. ees,8-. ees8-. c8-. f8-. ||
%65
ees8-. es8-. ees8-. c8-. ees4-- ees4-- \bar "|." |
}

% ------------------------------------------------------------
% SCORE ASSEMBLY
% ------------------------------------------------------------
\score {
  <<
    \new Staff \with {
      instrumentName = "Flute"
      shortInstrumentName = "Fl."
    } {
      \clef treble
      \set Staff.instrumentName = "Flute"
      \set Staff.midiInstrument = "flute"
      \fluteMusic
    }

    \new StaffGroup = "strings" <<
      \new Staff \with {
        instrumentName = "
         I"
        shortInstrumentName = "Vl. I"
      } {
        \clef treble
        \set Staff.instrumentName = "Violin I"
        \set Staff.midiInstrument = "violin"

        \violinOneMusic
      }

      \new Staff \with {
        instrumentName = "Violin II"
        shortInstrumentName = "Vl. II"
      } {
        \clef treble
        \set Staff.instrumentName = "Violin II"
        \set Staff.midiInstrument = "violin"

        \violinTwoMusic
      }

      \new Staff \with {
        instrumentName = "Viola"
        shortInstrumentName = "Vla."
      } {
        \clef alto
        \set Staff.instrumentName = "viola"
        \set Staff.midiInstrument = "viola"

        \violaMusic
      }

      \new Staff \with {
        instrumentName = "Violoncello"
        shortInstrumentName = "Vc."
      } {
        \clef bass
        \set Staff.instrumentName = "Violoncello"
        \set Staff.midiInstrument = "cello"

        \celloMusic
      }

      \new Staff \with {
        instrumentName = "Double Bass"
        shortInstrumentName = "D.B."
      } {
        \clef bass
        \set Staff.instrumentName = "Double Bass"
        \set Staff.midiInstrument = "contrabass"

        \bassMusic
      }
    >>
  >>

  \layout {
    \context {
      \Score
      \remove "Bar_number_engraver"
    }
  }

  \midi {
    \tempo 4 = 72
  }
}
