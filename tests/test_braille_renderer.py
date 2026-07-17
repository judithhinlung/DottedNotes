import pytest
from dottednotes.models.score import Score
from dottednotes.models.orchestra_score import OrchestraScore
from dottednotes.models.staff import Staff
from dottednotes.models.measure import Measure
from dottednotes.models.note import Note, Rest
from dottednotes.models.duration import Duration
from dottednotes.renderers.braille_renderer import BrailleRenderer, render_measure_slice, ensemble_abbrev_prefix


def test_solo_renderer():
    score = Score(title="Solo Piece")
    staff = Staff(name="Flute")
    m = Measure(number=1)
    # Add a C4 quarter note
    m.add_note(Note(dots=frozenset(), category=None, raw_brl="", note_name="C", octave=4, duration=Duration(value=4, dots=0)))
    staff.add_measure(m)
    score.add_staff(staff)

    renderer = BrailleRenderer(line_width=40)
    output = renderer.render(score)
    # Check that it contains title and measure 1
    # Title "Solo Piece" -> '⠠⠎⠕⠇⠕⠀⠠⠏⠊⠑⠉⠑⠲'
    assert '⠠⠎⠕⠇⠕⠀⠠⠏⠊⠑⠉⠑⠲' in output
    assert '⠁ ⠐⠹' in output


def test_piano_renderer():
    score = Score(title="Piano Piece")
    # Piano staves
    rh = Staff(name="Piano right hand")
    lh = Staff(name="Piano left hand")
    
    m1 = Measure(number=1)
    m1.add_note(Note(dots=frozenset(), category=None, raw_brl="", note_name="C", octave=4, duration=Duration(value=4, dots=0)))
    rh.add_measure(m1)
    
    m2 = Measure(number=1)
    m2.add_note(Note(dots=frozenset(), category=None, raw_brl="", note_name="C", octave=3, duration=Duration(value=4, dots=0)))
    lh.add_measure(m2)
    
    score.add_staff(rh)
    score.add_staff(lh)

    renderer = BrailleRenderer(line_width=40)
    output = renderer.render(score)
    # RH line: starts with '⠁ ' (measure 1 prefix) followed by RH hand sign '⠨⠜' and note
    assert '⠁ ⠨⠜⠐⠹' in output
    # LH line: starts with spaces, followed by LH hand sign '⠸⠜' and note
    # Prefix '⠁ ' is 2 chars, so LH line starts with 2 spaces
    assert '  ⠸⠜⠸⠹' in output


def test_orchestra_score_with_two_piano_staves_uses_piano_layout():
    # Regression test: a 2-staff OrchestraScore (as produced by LilypondParser
    # for any PianoStaff-containing input) must still get the piano hand-sign
    # layout, not the ensemble instrument-list layout.
    score = OrchestraScore(title="Piano Piece")
    rh = Staff(name="Piano right hand")
    lh = Staff(name="Piano left hand")

    m1 = Measure(number=1)
    m1.add_note(Note(dots=frozenset(), category=None, raw_brl="", note_name="C", octave=4, duration=Duration(value=4, dots=0)))
    rh.add_measure(m1)

    m2 = Measure(number=1)
    m2.add_note(Note(dots=frozenset(), category=None, raw_brl="", note_name="C", octave=3, duration=Duration(value=4, dots=0)))
    lh.add_measure(m2)

    score.add_staff(rh)
    score.add_staff(lh)

    renderer = BrailleRenderer(line_width=40)
    output = renderer.render(score)
    assert '⠁ ⠨⠜⠐⠹' in output
    assert '  ⠸⠜⠸⠹' in output


def test_orchestra_score_with_three_staves_uses_ensemble_layout():
    score = OrchestraScore(title="Trio")
    staves = []
    for name, note_name, octave in [("Violin", "C", 5), ("Viola", "G", 4), ("Cello", "C", 3)]:
        s = Staff(name=name)
        m = Measure(number=1)
        m.add_note(Note(dots=frozenset(), category=None, raw_brl="", note_name=note_name, octave=octave, duration=Duration(value=4, dots=0)))
        s.add_measure(m)
        staves.append(s)
        score.add_staff(s)

    renderer = BrailleRenderer(line_width=40)
    output = renderer.render(score)
    # Ensemble layout does not use the piano hand-sign prefixes.
    assert '⠨⠜' not in output
    assert '⠸⠜' not in output


def test_renderer_with_measure_numbers_turned_off():
    # 1. Solo layout
    score = Score(title="Solo Piece")
    staff = Staff(name="Flute")
    m = Measure(number=1)
    m.add_note(Note(dots=frozenset(), category=None, raw_brl="", note_name="C", octave=4, duration=Duration(value=4, dots=0)))
    staff.add_measure(m)
    score.add_staff(staff)

    renderer = BrailleRenderer(line_width=40, show_measure_numbers=False)
    output = renderer.render(score)
    assert '⠁ ' not in output  # No measure number prefix at start of line
    assert '⠐⠹' in output

    # 2. Piano layout
    score_piano = Score(title="Piano Piece")
    rh = Staff(name="Piano right hand")
    lh = Staff(name="Piano left hand")
    
    m1 = Measure(number=1)
    m1.add_note(Note(dots=frozenset(), category=None, raw_brl="", note_name="C", octave=4, duration=Duration(value=4, dots=0)))
    rh.add_measure(m1)
    
    m2 = Measure(number=1)
    m2.add_note(Note(dots=frozenset(), category=None, raw_brl="", note_name="C", octave=3, duration=Duration(value=4, dots=0)))
    lh.add_measure(m2)
    
    score_piano.add_staff(rh)
    score_piano.add_staff(lh)
    
    renderer_piano = BrailleRenderer(line_width=40, show_measure_numbers=False)
    output_piano = renderer_piano.render(score_piano)
    # Piano lines should start with hand signs directly without measure numbers/spaces prefix
    assert output_piano.splitlines()[-2] == '⠨⠜⠐⠹⠀'
    assert output_piano.splitlines()[-1] == '⠸⠜⠸⠹⠀'

    # 3. Ensemble layout
    score_ens = OrchestraScore(title="Trio")
    for name, note_name, octave in [("Violin", "C", 5), ("Viola", "G", 4), ("Cello", "C", 3)]:
        s = Staff(name=name)
        m = Measure(number=1)
        m.add_note(Note(dots=frozenset(), category=None, raw_brl="", note_name=note_name, octave=octave, duration=Duration(value=4, dots=0)))
        s.add_measure(m)
        score_ens.add_staff(s)

    renderer_ens = BrailleRenderer(line_width=40, show_measure_numbers=False)
    output_ens = renderer_ens.render(score_ens)
    assert '⠼' not in output_ens  # Heading line/numbers should be absent entirely


def test_ensemble_renderer_measure_numbers_alignment():
    score = OrchestraScore(title="Trio")
    
    # We want 2 measures to fit on the same line to test alignment of the second measure number
    s1 = Staff(name="Violin")
    m1 = Measure(number=1)
    m1.add_note(Note(dots=frozenset(), category=None, raw_brl="", note_name="C", octave=5, duration=Duration(value=4, dots=0)))
    s1.add_measure(m1)
    m2 = Measure(number=2)
    m2.add_note(Note(dots=frozenset(), category=None, raw_brl="", note_name="C", octave=5, duration=Duration(value=4, dots=0)))
    s1.add_measure(m2)
    score.add_staff(s1)
    
    s2 = Staff(name="Viola")
    m3 = Measure(number=1)
    m3.add_note(Note(dots=frozenset(), category=None, raw_brl="", note_name="G", octave=4, duration=Duration(value=4, dots=0)))
    s2.add_measure(m3)
    m4 = Measure(number=2)
    m4.add_note(Note(dots=frozenset(), category=None, raw_brl="", note_name="G", octave=4, duration=Duration(value=4, dots=0)))
    s2.add_measure(m4)
    score.add_staff(s2)
    
    renderer = BrailleRenderer(line_width=40, show_measure_numbers=True, compression_level="none")
    output = renderer.render(score)
    lines = output.splitlines()

    # Heading line immediately precedes the top (Violin) staff line.
    violin_line = next(l for l in lines if l.startswith('⠜VI'))
    heading_line = lines[lines.index(violin_line) - 1]

    # Recompute each measure's own start column from the same building
    # blocks the renderer uses for the staff line itself, rather than
    # hardcoding braille cell lengths. Per BANA 33.4.6, the marking sits
    # "one cell beyond the first music signs" of each measure -- i.e. one
    # column past where the measure's own content starts, not directly
    # above it (so a leading octave mark gets skipped, landing on the
    # note; with no octave mark, the offset still applies).
    slice_strs, _ = render_measure_slice(s1.measures, 0, len(s1.measures), None, s1.time_signature, "none")
    music_str = "".join(slice_strs)
    col = len(ensemble_abbrev_prefix(s1.name, music_str))
    for slice_str, digit in zip(slice_strs, ['⠁', '⠃']):
        assert heading_line[col + 1] == '⠼'
        assert heading_line[col + 2] == digit
        col += len(slice_str)
