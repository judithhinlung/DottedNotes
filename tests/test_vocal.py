import shutil
import subprocess
from pathlib import Path

import pytest
from dottednotes.exceptions import BrailleParseError
from dottednotes.models import Score, Staff, Note, Duration, Measure, TimeSignature
from dottednotes.parser.ensemble_parser import EnsembleParser, parse_lyrics
from dottednotes.parser.input_pipeline import BRLInputPipeline, ascii_braille_char_to_unicode
from dottednotes.parser.vocal_solo_parser import parse_vocal_solo
from dottednotes.parser.solo_with_accompaniment_parser import parse_solo_with_accompaniment
from dottednotes.renderers.braille_renderer import BrailleRenderer, encode_lyric_line
from dottednotes.models.instrument import InstrumentFamily, get_instrument_family


def _cells(ascii_braille: str) -> str:
    """Build a Unicode braille cell sequence from ASCII braille characters,
    for lyric-decoding tests where writing out literal braille glyphs by hand
    would be error-prone (e.g. accent-modifier and punctuation sequences)."""
    return "".join(ascii_braille_char_to_unicode(c) for c in ascii_braille)

FIXTURES = Path(__file__).parent / "fixtures"


def test_vocal_instrument_family():
    assert get_instrument_family("Soprano") == InstrumentFamily.VOCAL
    assert get_instrument_family("Alto") == InstrumentFamily.VOCAL
    assert get_instrument_family("Tenor") == InstrumentFamily.VOCAL
    assert get_instrument_family("Bass") == InstrumentFamily.VOCAL
    assert get_instrument_family("Voice") == InstrumentFamily.VOCAL
    assert get_instrument_family("Vocal") == InstrumentFamily.VOCAL


def test_parse_lyrics_simple():
    # "ho-ly" in braille is ⠓⠕⠤⠇⠽ (h-o-hyphen-l-y); capital indicator is
    # ⠠ (dot 6). Plain (non-repeated) lyric text has no repeat sign at all.
    cells = "⠠⠓⠕⠤⠇⠽"
    syllables = parse_lyrics(cells)

    assert syllables == [
        ("Ho", True),
        ("ly", False),
    ]


# ---------------------------------------------------------------------------
# S11c-15: BANA §35.4 repeat sign for words/phrases (⠔, dots 3,5, ASCII
# '9'). The sign sits immediately adjacent to the bracketed word/phrase --
# no intervening space -- and has three distinct encodings depending on
# repeat count. The old parser (pre-S11c-15) treated a *space-separated*
# run of '9' cells as its own token and duplicated only the preceding
# single word, which isn't this rule at all.
# ---------------------------------------------------------------------------


def test_parse_lyrics_repeat_sign_once_bana_example_35_4_1():
    # Manual Example 35.4-1: "9,BENEDICTUS49" -- one sign before and after
    # -> repeated once (said twice total). The closing punctuation (period,
    # ASCII '4') belongs only to the final iteration.
    syllables = parse_lyrics(_cells("9,BENEDICTUS49"))
    assert syllables == [("Benedictus", False), ("Benedictus.", False)]


def test_parse_lyrics_repeat_sign_twice_bana_example_35_4_2():
    # Manual Example 35.4-2: "99,ICH LIEBE DICH9 IN ..." -- two consecutive
    # signs before, one after -> repeated twice (said three times total),
    # bracketing a multi-word phrase. Text after the closing sign is not
    # repeated.
    syllables = parse_lyrics(_cells("99,ICH LIEBE DICH9 IN ,ZEIT"))
    assert [s for s, _ in syllables] == [
        "Ich", "liebe", "dich", "Ich", "liebe", "dich", "Ich", "liebe", "dich", "in", "Zeit",
    ]


def test_parse_lyrics_repeat_sign_numeral_prefixed_bana_example_35_4_3():
    # Manual Example 35.4-3: "#C9,HALLELUJAH69" -- numeral sign + digit "C"
    # (3) + one sign before, one sign after -> repeated 3 times (said 4
    # times total). The exclamation mark (ASCII '6') belongs only to the
    # final iteration.
    syllables = parse_lyrics(_cells("#C9,HALLELUJAH69"))
    assert [s for s, _ in syllables] == ["Hallelujah", "Hallelujah", "Hallelujah", "Hallelujah!"]
    assert syllables[0] == ("Hallelujah", False)
    assert syllables[-1] == ("Hallelujah!", False)


def test_parse_lyrics_repeat_sign_more_than_two_consecutive_signs_rejected():
    # Three or more consecutive opening signs isn't a valid encoding --
    # 3+ repetitions must use a numeral-sign-prefixed count instead.
    with pytest.raises(BrailleParseError):
        parse_lyrics(_cells("999,HI9"))


def test_parse_lyrics_repeat_sign_unterminated_raises():
    with pytest.raises(BrailleParseError):
        parse_lyrics(_cells("9,HI"))


def test_parse_lyrics_capitals_and_spaces():
    # UEB capitals: ,sing -> Sing; ,,song -> SONG
    # ⠠⠎⠊⠝⠛⠀⠠⠠⠎⠕⠝⠛ -> ,sing ,,song
    cells = "⠠⠎⠊⠝⠛⠀⠠⠠⠎⠕⠝⠛"
    syllables = parse_lyrics(cells)
    assert syllables == [
        ("Sing", False),
        ("SONG", False),
    ]


def test_parse_lyrics_ueb_punctuation():
    # UEB 7.1: semicolon (dots 2,3 / ASCII '2'), colon (dots 2,5 / ASCII '3'),
    # exclamation mark (dots 2,3,5 / ASCII '6'). Comma/period already covered
    # by test_parse_lyrics_simple via other fixtures.
    syllables = parse_lyrics(_cells("A2B3C6"))
    assert syllables == [("a;b:c!", False)]


def test_parse_lyrics_apostrophe():
    # UEB 7.6.6: apostrophe (dot 3, ASCII "'").
    syllables = parse_lyrics(_cells("DON'T"))
    assert syllables == [("don't", False)]


def test_parse_lyrics_question_mark_vs_opening_quote():
    # UEB 7.6.7: the single cell (dots 2,3,6 / ASCII '8') is a question mark
    # unless it's the first cell of a word, in which case it's an opening
    # double quotation mark; UEB 7.6.1's closing double quote (dots 3,5,6 /
    # ASCII '0') is unambiguous.
    syllables = parse_lyrics(_cells("WHY8"))
    assert syllables == [("why?", False)]

    syllables = parse_lyrics(_cells("8YES6 0"))
    assert syllables == [("“yes!", False), ("”", False)]


def test_parse_lyrics_two_cell_and_single_quotes():
    # UEB 7.6.7/7.6.8 unambiguous two-cell quotes (ASCII '^8'/'^0') and
    # UEB 7.6.2 single quotes (ASCII ',8'/',0').
    syllables = parse_lyrics(_cells("^8HI^0"))
    assert syllables == [("“hi”", False)]

    syllables = parse_lyrics(_cells(",8HI,0"))
    assert syllables == [("‘hi’", False)]


def test_parse_lyrics_numbers():
    # UEB Section 6: numeral sign '#' (dots 3,4,5,6) + a-j-shaped letter
    # cells reads as digits 1-9,0, terminated by a space or hyphen.
    syllables = parse_lyrics(_cells("VERSE #AB"))
    assert syllables == [("verse", False), ("12", False)]


def test_parse_lyrics_accented_letters():
    # UEB 4.2: "café" is c-a-f-[acute accent, ASCII '^/']-e.
    syllables = parse_lyrics(_cells("CAF^/E"))
    assert syllables == [("café", False)]

    # UEB 4.2.2: a capitalized accented letter places the capital indicator
    # (dot 6) before the modifier: "Étienne" is [cap][grave? no, acute]-e...
    # -t-i-e-n-n-e, matching the rulebook's own "Étienne" example.
    syllables = parse_lyrics(_cells(",^/ETIENNE"))
    assert syllables == [("Étienne", False)]

    # UEB 4.2.3: modifiers don't break whole-word capitalization -- "AOÛT"
    # (French for "August") is the rulebook's own example: ,,A O [circumflex]U T
    syllables = parse_lyrics(_cells(",,AO^%UT"))
    assert syllables == [("AOÛT", False)]


def test_parse_lyrics_unrecognized_cell_raises():
    # dots 1,2,3,4,5,6 (ASCII '=') has no assigned meaning in this decoder's
    # UEB Grade 1 subset and isn't a letter -- it must raise rather than
    # silently mis-decode, per BANA's "no silent failures" policy.
    with pytest.raises(BrailleParseError):
        parse_lyrics(_cells("A=B"))


def test_vocal_lyrics_mapping_integration():
    # A simple vocal + piano accompaniment BRF score. Per BANA Sec. 35.1/37.2,
    # a single voice's word line has *no* instrument abbreviation at all --
    # it's plain literary text at the margin, immediately followed by the
    # voice's ordinary WORD_SIGN-abbreviated music line (same §33.2 shape as
    # any other instrument's abbreviation).
    brf_text = (
        "⠠⠎⠕⠏⠗⠁⠝⠕⠀⠀⠀⠜⠎⠄\n"
        "⠠⠏⠊⠁⠝⠕⠀⠀⠀⠜⠏⠄\n"
        "\n"
        "⠼⠁\n"
        "⠠⠓⠕⠤⠇⠽\n"
        "⠜⠎⠄⠀⠐⠽⠉⠐⠵⠐⠯\n"
        "⠜⠏⠄⠀⠐⠽⠐⠵⠐⠯\n"
    )
    score = EnsembleParser().parse(brf_text)
    
    assert len(score.staves) == 2
    soprano_staff = score.staves[0]
    piano_staff = score.staves[1]
    
    assert soprano_staff.name == "Soprano"
    assert piano_staff.name == "Piano"
    
    # Soprano staff should have lyrics parsed and mapped
    # C4(slur) D4, E4 -> Group 1: [C4, D4], Group 2: [E4]
    # Syllables: Ho-ly, Ho-ly
    # Groups match to: "Ho --", "ly"
    assert soprano_staff.lyrics == ["Ho --", "ly"]
    
    # LilyPond output check
    ly_output = score.to_lilypond()
    
    # Check that Soprano staff uses \new Staff \with { ... } << \new Voice ... \new Lyrics \lyricsto ... >>
    assert '} <<' in ly_output
    assert '\\new Voice = "vocals_soprano"' in ly_output
    assert '\\new Lyrics \\lyricsto "vocals_soprano" { Ho -- ly }' in ly_output
    # Check that Piano staff uses standard \new Staff \with { ... } { ... }
    assert '} {' in ly_output


# ---------------------------------------------------------------------------
# S7b-9/S11c-11: real-fixture integration test -- vocal_test.brf (Soprano +
# Piano Right Hand + Piano Left-Hand, an art-song-shaped score with lyrics,
# a crescendo/decrescendo pair, and a whole-measure repeat sign that
# carries its own new dynamic marking) parses end to end, associates
# lyrics with the soprano line, and -- per CLAUDE.md's "check the compile
# log for warnings, not just the exit code" testing philosophy --
# transcribes to LilyPond that compiles with the real lilypond binary with
# zero warnings. Mirrors the tmp_path/skip-if pattern already established
# in test_lilypond_formatter.py's _compile_and_check_no_warnings for the
# other three formatting categories.
#
# S11c-11 rewrote this fixture from the (incorrect) §33 ensemble-parallel
# format into true BANA §35.1 (vocal solo) + §29.8 (keyboard accompaniment)
# format, parsed here via `parse_solo_with_accompaniment` instead of
# `EnsembleParser`. One consequence of the real format: unlike §33's
# instrument-list header, neither §35.1 nor §29.8 puts instrument *names*
# anywhere in the content itself (§35.1.2: "No part identifier is
# necessary... the voice category... will have been given in the
# preliminary material") -- so `staff.name` comes back as whatever generic
# default `BrailleParser` uses for an unnamed staff, not "Soprano"/"Piano
# Right Hand"/"Piano Left-Hand". A real CLI/UI workflow would need to
# supply those names from external context (the same way S10d-12's part
# extraction already needs outside metadata); this test checks structure
# and lyrics instead of recovered names.
# ---------------------------------------------------------------------------


def test_vocal_test_fixture_groups_staves_and_maps_lyrics():
    text = BRLInputPipeline().load(FIXTURES / "vocal_test.brf")
    score = parse_solo_with_accompaniment(text)

    assert len(score.staves) == 3
    assert get_instrument_family("Soprano") == InstrumentFamily.VOCAL
    assert get_instrument_family("Piano Right Hand") == InstrumentFamily.KEYBOARD_HARP
    assert get_instrument_family("Piano Left-Hand") == InstrumentFamily.KEYBOARD_HARP

    soprano_staff, piano_right_staff, piano_left_staff = score.staves
    assert soprano_staff.lyrics[:2] == ["Let", "me"]
    assert soprano_staff.lyrics[-1] == "hope."
    # "flowers" (2 syllables, both on their own note, no braille hyphen per
    # §35.1.1(a)) is written as one continuous word -- unlike the old
    # ensemble-format fixture, which baked a "flo --"/"wers" LilyPond-style
    # split into the content itself (not real BANA braille; see S11c-9's
    # test_vocal_solo_renderer_omits_print_hyphen_between_syllables for why
    # that split can't be recovered from braille alone).
    assert "flowers" in soprano_staff.lyrics
    assert piano_right_staff.lyrics == []
    assert piano_left_staff.lyrics == []


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


def _load_vocal_test_score() -> Score:
    """Parse vocal_test.brf and assign the instrument names its LilyPond
    ground truth expects -- not recoverable from §35.1/§29.8 content
    itself (see the module note above `test_vocal_test_fixture_groups_
    staves_and_maps_lyrics`), so a real workflow would supply them from
    external context the same way this test does explicitly."""
    from dottednotes.models.orchestra_score import OrchestraScore

    text = BRLInputPipeline().load(FIXTURES / "vocal_test.brf")
    score = parse_solo_with_accompaniment(text)
    score.staves[0].name = "Soprano"
    score.staves[1].name = "Piano Right Hand"
    score.staves[2].name = "Piano Left-Hand"

    combined = OrchestraScore(title=score.title)
    for staff in score.staves:
        combined.add_staff(staff)
    return combined


def test_vocal_test_fixture_matches_ground_truth():
    score = _load_vocal_test_score()

    ly_output = score.to_lilypond()
    ground_truth = (FIXTURES / "vocal_test.ly").read_text(encoding="utf-8")
    assert ly_output == ground_truth


def test_vocal_test_fixture_compiles_cleanly(tmp_path: Path):
    if not shutil.which("lilypond"):
        pytest.skip("lilypond binary not found; skipping compile test")

    score = _load_vocal_test_score()

    ly_output = score.to_lilypond()
    assert '\\new Voice = "vocals_soprano"' in ly_output
    assert '\\new Lyrics \\lyricsto "vocals_soprano"' in ly_output

    _compile_and_check_no_warnings(ly_output, tmp_path, "vocal_test")


def test_parse_strophic_multiverse_lyrics_and_refrain():
    # Soprano instrument abbreviation is ⠜⠎⠄ (\x1cs.)
    # We will provide:
    # Verse 1 text: ⠶⠼⠁⠶⠀⠠⠓⠕⠤⠇⠽ (brackets around number 1, then "Ho-ly")
    # Verse 2 text: ⠶⠼⠃⠶⠀⠠⠛⠇⠕⠤⠗⠽ (brackets around number 2, then "Glo-ry")
    # Soprano music line
    # Then a second system representing a refrain:
    # Refrain text: ⠠⠗⠑⠋⠗⠁⠊⠝⠀⠠⠁⠤⠍⠑⠝ ("Refrain A-men")
    # Soprano music line
    brf_text = (
        "⠠⠎⠕⠏⠗⠁⠝⠕⠀⠀⠀⠜⠎⠄\n"
        "\n"
        "⠼⠁\n"
        "⠶⠼⠁⠶⠀⠠⠓⠕⠤⠇⠽\n"
        "⠶⠼⠃⠶⠀⠠⠛⠇⠕⠤⠗⠽\n"
        "⠜⠎⠄⠀⠐⠽⠉⠐⠵⠐⠯\n"
        "\n"
        "⠼⠃\n"
        "⠠⠗⠑⠋⠗⠁⠊⠝⠀⠠⠁⠤⠍⠑⠝\n"
        "⠜⠎⠄⠀⠐⠽⠉⠐⠵⠐⠯\n"
    )
    
    score = EnsembleParser().parse(brf_text)
    assert len(score.staves) == 1
    staff = score.staves[0]
    
    assert staff.name == "Soprano"
    assert len(staff.verses) == 2
    
    # Verse 1: "Ho --", "ly", "A --", "men"
    # Verse 2: "Glo --", "ry", "A --", "men"
    # (Since system 2 is a single refrain line, it is replicated across all verses)
    # The leading "1."/"2." verse-number prefix is NOT baked into the first
    # syllable -- it lives only in staff.verse_prefixes, and rendering adds
    # the `\set stanza = "..."` directive from there exactly once (S8b-13).
    # The refrain's "Refrain." label, however, is a *mid-stream* stanza
    # change partway through the verse's lyrics, which rendering has no
    # other way to express -- so that one is still baked into the syllable.
    assert staff.verses[0] == ['Ho --', 'ly', '\\set stanza = "Refrain. " A --', 'men']
    assert staff.verses[1] == ['Glo --', 'ry', '\\set stanza = "Refrain. " A --', 'men']

    assert staff.verse_prefixes == ["1.", "2."]

    ly_output = score.to_lilypond()

    # Verify that the stanzas and stacked lyrics are output correctly, with
    # each verse's leading stanza directive appearing exactly once (S8b-13
    # regression check -- a loose substring check can't detect a doubled
    # directive sitting in front of the very text it's checking for).
    assert '\\set stanza = "1. " Ho -- ly \\set stanza = "Refrain. " A -- men' in ly_output
    assert '\\set stanza = "2. " Glo -- ry \\set stanza = "Refrain. " A -- men' in ly_output
    assert ly_output.count('\\set stanza = "1. "') == 1
    assert ly_output.count('\\set stanza = "2. "') == 1
    assert ly_output.count('\\set stanza = "Refrain. "') == 2
    assert '\\new Lyrics \\lyricsto "vocals_soprano"' in ly_output
    assert ly_output.count('\\new Lyrics \\lyricsto') == 2


def test_parse_strophic_with_word_number_verse_prefixes():
    # Let's test a plain number sign like ⠼⠁ (without brackets) at the start of a verse line.
    # ⠼⠁⠀⠠⠓⠕⠤⠇⠽ -> 1. Ho-ly
    # ⠼⠃⠀⠠⠛⠇⠕⠤⠗⠽ -> 2. Glo-ry
    brf_text = (
        "⠠⠎⠕⠏⠗⠁⠝⠕⠀⠀⠀⠜⠎⠄\n"
        "\n"
        "⠼⠁\n"
        "⠼⠁⠀⠠⠓⠕⠤⠇⠽\n"
        "⠼⠃⠀⠠⠛⠇⠕⠤⠗⠽\n"
        "⠜⠎⠄⠀⠐⠽⠉⠐⠵⠐⠯\n"
    )
    score = EnsembleParser().parse(brf_text)
    staff = score.staves[0]
    
    assert staff.verse_prefixes == ["1.", "2."]
    # The verse-number prefix lives only in staff.verse_prefixes, not baked
    # into the first syllable -- rendering adds it exactly once (S8b-13).
    assert staff.verses[0] == ['Ho --', 'ly']
    assert staff.verses[1] == ['Glo --', 'ry']

    ly_output = score.to_lilypond()
    assert '\\set stanza = "1. " Ho -- ly' in ly_output
    assert '\\set stanza = "2. " Glo -- ry' in ly_output
    assert ly_output.count('\\set stanza = "1. "') == 1
    assert ly_output.count('\\set stanza = "2. "') == 1


# ---------------------------------------------------------------------------
# S11c-9: BANA §35.1 solo-vocal line-by-line braille format (words at cell
# 1, paired music at cell 3, no instrument-abbreviation prefix) -- distinct
# from both the plain instrumental SINGLE_LINE format and the §33
# ensemble-abbreviation format `EnsembleParser` already covers.
# ---------------------------------------------------------------------------


def _vocal_solo_score(lyrics=("Sing", "high")) -> Score:
    score = Score(title="")
    staff = Staff(name="Soprano")
    staff.time_signature = TimeSignature(
        dots=frozenset(), category=None, raw_brl="", numerator=4, denominator=4
    )
    m = Measure(number=1)
    c = Note(dots=frozenset(), category=None, raw_brl="", note_name="C", octave=4, duration=Duration(value=4))
    c.slur_start = True
    d = Note(dots=frozenset(), category=None, raw_brl="", note_name="D", octave=4, duration=Duration(value=4))
    d.slur_end = True
    e = Note(dots=frozenset(), category=None, raw_brl="", note_name="E", octave=4, duration=Duration(value=4))
    for note in (c, d, e):
        m.add_note(note)
    staff.add_measure(m)
    # A melisma ("Sing" spans the slurred C/D pair -- one word, one
    # syllable, sung across two notes) followed by a separate word ("high")
    # on the plain E -- two distinct, space-separated braille words, so the
    # round trip below doesn't run into §35.1.1(a)'s hyphen-omission rule
    # (see test_vocal_solo_renderer_omits_print_hyphen_between_syllables
    # for that case, which is legitimately lossy on the way back in).
    staff.lyrics = list(lyrics)
    score.add_staff(staff)
    return score


def test_vocal_solo_renderer_uses_cell1_cell3_no_abbreviation():
    score = _vocal_solo_score()
    output = BrailleRenderer(line_width=40).render(score)
    lines = [line for line in output.split("\n") if line]

    # lines[0] is the cell-9 signature header; the parallel starts at [1].
    # Lyric line at cell 1 (no leading blank cells).
    assert not lines[1].startswith('⠀')
    # Music line at cell 3 (exactly 2 leading blank cells).
    assert lines[2].startswith('⠀⠀') and not lines[2].startswith('⠀⠀⠀')
    # §35.1.2: "No part identifier is necessary" -- no abbreviation sign.
    assert '⠜' not in lines[2]


def test_vocal_solo_renderer_omits_print_hyphen_between_syllables():
    # §35.1.1(a): a print hyphen dividing one word's syllables is not
    # written in braille -- "Ho --"/"ly" (the LilyPond-flavored syllable
    # continuation convention `Staff.lyrics` uses) must render as the
    # single concatenated word "Holy", with no hyphen and no space. This
    # is inherently lossy on the way back in (nothing in the braille marks
    # where "Holy" divides into syllables -- see the module docstring), so
    # it's covered here as a one-way render check, not a round trip.
    score = _vocal_solo_score(lyrics=["Ho --", "ly"])
    output = BrailleRenderer(line_width=40).render(score)
    lines = [line for line in output.split("\n") if line]
    assert lines[1] == encode_lyric_line(["Holy"])


def test_encode_lyric_line_handles_accented_letters_round_trip():
    # BANA §35.1.1(d): "Accented letters in foreign words in an English
    # language context" -- e.g. a German lied's "schön". Real-world
    # regression: Schumann's Dichterliebe (tests/fixtures/
    # dichterliebe01.musicxml) has umlauts in its German lyrics, which
    # crashed BrailleRenderer._render_vocal_solo() the first time a real
    # vocal+piano MusicXML fixture exercised this code path end to end.
    encoded = encode_lyric_line(["schön", "Übung"])
    syllables = parse_lyrics(encoded)
    assert [s for s, _ in syllables] == ["schön", "Übung"]


def test_encode_lyric_line_treats_smart_apostrophe_as_plain_apostrophe():
    # MusicXML sources commonly spell a contraction apostrophe as the
    # Unicode "smart" right single quotation mark (U+2019) rather than a
    # plain ASCII "'" -- also a real Dichterliebe regression.
    encoded = encode_lyric_line(["sagen’s"])
    syllables = parse_lyrics(encoded)
    assert [s for s, _ in syllables] == ["sagen's"]


def test_vocal_solo_round_trips_through_parser():
    score = _vocal_solo_score()
    output = BrailleRenderer(line_width=40).render(score)

    parsed = parse_vocal_solo(output)

    assert len(parsed.staves) == 1
    staff = parsed.staves[0]
    assert staff.lyrics == ["Sing", "high"]
    assert len(staff.measures) == 1
    notes = staff.measures[0].notes
    assert [(n.note_name, n.octave) for n in notes] == [("C", 4), ("D", 4), ("E", 4)]
    assert notes[0].slur_start and notes[1].slur_end


def test_vocal_solo_parser_rejects_input_with_no_music_line():
    with pytest.raises(BrailleParseError):
        parse_vocal_solo("⠠⠓⠕⠤⠇⠽")


def test_vocal_solo_does_not_compress_repeated_measure_into_measure_repeat_sign():
    # Two musically-identical measures with *different* lyrics -- BANA's
    # measure-repeat sign (used elsewhere for instrumental parts) has no
    # discrete notes for a reader to align new words against, so it must
    # never be used here even though the melody repeats verbatim.
    score = Score(title="")
    staff = Staff(name="Soprano")
    staff.time_signature = TimeSignature(
        dots=frozenset(), category=None, raw_brl="", numerator=4, denominator=4
    )
    for i in range(2):
        m = Measure(number=i + 1)
        for name in ("C", "D", "E", "F"):
            m.add_note(Note(dots=frozenset(), category=None, raw_brl="", note_name=name, octave=4, duration=Duration(value=4)))
        staff.add_measure(m)
    staff.lyrics = ["One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight"]
    score.add_staff(staff)

    output = BrailleRenderer(line_width=20).render(score)
    # BANA's measure-repeat cell (⠶) must not appear -- the second measure
    # is written out in full, with its own distinct lyrics.
    assert '⠶' not in output

    parsed = parse_vocal_solo(output)
    assert parsed.staves[0].lyrics == ["One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight"]
    assert len(parsed.staves[0].measures) == 2


# ---------------------------------------------------------------------------
# S11c-16: BANA §35.9/§35.10 -- vocal solo measure numbers are omitted by
# default, but a part extracted from a choral/full score whose print
# source numbers by page layout (not musical structure) may show a real
# measure number at a configurable parallel cadence instead.
# ---------------------------------------------------------------------------


def _numbered_vocal_score(n_measures=4):
    score = Score(title="")
    staff = Staff(name="Soprano")
    staff.time_signature = TimeSignature(
        dots=frozenset(), category=None, raw_brl="", numerator=4, denominator=4
    )
    words = ["alpha", "bravo", "charlie", "delta", "echo", "foxtrot",
             "golf", "hotel", "india", "juliet", "kilo", "lima",
             "mike", "november", "oscar", "papa"]
    lyrics = []
    for i in range(n_measures):
        m = Measure(number=i + 1)
        for name in ("C", "D", "E", "F"):
            m.add_note(Note(dots=frozenset(), category=None, raw_brl="", note_name=name, octave=5, duration=Duration(value=4)))
        staff.add_measure(m)
        lyrics.extend(words[i * 4:i * 4 + 4])
    staff.lyrics = lyrics
    score.add_staff(staff)
    return score


def test_vocal_solo_measure_numbers_off_by_default():
    # §35.9's default ("not usually included") round-trips cleanly with no
    # measure-number stripping requested -- confirming no number was
    # actually inserted (a raw-cell scan can't tell this apart from a
    # lowercase word starting with a letter that happens to share a cell
    # with a digit, e.g. "alpha" and digit 1 both start with dot 1).
    score = _numbered_vocal_score()
    output = BrailleRenderer(line_width=12).render(score)

    parsed = parse_vocal_solo(output)
    assert parsed.staves[0].lyrics == score.staves[0].lyrics


def test_vocal_solo_measure_number_cadence_round_trips():
    score = _numbered_vocal_score()
    renderer = BrailleRenderer(line_width=12, vocal_measure_number_every=2)
    output = renderer.render(score)

    parsed = parse_vocal_solo(output, has_measure_numbers=True)
    assert parsed.staves[0].lyrics == score.staves[0].lyrics
    assert len(parsed.staves[0].measures) == 4


def test_vocal_solo_measure_number_every_1_shows_every_parallel():
    score = _numbered_vocal_score()
    renderer = BrailleRenderer(line_width=12, vocal_measure_number_every=1)
    output = renderer.render(score)
    lines = [l for l in output.split("\n") if l]

    from dottednotes.bana_symbols import LITERARY_DIGITS
    # Every parallel's word line (i.e. every line starting a new lyric
    # phrase, not a run-over continuation at cell 5) must start with a digit.
    word_line_starts = [l for l in lines[1:] if not l.startswith('⠀')]
    assert word_line_starts
    assert all(l[0] in LITERARY_DIGITS for l in word_line_starts)

    parsed = parse_vocal_solo(output, has_measure_numbers=True)
    assert parsed.staves[0].lyrics == score.staves[0].lyrics


def test_vocal_solo_rejects_negative_measure_number_cadence():
    with pytest.raises(ValueError):
        BrailleRenderer(vocal_measure_number_every=-1)
