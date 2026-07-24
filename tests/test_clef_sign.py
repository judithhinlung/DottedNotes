"""Tests for the "include_clef_sign" setting (BANA Par. 4.1: clef signs
are routinely omitted in braille music transcription, off by default here;
when on, for a facsimile transcription, the clef is stated once, right
after the first measure's number -- not glued onto the key/time signature
line -- per Par. 10.1.2/6.5.1's ordering, with a dot-3 separator (Par. 4.2)
inserted if the sign that follows contains dot 1, 2, or 3.
"""
from dottednotes.models.note import Note
from dottednotes.models.duration import Duration
from dottednotes.models.measure import Measure
from dottednotes.models.staff import Staff
from dottednotes.models.score import Score
from dottednotes.models.clef import Clef, ClefType
from dottednotes.models.key_signature import KeySignature
from dottednotes.models.time_signature import TimeSignature
from dottednotes.models.dynamic import Dynamic, DynamicLevel
from dottednotes.renderers.braille_renderer import BrailleRenderer


def _note(name="C", octave=4, value=4, dynamics=None):
    return Note(dots=frozenset(), category=None, raw_brl="", note_name=name, octave=octave,
                duration=Duration(value), dynamics=dynamics or [])


def _clef(clef_type=ClefType.TREBLE):
    return Clef(dots=frozenset(), category=None, raw_brl="", clef_type=clef_type)


def _key_sig(n=0):
    return KeySignature(dots=frozenset(), category=None, raw_brl="", sharps_or_flats=n)


def _solo_score(measures_notes, clef=None, key_signature=None, time_signature=None):
    staff = Staff(name="Violin", clef=clef, key_signature=key_signature, time_signature=time_signature)
    staff.measures = [Measure(number=i + 1, notes=notes) for i, notes in enumerate(measures_notes)]
    return Score(title="", staves=[staff])


def test_default_off_omits_clef_entirely():
    score = _solo_score([[_note("C")]], clef=_clef(), key_signature=_key_sig(1))
    output = BrailleRenderer(line_width=40, include_clef_sign=False).render(score)
    assert '⠜' not in output


def test_clef_not_glued_to_key_signature_line():
    score = _solo_score([[_note("C")]], clef=_clef(), key_signature=_key_sig(1))
    output = BrailleRenderer(line_width=40, include_clef_sign=True).render(score)
    lines = output.splitlines()
    # The signature line (key/time signature) must not contain the clef.
    sig_line = next(line for line in lines if '⠩' in line)
    assert '⠜' not in sig_line


def test_clef_appears_once_after_first_measure_number():
    score = _solo_score([[_note("C")], [_note("D")]], clef=_clef(), key_signature=_key_sig(0))
    output = BrailleRenderer(line_width=40, include_clef_sign=True).render(score)
    assert output.count('⠜⠌⠇') == 1
    # Right after the measure-1 number, before the note's own content.
    idx = output.index('⠼⠁')
    assert output[idx:idx + 10].startswith('⠼⠁⠀⠜⠌⠇')


def test_clef_not_restated_on_line_wrap():
    # Narrow width forces each measure onto its own line -- the clef must
    # still appear only once (at the very first measure), not restated at
    # every new line the way the octave mark is.
    score = _solo_score([[_note("C")], [_note("D")], [_note("E")]], clef=_clef())
    output = BrailleRenderer(line_width=6, include_clef_sign=True).render(score)
    assert output.count('⠜⠌⠇') == 1


def test_bass_clef_cell():
    score = _solo_score([[_note("C", octave=3)]], clef=_clef(ClefType.BASS))
    output = BrailleRenderer(line_width=40, include_clef_sign=True).render(score)
    assert '⠜⠼⠇' in output


def test_dot3_separator_inserted_when_following_sign_has_dot_1_2_or_3():
    # BANA Par. 4.2: a dynamic marking (⠺ mf-like dynamics contain dot 1/2/3
    # cells) immediately after the clef needs a dot-3 separator.
    score = _solo_score([[_note("C", dynamics=[Dynamic(level=DynamicLevel.F)])]], clef=_clef())
    output = BrailleRenderer(line_width=40, include_clef_sign=True).render(score)
    idx = output.index('⠜⠌⠇')
    # Immediately after the clef cells, before the dynamic mark, is the dot-3 separator.
    assert output[idx + 3] == '⠄'


def test_no_dot3_separator_before_bare_octave_mark():
    # An octave mark alone (no dot 1/2/3 in any of the 7 octave cells) needs
    # no separator after the clef.
    score = _solo_score([[_note("C")]], clef=_clef())
    output = BrailleRenderer(line_width=40, include_clef_sign=True).render(score)
    idx = output.index('⠜⠌⠇')
    assert output[idx + 3] != '⠄'


def test_no_clef_when_staff_has_none():
    score = _solo_score([[_note("C")]], clef=None)
    output = BrailleRenderer(line_width=40, include_clef_sign=True).render(score)
    assert '⠜' not in output
