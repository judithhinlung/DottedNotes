import pytest
from dottednotes.bana_symbols import SymbolCategory
from dottednotes.models import Note, Chord, Duration, Fingering


def test_fingering_single_to_lilypond():
    f = Fingering(dots=frozenset([1]), category=SymbolCategory.FINGERING, raw_brl='⠁', finger=1)
    assert f.to_lilypond() == "-1"


def test_fingering_change_to_lilypond():
    f = Fingering(dots=frozenset([1, 4]), category=SymbolCategory.FINGERING, raw_brl='⠁⠉⠃', finger=1, change_to=2)
    assert f.to_lilypond() == "-1-2"


def test_fingering_alternative_to_lilypond():
    f = Fingering(dots=frozenset([1, 2]), category=SymbolCategory.FINGERING, raw_brl='⠁⠃', finger=1, alternative=2)
    assert f.to_lilypond() == '-\\markup \\center-column { "2" "1" }'


def test_fingering_alternative_with_first_omitted():
    f = Fingering(dots=frozenset([6, 2]), category=SymbolCategory.FINGERING, raw_brl='⠠⠃', first_omitted=True, alternative=2)
    assert f.to_lilypond() == '-\\markup \\center-column { "2" "" }'


def test_fingering_alternative_with_second_omitted():
    f = Fingering(dots=frozenset([1, 3]), category=SymbolCategory.FINGERING, raw_brl='⠁⠄', finger=1, second_omitted=True)
    assert f.to_lilypond() == '-\\markup \\center-column { "" "1" }'


def test_note_with_fingering_to_lilypond():
    dur = Duration(value=4)
    note = Note(
        dots=frozenset(),
        category=SymbolCategory.NOTE,
        raw_brl='⠹',
        note_name='C',
        octave=4,
        duration=dur,
    )
    f = Fingering(dots=frozenset([1]), category=SymbolCategory.FINGERING, raw_brl='⠁', finger=1)
    note.fingerings.append(f)
    assert note.to_lilypond() == "c'4-1"


def test_chord_with_fingering_to_lilypond():
    dur = Duration(value=4)
    n1 = Note(
        dots=frozenset(),
        category=SymbolCategory.NOTE,
        raw_brl='⠹',
        note_name='C',
        octave=4,
        duration=dur,
    )
    n1.fingerings.append(Fingering(dots=frozenset([1]), category=SymbolCategory.FINGERING, raw_brl='⠁', finger=1))
    
    n2 = Note(
        dots=frozenset(),
        category=SymbolCategory.NOTE,
        raw_brl='⠫',
        note_name='E',
        octave=4,
        duration=dur,
    )
    n2.fingerings.append(Fingering(dots=frozenset([2]), category=SymbolCategory.FINGERING, raw_brl='⠃', finger=2))
    
    chord = Chord(notes=[n1, n2])
    assert chord.to_lilypond() == "<c-1 e-2>4"
