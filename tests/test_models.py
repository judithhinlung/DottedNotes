import pytest

from dottednotes.bana_symbols import SymbolCategory
from dottednotes.models import (
    Accidental,
    AccidentalType,
    Articulation,
    ArticulationType,
    BrailleSymbol,
    Clef,
    ClefType,
    CLEF_TO_LILYPOND,
    BreathMark,
    BreathMarkVariant,
    Duration,
    Dynamic,
    DynamicLevel,
    Fermata,
    FermataShape,
    GraceNote,
    KEY_TO_LILYPOND,
    KeySignature,
    Measure,
    Note,
    Ornament,
    OrnamentType,
    ORNAMENT_TO_LILYPOND,
    Rest,
    Score,
    Staff,
    TimeSignature,
    VALID_DENOMINATORS,
)


def test_braille_symbol_requires_to_lilypond():
    """BrailleSymbol subclasses must implement to_lilypond."""
    import pytest

    sym = BrailleSymbol(
        dots=frozenset([1, 2]),
        category=SymbolCategory.NOTE,
        raw_brl='⠃'
    )
    with pytest.raises(NotImplementedError):
        sym.to_lilypond()


def test_braille_symbol_repr():
    sym = BrailleSymbol(
        dots=frozenset([1, 2]),
        category=SymbolCategory.NOTE,
        raw_brl='⠃'
    )
    assert repr(sym) == "BrailleSymbol(dots=frozenset({1, 2}), category=NOTE)"


def test_duration_to_lilypond():
    assert Duration(4).to_lilypond() == "4"
    assert Duration(4, dots=1).to_lilypond() == "4."
    assert Duration(8, dots=2).to_lilypond() == "8.."
    assert Duration(1).to_lilypond() == "1"


def test_duration_to_lilypond_all_valid_values():
    for value in [1, 2, 4, 8, 16, 32, 64]:
        assert Duration(value).to_lilypond() == str(value)
    assert Duration(0).to_lilypond() == r"\breve"


def test_double_dotted_half():
    assert Duration(value=2, dots=2).to_lilypond() == "2.."


def test_invalid_duration_value_raises():
    import pytest
    with pytest.raises(ValueError):
        Duration(value=3)


def test_breve_duration():
    d = Duration(value=0)
    assert d.to_lilypond() == r"\breve"
    assert d.duration_in_ticks() == 192
    
    d_dotted = Duration(value=0, dots=1)
    assert d_dotted.to_lilypond() == r"\breve."
    assert d_dotted.duration_in_ticks() == 288


def test_invalid_dot_count_raises():
    # BANA Par. 2.3 has no cap on dot count (S10d-9) -- only a negative
    # count is actually invalid.
    import pytest
    with pytest.raises(ValueError):
        Duration(value=4, dots=-1)


def test_duration_in_ticks_quarter():
    assert Duration(value=4).duration_in_ticks() == 24


def test_duration_in_ticks_dotted_quarter():
    assert Duration(value=4, dots=1).duration_in_ticks() == 36


def test_duration_in_ticks_half():
    assert Duration(value=2).duration_in_ticks() == 48


def test_duration_in_ticks_whole():
    assert Duration(value=1).duration_in_ticks() == 96


def test_duration_in_ticks_eighth():
    assert Duration(value=8).duration_in_ticks() == 12


def test_duration_in_ticks_double_dotted():
    assert Duration(value=4, dots=2).duration_in_ticks() == 42


def test_duration_in_ticks_sixteenth():
    assert Duration(value=16).duration_in_ticks() == 6


def test_duration_in_ticks_triplet_eighth():
    assert Duration(value=8, is_triplet=True).duration_in_ticks() == 8


def test_duration_in_ticks_triplet_quarter():
    assert Duration(value=4, is_triplet=True).duration_in_ticks() == 16


def test_duration_in_ticks_triplet_sixteenth():
    assert Duration(value=16, is_triplet=True).duration_in_ticks() == 4


# --- Arbitrary tuplet ratios (S10d-4, BANA 8.5) ---

def test_duration_in_ticks_quintuplet_ratio():
    # 5 eighth notes in the time of 4 eighth notes (4/5 scale).
    assert Duration(value=8, tuplet_ratio=(5, 4)).duration_in_ticks() == 9

def test_duration_in_ticks_septuplet_ratio():
    # 7 sixteenth notes in the time of 4 sixteenth notes (4/7 scale);
    # verifies exact integer math for a ratio TICKS_PER_QUARTER (24)
    # divides cleanly for this specific value/ratio combination.
    assert Duration(value=16, tuplet_ratio=(7, 4)).duration_in_ticks() == \
        Duration(value=16).duration_in_ticks() * 4 // 7

def test_duration_tuplet_ratio_takes_priority_over_is_triplet():
    # If both were somehow set, tuplet_ratio (the exact value) wins over
    # the hardcoded 2/3 triplet shortcut.
    d = Duration(value=8, is_triplet=True, tuplet_ratio=(5, 4))
    assert d.duration_in_ticks() == Duration(value=8, tuplet_ratio=(5, 4)).duration_in_ticks()


# --- Note values finer than 64th and 3+ augmentation dots (S10d-9) ---

def test_duration_128th_note_is_valid():
    d = Duration(value=128)
    assert d.to_lilypond() == "128"

def test_duration_three_dots():
    # BANA Par. 2.3: "the same number of dot 3s are given in the braille"
    # -- no cap at 2.
    d = Duration(value=4, dots=3)
    assert d.to_lilypond() == "4..."
    # A quarter note is 24 ticks; 3 dots scale by (2^4 - 1)/2^3 = 15/8,
    # so 24 * 15 // 8 = 45.
    assert d.duration_in_ticks() == 45

def test_duration_four_dots_on_breve():
    d = Duration(value=0, dots=4)
    assert d.to_lilypond() == r"\breve...."

def test_duration_128th_note_does_not_vanish_from_beat_count():
    # TICKS_PER_QUARTER (24) cannot exactly represent a 128th note (24*4/128
    # = 0.75) -- this must clamp to a minimum of 1 tick, not truncate to 0
    # and silently disappear from beat-accounting (S10d-9).
    assert Duration(value=128).duration_in_ticks() > 0

def test_duration_dots_formula_matches_previous_hardcoded_cases():
    # Regression guard: the general formula must reproduce the exact
    # values the old hardcoded 0/1/2 branches gave.
    assert Duration(value=8, dots=0).duration_in_ticks() == 12
    assert Duration(value=8, dots=1).duration_in_ticks() == 18
    assert Duration(value=8, dots=2).duration_in_ticks() == 21


def _make_note(note_name, octave, duration_value, dots=0, accidental=None, articulations=None,
               ornaments=None, fermata=None, breath_mark=None):
    return Note(
        dots=frozenset(),
        category=SymbolCategory.NOTE,
        raw_brl='⠀',
        note_name=note_name,
        octave=octave,
        duration=Duration(value=duration_value, dots=dots),
        accidental=accidental,
        articulations=articulations or [],
        ornaments=ornaments or [],
        fermata=fermata,
        breath_mark=breath_mark,
    )


def test_middle_c_quarter():
    note = _make_note('C', 4, 4)
    assert note.to_lilypond() == "c'4"


def test_b_flat_half_note():
    note = _make_note('B', 4, 2, accidental=Accidental(dots=frozenset(), category=SymbolCategory.ACCIDENTAL, raw_brl='⠣', type=AccidentalType.FLAT))
    assert note.to_lilypond() == "bes'2"


def test_f_sharp_eighth():
    note = _make_note('F', 5, 8, accidental=Accidental(dots=frozenset(), category=SymbolCategory.ACCIDENTAL, raw_brl='⠩', type=AccidentalType.SHARP))
    assert note.to_lilypond() == "fis''8"


def test_all_natural_note_names():
    expected = {
        'C': 'c', 'D': 'd', 'E': 'e', 'F': 'f',
        'G': 'g', 'A': 'a', 'B': 'b',
    }
    for name, ly in expected.items():
        note = _make_note(name, 4, 4)
        assert note.to_lilypond().startswith(ly), f"{name} should produce {ly}..."


def test_octave_marks_all_octaves():
    expected_marks = {
        1: "c,,4", 2: "c,4", 3: "c4", 4: "c'4",
        5: "c''4", 6: "c'''4", 7: "c''''4",
    }
    for octave, expected in expected_marks.items():
        note = _make_note('C', octave, 4)
        assert note.to_lilypond() == expected, f"octave {octave}: expected {expected!r}"


def test_dotted_quarter_note():
    note = _make_note('G', 4, 4, dots=1)
    assert note.to_lilypond() == "g'4."


def test_note_with_staccato():
    art = Articulation(ArticulationType.STACCATO)
    note = _make_note('D', 4, 4, articulations=[art])
    assert note.to_lilypond() == "d'4-."


def test_note_with_dynamic_p():
    note = Note(
        dots=frozenset(), category=SymbolCategory.NOTE, raw_brl='⠹',
        note_name='C', octave=4, duration=Duration(value=4),
        dynamics=[Dynamic(DynamicLevel.P)],
    )
    assert note.to_lilypond() == r"c'4\p"


def test_note_articulation_before_dynamic():
    # In LilyPond, articulations are written before dynamics.
    note = Note(
        dots=frozenset(), category=SymbolCategory.NOTE, raw_brl='⠹',
        note_name='C', octave=4, duration=Duration(value=4),
        dynamics=[Dynamic(DynamicLevel.F)],
        articulations=[Articulation(ArticulationType.STACCATO)],
    )
    assert note.to_lilypond() == r"c'4-.\f"


def test_note_with_crescendo_start():
    note = Note(
        dots=frozenset(), category=SymbolCategory.NOTE, raw_brl='⠹',
        note_name='G', octave=4, duration=Duration(value=4),
        dynamics=[Dynamic(DynamicLevel.CRESCENDO_START)],
    )
    assert note.to_lilypond() == r"g'4\<"


def test_note_with_crescendo_end():
    note = Note(
        dots=frozenset(), category=SymbolCategory.NOTE, raw_brl='⠹',
        note_name='G', octave=4, duration=Duration(value=4),
        dynamics=[Dynamic(DynamicLevel.CRESCENDO_END)],
    )
    assert note.to_lilypond() == r"g'4\!"


# ---------------------------------------------------------------------------
# S4-3: Note tie / slur / phrase-slur fields and LilyPond rendering
# ---------------------------------------------------------------------------

def test_note_with_tie():
    note = Note(
        dots=frozenset(), category=SymbolCategory.NOTE, raw_brl='',
        note_name='C', octave=4, duration=Duration(value=4), tie=True,
    )
    assert note.to_lilypond() == "c'4~"


def test_note_with_slur_start():
    note = Note(
        dots=frozenset(), category=SymbolCategory.NOTE, raw_brl='',
        note_name='C', octave=4, duration=Duration(value=4), slur_start=True,
    )
    assert note.to_lilypond() == "c'4("


def test_note_with_slur_end():
    note = Note(
        dots=frozenset(), category=SymbolCategory.NOTE, raw_brl='',
        note_name='G', octave=4, duration=Duration(value=4), slur_end=True,
    )
    assert note.to_lilypond() == "g'4)"


def test_note_with_slur_bracket_open_mark():
    note = Note(
        dots=frozenset(), category=SymbolCategory.NOTE, raw_brl='',
        note_name='F', octave=4, duration=Duration(value=4), slur_bracket_open=True,
    )
    assert note.to_lilypond() == r"f'4\("


def test_note_with_slur_bracket_close():
    note = Note(
        dots=frozenset(), category=SymbolCategory.NOTE, raw_brl='',
        note_name='F', octave=4, duration=Duration(value=8), slur_bracket_close=True,
    )
    assert note.to_lilypond() == r"f'8\)"


def test_note_articulation_before_tie():
    note = Note(
        dots=frozenset(), category=SymbolCategory.NOTE, raw_brl='',
        note_name='C', octave=4, duration=Duration(value=4),
        articulations=[Articulation(type=ArticulationType.STACCATO)],
        tie=True,
    )
    assert note.to_lilypond() == "c'4-.~"


def test_note_no_slur_marks_by_default():
    note = _make_note('C', 4, 4)
    ly = note.to_lilypond()
    assert '~' not in ly
    assert '(' not in ly
    assert ')' not in ly


def test_invalid_note_name_raises():
    import pytest
    with pytest.raises(ValueError):
        _make_note('H', 4, 4)


def test_invalid_octave_raises():
    import pytest
    with pytest.raises(ValueError):
        _make_note('C', 9, 4)


def _make_accidental(accidental_type):
    return Accidental(
        dots=frozenset(),
        category=SymbolCategory.ACCIDENTAL,
        raw_brl='⠀',
        type=accidental_type,
    )


def test_accidental_sharp():
    assert _make_accidental(AccidentalType.SHARP).to_lilypond() == 'is'


def test_accidental_flat():
    assert _make_accidental(AccidentalType.FLAT).to_lilypond() == 'es'


def test_accidental_natural():
    assert _make_accidental(AccidentalType.NATURAL).to_lilypond() == ''


def test_accidental_double_sharp():
    assert _make_accidental(AccidentalType.DOUBLE_SHARP).to_lilypond() == 'isis'


def test_accidental_double_flat():
    assert _make_accidental(AccidentalType.DOUBLE_FLAT).to_lilypond() == 'eses'


def test_quarter_rest():
    rest = Rest(
        dots=frozenset(),
        category=SymbolCategory.REST,
        raw_brl='⠀',
        duration=Duration(value=4)
    )
    assert rest.to_lilypond() == "r4"


def test_full_measure_rest():
    rest = Rest(
        dots=frozenset(),
        category=SymbolCategory.REST,
        raw_brl='⠀',
        duration=Duration(value=1),
        is_full_measure=True
    )
    assert rest.to_lilypond() == "R1"


def test_dotted_half_rest():
    rest = Rest(
        dots=frozenset(),
        category=SymbolCategory.REST,
        raw_brl='⠀',
        duration=Duration(value=2, dots=1)
    )
    assert rest.to_lilypond() == "r2."


def test_measure_add_note():
    measure = Measure(number=1)
    measure.add_note(_make_note('C', 4, 4))
    measure.add_note(_make_note('E', 4, 4))
    assert len(measure.notes) == 2


def test_staff_add_measure():
    staff = Staff(name="right hand")
    staff.add_measure(Measure(number=1))
    assert len(staff.measures) == 1


def _make_full_measure_rest():
    return Rest(
        dots=frozenset(),
        category=SymbolCategory.REST,
        raw_brl='⠀',
        duration=Duration(value=1),
        is_full_measure=True,
    )


def test_staff_to_lilypond_measure_numbers_off_by_default():
    staff = Staff(name="right hand")
    for n in (1, 2):
        m = Measure(number=n)
        m.add_note(_make_note('C', 4, 4))
        staff.add_measure(m)
    ly = staff.to_lilypond()
    assert '%' not in ly


def test_staff_to_lilypond_measure_numbers_on():
    staff = Staff(name="right hand")
    for n in (1, 2):
        m = Measure(number=n)
        m.add_note(_make_note('C', 4, 4))
        staff.add_measure(m)
    ly = staff.to_lilypond(measure_numbers=True)
    lines = ly.splitlines()
    assert '    % 1' in lines
    assert '    % 2' in lines
    # The comment must be its own line, never sharing a line with the
    # measure's notes -- LilyPond's `%` comments out the rest of the line,
    # so "% 1 c4 c4 |" on one line would silently drop the music.
    assert not any(line.strip().startswith('%') and 'c4' in line for line in lines)


def test_staff_to_lilypond_measure_numbers_pickup_uses_real_margin_number():
    # A 0-numbered pickup measure (BANA convention) must show "% 0", not a
    # freshly-enumerated "% 1".
    staff = Staff(name="right hand")
    pickup = Measure(number=0)
    pickup.add_note(_make_note('C', 4, 4))
    staff.add_measure(pickup)
    m1 = Measure(number=1)
    m1.add_note(_make_note('D', 4, 4))
    staff.add_measure(m1)
    ly = staff.to_lilypond(measure_numbers=True)
    lines = ly.splitlines()
    assert '    % 0' in lines
    assert '    % 1' in lines


def test_staff_to_lilypond_measure_numbers_rest_run_shows_range():
    staff = Staff(name="right hand")
    m1 = Measure(number=1)
    m1.add_note(_make_note('C', 4, 4))
    staff.add_measure(m1)
    for n in (2, 3, 4, 5):
        m = Measure(number=n)
        m.add_note(_make_full_measure_rest())
        staff.add_measure(m)
    m6 = Measure(number=6)
    m6.add_note(_make_note('D', 4, 4))
    staff.add_measure(m6)
    ly = staff.to_lilypond(measure_numbers=True)
    lines = ly.splitlines()
    assert '    % 1' in lines
    assert '    % 2-5' in lines
    assert '    % 6' in lines
    assert not any(line.strip() == '% 2' for line in lines)


def test_staff_generates_real_volta_repeat_structure():
    # BANA Chapter 17/Par. 17.1.1 first/second endings -> LilyPond's real
    # \repeat volta N { ... } \alternative { \volta k {...} ... } structure
    # (Notation Reference Sec. 4.1.3), not the placeholder "% ending N"
    # comment. bar_line_type='forward_repeat' on measure 1 means (this
    # codebase's tested convention) "the repeat starts at measure 2".
    staff = Staff(name="right hand")
    m1 = Measure(number=1, bar_line_type='forward_repeat')
    m1.add_note(_make_note('C', 4, 4))
    m2 = Measure(number=2)
    m2.add_note(_make_note('D', 4, 4))
    m3 = Measure(number=3, ending_numbers=[1])
    m3.add_note(_make_note('E', 4, 4))
    m4 = Measure(number=4, ending_numbers=[2])
    m4.add_note(_make_note('F', 4, 4))
    m5 = Measure(number=5)
    m5.add_note(_make_note('G', 4, 4))
    for m in (m1, m2, m3, m4, m5):
        staff.add_measure(m)

    ly = staff.to_lilypond()

    assert 'c4 \\bar ".|:"' in ly  # forward repeat still on measure 1
    assert '\\repeat volta 2 {' in ly
    assert 'd4 |' in ly  # the shared measure, inside the \repeat volta block
    assert '\\alternative {' in ly
    assert '\\volta 1 {' in ly
    assert '\\volta 2 {' in ly
    assert 'e4 |' in ly
    assert 'f4 |' in ly
    assert 'g4 |' in ly  # material after the alternative block, unaffected
    # The shared measure must appear inside \repeat volta, not duplicated
    # or dropped.
    assert ly.count('d4 |') == 1


def test_staff_volta_combined_ending_uses_volta_numberlist():
    staff = Staff(name="right hand")
    m1 = Measure(number=1, bar_line_type='forward_repeat')
    m1.add_note(_make_note('C', 4, 4))
    m2 = Measure(number=2, ending_numbers=[1, 2])
    m2.add_note(_make_note('D', 4, 4))
    staff.add_measure(m1)
    staff.add_measure(m2)

    ly = staff.to_lilypond()
    assert '\\repeat volta 1 {' in ly  # one combined branch, not two
    assert '\\volta 1,2 {' in ly


def test_staff_volta_pitch_chaining_is_sequential_not_reset():
    # Verified against the real lilypond 2.24.4 binary's \displayLilyMusic
    # output: \repeat volta, \alternative, and \volta k are all no-ops for
    # \relative pitch tracking -- pure sequential chaining through the
    # token stream, same as << \\ >> elsewhere in this codebase. So
    # \volta 2's first note must be spelled relative to \volta 1's LAST
    # note (B4, MIDI 71), not relative to the shared section's last note
    # (C4, MIDI 60) independently.
    staff = Staff(name="right hand")
    m1 = Measure(number=1, bar_line_type='forward_repeat')
    m1.add_note(_make_note('C', 4, 4))
    m2 = Measure(number=2)
    m2.add_note(_make_note('C', 4, 4))  # shared section's last note: C4
    m3 = Measure(number=3, ending_numbers=[1])
    m3.add_note(_make_note('B', 4, 4))  # \volta 1's last note: B4
    m4 = Measure(number=4, ending_numbers=[2])
    m4.add_note(_make_note('G', 5, 4))
    for m in (m1, m2, m3, m4):
        staff.add_measure(m)

    ly = staff.to_lilypond()
    # G5 relative to B4 (up a minor 6th) resolves to a single octave mark
    # (g'4). Relative to C4 instead (an incorrect reset to the shared
    # section) it would resolve to two (g''4) -- confirms which reference
    # point is actually used.
    assert "g'4" in ly
    assert "g''4" not in ly


def test_staff_volta_without_forward_repeat_treats_everything_before_as_shared():
    # No bar_line_type='forward_repeat' anywhere -- falls back to treating
    # every measure since the start of the staff (or the end of a previous
    # volta group) as the shared section, per _find_volta_groups()'s
    # documented fallback.
    staff = Staff(name="right hand")
    m1 = Measure(number=1)
    m1.add_note(_make_note('C', 4, 4))
    m2 = Measure(number=2, ending_numbers=[1])
    m2.add_note(_make_note('D', 4, 4))
    m3 = Measure(number=3, ending_numbers=[2])
    m3.add_note(_make_note('E', 4, 4))
    for m in (m1, m2, m3):
        staff.add_measure(m)

    ly = staff.to_lilypond()
    assert '\\repeat volta 2 {' in ly
    assert 'c4 |' in ly
    # c4 must be inside \repeat volta, not before it.
    assert ly.index('\\repeat volta 2 {') < ly.index('c4 |')


def test_staff_multiple_volta_groups_in_one_staff():
    staff = Staff(name="right hand")
    m1 = Measure(number=1, ending_numbers=[1])
    m1.add_note(_make_note('C', 4, 4))
    m2 = Measure(number=2, ending_numbers=[2])
    m2.add_note(_make_note('D', 4, 4))
    m3 = Measure(number=3)
    m3.add_note(_make_note('E', 4, 4))
    m4 = Measure(number=4, ending_numbers=[1])
    m4.add_note(_make_note('F', 4, 4))
    m5 = Measure(number=5, ending_numbers=[2])
    m5.add_note(_make_note('G', 4, 4))
    for m in (m1, m2, m3, m4, m5):
        staff.add_measure(m)

    ly = staff.to_lilypond()
    assert ly.count('\\repeat volta 2 {') == 2
    assert ly.count('\\alternative {') == 2
    assert 'e4 |' in ly  # the standalone measure between the two groups


def test_score_add_staff():
    score = Score(title="Ode to Joy", composer="Beethoven")
    score.add_staff(Staff(name="right hand"))
    score.add_staff(Staff(name="left hand"))
    assert len(score.staves) == 2
    assert score.title == "Ode to Joy"


def test_articulation_staccato():
    assert Articulation(ArticulationType.STACCATO).to_lilypond() == '-.'


def test_articulation_accent():
    assert Articulation(ArticulationType.ACCENT).to_lilypond() == '->'


def test_articulation_tenuto():
    assert Articulation(ArticulationType.TENUTO).to_lilypond() == '--'


def test_articulation_expressive_accent():
    assert Articulation(ArticulationType.EXPRESSIVE_ACCENT).to_lilypond() == '-^'


def test_articulation_mezzo_staccato():
    assert Articulation(ArticulationType.MEZZO_STACCATO).to_lilypond() == '-_'


def test_articulation_swell():
    assert Articulation(ArticulationType.SWELL).to_lilypond() == r'\espressivo'


def test_articulation_staccatissimo():
    assert Articulation(ArticulationType.STACCATISSIMO).to_lilypond() == '-!'


def test_fermata_normal_to_lilypond_and_braille():
    f = Fermata(shape=FermataShape.NORMAL)
    assert f.to_lilypond() == r'\fermata'
    assert f.to_braille() == '⠣⠇'


def test_fermata_between_notes_to_braille():
    assert Fermata(shape=FermataShape.BETWEEN_NOTES).to_braille() == '⠐⠣⠇'
    # No distinct print shape from the plain variant.
    assert Fermata(shape=FermataShape.BETWEEN_NOTES).to_lilypond() == r'\fermata'


def test_fermata_squared_and_tent_to_lilypond_and_braille():
    assert Fermata(shape=FermataShape.SQUARED).to_lilypond() == r'\henzelongfermata'
    assert Fermata(shape=FermataShape.SQUARED).to_braille() == '⠰⠣⠇'
    assert Fermata(shape=FermataShape.TENT).to_lilypond() == r'\henzeshortfermata'
    assert Fermata(shape=FermataShape.TENT).to_braille() == '⠘⠣⠇'


def test_note_with_fermata_to_lilypond():
    note = _make_note('C', 4, 4, fermata=Fermata())
    assert note.to_lilypond() == "c'4\\fermata"


def test_note_with_fermata_to_braille_places_after_fingering():
    from dottednotes.models import Fingering
    note = _make_note('C', 4, 4, fermata=Fermata())
    note.fingerings = [Fingering(dots=frozenset(), category=None, raw_brl='', finger=1)]
    brl = note.to_braille(is_measure_start=True)
    fermata_brl = Fermata().to_braille()
    fingering_brl = note.fingerings[0].to_braille()
    # Par. 22.2: fermata follows the note and follows any fingering already
    # on it.
    assert brl.index(fingering_brl) < brl.index(fermata_brl)


def test_measure_bar_line_fermata_on_plain_bar_line():
    m = Measure(number=1, bar_line_fermata=True)
    ly, _ = m.to_lilypond()
    assert ly.strip() == '|'  # no confirmed LilyPond syntax -- omitted, not guessed
    brl, _ = m.to_braille()
    from dottednotes.bana_symbols import FERMATA_OVER_BAR_LINE_CELL
    assert brl == FERMATA_OVER_BAR_LINE_CELL


def test_measure_bar_line_fermata_on_final_double_bar():
    m = Measure(number=1, bar_line_type='final_double_bar', bar_line_fermata=True)
    brl, _ = m.to_braille()
    assert brl == '⠣⠅' + Fermata().to_braille()


def test_breath_mark_half_to_lilypond_and_braille():
    bm = BreathMark(variant=BreathMarkVariant.HALF)
    assert bm.to_lilypond() == "\\set breathMarkType = #'comma \\breathe"
    assert bm.to_braille() == '⠨⠂'


def test_breath_mark_full_to_lilypond_and_braille():
    bm = BreathMark(variant=BreathMarkVariant.FULL)
    assert bm.to_lilypond() == "\\set breathMarkType = #'caesura \\breathe"
    assert bm.to_braille() == '⠠⠌'


def test_note_with_breath_mark_to_lilypond_is_a_separate_trailing_event():
    note = _make_note('C', 4, 4, breath_mark=BreathMark())
    ly = note.to_lilypond()
    # \breathe is a standalone event, not glued to the note like an
    # articulation -- must be space-separated so it tokenizes as its own
    # music event when placed in a measure alongside the following note.
    assert ly == "c'4 \\set breathMarkType = #'comma \\breathe"


def test_note_with_fermata_and_breath_mark_to_braille_order():
    note = _make_note('C', 4, 4, fermata=Fermata(), breath_mark=BreathMark())
    brl = note.to_braille(is_measure_start=True)
    assert brl.index(Fermata().to_braille()) < brl.index(BreathMark().to_braille())


def test_fermata_and_breath_mark_survive_measure_to_lilypond():
    # Note.to_relative_lilypond() -- the method Measure.to_lilypond() (and
    # therefore Score.to_lilypond(), the actual production path) calls --
    # duplicates to_lilypond()'s string-building rather than reusing it.
    # Testing only note.to_lilypond() directly (as the tests above do) would
    # miss a fermata/breath mark that was added to one method but not the
    # other; this locks in the real Measure-level path.
    m = Measure(number=1)
    m.add_note(_make_note('C', 4, 4, fermata=Fermata(), breath_mark=BreathMark(variant=BreathMarkVariant.FULL)))
    ly, _ = m.to_lilypond()
    assert '\\fermata' in ly
    assert "\\set breathMarkType = #'caesura \\breathe" in ly


def test_measure_volta_single_ending_to_braille():
    m = Measure(number=5, ending_numbers=[1])
    m.add_note(_make_note('C', 4, 4))
    brl, _ = m.to_braille()
    # NUMBER_SIGN + digit 1, then the octave mark (dot 5 only -- never
    # dots 1/2/3, so no dot-3 separator here) forced by is_measure_start.
    assert brl.startswith('⠼⠂')
    assert '⠄' not in brl[:3]  # no spurious separator before an octave mark


def test_measure_volta_combined_ending_gets_own_indicator_per_number():
    m = Measure(number=5, ending_numbers=[1, 2])
    m.add_note(Rest(dots=frozenset(), category=SymbolCategory.REST, raw_brl='', duration=Duration(value=4)))
    brl, _ = m.to_braille()
    # Rest cells don't go through octave-mark logic, so the volta sign is
    # immediately followed by the rest cell, which contains dots 1-3 --
    # Par. 17.1.1's dot-3 separator must appear.
    assert brl == '⠼⠂⠼⠆⠄⠧⠀'


def test_measure_to_lilypond_ignores_ending_numbers():
    # Measure.to_lilypond() deliberately does not special-case
    # ending_numbers -- \repeat volta/\alternative wraps a whole *range* of
    # measures, which only Staff.to_lilypond() (the sole production caller)
    # can see. See test_staff_generates_real_volta_repeat_structure in this
    # file for the real behavior.
    m = Measure(number=5, ending_numbers=[1])
    m.add_note(_make_note('C', 4, 4))
    ly, _ = m.to_lilypond()
    assert '%' not in ly
    assert ly.strip() == "c4 |"


def test_measure_without_ending_numbers_unaffected():
    m = Measure(number=1)
    m.add_note(_make_note('C', 4, 4))
    brl, _ = m.to_braille()
    assert not brl.startswith('⠼')
    ly, _ = m.to_lilypond()
    assert '%' not in ly


def test_chord_with_fermata_and_breath_mark_to_lilypond():
    from dottednotes.models import Chord
    written = _make_note('E', 4, 4, fermata=Fermata(shape=FermataShape.SQUARED), breath_mark=BreathMark())
    other = _make_note('C', 4, 4)
    chord = Chord(notes=[written, other])
    ly = chord.to_lilypond()
    assert '\\henzelongfermata' in ly
    assert "\\set breathMarkType = #'comma \\breathe" in ly
    ly_rel, _ = chord.to_relative_lilypond(60)
    assert '\\henzelongfermata' in ly_rel
    assert "\\set breathMarkType = #'comma \\breathe" in ly_rel


def test_note_with_accent():
    art = Articulation(ArticulationType.ACCENT)
    note = _make_note('C', 4, 4, articulations=[art])
    assert note.to_lilypond() == "c'4->"


def test_note_with_multiple_articulations():
    articulations = [
        Articulation(ArticulationType.TENUTO),
        Articulation(ArticulationType.STACCATO),
    ]
    note = _make_note('G', 5, 8, articulations=articulations)
    assert note.to_lilypond() == "g''8---."


def test_dynamic_ppp():
    assert Dynamic(DynamicLevel.PPP).to_lilypond() == r'\ppp'


def test_dynamic_pp():
    assert Dynamic(DynamicLevel.PP).to_lilypond() == r'\pp'


def test_dynamic_p():
    assert Dynamic(DynamicLevel.P).to_lilypond() == r'\p'


def test_dynamic_mp():
    assert Dynamic(DynamicLevel.MP).to_lilypond() == r'\mp'


def test_dynamic_mf():
    assert Dynamic(DynamicLevel.MF).to_lilypond() == r'\mf'


def test_dynamic_f():
    assert Dynamic(DynamicLevel.F).to_lilypond() == r'\f'


def test_dynamic_ff():
    assert Dynamic(DynamicLevel.FF).to_lilypond() == r'\ff'


def test_dynamic_fff():
    assert Dynamic(DynamicLevel.FFF).to_lilypond() == r'\fff'


def test_dynamic_sf():
    assert Dynamic(DynamicLevel.SF).to_lilypond() == r'\sf'


def test_dynamic_sfz():
    assert Dynamic(DynamicLevel.SFZ).to_lilypond() == r'\sfz'


def test_dynamic_fp():
    assert Dynamic(DynamicLevel.FP).to_lilypond() == r'\fp'


def test_dynamic_crescendo_start():
    assert Dynamic(DynamicLevel.CRESCENDO_START).to_lilypond() == r'\<'


def test_dynamic_crescendo_end():
    assert Dynamic(DynamicLevel.CRESCENDO_END).to_lilypond() == r'\!'


def test_dynamic_decrescendo_start():
    assert Dynamic(DynamicLevel.DECRESCENDO_START).to_lilypond() == r'\>'


def test_dynamic_decrescendo_end():
    assert Dynamic(DynamicLevel.DECRESCENDO_END).to_lilypond() == r'\!'


def test_note_with_all_components():
    """Integration test: note with accidental, duration, and articulation."""
    note = Note(
        dots=frozenset([1, 4]),
        category=SymbolCategory.NOTE,
        raw_brl='⠉',
        note_name='B',
        octave=4,
        duration=Duration(value=4, dots=1),
        accidental=Accidental(
            dots=frozenset(),
            category=SymbolCategory.ACCIDENTAL,
            raw_brl='⠀',
            type=AccidentalType.FLAT,
        ),
        articulations=[Articulation(ArticulationType.STACCATO)],
    )
    # B-flat, octave 4, dotted quarter, staccato
    assert note.to_lilypond() == "bes'4.-."


# ---------------------------------------------------------------------------
# S3-1: KeySignature class
# ---------------------------------------------------------------------------

def _make_ks(sharps_or_flats: int) -> KeySignature:
    """Helper: build a KeySignature with dummy BrailleSymbol fields."""
    return KeySignature(
        dots=frozenset(),
        category=SymbolCategory.KEY_SIGNATURE,
        raw_brl='',
        sharps_or_flats=sharps_or_flats,
    )


# --- to_lilypond() for all 15 standard keys ---

def test_key_c_major():
    assert _make_ks(0).to_lilypond() == r'\key c \major'

def test_key_g_major():
    assert _make_ks(1).to_lilypond() == r'\key g \major'

def test_key_d_major():
    assert _make_ks(2).to_lilypond() == r'\key d \major'

def test_key_a_major():
    assert _make_ks(3).to_lilypond() == r'\key a \major'

def test_key_e_major():
    assert _make_ks(4).to_lilypond() == r'\key e \major'

def test_key_b_major():
    assert _make_ks(5).to_lilypond() == r'\key b \major'

def test_key_fis_major():
    assert _make_ks(6).to_lilypond() == r'\key fis \major'

def test_key_cis_major():
    assert _make_ks(7).to_lilypond() == r'\key cis \major'

def test_key_f_major():
    assert _make_ks(-1).to_lilypond() == r'\key f \major'

def test_key_bes_major():
    assert _make_ks(-2).to_lilypond() == r'\key bes \major'

def test_key_ees_major():
    assert _make_ks(-3).to_lilypond() == r'\key ees \major'

def test_key_aes_major():
    assert _make_ks(-4).to_lilypond() == r'\key aes \major'

def test_key_des_major():
    assert _make_ks(-5).to_lilypond() == r'\key des \major'

def test_key_ges_major():
    assert _make_ks(-6).to_lilypond() == r'\key ges \major'

def test_key_ces_major():
    assert _make_ks(-7).to_lilypond() == r'\key ces \major'


# --- KEY_TO_LILYPOND table completeness ---

def test_key_to_lilypond_covers_all_standard_keys():
    assert set(KEY_TO_LILYPOND.keys()) == set(range(-7, 8))


# --- Validation ---

def test_key_signature_boundary_values_are_valid():
    _make_ks(7)   # C# major — must not raise
    _make_ks(-7)  # Cb major — must not raise


# --- Beyond +/-7 accidentals (S10d-8, BANA Par. 6.5: numeral-prefixed
# form has no stated cap) ---

def test_key_signature_beyond_seven_sharps_does_not_raise():
    ks = _make_ks(8)
    assert ks.sharps_or_flats == 8

def test_key_signature_beyond_seven_flats_does_not_raise():
    ks = _make_ks(-8)
    assert ks.sharps_or_flats == -8

def test_key_signature_eight_sharps_lilypond():
    # G# major (8 sharps): continuing the circle of fifths past C# (7
    # sharps) needs F## as the 8th sharp, so the tonic itself must be
    # spelled G# (not the enharmonic Ab).
    assert _make_ks(8).to_lilypond() == r'\key gis \major'

def test_key_signature_eleven_flats_lilypond():
    # Ab major with a double flat (11 flats overall, found via the
    # MusicXML Test Suite's own 13aa-KeySignatures-Extreme.xml, fifths=-11).
    assert _make_ks(-11).to_lilypond() == r'\key aeses \major'

def test_key_signature_eight_sharps_braille():
    # BANA Par. 6.5: numeral sign + digit(s) + a single sharp sign.
    assert _make_ks(8).to_braille() == '⠼⠓⠩'

def test_key_signature_eleven_flats_braille():
    assert _make_ks(-11).to_braille() == '⠼⠁⠁⠣'


# --- Non-traditional / microtonal key signatures (S10d-7, BANA 6.5.1) ---

def _make_non_traditional_ks(pitches):
    return KeySignature(dots=frozenset(), category=SymbolCategory.KEY_SIGNATURE, raw_brl='',
                         non_traditional_pitches=pitches)

def test_key_signature_requires_exactly_one_of_the_two_variants():
    with pytest.raises(ValueError):
        KeySignature(dots=frozenset(), category=None, raw_brl='')
    with pytest.raises(ValueError):
        KeySignature(dots=frozenset(), category=None, raw_brl='', sharps_or_flats=1,
                      non_traditional_pitches=[('F', 1.0, None)])

def test_key_signature_non_traditional_braille_uses_music_parenthesis_and_clef():
    # BANA Par. 6.5.1: "music parenthesis, hand or clef sign, accidental,
    # octave mark, note(s), closing music parenthesis" -- confirmed the
    # music parenthesis sign (Table 1, ⠠⠄) and that the clef component
    # matches this project's own ClefType.TREBLE cell (⠜⠌⠇) exactly.
    ks = _make_non_traditional_ks([('F', 1.0, None)])
    braille = ks.to_braille()
    assert braille.startswith('⠠⠄⠜⠌⠇')
    assert braille.endswith('⠠⠄')
    assert '⠩' in braille  # sharp accidental present somewhere in the middle

def test_key_signature_non_traditional_braille_multiple_pitches():
    ks = _make_non_traditional_ks([('F', 1.0, None), ('A', -1.0, None), ('B', -1.0, None)])
    braille = ks.to_braille()
    # One parenthesis-wrapped construction per altered pitch (3 opens, 3 closes).
    assert braille.count('⠠⠄') == 6

def test_key_signature_non_traditional_braille_quarter_tone_accidentals():
    # BANA Table 6's quarter/three-quarter step accidentals.
    ks = _make_non_traditional_ks([('D', 0.5, None), ('G', -1.5, None)])
    braille = ks.to_braille()
    assert '⠈⠩' in braille  # quarter-sharp
    assert '⠸⠣' in braille  # three-quarter-flat

def test_key_signature_non_traditional_lilypond_raises_clean_error():
    from dottednotes.exceptions import DottedNotesError
    ks = _make_non_traditional_ks([('F', 1.0, None)])
    with pytest.raises(DottedNotesError):
        ks.to_lilypond()


# --- BrailleSymbol contract ---

def test_key_signature_has_raw_brl_field():
    ks = _make_ks(1)
    assert hasattr(ks, 'raw_brl')

def test_key_signature_category_is_key_signature():
    ks = _make_ks(0)
    assert ks.category == SymbolCategory.KEY_SIGNATURE


# ---------------------------------------------------------------------------
# S3-2: TimeSignature class
# ---------------------------------------------------------------------------

def _make_ts(numerator: int, denominator: int) -> TimeSignature:
    return TimeSignature(
        dots=frozenset(),
        category=SymbolCategory.TIME_SIGNATURE,
        raw_brl='',
        numerator=numerator,
        denominator=denominator,
    )


def test_time_4_4_lilypond():
    assert _make_ts(4, 4).to_lilypond() == r'\time 4/4'


def test_time_3_4_lilypond():
    assert _make_ts(3, 4).to_lilypond() == r'\time 3/4'


def test_time_6_8_lilypond():
    assert _make_ts(6, 8).to_lilypond() == r'\time 6/8'


def test_time_2_2_lilypond():
    assert _make_ts(2, 2).to_lilypond() == r'\time 2/2'


def test_time_12_8_lilypond():
    assert _make_ts(12, 8).to_lilypond() == r'\time 12/8'


def test_beats_per_measure_4_4():
    assert _make_ts(4, 4).beats_per_measure() == 4.0


def test_beats_per_measure_3_4():
    assert _make_ts(3, 4).beats_per_measure() == 3.0


def test_beats_per_measure_6_8():
    assert _make_ts(6, 8).beats_per_measure() == 3.0


def test_beats_per_measure_2_2():
    assert _make_ts(2, 2).beats_per_measure() == 4.0


def test_beats_per_measure_12_8():
    assert _make_ts(12, 8).beats_per_measure() == 6.0


def test_beats_per_measure_1_4():
    assert _make_ts(1, 4).beats_per_measure() == 1.0


def test_time_as_tuple():
    assert _make_ts(6, 8).as_tuple() == (6, 8)


def test_time_invalid_denominator_raises():
    with pytest.raises(ValueError):
        _make_ts(4, 3)


def test_time_invalid_denominator_5_raises():
    with pytest.raises(ValueError):
        _make_ts(4, 5)


def test_time_invalid_numerator_zero_raises():
    with pytest.raises(ValueError):
        _make_ts(0, 4)


def test_time_invalid_numerator_negative_raises():
    with pytest.raises(ValueError):
        _make_ts(-1, 4)


def test_time_valid_denominators_all_pass():
    from dottednotes.models import VALID_DENOMINATORS
    for denom in VALID_DENOMINATORS:
        _make_ts(4, denom)   # must not raise


def test_time_signature_has_raw_brl_field():
    ts = _make_ts(4, 4)
    assert hasattr(ts, 'raw_brl')


def test_time_signature_category_is_time_signature():
    ts = _make_ts(4, 4)
    assert ts.category == SymbolCategory.TIME_SIGNATURE


# ---------------------------------------------------------------------------
# S3-3: Clef class
# ---------------------------------------------------------------------------

def _make_clef(clef_type: ClefType) -> Clef:
    return Clef(
        dots=frozenset(),
        category=SymbolCategory.CLEF,
        raw_brl='',
        clef_type=clef_type,
    )


def test_clef_treble():
    assert _make_clef(ClefType.TREBLE).to_lilypond() == r'\clef treble'


def test_clef_bass():
    assert _make_clef(ClefType.BASS).to_lilypond() == r'\clef bass'


def test_clef_alto():
    assert _make_clef(ClefType.ALTO).to_lilypond() == r'\clef alto'


def test_clef_tenor():
    assert _make_clef(ClefType.TENOR).to_lilypond() == r'\clef tenor'


def test_clef_to_lilypond_map_covers_all_types():
    for clef_type in ClefType:
        assert clef_type in CLEF_TO_LILYPOND


def test_clef_has_raw_brl_field():
    assert hasattr(_make_clef(ClefType.TREBLE), 'raw_brl')


def test_clef_category_is_clef():
    assert _make_clef(ClefType.TREBLE).category == SymbolCategory.CLEF


# ---------------------------------------------------------------------------
# Ornament model tests
# ---------------------------------------------------------------------------

def test_ornament_to_lilypond_trill():
    assert Ornament(type=OrnamentType.TRILL).to_lilypond() == r'\trill'


def test_ornament_to_lilypond_trill_span_start():
    assert Ornament(type=OrnamentType.TRILL_SPAN_START).to_lilypond() == r'\startTrillSpan'


def test_ornament_to_lilypond_trill_span_end():
    assert Ornament(type=OrnamentType.TRILL_SPAN_END).to_lilypond() == r'\stopTrillSpan'


def test_ornament_to_lilypond_mordent():
    assert Ornament(type=OrnamentType.MORDENT).to_lilypond() == r'\mordent'


def test_ornament_to_lilypond_upper_mordent():
    assert Ornament(type=OrnamentType.UPPER_MORDENT).to_lilypond() == r'\prall'


def test_ornament_to_lilypond_extended_mordent():
    assert Ornament(type=OrnamentType.EXTENDED_MORDENT).to_lilypond() == r'\downmordent'


def test_ornament_to_lilypond_extended_upper_mordent():
    assert Ornament(type=OrnamentType.EXTENDED_UPPER_MORDENT).to_lilypond() == r'\upmordent'


def test_ornament_to_lilypond_turn():
    assert Ornament(type=OrnamentType.TURN).to_lilypond() == r'\turn'


def test_ornament_to_lilypond_inverted_turn():
    assert Ornament(type=OrnamentType.INVERTED_TURN).to_lilypond() == r'\reverseturn'


def test_ornament_to_lilypond_glissando():
    assert Ornament(type=OrnamentType.GLISSANDO).to_lilypond() == r'\glissando'


def test_ornament_to_lilypond_map_covers_all_types():
    for orn_type in OrnamentType:
        assert orn_type in ORNAMENT_TO_LILYPOND


def _make_grace_note(note_name='E', octave=4, long_appoggiatura=False):
    note = Note(
        dots=frozenset(),
        category=SymbolCategory.NOTE,
        raw_brl='⠀',
        note_name=note_name,
        octave=octave,
        duration=Duration(value=8),
    )
    return GraceNote(notes=[note], long_appoggiatura=long_appoggiatura)


def test_grace_note_short_to_lilypond():
    gn = _make_grace_note('E', 4, long_appoggiatura=False)
    result = gn.to_lilypond()
    assert result.startswith(r'\grace')
    assert "e'" in result
    assert r'\appoggiatura' not in result


def test_grace_note_long_to_lilypond():
    gn = _make_grace_note('E', 4, long_appoggiatura=True)
    result = gn.to_lilypond()
    assert result.startswith(r'\appoggiatura')
    assert "e'" in result
    assert result.count(r'\grace') == 0


def test_note_with_ornament_trill():
    note = _make_note('G', 4, 4, ornaments=[Ornament(type=OrnamentType.TRILL)])
    assert note.to_lilypond() == r"g'4\trill"


def test_note_with_ornament_turn():
    note = _make_note('A', 5, 8, ornaments=[Ornament(type=OrnamentType.TURN)])
    assert note.to_lilypond() == r"a''8\turn"


def test_note_articulations_precede_ornaments():
    art = Articulation(ArticulationType.STACCATO)
    note = _make_note('C', 4, 4,
                      ornaments=[Ornament(type=OrnamentType.TRILL)],
                      articulations=[art])
    ly = note.to_lilypond()
    staccato_pos = ly.index('-.')
    trill_pos = ly.index(r'\trill')
    assert staccato_pos < trill_pos


def test_note_multiple_ornaments():
    note = _make_note('D', 4, 4, ornaments=[
        Ornament(type=OrnamentType.TRILL_SPAN_START),
        Ornament(type=OrnamentType.TURN),
    ])
    ly = note.to_lilypond()
    assert r'\startTrillSpan' in ly
    assert r'\turn' in ly


def test_note_with_grace_note_prepended():
    note = Note(
        dots=frozenset(),
        category=SymbolCategory.NOTE,
        raw_brl='⠀',
        note_name='C',
        octave=4,
        duration=Duration(value=4),
        grace_note=_make_grace_note('B', 3, long_appoggiatura=False),
    )
    ly = note.to_lilypond()
    assert ly.startswith(r'\grace')
    assert "c'" in ly


def test_note_grace_note_before_main_note():
    note = Note(
        dots=frozenset(),
        category=SymbolCategory.NOTE,
        raw_brl='⠀',
        note_name='C',
        octave=4,
        duration=Duration(value=4),
        grace_note=_make_grace_note('B', 3, long_appoggiatura=False),
    )
    ly = note.to_lilypond()
    grace_pos = ly.index(r'\grace')
    main_pos = ly.index("c'")
    assert grace_pos < main_pos


def test_note_with_long_grace_note():
    note = Note(
        dots=frozenset(),
        category=SymbolCategory.NOTE,
        raw_brl='⠀',
        note_name='D',
        octave=5,
        duration=Duration(value=2),
        grace_note=_make_grace_note('C', 5, long_appoggiatura=True),
    )
    ly = note.to_lilypond()
    assert ly.startswith(r'\appoggiatura')
    assert "d''" in ly


def test_note_with_multiple_grace_notes():
    gn1 = Note(dots=frozenset(), category=SymbolCategory.NOTE, raw_brl='⠀',
               note_name='C', octave=4, duration=Duration(value=8))
    gn2 = Note(dots=frozenset(), category=SymbolCategory.NOTE, raw_brl='⠀',
               note_name='D', octave=4, duration=Duration(value=8))
    gn3 = Note(dots=frozenset(), category=SymbolCategory.NOTE, raw_brl='⠀',
               note_name='E', octave=4, duration=Duration(value=8))
    note = Note(
        dots=frozenset(), category=SymbolCategory.NOTE, raw_brl='⠀',
        note_name='F', octave=4, duration=Duration(value=4),
        grace_note=GraceNote(notes=[gn1, gn2, gn3]),
    )
    ly = note.to_lilypond()
    assert ly.startswith(r'\grace')
    assert "c'" in ly
    assert "d'" in ly
    assert "e'" in ly
    assert "f'" in ly
    grace_end = ly.index('}')
    main_pos = ly.index("f'")
    assert grace_end < main_pos


def test_note_no_grace_note_no_prefix():
    note = _make_note('F', 4, 4)
    assert not note.to_lilypond().startswith(r'\grace')
    assert not note.to_lilypond().startswith(r'\appoggiatura')


# --- Grace note octave-mark forcing at a new braille line (BANA 3.2.1) ---
#
# GraceNote.to_braille() used to hardcode is_measure_start=False for every
# grace note regardless of what its caller passed in, so a note whose
# grace note happened to start a new braille line lost its required forced
# octave mark entirely -- neither the grace note nor the main note that
# follows it got one, since Note.to_braille() also clears is_measure_start
# to False for the main note once a grace note has been rendered (correct,
# once the grace note itself carries the force responsibility).

def test_grace_note_forces_octave_mark_at_line_start():
    prev = _make_note('B', 4, 4)
    main = _make_note('C', 5, 4)
    main.grace_note = GraceNote(notes=[_make_note('D', 5, 8)])
    brl = main.to_braille(prev_note=prev, is_measure_start=True)
    assert '⠨' in brl  # octave 5 mark, forced on the grace note

def test_grace_note_does_not_force_mark_mid_line():
    # Same notes, but NOT a line start -- stepwise motion from a close
    # prev_note needs no mark, confirming the fix doesn't over-force.
    prev = _make_note('C', 5, 4)
    main = _make_note('C', 5, 4)
    main.grace_note = GraceNote(notes=[_make_note('D', 5, 8)])
    brl = main.to_braille(prev_note=prev, is_measure_start=False)
    assert '⠨' not in brl

def test_multiple_grace_notes_force_mark_only_on_the_first():
    prev = _make_note('B', 4, 4)
    main = _make_note('C', 5, 4)
    gn1 = _make_note('D', 5, 8)
    gn2 = _make_note('D', 5, 8)  # same pitch as gn1 -- would need no mark of its own
    main.grace_note = GraceNote(notes=[gn1, gn2])
    brl = main.to_braille(prev_note=prev, is_measure_start=True)
    assert brl.count('⠨') == 1

def test_four_or_more_grace_notes_force_mark_only_on_the_first():
    prev = _make_note('B', 4, 4)
    main = _make_note('C', 5, 4)
    grace_notes = [_make_note(n, 5, 8) for n in ('D', 'E', 'F', 'G')]
    main.grace_note = GraceNote(notes=grace_notes)
    brl = main.to_braille(prev_note=prev, is_measure_start=True)
    assert brl.count('⠨') == 1

def test_grace_note_first_note_of_piece_still_forces_mark():
    # prev_note=None (very first note of the whole piece) already forced
    # the mark before this fix too -- confirm no regression there.
    main = _make_note('C', 5, 4)
    main.grace_note = GraceNote(notes=[_make_note('D', 5, 8)])
    brl = main.to_braille(prev_note=None, is_measure_start=True)
    assert '⠨' in brl


def test_instrument_family_resolution():
    from dottednotes.models.instrument import get_instrument_family, InstrumentFamily, InstrumentInfo

    # Exact match from Table 29
    assert get_instrument_family('Piccolo') == InstrumentFamily.WOODWIND
    assert get_instrument_family('Trumpet') == InstrumentFamily.BRASS
    assert get_instrument_family('Kettledrums') == InstrumentFamily.PERCUSSION
    assert get_instrument_family('Piano right hand') == InstrumentFamily.KEYBOARD_HARP
    assert get_instrument_family('Violoncello') == InstrumentFamily.STRING

    # Fallback/case-insensitive matching
    assert get_instrument_family('  violin iii  ') == InstrumentFamily.STRING
    assert get_instrument_family('Alto Flute') == InstrumentFamily.WOODWIND
    assert get_instrument_family('Tenor Trombone') == InstrumentFamily.BRASS
    assert get_instrument_family('Conga Drum') == InstrumentFamily.PERCUSSION
    assert get_instrument_family('Harpsichord') == InstrumentFamily.KEYBOARD_HARP

    # Unknown instrument
    assert get_instrument_family('Synthesizer') is None

    # Plucked string instruments
    assert get_instrument_family('Guitar') == InstrumentFamily.PLUCKED_STRING
    assert get_instrument_family('Banjo') == InstrumentFamily.PLUCKED_STRING
    assert get_instrument_family('Acoustic guitar') == InstrumentFamily.PLUCKED_STRING

    # InstrumentInfo property
    info = InstrumentInfo(name="Violin I", abbreviation="v1")
    assert info.family == InstrumentFamily.STRING

    info_gtr = InstrumentInfo(name="Classical Guitar", abbreviation="gtr")
    assert info_gtr.family == InstrumentFamily.PLUCKED_STRING


def test_default_clef_resolution():
    # S10d-12 fix: conventional clefs are looked up by instrument name, not
    # inferred from register -- a second violin should be treble even if
    # its written notes happen to sit below middle C.
    from dottednotes.models.instrument import get_default_clef
    from dottednotes.models.clef import ClefType

    assert get_default_clef('Violin I') == ClefType.TREBLE
    assert get_default_clef('Violin II') == ClefType.TREBLE
    assert get_default_clef('Viola') == ClefType.ALTO
    assert get_default_clef('Violoncello') == ClefType.BASS
    assert get_default_clef('Double bass') == ClefType.BASS
    assert get_default_clef('Bassoon') == ClefType.BASS
    assert get_default_clef('Trumpet') == ClefType.TREBLE

    # Fallback keyword matching for names outside the exact Table 29 roster
    # (e.g. a MusicXML part named "Cello" rather than "Violoncello").
    assert get_default_clef('Cello') == ClefType.BASS
    assert get_default_clef('Violin 2') == ClefType.TREBLE

    # Piano/harp hands and unrecognized names have no fixed convention --
    # Staff._resolve_clef() falls back to its register-based heuristic.
    assert get_default_clef('Piano right hand') is None
    assert get_default_clef('Piano left hand') is None
    assert get_default_clef('right hand') is None
    assert get_default_clef('Synthesizer') is None


def test_staff_resolve_clef_uses_instrument_convention_over_register():
    # Regression test (S10d-12): a Violin II staff whose first written note
    # is below middle C must still resolve to treble clef -- the old
    # register-only heuristic (octave >= 4 -> treble, else bass) got this
    # wrong for string instruments, which are always notated in treble
    # clef regardless of how low a given passage sits.
    from dottednotes.models.instrument import get_default_clef  # noqa: F401 (documents intent)

    staff = Staff(name="Violin II")
    m = Measure(number=1)
    m.add_note(_make_note('G', 3, 4))  # below middle C
    staff.add_measure(m)

    assert staff._resolve_clef() == r'\clef treble'

    # A cello staff with a high first note must still resolve to bass clef.
    cello = Staff(name="Violoncello")
    m2 = Measure(number=1)
    m2.add_note(_make_note('C', 5, 4))  # well above middle C
    cello.add_measure(m2)

    assert cello._resolve_clef() == r'\clef bass'

    # Piano hands keep the old register-based heuristic (no fixed convention).
    piano_lh = Staff(name="Piano left hand")
    m3 = Measure(number=1)
    m3.add_note(_make_note('C', 5, 4))  # a left hand passage that crosses high
    piano_lh.add_measure(m3)

    assert piano_lh._resolve_clef() == r'\clef treble'


def test_score_staff_grouping():
    # Helper to build a basic staff with a single C4 note
    def make_staff(name):
        staff = Staff(name=name)
        m = Measure(number=1)
        m.add_note(_make_note('C', 4, 4))
        staff.add_measure(m)
        return staff

    # 1. Single staff: no grouping
    score1 = Score()
    score1.add_staff(make_staff("Violin"))
    ly1 = score1.to_lilypond()
    assert r'\new StaffGroup' not in ly1
    assert r'\new Staff' not in ly1  # Single staff is wrapped in \relative c' directly
    assert r"\relative c' {" in ly1

    # 2. Grouped strings (Violin I and Violin II)
    score2 = Score()
    score2.add_staff(make_staff("Violin I"))
    score2.add_staff(make_staff("Violin II"))
    ly2 = score2.to_lilypond()
    assert r'\new StaffGroup <<' in ly2
    assert ly2.count(r'\new Staff {') == 2
    assert r'<<' in ly2
    assert r'>>' in ly2

    # 3. Piano right/left hands
    score3 = Score()
    score3.add_staff(make_staff("right hand"))
    score3.add_staff(make_staff("left hand"))
    ly3 = score3.to_lilypond()
    assert r'\new PianoStaff <<' in ly3
    assert ly3.count(r'\new Staff {') == 2

    # 4. Mixed: Flute (Woodwind, length 1) and Violins (String, length 2)
    score4 = Score()
    score4.add_staff(make_staff("Flute"))
    score4.add_staff(make_staff("Violin I"))
    score4.add_staff(make_staff("Violin II"))
    ly4 = score4.to_lilypond()
    # Should have a global << >> wrapping the single Flute staff and the String StaffGroup
    assert r'\score {' in ly4
    assert '  <<\n    \\new Staff {' in ly4
    assert r'\new Staff {' in ly4
    assert r'\new StaffGroup <<' in ly4
    assert ly4.count(r'\new Staff {') == 3


def test_get_transposition():
    from dottednotes.models.transposition import get_transposition

    # Horn in F sounds a perfect 5th lower than written.
    assert get_transposition("Horn in F") == ("c'", 'f')
    # Clarinet in B-flat sounds a major 2nd lower than written.
    assert get_transposition("Clarinet in B-flat") == ("c'", 'bes')
    # Alternate flat spellings normalize to the same entry.
    assert get_transposition("Clarinet in Bb") == ("c'", 'bes')
    # Clarinet in A sounds a minor 3rd lower than written.
    assert get_transposition("Clarinet in A") == ("c'", 'a')
    # Trumpet in C is non-transposing (written == concert).
    assert get_transposition("Trumpet in C") == ("c'", "c'")
    # Non-transposing / unrecognized instrument names.
    assert get_transposition("Violin I") is None
    assert get_transposition("Flute") is None


def test_transposition_from_interval():
    from dottednotes.models.transposition import transposition_from_interval

    # Each expected result is cross-checked against get_transposition()'s
    # matching hardcoded entry above (S10b-2) -- the generic interval-based
    # formula must reproduce the same pitches as the name-string table for
    # the instruments both cover, since it's meant to replace name-matching
    # for MusicXML import, not disagree with it.

    # Horn in F: perfect 5th down. music21 Interval('P-5') gives
    # diatonic.generic.staffDistance=-4, chromatic.semitones=-7.
    assert transposition_from_interval(-4, -7) == ("c'", 'f')

    # Clarinet in Bb: major 2nd down. Interval('M-2') gives
    # staffDistance=-1, semitones=-2. Spelled "bes", not the chromatically
    # equivalent "ais" -- the diatonic step count is what picks the letter.
    assert transposition_from_interval(-1, -2) == ("c'", 'bes')

    # Clarinet in A: minor 3rd down. Interval('m-3') gives
    # staffDistance=-2, semitones=-3.
    assert transposition_from_interval(-2, -3) == ("c'", 'a')

    # Zero interval (e.g. Trumpet in C) -- non-transposing, no wrapping needed.
    assert transposition_from_interval(0, 0) is None


def test_score_transposes_horn_to_concert_pitch_by_default():
    staff = Staff(name="Horn in F")
    m = Measure(number=1)
    m.add_note(_make_note('C', 4, 4))
    staff.add_measure(m)
    score = Score()
    score.add_staff(staff)

    concert_ly = score.to_lilypond()
    assert r"\transpose c' f {" in concert_ly
    assert "c4" in concert_ly  # written pitch is untouched; \transpose does the work

    written_ly = score.to_lilypond(concert_pitch=False)
    assert r'\transpose' not in written_ly
    assert "c4" in written_ly


def test_score_transposes_clarinet_in_bflat_to_concert_pitch():
    staff = Staff(name="Clarinet in B-flat")
    m = Measure(number=1)
    m.add_note(_make_note('C', 4, 4))
    staff.add_measure(m)
    score = Score()
    score.add_staff(staff)

    concert_ly = score.to_lilypond()
    assert r"\transpose c' bes {" in concert_ly

    written_ly = score.to_lilypond(concert_pitch=False)
    assert r'\transpose' not in written_ly


def test_score_prefers_resolved_transposition_over_name_lookup():
    # "Bb Clarinet" doesn't match get_transposition()'s "<instrument> in
    # <key>" pattern -- this is exactly the real-world MusicXML part-name
    # variance S10b-2 exists for. resolved_transposition (set directly here
    # to isolate this from the MusicXML importer, tested separately in
    # test_musicxml_parser.py) must still produce the \transpose wrapping.
    staff = Staff(name="Bb Clarinet", resolved_transposition=("c'", "bes"))
    m = Measure(number=1)
    m.add_note(_make_note('C', 4, 4))
    staff.add_measure(m)
    score = Score()
    score.add_staff(staff)

    concert_ly = score.to_lilypond()
    assert r"\transpose c' bes {" in concert_ly


def test_score_does_not_transpose_non_transposing_staves():
    staff = Staff(name="Violin I")
    m = Measure(number=1)
    m.add_note(_make_note('C', 4, 4))
    staff.add_measure(m)
    score = Score()
    score.add_staff(staff)

    assert r'\transpose' not in score.to_lilypond()


def test_score_transpose_wrapping_in_multi_staff_group():
    def make_staff(name):
        staff = Staff(name=name)
        m = Measure(number=1)
        m.add_note(_make_note('C', 4, 4))
        staff.add_measure(m)
        return staff

    score = Score()
    score.add_staff(make_staff("Horn in F"))
    score.add_staff(make_staff("Flute"))
    ly = score.to_lilypond()
    assert r"\transpose c' f {" in ly
    assert ly.count(r'\new Staff {') == 2


# --- S7-1: \header / \score / \layout / \midi wrapping ---
# (formerly covered by the now-removed LilypondRenderer / test_renderers.py;
# Score.to_lilypond() is the one renderer now, so this coverage moved here.)

def test_score_to_lilypond_includes_version():
    assert r'\version' in Score().to_lilypond()


def test_score_to_lilypond_empty_score_has_no_header_or_score_block():
    ly = Score().to_lilypond()
    assert r'\version "2.24.0"' in ly
    assert r'#(set-global-staff-size 20.0)' in ly
    assert r'\paper {' in ly
    assert r'\header' not in ly
    assert r'\score' not in ly


def test_score_to_lilypond_header_includes_copyright_and_tagline():
    score = Score(title="Title", copyright="© 2026", tagline="Mutopia Tagline")
    ly = score.to_lilypond()
    assert 'copyright = "© 2026"' in ly
    assert 'tagline = "Mutopia Tagline"' in ly


def test_score_to_lilypond_custom_paper_size():
    score = Score()
    ly_letter = score.to_lilypond(paper_size="letter")
    assert '#(set-paper-size "letter")' in ly_letter

    ly_a4 = score.to_lilypond(paper_size="a4")
    assert '#(set-paper-size "a4")' in ly_a4


def test_score_to_lilypond_no_header_when_title_and_composer_unset():
    staff = Staff(name="Violin")
    m = Measure(number=1)
    m.add_note(_make_note('C', 4, 4))
    staff.add_measure(m)
    score = Score()
    score.add_staff(staff)
    assert r'\header' not in score.to_lilypond()


def test_score_to_lilypond_header_includes_title_and_composer():
    staff = Staff(name="Violin")
    m = Measure(number=1)
    m.add_note(_make_note('C', 4, 4))
    staff.add_measure(m)
    score = Score(title="Moonlight Sonata", composer="Beethoven")
    score.add_staff(staff)
    ly = score.to_lilypond()
    assert r'\header {' in ly
    assert 'title = "Moonlight Sonata"' in ly
    assert 'composer = "Beethoven"' in ly
    # \header comes after \version and before \score, per S7-1.
    assert ly.index(r'\version') < ly.index(r'\header') < ly.index(r'\score')


def test_score_to_lilypond_header_present_even_with_no_staves():
    # Matches the old LilypondRenderer behavior: header metadata doesn't
    # depend on there being any music.
    score = Score(title="Moonlight Sonata", composer="Beethoven")
    ly = score.to_lilypond()
    assert "Moonlight Sonata" in ly
    assert "Beethoven" in ly
    assert r'\score' not in ly  # no music to wrap


def test_score_to_lilypond_header_omits_unset_field_individually():
    staff = Staff(name="Violin")
    m = Measure(number=1)
    m.add_note(_make_note('C', 4, 4))
    staff.add_measure(m)

    title_only = Score(title="Moonlight Sonata")
    title_only.add_staff(staff)
    ly_title = title_only.to_lilypond()
    assert 'title = "Moonlight Sonata"' in ly_title
    assert 'composer' not in ly_title

    composer_only = Score(composer="Beethoven")
    composer_only.add_staff(staff)
    ly_composer = composer_only.to_lilypond()
    assert 'composer = "Beethoven"' in ly_composer
    assert 'title' not in ly_composer


def test_score_to_lilypond_header_escapes_embedded_quotes_and_backslashes():
    staff = Staff(name="Violin")
    m = Measure(number=1)
    m.add_note(_make_note('C', 4, 4))
    staff.add_measure(m)
    score = Score(title='Sonata "Pathetique"', composer=r'C:\composers\beethoven')
    score.add_staff(staff)
    ly = score.to_lilypond()
    assert r'title = "Sonata \"Pathetique\""' in ly
    assert r'composer = "C:\\composers\\beethoven"' in ly


def test_score_to_lilypond_single_staff_wraps_in_score_layout_midi():
    staff = Staff(name="Violin")
    m = Measure(number=1)
    m.add_note(_make_note('C', 4, 4))
    staff.add_measure(m)
    score = Score()
    score.add_staff(staff)
    ly = score.to_lilypond()
    assert r'\score {' in ly
    assert r'\layout { }' in ly
    assert r'\midi { }' in ly
    # \score must wrap the music, not sit alongside it.
    assert ly.index(r'\score {') < ly.index(r"\relative c'") < ly.rindex('}')


def test_score_to_lilypond_multi_staff_wraps_in_single_score_block():
    def make_staff(name):
        staff = Staff(name=name)
        m = Measure(number=1)
        m.add_note(_make_note('C', 4, 4))
        staff.add_measure(m)
        return staff

    score = Score()
    score.add_staff(make_staff("Violin I"))
    score.add_staff(make_staff("Violin II"))
    ly = score.to_lilypond()
    assert ly.count(r'\score {') == 1
    assert ly.count(r'\layout { }') == 1
    assert ly.count(r'\midi { }') == 1

