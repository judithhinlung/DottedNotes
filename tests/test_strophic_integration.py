import shutil
import subprocess
import warnings
from pathlib import Path

import pytest
from dottednotes.models import Duration, Measure, Note, Score, Staff, TimeSignature
from dottednotes.parser.input_pipeline import BRLInputPipeline
from dottednotes.parser.strophic_song_parser import (
    _is_no_words_marker, _strip_margin_measure_number, _verse_marker,
    parse_strophic_song, parse_strophic_song_with_accompaniment,
)
from dottednotes.renderers.braille_renderer import BrailleRenderer, encode_lyric_line


def _note(name: str, octave: int, **kwargs) -> Note:
    return Note(dots=frozenset(), category=None, raw_brl="", note_name=name, octave=octave,
                duration=Duration(value=4), **kwargs)

FIXTURES = Path(__file__).parent / "fixtures"


def _compile_and_check_no_warnings(ly_output: str, tmp_path: Path, basename: str) -> Path:
    """Write `ly_output` to `tmp_path`, compile it with the real `lilypond`
    binary (no --silent, so its full log is available), assert success and
    a non-empty PDF, and assert the compile log contains no "warning" text
    -- a clean exit code alone doesn't mean LilyPond was happy with the
    engraving. Returns the produced PDF path for optional manual review.
    """
    ly_file = tmp_path / f"{basename}.ly"
    ly_file.write_text(ly_output, encoding="utf-8")
    result = subprocess.run(
        ["lilypond", "-o", str(tmp_path / basename), str(ly_file)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"LilyPond compilation failed:\n{result.stderr}"

    combined_log = (result.stdout + result.stderr).lower()
    assert "warning" not in combined_log, (
        f"LilyPond reported a warning during compilation:\n{result.stdout}\n{result.stderr}"
    )

    pdf_path = tmp_path / f"{basename}.pdf"
    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 0
    return pdf_path


def test_strophic_fixture_parses_without_warnings():
    text = BRLInputPipeline().load(FIXTURES / "strophic_song_test.brf")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        parse_strophic_song(text)
    assert not caught, [str(w.message) for w in caught]


def test_strophic_fixture_verses_and_refrain_match_expected():
    text = BRLInputPipeline().load(FIXTURES / "strophic_song_test.brf")
    score = parse_strophic_song(text)

    staff = score.staves[0]
    # Verse 1 has no prefix (BANA 35.7: "The numeral 1 is not shown in the
    # braille even if it has been included in the print"); verse 2 (the
    # "<#b">" overflow block) is prefixed "2.".
    assert staff.verse_prefixes == [None, "2."]
    # Verse 1's own text ("Fly away oh my friend, Please go quickly.") is
    # followed by the refrain ("Go far away, please go far away."),
    # replicated onto verse 2's own text ("Everyone has gone to sleep,
    # Tarry no more.") via the bare trailing "REFRAIN" marker (BANA 35.7.2)
    # -- reusing the already-parsed refrain syllables, not re-parsing them.
    assert staff.verses[0] == [
        "Fly", "away", "oh", "my", "friend,",
        "Ple --", "ase", "go", "quickly.",
        "Go", "far", "away,", "please", "go", "far", "away.",
    ]
    assert staff.verses[1] == [
        "Everyone", "has", "gone", "to", "sleep,",
        "Tar --", "ry", "no", "more.",
        "Go", "far", "away,", "please", "go", "far", "away.",
    ]


def test_strophic_fixture_chords_match_expected():
    # Verse 1's two chord lines (Bb over "Fly away oh my friend," and
    # Bb/F7/Bb over "Please go quickly.") and the refrain's chord line
    # (Eb/Bb/Bb over "Go far away, please go far away.") -- BANA 36.1
    # aligns each chord's column to the syllable it's placed under, and
    # that syllable's position pairs 1:1 (BANA 35.1) with a melody note.
    text = BRLInputPipeline().load(FIXTURES / "strophic_song_test.brf")
    score = parse_strophic_song(text)

    chords = [
        (c.root, c.accidental, c.extensions) if c is not None else None
        for _, c in score.chord_names.entries
    ]
    assert chords == [
        ("B", "flat", []), ("B", "flat", []), None, None, None, None,
        ("F", None, [(7, None)]), None, None,
        ("B", "flat", []), None,
        ("E", "flat", []), ("B", "flat", []), ("B", "flat", []),
        None, None, None, None, None, None,
    ]


def test_strophic_fixture_matches_ground_truth_ly():
    text = BRLInputPipeline().load(FIXTURES / "strophic_song_test.brf")
    score = parse_strophic_song(text)

    ly_output = score.to_lilypond(category_override="Strophic Song")
    ground_truth = (FIXTURES / "strophic_song_test.ly").read_text(encoding="utf-8")
    assert ly_output == ground_truth


def test_strophic_fixture_compiles_cleanly(tmp_path: Path):
    if not shutil.which("lilypond"):
        pytest.skip("lilypond binary not found; skipping compile test")

    text = BRLInputPipeline().load(FIXTURES / "strophic_song_test.brf")
    score = parse_strophic_song(text)

    ly_output = score.to_lilypond(category_override="Strophic Song")
    assert '\\new ChordNames' in ly_output
    assert '\\new Lyrics \\lyricsto' in ly_output

    _compile_and_check_no_warnings(ly_output, tmp_path, "strophic_song_test")


def test_strophic_fixture_braille_render_includes_overflow_verse_text():
    # S11c-25: BrailleRenderer used to read only staff.lyrics (verse 1),
    # silently dropping every further verse of a strophic song from the
    # BRF output. strophic_song_test.brf/.ly has 2 verses -- verse 2's
    # own text ("Everyone has gone to sleep, Tarry no more.") must now
    # appear in the rendered BRF, introduced by its BANA §35.7
    # verse-number marker ("<#b">" for verse 2), not just verse 1's.
    text = BRLInputPipeline().load(FIXTURES / "strophic_song_test.brf")
    score = parse_strophic_song(text)

    brf_output = BrailleRenderer().render(score)
    lines = brf_output.rstrip("\n").split("\n")

    verse2_lines = [l for l in lines if _verse_marker(l) is not None]
    assert len(verse2_lines) == 1, lines
    verse_num, rest = _verse_marker(verse2_lines[0])
    assert verse_num == 2
    assert rest.startswith(encode_lyric_line(["Everyone", "has", "gone"]))

    # The remainder of verse 2's text (wrapped onto a run-over line, cell
    # 3) must also be present, not truncated.
    verse2_text_lines = lines[lines.index(verse2_lines[0]):]
    joined = "".join(l.lstrip("⠀") for l in verse2_text_lines)
    assert encode_lyric_line(["more."]) in joined

    # Verse 1 must still be present and unaffected by this change.
    assert encode_lyric_line(["Fly", "away"]) in brf_output


def test_encode_overflow_verses_round_trips_verse_number_marker():
    from dottednotes.models.staff import Staff
    staff = Staff(name="Voice")
    staff.verses = [["Verse", "one"], ["Verse", "two"], ["Verse", "three"]]
    staff.verse_prefixes = [None, "2.", "3."]

    from dottednotes.renderers.braille_renderer import encode_overflow_verses
    lines = encode_overflow_verses(staff, line_width=40)
    assert len(lines) == 2

    for line, expected_num in zip(lines, [2, 3]):
        verse_num, rest = _verse_marker(line)
        assert verse_num == expected_num
        assert rest == encode_lyric_line(staff.verses[expected_num - 1])


def test_encode_overflow_verses_empty_for_single_verse():
    from dottednotes.models.staff import Staff
    from dottednotes.renderers.braille_renderer import encode_overflow_verses
    staff = Staff(name="Voice")
    staff.verses = [["Only", "verse"]]
    staff.verse_prefixes = [None]
    assert encode_overflow_verses(staff, line_width=40) == []


def test_strip_margin_measure_number_pickup_with_partial_mark():
    # BANA 24.1.1: "#J' " -- NUMBER_SIGN + digit J (0) + dot-3 partial mark
    # + blank cell -- is segment 0 beginning with a partial (pickup)
    # measure. Only the marker is stripped; the lyric content is untouched.
    line = '⠼⠚⠄⠀⠠⠁⠀⠃'  # "#J' ,A B" -- enough to show the boundary
    assert _strip_margin_measure_number(line) == '⠠⠁⠀⠃'


def test_strip_margin_measure_number_without_partial_mark():
    # "#A " -- NUMBER_SIGN + digit A (1) + blank cell, no partial mark --
    # a segment starting on a full measure.
    line = '⠼⠁⠀⠠⠁'  # "#A ,A"
    assert _strip_margin_measure_number(line) == '⠠⠁'


def test_strip_margin_measure_number_leaves_ordinary_lyric_line_untouched():
    # No NUMBER_SIGN prefix -- an ordinary lyric line, not a margin number.
    line = '⠠⠁⠀⠃⠕⠞⠞⠇⠑'  # ",A BOTTLE"
    assert _strip_margin_measure_number(line) == line


def test_pickup_continuation_fixture_parses_with_expected_warnings_only():
    # The fixture opens with a BANA 24.1.1 margin pickup number ("#J' ",
    # segment 0 with the dot-3 partial-measure mark) and its last melody
    # line ends in a BANA 1.11 music hyphen -- the warnings below are the
    # legitimate pickup and short-final-measure beat counts (same
    # convention as lead_sheet_test.brf), not parsing bugs. Anything else
    # would be.
    text = BRLInputPipeline().load(FIXTURES / "strophic_song_pickup_continuation_test.brf")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        score = parse_strophic_song(text)

    messages = [str(w.message) for w in caught]
    assert len(messages) == 2, messages
    assert "Measure 1: expected 3.0 beats but counted 0.5" in messages[0]
    assert "Measure 5: expected 3.0 beats but counted 2.5" in messages[1]

    staff = score.staves[0]
    assert staff.lyrics == [
        "Hello", "little", "song,", "Sing", "it", "loud", "and", "long.",
    ]


def test_pickup_continuation_fixture_merges_measure_across_line_break():
    # The music hyphen at the end of group 1's melody line must glue onto
    # group 2's melody line into one continuous measure (measure 3), not
    # split into two separate short measures -- confirmed by it totaling
    # the same tick count as the surrounding full measures (2 and 4).
    text = BRLInputPipeline().load(FIXTURES / "strophic_song_pickup_continuation_test.brf")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        score = parse_strophic_song(text)

    staff = score.staves[0]
    assert len(staff.measures) == 5
    assert staff.measures[2].total_ticks() == staff.measures[1].total_ticks()
    assert [n.note_name for n in staff.measures[2].notes] == ["G", "F", "F", "F", "E"]


def test_pickup_continuation_fixture_matches_ground_truth_ly():
    text = BRLInputPipeline().load(FIXTURES / "strophic_song_pickup_continuation_test.brf")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        score = parse_strophic_song(text)

    ly_output = score.to_lilypond(category_override="Strophic Song")
    ground_truth = (FIXTURES / "strophic_song_pickup_continuation_test.ly").read_text(encoding="utf-8")
    assert ly_output == ground_truth
    assert "\\partial 8" in ly_output


def test_pickup_continuation_fixture_compiles_cleanly(tmp_path: Path):
    if not shutil.which("lilypond"):
        pytest.skip("lilypond binary not found; skipping compile test")

    text = BRLInputPipeline().load(FIXTURES / "strophic_song_pickup_continuation_test.brf")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        score = parse_strophic_song(text)

    ly_output = score.to_lilypond(category_override="Strophic Song")
    _compile_and_check_no_warnings(ly_output, tmp_path, "strophic_song_pickup_continuation_test")


# ---------------------------------------------------------------------------
# BANA 36.3.6/35.7.2 "NO WORDS" marker: a fully-capitalized (or italicized)
# word line reading literally "no words" stands in for real lyrics during
# an instrumental passage with nothing to sing.
# ---------------------------------------------------------------------------


def test_is_no_words_marker_matches_case_insensitively():
    assert _is_no_words_marker(BRLInputPipeline()._ascii_to_unicode(",,NO ,,WORDS"))
    assert _is_no_words_marker(BRLInputPipeline()._ascii_to_unicode("no words"))


def test_is_no_words_marker_rejects_ordinary_lyric_text():
    assert not _is_no_words_marker(BRLInputPipeline()._ascii_to_unicode(",HELLO WORLD"))
    assert not _is_no_words_marker(BRLInputPipeline()._ascii_to_unicode(",,NO WAY"))


def test_no_words_group_excluded_from_lyric_alignment():
    # A "NO WORDS" group inserted between two sung groups must contribute
    # no syllables of its own, and must not shift the real syllables that
    # follow it out of alignment with their notes (BANA 36.3.6/35.7.2 --
    # it's an instrumental passage, not a lyric to sing).
    ascii_text = (
        '                  <<#C4\n'
        ',FLY AWAY OH MY FRIEND1\n'
        ',B<      ,B<\n'
        '  "W[W    W?:\n'
        ',,NO ,,WORDS\n'
        '  "W[W\n'
        ',PLE-ASE GO QUICKLY4\n'
        ',F#G        ,B<\n'
        '  $C:?      ?T<K'
    )
    text = BRLInputPipeline()._ascii_to_unicode(ascii_text)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        score = parse_strophic_song(text)
    assert not caught, [str(w.message) for w in caught]

    assert score.staves[0].lyrics == [
        "Fly", "away", "oh", "my", "friend,",
        "Ple --", "ase", "go", "quickly.",
    ]


# ---------------------------------------------------------------------------
# BANA 29.8 keyboard accompaniment, appended to a strophic vocal part.
# ---------------------------------------------------------------------------


def _strophic_score_with_piano() -> Score:
    score = Score(title="")
    vocal = Staff(name="Soprano")
    vocal.time_signature = TimeSignature(
        dots=frozenset(), category=None, raw_brl="", numerator=4, denominator=4
    )
    m = Measure(number=1)
    for note in (_note("C", 5), _note("D", 5), _note("E", 5), _note("F", 5)):
        m.add_note(note)
    vocal.add_measure(m)
    vocal.lyrics = ["Sing", "a", "song", "now"]
    vocal.verses = [["Sing", "a", "song", "now"], ["Verse", "two", "words", "here"]]
    vocal.verse_prefixes = [None, "2."]

    rh = Staff(name="Piano right hand")
    rh.time_signature = vocal.time_signature
    m2 = Measure(number=1)
    for note in (_note("G", 4), _note("G", 4), _note("G", 4), _note("G", 4)):
        m2.add_note(note)
    rh.add_measure(m2)

    lh = Staff(name="Piano left hand")
    lh.time_signature = vocal.time_signature
    m3 = Measure(number=1)
    for note in (_note("C", 3), _note("C", 3), _note("C", 3), _note("C", 3)):
        m3.add_note(note)
    lh.add_measure(m3)

    score.add_staff(vocal)
    score.add_staff(rh)
    score.add_staff(lh)
    return score


def test_strophic_song_with_accompaniment_round_trips_through_parser():
    score = _strophic_score_with_piano()
    output = BrailleRenderer(line_width=40).render(score)

    parsed = parse_strophic_song_with_accompaniment(output)

    assert len(parsed.staves) == 3
    vocal, rh, lh = parsed.staves
    assert vocal.lyrics == ["Sing", "a", "song", "now"]
    assert vocal.verses == [["Sing", "a", "song", "now"], ["Verse", "two", "words", "here"]]
    assert [(n.note_name, n.octave) for n in vocal.measures[0].notes] == [
        ("C", 5), ("D", 5), ("E", 5), ("F", 5),
    ]
    assert [(n.note_name, n.octave) for n in rh.measures[0].notes] == [
        ("G", 4), ("G", 4), ("G", 4), ("G", 4),
    ]
    assert [(n.note_name, n.octave) for n in lh.measures[0].notes] == [
        ("C", 3), ("C", 3), ("C", 3), ("C", 3),
    ]


def test_strophic_song_without_blank_line_still_parses_vocal_only():
    # No accompaniment block present -- must behave exactly like a direct
    # parse_strophic_song() call, not require a blank line that isn't there.
    text = BRLInputPipeline().load(FIXTURES / "strophic_song_test.brf")
    assert len(parse_strophic_song_with_accompaniment(text).staves) == 1


def test_strophic_song_with_accompaniment_ignores_trailing_newline():
    # A source file's own trailing "\n" must not be mistaken for the blank
    # line that separates the vocal block from an accompaniment block --
    # otherwise every ordinary vocal-only .brf (which always ends in a
    # newline) would be misrouted into expecting a keyboard block.
    text = BRLInputPipeline().load(FIXTURES / "strophic_song_test.brf").rstrip("\n") + "\n"
    assert len(parse_strophic_song_with_accompaniment(text).staves) == 1


def test_strophic_song_with_accompaniment_overrides_disagreeing_piano_key_signature():
    # A piece has one key signature throughout -- if the accompaniment's
    # own (independently restated) header disagrees with the vocal's
    # (e.g. one sharp short, a transcription slip), every staff
    # must still end up in the vocal's key, flagged with a warning rather
    # than silently producing a staff in the wrong key (which also throws
    # off that key's own implied accidentals, e.g. a scale degree that's
    # sharped in the true key but not in the staff's own wrong one).
    vocal = '        %%%#F8\n,SING1\n  "F"F"F"F"F"F'
    piano = '        %%#F8\nA .>"F"F"F"F"F"F\n  _>"F"F"F"F"F"F'
    text = BRLInputPipeline()._ascii_to_unicode(vocal + '\n\n' + piano)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        score = parse_strophic_song_with_accompaniment(text)

    assert all(s.key_signature.sharps_or_flats == 3 for s in score.staves)
    messages = [str(w.message) for w in caught]
    assert any("key signature" in m and "disagrees" in m for m in messages), messages
