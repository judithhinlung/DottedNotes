import pytest
from dottednotes.models.score import Score
from dottednotes.models.orchestra_score import OrchestraScore
from dottednotes.models.staff import Staff
from dottednotes.models.measure import Measure
from dottednotes.models.note import Note, Rest
from dottednotes.models.duration import Duration
from dottednotes.renderers.braille_renderer import BrailleRenderer, render_measure_slice, ensemble_abbrev_prefix, encode_literary_braille, abbrev_to_brl, wrap_run_over_line, pad_to_boundary, staff_abbreviation


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
    violin_prefix = '⠜' + abbrev_to_brl('vi')
    violin_line = next(l for l in lines if l.startswith(violin_prefix))
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
    # Each interior measure boundary is a fixed table column: the widest
    # rendering of that measure across staves, plus a 2-cell gap (BANA
    # 33.4) -- both staves render identically here, so that's just this
    # measure's own length + 2.
    for slice_str, digit in zip(slice_strs, ['⠁', '⠃']):
        assert heading_line[col + 1] == '⠼'
        assert heading_line[col + 2] == digit
        col += len(slice_str) + 2


def test_encode_literary_braille_double_capital_for_all_caps_word():
    # A whole word of 2+ uppercase letters takes the double capital sign
    # (dots 6,6) once, not a single capital sign before every letter.
    assert encode_literary_braille("II") == '⠠⠠⠊⠊⠲'
    assert encode_literary_braille("SATB Choir") == '⠠⠠⠎⠁⠞⠃⠀⠠⠉⠓⠕⠊⠗⠲'


def test_encode_literary_braille_single_capital_for_title_case_word():
    # A normally-capitalized (title case) word still gets one capital
    # sign before its single capitalized letter, not the double sign.
    assert encode_literary_braille("Song") == '⠠⠎⠕⠝⠛⠲'
    assert encode_literary_braille("Symphony No. II") == '⠠⠎⠽⠍⠏⠓⠕⠝⠽⠀⠠⠝⠕⠨⠀⠠⠠⠊⠊⠲'


def test_staff_abbreviation_resolves_plural_section_names_to_table_29():
    # BANA Table 29 keys are singular solo-instrument names ("Violin I",
    # "Viola", "Violoncello", "Double bass"), but real MusicXML part names
    # from orchestral scores are plural/section-style ("Violins I",
    # "Violas", "Violoncellos", "Double Basses"). Without singularizing,
    # all of these collapse to the same first-two-letters fallback
    # ("vi"), colliding with each other and losing Table 29's abbreviations
    # entirely.
    assert staff_abbreviation("Violins I") == "v1"
    assert staff_abbreviation("Violins II") == "v2"
    assert staff_abbreviation("Violas") == "vl"
    assert staff_abbreviation("Violoncellos") == "vc"
    assert staff_abbreviation("Double Basses") == "db"

    # Combined-instrument staff names (one staff notating two doubled
    # parts) are an explicit scope boundary -- BANA 33.2.2's combined-
    # numbering convention for these is out of scope here, so they must
    # keep falling through to the existing first-two-letters heuristic
    # unchanged, not accidentally match a singularization candidate.
    assert staff_abbreviation("Piccolo, Flutes I/II") == "pi"
    assert staff_abbreviation("Clarinets I/II in B-flat") == "cl"
    assert staff_abbreviation("Bassoons I/II") == "ba"
    assert staff_abbreviation("Horns in F I/II") == "ho"


def test_ensemble_cross_staff_measure_alignment_with_mismatched_content():
    # BANA 33.4: "the first signs of the measures are vertically aligned
    # in all parts" -- a resting staff's short measure must be padded to
    # match a busy staff's longer measure so the NEXT measure starts at
    # the same column in every part, and the heading numbers land
    # correctly relative to every staff, not just staff 0.
    #
    # Flute rests for measure 1 only (not the whole system) so it stays
    # *active* per BANA 33.1's tacet-staff omission and this test still
    # exercises cross-staff column alignment within one shared system --
    # a staff tacet for an entire system is dropped from it instead (see
    # test_ensemble_renderer_omits_staff_tacet_for_an_entire_system).
    score = OrchestraScore(title="Trio")

    flute = Staff(name="Flute")
    m1 = Measure(number=1)
    m1.add_note(Rest(dots=frozenset(), category=None, raw_brl="", duration=Duration(value=1, dots=0), is_full_measure=True))
    flute.add_measure(m1)
    m2 = Measure(number=2)
    m2.add_note(Note(dots=frozenset(), category=None, raw_brl="", note_name="C", octave=5, duration=Duration(value=1, dots=0)))
    flute.add_measure(m2)
    score.add_staff(flute)

    violin = Staff(name="Violin")
    for n, note_names in [(1, ["C", "D", "E", "F"]), (2, ["G", "A", "B", "C"])]:
        m = Measure(number=n)
        for note_name in note_names:
            m.add_note(Note(dots=frozenset(), category=None, raw_brl="", note_name=note_name, octave=5, duration=Duration(value=4, dots=0)))
        violin.add_measure(m)
    score.add_staff(violin)

    rendered = BrailleRenderer(line_width=40, compression_level="none").render(score)
    lines = rendered.splitlines()

    heading = next(l for l in lines if l.startswith('     ⠼'))
    flute_line = next(l for l in lines if l.startswith('⠜' + abbrev_to_brl('fl')))
    violin_line = next(l for l in lines if l.startswith('⠜' + abbrev_to_brl('vi')))

    # Both staves' second measure must start at the same column. Flute's
    # own measure-2 content starts with its octave mark (⠨, dot 4-6 --
    # the treble-octave-5 mark), located directly rather than assumed
    # from line length, since Flute is no longer a bare rest to the end.
    flute_m2_col = flute_line.index('⠨')
    violin_m2_col = violin_line.index('⠳')  # first note of measure 2 (G)
    assert flute_m2_col == violin_m2_col

    # The second measure's number sits one cell beyond that shared
    # column, landing on Violin's second note of measure 2 (not its
    # first, since there's no octave mark to skip there).
    assert heading[violin_m2_col + 1] == '⠼'
    assert violin_line[violin_m2_col + 1] == '⠪'  # A, the second note

    # BANA 33.4/Example 33.4.6-1: the shared column is exactly 2 cells
    # past the longest staff's own content for that measure -- like a
    # table column, not just "wide enough to fit". Violin is the longest
    # (Flute rests), so Violin's own gap before measure 2 is exactly 2
    # plain blank cells (well under the >6 guide-dot threshold).
    violin_m1_end = violin_m2_col - 2
    assert violin_line[violin_m1_end:violin_m2_col] == chr(0x2800) * 2


def test_ensemble_renderer_omits_staff_tacet_for_an_entire_system():
    # BANA 33.1: "each parallel contain[s] only the music of the
    # instruments that have music to play in those measures. An instrument
    # that has only rests in those measures is omitted from the parallel."
    # Flute rests for measures 1-2 entirely, then plays measures 3-4;
    # line_width=20 forces a system break right at that boundary (verified
    # by actually rendering the case), so Flute must be entirely absent
    # from the first system's staff_lines and reappear -- with its
    # abbreviation prefix restated -- in the second system.
    score = OrchestraScore(title="Test")

    flute = Staff(name="Flute")
    for n in [1, 2]:
        m = Measure(number=n)
        m.add_note(Rest(dots=frozenset(), category=None, raw_brl="", duration=Duration(value=1, dots=0), is_full_measure=True))
        flute.add_measure(m)
    for n in [3, 4]:
        m = Measure(number=n)
        m.add_note(Note(dots=frozenset(), category=None, raw_brl="", note_name="C", octave=5, duration=Duration(value=1, dots=0)))
        flute.add_measure(m)
    score.add_staff(flute)

    violin = Staff(name="Violin")
    for n in [1, 2, 3, 4]:
        m = Measure(number=n)
        for note_name in ["C", "D", "E", "F"]:
            m.add_note(Note(dots=frozenset(), category=None, raw_brl="", note_name=note_name, octave=5, duration=Duration(value=4, dots=0)))
        violin.add_measure(m)
    score.add_staff(violin)

    rendered = BrailleRenderer(line_width=20, compression_level="none").render(score)
    systems = rendered.split("\n\n")
    assert len(systems) == 2

    first_system_lines = systems[0].splitlines()
    flute_prefix = '⠜' + abbrev_to_brl('fl')
    violin_prefix = '⠜' + abbrev_to_brl('vi')
    assert not any(l.startswith(flute_prefix) for l in first_system_lines)
    assert any(l.startswith(violin_prefix) for l in first_system_lines)

    second_system_lines = systems[1].splitlines()
    assert any(l.startswith(flute_prefix) for l in second_system_lines)
    assert any(l.startswith(violin_prefix) for l in second_system_lines)


def test_ensemble_renderer_all_staves_tacet_falls_back_to_showing_everything():
    # A measure range where every staff is tacet simultaneously can't
    # happen in real orchestral music (nothing would be there to
    # transcribe), but `active_staff_indices` falls back to showing every
    # staff rather than producing an empty system if it ever does. A more
    # BANA-idiomatic single-line representation for a full-ensemble rest
    # (rather than each staff's rest repeated) is a possible future
    # improvement, not attempted here.
    score = OrchestraScore(title="All Rest")
    for name in ["Flute", "Violin"]:
        staff = Staff(name=name)
        for n in [1, 2]:
            m = Measure(number=n)
            m.add_note(Rest(dots=frozenset(), category=None, raw_brl="", duration=Duration(value=1, dots=0), is_full_measure=True))
            staff.add_measure(m)
        score.add_staff(staff)

    rendered = BrailleRenderer(line_width=40, compression_level="none").render(score)
    lines = rendered.splitlines()

    assert any(l.startswith('⠜' + abbrev_to_brl('fl')) for l in lines)
    assert any(l.startswith('⠜' + abbrev_to_brl('vi')) for l in lines)


def test_pad_to_boundary_uses_guide_dots_with_blanks_on_both_sides():
    # BANA 28.1.3/33.4/Example 33.4.6-1: a gap of more than 6 cells is
    # guide dots (dot 3), separated from this staff's own content by one
    # blank cell AND from the next measure by one blank cell -- not
    # flush against the following measure.
    padded = pad_to_boundary("⠍", width=10)
    assert padded[0] == '⠍'
    assert padded[1] == chr(0x2800)  # blank separating content from dots
    assert padded[2:-1] == '⠄' * 7   # 7 guide dots (minimum 5, BANA 28.1.3)
    assert padded[-1] == chr(0x2800)  # blank separating dots from what follows
    assert len(padded) == 10


def test_pad_to_boundary_uses_plain_blanks_for_a_small_gap():
    # A gap of 6 or fewer cells (e.g. the fixed 2-cell table-column gap
    # when a staff is already the widest) is plain blanks, not dots.
    assert pad_to_boundary("⠍", width=3) == "⠍" + chr(0x2800) * 2


def test_wrap_run_over_line_marks_continuation_with_music_hyphen():
    # BANA 1.11 (the music hyphen)/28.1.2/33.4.7: a line too long to fit
    # is cut with dot 5 directly abutting the last cell that fits (no
    # space before it), and the remainder continues on the next line
    # indented two cells, with no further indent growth on later lines.
    line = "⠜FL⠄" + "⠹" * 10
    wrapped = wrap_run_over_line(line, width=8)
    assert all(len(w) <= 8 for w in wrapped)
    assert "".join(w.rstrip('⠐').removeprefix("  ") for w in wrapped[:-1]) + wrapped[-1].removeprefix("  ") == line
    for w in wrapped[:-1]:
        assert w.endswith('⠐')
    assert not wrapped[-1].endswith('⠐')
    assert all(w.startswith("  ") for w in wrapped[1:])


def test_wrap_run_over_line_no_op_when_it_already_fits():
    assert wrap_run_over_line("⠜FL⠄⠹⠹", width=40) == ["⠜FL⠄⠹⠹"]


def test_ensemble_renderer_splits_overlong_measure_into_run_over_lines():
    # A single measure that's too dense to fit even alone (the "force 1
    # measure" fallback) must be split into run-over lines rather than
    # emitted as one line wider than line_width.
    score = OrchestraScore(title="Solo")
    staff = Staff(name="Flute")
    m = Measure(number=1)
    for i in range(30):
        # Alternate octaves so each note needs its own octave mark,
        # keeping the measure from compressing down to something that
        # already fits.
        octave = 5 if i % 2 == 0 else 6
        m.add_note(Note(dots=frozenset(), category=None, raw_brl="", note_name="C", octave=octave, duration=Duration(value=4, dots=0)))
    staff.add_measure(m)
    score.add_staff(staff)
    # A second staff so this routes through _render_ensemble, not _render_solo.
    other = Staff(name="Oboe")
    m2 = Measure(number=1)
    m2.add_note(Rest(dots=frozenset(), category=None, raw_brl="", duration=Duration(value=1, dots=0), is_full_measure=True))
    other.add_measure(m2)
    score.add_staff(other)

    rendered = BrailleRenderer(line_width=20, compression_level="none").render(score)
    lines = rendered.splitlines()
    assert all(len(l) <= 20 for l in lines)
    flute_lines = [l for l in lines if l.startswith('⠜' + abbrev_to_brl('fl')) or l.startswith("  ")]
    assert any(l.endswith('⠐') for l in flute_lines)
