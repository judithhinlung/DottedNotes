\version "2.24.4"

upper = \relative c'' { \clef treble
\key g \major
\time 3/4 \tempo "allegro moderato"
%1
<<{ g8.\mf b16 d4-. g4-.}\\{d,4\mf g4 g4}>> |
%2
<<{fis'8( e8) d8-. e8-. d8-.( c8-.)}\\{a4 b8-. c8-. b8-. a8-.}>> |
%3
<<{b8.( g16) e4-. c'8-. b8-.}\\{d,4 c4 e8 d8}>> |
%4
b'8.( g16) <b d,>4 <a d,>4 |
%5
<<{g8.\mp( a16) b4 e8-. d8-.}\\{d,4\mp d4 c'8-. b8-.}>> |
%6
<<{d8.( fis16) g4 b,8-.( c8-.)}\\{c4 b4 g8-. a8-.}>> |
%7
<b d,>8.( g16) e4 c'8-. b8-. |
%8
<a c,>8. <g c,>16 <g d>4 <fis c>4 |
%9
<g b,>2 fis8-. g8-. |
%10
<<{ \grace {a8(} g4\<) fis8-. g8-. a8-. b8-.\!}\\{d,4 d8-. e8-. fis8-. g8-.}>> |
%11
<<{\grace {c8(} b4) a8-. b8-. c8-. d8-.}\\{g,4 fis8-. g8-. a8-.b8-.}>> |
%12
<c e,>8(\> <b e,>8) <a e>8-. <g d>8-. <fis c>8-. <e b>8-. |
%13
<d a>2.\p |
%14
<<{\grace { b'8(} a4\<) gis8-. a8-. b8-. c8-.\!}\\{e,4 e8-. fis8-. gis8-. a8-.}>> |
%15
<<{\grace {d8(} c4) b8-. c8-. d8-. e8-.}\\{a,4 gis8-. a8-. b8-. c8-.}>> |
%16
g'8\f( e8) a8( a,8) e'8( a,8) |
%17
<d a fis>2 <cis g e>4 |
%18
<<{d8( fis8) g8( e8) fis4}\\{fis,4 g4 a4}>> |
%19
<<{fis'8( a8) b8( g8) a4-.}\\{a,4 b4 cis4}>> |
%20
<<{g'8( fis8) e8( d8) cis8( b8)}\\{b4 a4 g4}>> |
%21
<<{e'8( d8) cis8( b8) a8( d8)}\\{a4 g4 fis4}>> |
%22
<cis'\< g e>8 <d a fis>8 <e b g>8 <fis cis a>8 <g d b>4 |
%23
<a e cis>2. |
%24
d,,8.\mf fis16 a4 d4 |
%25
fis,8( a8) d8-. e8-. fis8-. g8-. |
%26
<<{g8(\> fis8) e8( d8) cis8( b8\!)}\\{b4 a4 g4}>> |
%27
a2.\p |
%28
<<{g8.\mf b16 d4-. g4-.}\\{d,4 g4 g4}>> |
%29
<<{fis'8(e8) d8-. e8-. d8-. c8-.}\\{a4 b8-. c8-. b8-. a8-.}>> |
%30
<<{b8.( g16) e4-. c'8-. b8-.}\\{d,4 c4 e8 d8}>> |
%31
b'8.( g16) <b d,>4 <a d,>4 |
%32
<<{g8.( a16) b4 e8-. d8-.}\\{d,4 d4 c'8-. b8-.}>> |
%33
<<{d8.( fis16) g4 b,8-.( c8-.)}\\{c4 b4 g8-. a8-.}>> |
%34
<b d,>8.( g16) e4 c'8-. b8-. |
%35
<a c,>8. <g c,>16 <g d>4 <fis c>4 |
%36
<g d b>2 <e b g>4\p |
%37
c8. e16 g4 f4 |
%38
f8-. a8-. c8-. f,8-. e8-. f8-. |
%39
a8\< b8 c8 d8 e8 fis8 |
%40
<g d b>4\f <g e c>4 <fis d a>4 |
%41
<b, g>8\dim( d8) <g b,>8( b8) < d g,>8( g8\!) \bar "|." |
} 
lower = \relative c { \clef bass
\key g \major \time 3/4
%1
b'4\mf b4 e,4 |
%2
c4 g'8( e8) g8( fis8) |
%3
b,4 c4 g'8 g8 |
%4
d4 g4 fis4 |
%5
g4\mp g4 c,8-. d8-. |
%7
fis4 g4 d'8-. c8-. |
%7
g4 c4 e8-. d8-. |
%8
d,4 d4 a'4 |
%9
g2 d4 |
%10
d,4\< a'8-. g8-. fis8-. d8-. |
%11
g4 c8-. b8-. a8-. g8-. |
%12
c4\> d8-. e8-. fis8-. g8-. |
%13
fis8-.\p e8-. d8-. c8-. b8-. a8-. |
%14
e4\< b'8-. a8-. gis8-. e8-. |
%15
b'4 e8-. d8-. cis8-. a8-. |
%16
<cis e a>4\f <cis g' a>4 <a e' a>4 |
%17
d4 d'4 a4 |
%18
r4 a4 fis8( d8) |
%19
r4 g4 e'8( a,8) |
%20
r4 a2~ |
%21
a4 a4 fis8( d8) |
%22
g8.\< fis16 e8 fis8 e4 |
%23
a8 a,8 cis8 e8 a8 b8 |
%24
a8.\mf( fis16) d4 fis4 |
%25
a4 fis8-. g8-. a8-. b8-. |
%26
g'4--\> g,4-- a4-- |
%27
fis8-.\p e8-. d8-. c8-.b8-. a8-. |
%28
b4\mf b4 e,4 |
%29
c'4 g'8( e8) g8( fis8) |
%30
b,4 c4 g'8 g8 |
%31
d4 g4 fis4 |
%32
g4 g4 c,8-. d8-. |
%33
fis4 g4 d'8-. c8-. |
%34
g4 c4 e8-. d8-. |
%35
d,4 d4 a'4 |
%36
g2 <e, e'>4 |
%37
<a g'>8. a16 <a g'>4 <g d' f>4 |
%38
<g d' f>4 <g c f>4 <g b f'>4 |
%39
<g d'>2.\< |
%40
<g d'>4 <e e'>4 <d d'>4 |
%41
<g d'>2.\! \bar "|." |
}
\score {
\new PianoStaff \with { instrumentName = "Piano" midiInstrument = "acoustic grand" } <<
\new Staff = "upper" \upper
\new Staff = "lower" \lower >>
\layout { }
\midi { } }
