import pytest
from dottednotes.models.note import Note, Rest
from dottednotes.models.chord import Chord
from dottednotes.models.in_accord import InAccord
from dottednotes.models.measure import Measure
from dottednotes.models.duration import Duration
from dottednotes.models.articulation import Articulation, ArticulationType
from dottednotes.models.text_marking import TextMarking, TextMarkingType
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


def test_musical_equals_in_accord_ignores_notation_only_field():
    # Identical pitches/durations across both parts, differing only in a
    # notation-only field (articulation_format, set by the rendering-time
    # carry-shorthand pass) -- must still be musically equal, unlike
    # Python's default dataclass == (the bug this method fixes).
    def make_note(art_format="single"):
        n = Note(dots=frozenset(), category=None, raw_brl="", note_name="C", octave=4, duration=Duration(4))
        n.articulation_format = art_format
        return n

    ia1 = InAccord(parts=[[make_note("single")], [make_note("single")]])
    ia2 = InAccord(parts=[[make_note("start_carry")], [make_note("single")]])

    assert ia1 != ia2  # default dataclass == sees the difference
    assert ia1.musical_equals(ia2)  # musical_equals doesn't


def test_musical_equals_in_accord_detects_real_pitch_difference():
    n_c = Note(dots=frozenset(), category=None, raw_brl="", note_name="C", octave=4, duration=Duration(4))
    n_d = Note(dots=frozenset(), category=None, raw_brl="", note_name="D", octave=4, duration=Duration(4))

    ia1 = InAccord(parts=[[n_c], [n_c]])
    ia2 = InAccord(parts=[[n_d], [n_c]])

    assert not ia1.musical_equals(ia2)


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


def test_solo_margin_measure_number_carries_number_sign():
    # BANA 24.1.1 (Example 24.1.1-1: "#A", "#E'"): a single-line solo
    # margin measure number carries the number sign (⠼), unlike a keyboard
    # bar-over-bar parallel's margin number (BANA 29.3(b): "given without
    # the numeric indicator").
    brf = "⠐⠹⠱⠀⠹⠱"
    score = parse_brf(brf)
    renderer = BrailleRenderer(line_width=40, show_measure_numbers=True)
    output = renderer.render(score)
    assert output.startswith("⠼⠁ ")


def test_octave_mark_forced_after_leading_rest_starting_a_new_braille_line():
    # BANA 3.2.1: "The octave is always marked for the first note of a
    # braille line." Measure 2 opens with a rest, then D4 -> E4 is a step
    # (BANA 3.2.2(a) would normally omit the mark) -- but forcing a narrow
    # line_width pushes measure 2 onto its own braille line, so E still
    # needs a fresh octave mark despite the leading rest and the small
    # melodic interval.
    brf = "⠐⠹⠱⠀⠧⠫"  # M1: C4 D4 | M2: rest, E (no mark needed by interval alone)
    score = parse_brf(brf)
    renderer = BrailleRenderer(line_width=8, show_measure_numbers=True)
    lines = renderer.render(score).strip("\n").split("\n")
    assert len(lines) == 2
    # Line 2: measure-number prefix, rest, then a forced octave mark (⠐)
    # before E (⠫) -- not "⠧⠫" with no mark.
    assert lines[1].endswith("⠧⠐⠫⠀")


def test_word_sign_expression_precedes_mid_piece_text_marking():
    # BANA 22.3: a mid-piece word-sign expression is introduced by the word
    # sign (⠜) and, per 22.3(b), is brailled without capitalization
    # regardless of print casing.
    marking = TextMarking(text="Dolce", type=TextMarkingType.EXPRESSION)
    brl = marking.to_braille(inline=True)
    assert brl.startswith("⠜")
    assert "⠠" not in brl  # no capital indicator -- 22.3(b)


def test_measure_with_text_marking_forces_octave_mark_and_end_word_sign():
    # BANA 3.2.1: the first note following a word sign always needs an
    # octave mark, regardless of is_measure_start or melodic interval.
    # BANA 22.3(d): the word-sign expression must be followed by dot 3
    # when the next sign contains dots 1/2/3 -- here a rest (⠧, dots
    # 1,2,3,6), so the separator is required.
    m = Measure(number=1)
    m.text_markings = [TextMarking(text="rit.", type=TextMarkingType.EXPRESSION)]
    m.add_note(Rest(dots=frozenset(), category=None, raw_brl="", duration=Duration(4)))
    m.add_note(Note(dots=frozenset(), category=None, raw_brl="", note_name="E", octave=4, duration=Duration(4)))
    brl, _ = m.to_braille(is_measure_start=False)
    # ⠜ + lowercase "rit" (period stripped, no capital indicator) + dot-3
    # separator (⠄) before the rest, then the rest, then a forced octave
    # mark before E.
    assert brl.startswith("⠜⠗⠊⠞⠄⠧⠐⠫")
