import pytest
from dottednotes.models.note import Note, Rest
from dottednotes.models.chord import Chord
from dottednotes.models.measure import Measure
from dottednotes.models.duration import Duration
from dottednotes.models.articulation import Articulation, ArticulationType
from dottednotes.renderers.braille_renderer import BrailleRenderer
from dottednotes.parser.braille_parser import BrailleParser
from dottednotes.parser.tokenizer import BrailleTokenizer
from dottednotes.models.score import Score


def parse_brf(brf_text: str) -> Score:
    tokens = BrailleTokenizer().tokenize(brf_text)
    return BrailleParser(tokens=tokens).parse()


def test_musical_equals_note():
    n1 = Note(dots=frozenset(), category=None, raw_brl="", note_name="C", octave=4, duration=Duration(4))
    n2 = Note(dots=frozenset(), category=None, raw_brl="", note_name="C", octave=4, duration=Duration(4))
    n3 = Note(dots=frozenset(), category=None, raw_brl="", note_name="D", octave=4, duration=Duration(4))

    assert n1.musical_equals(n2)
    assert not n1.musical_equals(n3)


def test_musical_equals_rest():
    r1 = Rest(dots=frozenset(), category=None, raw_brl="", duration=Duration(4))
    r2 = Rest(dots=frozenset(), category=None, raw_brl="", duration=Duration(4))
    r3 = Rest(dots=frozenset(), category=None, raw_brl="", duration=Duration(8))

    assert r1.musical_equals(r2)
    assert not r1.musical_equals(r3)


def test_musical_equals_note_ignores_articulation_explicit_flag():
    # Same pitch/duration/articulation type, differing only in whether the
    # articulation was written explicitly vs. carried from parser state --
    # that's notation-only bookkeeping, not a musical difference, so it must
    # not affect musical_equals() (used for measure-repeat compression).
    n1 = Note(
        dots=frozenset(), category=None, raw_brl="", note_name="C", octave=4,
        duration=Duration(4),
        articulations=[Articulation(type=ArticulationType.STACCATO, explicit=True)],
    )
    n2 = Note(
        dots=frozenset(), category=None, raw_brl="", note_name="C", octave=4,
        duration=Duration(4),
        articulations=[Articulation(type=ArticulationType.STACCATO, explicit=False)],
    )

    assert n1.musical_equals(n2)


def test_musical_equals_chord():
    n1 = Note(dots=frozenset(), category=None, raw_brl="", note_name="C", octave=4, duration=Duration(4))
    n2 = Note(dots=frozenset(), category=None, raw_brl="", note_name="E", octave=4, duration=Duration(4))
    c1 = Chord(notes=[n1, n2])
    c2 = Chord(notes=[n1, n2])
    c3 = Chord(notes=[n1])

    assert c1.musical_equals(c2)
    assert not c1.musical_equals(c3)


def test_musical_equals_measure():
    n1 = Note(dots=frozenset(), category=None, raw_brl="", note_name="C", octave=4, duration=Duration(4))
    m1 = Measure(number=1)
    m1.add_note(n1)

    m2 = Measure(number=2)
    m2.add_note(n1)

    m3 = Measure(number=3)
    m3.add_note(Rest(dots=frozenset(), category=None, raw_brl="", duration=Duration(4)))

    assert m1.musical_equals(m2)
    assert not m1.musical_equals(m3)


def test_compression_none():
    # In 'none' compression:
    # - Articulation runs should NOT use carry shorthand (they are rendered individually).
    # - Repeated measures should NOT be compressed to measure repeat signs.
    brf = "⠦⠹⠦⠹⠦⠹⠦⠹"  # Run of 4 staccato notes
    score = parse_brf(brf)
    renderer = BrailleRenderer(compression_level="none")
    output = renderer.render(score)
    # Since compression_level is none, every note should explicitly output staccato '⠦'.
    # In BRL, staccato prefix is ⠦, so we should see ⠦ 4 times in the output.
    assert output.count("⠦") == 4

    # Repeated measures:
    # ⠐⠹⠀⠐⠹ (Measure 1 then Measure 2 identical)
    brf = "⠐⠹⠀⠐⠹"
    score = parse_brf(brf)
    output = renderer.render(score)
    # Output should contain ⠹ twice, rather than a repeat cell ⠶.
    assert output.count("⠹") == 2
    assert "⠶" not in output


def test_compression_minimal():
    # In 'minimal' compression:
    # - Articulation runs use carry shorthand.
    # - Repeated measures use measure repeat signs.
    brf = "⠦⠹⠦⠹⠦⠹⠦⠹"
    score = parse_brf(brf)
    renderer = BrailleRenderer(compression_level="minimal")
    output = renderer.render(score)
    # Run of 4 staccato notes should be compressed using carry:
    # Note 1: ⠦⠦ (start carry, doubled)
    # Note 2, 3: staccato omitted
    # Note 4: ⠦ (stop carry -- plain sign, same as an unshortened note)
    assert output.count("⠦⠦") == 1
    # ⠘⠦ is a distinct, real BANA symbol (expressive_accent) -- it must never
    # appear here, since that would mean the carry-terminating note was
    # misrendered as an accent instead of a plain staccato.
    assert "⠘⠦" not in output
    assert output.count("⠦") == 3  # doubled start (2) + omitted middles (0) + plain stop (1)

    # Repeated measures:
    brf = "⠐⠹⠀⠐⠹"
    score = parse_brf(brf)
    output = renderer.render(score)
    # Measure 2 should be replaced by measure repeat sign '⠶'.
    assert "⠶" in output
