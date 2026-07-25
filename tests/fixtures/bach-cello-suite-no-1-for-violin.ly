\version "2.26.0"
% automatically converted by musicxml2ly from bach-cello-suite-no-1-for-violin.mxl
\pointAndClickOff

%% additional definitions required by the score:
D = \tweak Stem.direction #DOWN \etc
U = \tweak Stem.direction #UP \etc


\header {
  title = \markup \normal-text \normalsize \fontsize #6.786
  "Bach Cello Suite No. 1 For Violin"
  composer = \markup \normal-text \normalsize \fontsize #0.786 "J.S. Bach"
  poet = \markup \normal-text \normalsize \fontsize #0.786
  "Adapted for violin by Vittoria"
  copyright = \markup \normal-text \normalsize \fontsize #2.120
  "Arranged by mateuszswoboda"
  "id: software" = "MuseScore 1.3"
  "id: encoding-date" = "2015-01-27"
  "id: source" = "http://musescore.com/score/116486"
}
#(set-global-staff-size 20.07501264566929)
\paper {
  paper-width = 21.0\cm
  paper-height = 29.7\cm
  top-margin = 1.0\cm
  bottom-margin = 2.0\cm
  left-margin = 1.0\cm
  right-margin = 1.0\cm
  indent = 1.62\cm
  short-indent = 1.08\cm
}
\layout {
  \context {
    \Staff
    printKeyCancellation = ##f
  }
  \context {
    \Score
    autoBeaming = ##f
  }
}
PartPOneVoiceOne = \relative d' {
  \clef "treble" \numericTimeSignature \time 4/4 \key d \major \U d16 [ ^\markup
  Maestoso \U a'16 \U fis'16 \U e16 ] \U fis16 [ \U a,16 \U fis'16 \U a,16 ] \U
  d,16 [ \U a'16 \U fis'16 \U e16 ] \U fis16 [ \U a,16 \U fis'16 \U a,16 ] | % 1
  \D d,16 [ \D b'16 \D g'16 \D fis16 ] \D g16 [ \D b,16 \D g'16 \D b,16 ] \D d,16
  [ \D b'16 \D g'16 \D fis16 ] \D g16 [ \D b,16 \D g'16 \D b,16 ] \break | % 2
  \D d,16 [ \D cis'16 \D g'16 \D fis16 ] \D g16 [ \D cis,16 \D g'16 \D cis,16 ]
  \D d,16 [ \D cis'16 \D g'16 \D fis16 ] \D g16 [ \D cis,16 \D g'16 \D cis,16 ]
  | % 3
  \D d,16 [ \D d'16 \D fis16 \D e16 ] \D fis16 [ \D d16 \D fis16 \D d16 ] \D d,16
  [ \D d'16 \D fis16 \D e16 ] \D fis16 [ \D d16 \D fis16 \D cis16 ] \break | % 4
  \D d,16 [ \D b'16 \D fis'16 \D e16 ] \D fis16 [ \D d16 \D cis16 \D d16 ] \D b16
  [ \D d16 \D cis16 \D d16 ] \U fis,16 [ \U a16 \U g16 \U fis16 ] | % 5
  \D gis16 [ \D d'16 \D e16 \D d16 ] \D e16 [ \D d16 \D e16 \D d16 ] \D gis,16 [
  \D d'16 \D e16 \D d16 ] \D e16 [ \D d16 \D e16 \D d16 ] \break | % 6
  \D cis16 [ \D e16 \D a16 \D g16 ] \D a16 [ \D e16 \D d16 \D e16 ] \D cis16 [
  \D e16 \D d16 \D e16 ] \U a,16 [ \U cis16 \U b16 \U a16 ] | % 7
  \U b,16 [ \U fis'16 \U d'16 \U cis16 ] \U d16 [ \U fis,16 \U d'16 \U fis,16 ]
  \U b,16 [ \U fis'16 \U d'16 \U cis16 ] \U d16 [ \U fis,16 \U d'16 \U fis,16 ]
  \break | % 8
  \U b,16 [ \U gis'16 \U a16 \U b16 ] \U a16 [ \U gis16 \U fis16 \U e16 ] \D d'16
  [ \D cis16 \D b16 \D a'16 ] \D gis!16 [ \D fis16 \D e16 \D d16 ] | % 9

  \barNumberCheck #10
  \D cis16 [ \D b16 \D a16 \D a'16 ] \D e16 [ \D a16 \D cis,16 \D e16 ] \D a,16
  [ \D b16 \D cis16 \D e16 ] \D d16 [ \D cis16 \D b16 \D a16 ] \break | % 10
  \D dis16 [ \D a16 \D c16 \D b16 ] \U c16 [ \U a16 \U dis16 \U a16 ] \D fis'16
  [ \D a,16 \D c16 \D b16 ] \U c16 [ \U a16 \U dis16 \U a16 ] | % 11
  \D g16 [ \D b16 \D e16 \D fis16 ] \D g16 [ \D e16 \D b16 \D a16 ] \D g16 [ \D
  b16 \D e16 \D fis16 ] \D g16 [ \D e16 \D cis16 \D b16 ] \break | % 12
  \U ais16 [ \U cis16 \U ais16 \U cis16 ] \D e16 [ \D cis16 \D e16 \D cis16 ] \U
  ais16 [ \U cis16 \U ais16 \U cis16 ] \D e16 [ \D cis16 \D e16 \D cis16 ] | % 13
  \D d16 [ \D cis16 \D b16 \D d16 ] \D cis16 [ \D d16 \D e16 \D cis16 ] \D d16 [
  \D cis16 \D b16 \D a16 ] \U g16 [ \U fis16 \U e16 \U d16 ] \break | % 14
  \U cis16 [ \U g'16 \U a16 \U g16 ] \U a16 [ \U g16 \U a16 \U g16 ] \U cis,16 [
  \U g'16 \U a16 \U g16 ] \U a16 [ \U g16 \U a16 \U g16 ] | % 15
  \U d16 [ \U fis16 \U cis'16 \U b16 ] \U cis16 [ \U fis,16 \U cis'16 \U fis,16
  ] \U d16 [ \U fis16 \U cis'16 \U b16 ] \U cis16 [ \U d,16 \U cis'16 \U d,16 ]
  \break | % 16
  \U d16 [ \U g16 \U b16 \U a16 ] \U b16 [ \U g16 \U b16 \U g16 ] \U d16 [ \U g16
  \U b16 \U a16 ] \U b16 [ \U g16 \U b16 \U g16 ] | % 17
  \D d16 [ \D cis'16 \D g'16 \D fis16 ] \D g16 [ \D cis,16 \D g'16 \D cis,16 ]
  \D d,16 [ \D cis'16 \D g'16 \D fis16 ] \D g16 [ \D cis,16 \D g'16 \D cis,16 ]
  \pageBreak | % 18
  \U d,16 [ \U a'16 \U fis'16 \U e16 ] \D fis16 [ \D d16 \D cis16 \D b16 ] \U a16
  [ \U g16 \U fis16 \U e16 ] \U d16 [ \U cis16 \U b16 \U a16 ] | % 19

  \barNumberCheck #20
  \U gis16 [ \U e'16 \U b'16 \U cis16 ] \D d16 [ \D b16 \D cis16 \D d16 ] \U
  gis,,16 [ \U e'16 \U b'16 \U cis16 ] \D d16 [ \D b16 \D cis16 \D d16 ] \break
  | % 20
  \U g,,!16 [ \U e'16 \U a16 \U b16 ] \D cis16 [ \D a16 \D b16 \D cis16 ] \U g,16
  [ \U e'16 \U a16 \U b16 ] \D cis16 [ \D a16 \D b16 \D cis16 ] | % 21
  \U g,16 [ \U e'16 \U a16 \U cis16 ] \D e16 [ \D gis16 \D a8 ~ ] \U a16
  ^\fermata [ \U e,16 \U fis16 \U g16 ] \D a16 [ \D b16 \D cis16 \D d16 ] \break
  | % 22
  \D e16 [ \D cis16 \D a16 \D b16 ] \D cis16 [ \D d16 \D e16 \D fis16 ] \D g16 [
  \D e16 \D cis16 \D d16 ] \D e16 [ \D fis16 \D g16 \D a16 ] | % 23
  \D bes16 [ \D a16 \D gis16 \D a16 ] \D a16 [ \D g16 \D fis16 \D g16 ] \D g16 [
  \D e16 \D cis16 \D b16 ] \U a16 [ \U e16 \U fis16 \U g16 ] \break | % 24
  \U a,16 [ \U e'16 \U a16 \U cis16 ] \D e16 [ \D fis16 \D g16 \D e16 ] \U fis16
  [ \U d16 \U a16 \U g16 ] \U fis16 [ \U d16 \U e16 \U fis16 ] | % 25
  \U a,16 [ \U d16 \U fis16 \U a16 ] \D d16 [ \D e16 \D fis16 \D d16 ] \D gis16
  [ \D fis!16 \D e16 \D f16 ] \D f16 [ \D e16 \D dis16 \D e16 ] \break | % 26
  \D e16 [ \D d!16 \D cis16 \D d16 ] \U d16 [ \U b16 \U gis16 \U fis16 ] \U e16
  [ \U gis16 \U b16 \U d16 ] \D e16 [ \D g16 \D a16 \D g16 ] | % 27
  \D a16 [ \D e16 \D cis16 \D b16 ] \D cis16 [ \D e16 \D a,16 \D cis16 ] \U e,16
  [ \U a16 \U g16 \U fis16 ] \U e16 [ \U d16 \U cis16 \U b16 ] \break | % 28
  \D a8 [ \D g''16 \D fis16 ] \D e16 [ \D d16 \D cis16 \D b16 ] \D a16 [ \D g'16
  \D fis16 \D e16 ] \D d16 [ \D cis16 \D b16 \D a16 ] | % 29

  \barNumberCheck #30
  \D g16 [ \D fis'16 \D e16 \D d16 ] \U cis16 [ \U b16 \U a16 \U g16 ] \D fis16
  [ \D e'16 \D d16 \D cis16 ] \U b16 [ \U a16 \U g16 \U fis16 ] \break | % 30
  \D e16 [ \D d'16 \D cis16 \D b16 ] \D cis16 [ \D e16 \D a,16 \D e'16 ] \D b16
  [ \D e16 \D cis16 \D e16 ] \D d16 [ \D e16 \D b16 \D e16 ] | % 31
  \D cis16 [ \D e16 \D a,16 \D e'16 ] \D d16 [ \D e16 \D b16 \D e16 ] \D cis16 [
  \D e16 \D a,16 \D e'16 ] \D d16 [ \D e16 \D b16 \D e16 ] \break | % 32
  \D cis16 [ \D e16 \D a,16 \D e'16 ] \D b16 [ \D e16 \D cis16 \D e16 ] \D d16
  \U e16 \D e16 \U e16 \D fis16 \U e16 \U a,16 \U e'16 | % 33
  \D e16 \U e16 \D fis16 \U e16 \D g16 \U e16 \U a,16 \U e'16 \D fis16 \U e16 \D
  g16 \U e16 \D a16 \U e16 \D fis16 \U e16 \break | % 34
  \D g16 \U e16 \D fis16 \U e16 \D g16 \U e16 \D e16 \U e16 \D fis16 \U e16 \D e16
  \U e16 \D fis16 \U e16 \D d16 \U e16 | % 35
  \D e16 \U e16 \D d16 \U e16 \D e16 \U e16 \D cis16 \U e16 \D d16 [ \D e16 \D
  cis16 \D e16 ] \D d16 [ \D e16 \D b16 \D e16 ] \break | % 36
  \D cis16 [ \D e16 \D a,16 \D b16 ] \U c16 [ \U a16 \U cis16 \U a16 ] \U d16 [
  \U a16 \U dis16 \U a16 ] \U e'16 [ \U a,16 \U f'16 \U a,16 ] | % 37
  \U fis'!16 [ \U a,16 \U g'!16 \U a,16 ] \U gis'16 [ \U a,16 \U a'16 \U a,16 ]
  \U bes'16 [ \U a,16 \U b'16 \U a,16 ] \U c'16 [ \U a,16 \U cis'16 \U a,16 ]
  \pageBreak | % 38
  \D d'16 [ \D fis,16 \D a,16 \D fis'16 ] \D d'16 [ \D fis,16 \D d'16 \D fis,16
  ] \D d'16 [ \D fis,16 \D a,16 \D fis'16 ] \D d'16 [ \D fis,16 \D d'16 \D fis,16
  ] | % 39

  \barNumberCheck #40
  \D d'16 [ \D e,16 \D a,16 \D e'16 ] \D d'16 [ \D e,16 \D d'16 \D e,16 ] \D d'16
  [ \D e,16 \D a,16 \D e'16 ] \D d'16 [ \D e,16 \D d'16 \D e,16 ] \break | % 40
  \D cis'16 [ \D g16 \D a,16 \D g'16 ] \D cis16 [ \D g16 \D cis16 \D g16 ] \D
  cis16 [ \D g16 \D a,16 \D g'16 ] \D cis16 [ \D g16 \D cis16 \D g16 ] | % 41
  \U <fis, a d>4 \D <d' fis d'>2 r4 \bar "|."
}


% The score definition
\score {
  <<
    \new Staff = "P1" <<
      \set Staff.instrumentName = "Violin"
      \set Staff.shortInstrumentName = "Vln."
      \context Staff <<
        \override Staff.BarLine.allow-span-bar = ##f
        \mergeDifferentlyDottedOn
        \mergeDifferentlyHeadedOn
        \context Voice = "PartPOneVoiceOne" {
          \PartPOneVoiceOne
        }
      >>
    >>
  >>
  \layout {}
  % To create MIDI output, uncomment the following line:
  % \midi { \tempo 4 = 72 }
}

