import pytest
from dottednotes.parser.braille_parser import BrailleParser
from dottednotes.parser.tokenizer import BrailleTokenizer
from dottednotes.parser.ensemble_parser import EnsembleParser
from dottednotes.validation.validator import BANAValidator
from dottednotes.models.score import Score
from dottednotes.models.staff import Staff
from dottednotes.models.measure import Measure
from dottednotes.models.note import Note
from dottednotes.models.duration import Duration
from dottednotes.renderers.braille_renderer import BrailleRenderer, encode_literary_braille
from dottednotes.renderers.brf_writer import BRFWriter


def parse_brf(brf_text: str) -> Score:
    tokens = BrailleTokenizer().tokenize(brf_text)
    return BrailleParser(tokens=tokens).parse()


def test_layout_title_centering():
    # Title not centered (offset to the left or lacks 3 spaces margins)
    brf_text = "⠠⠎⠕⠝⠛⠲\n⠐⠹"
    score = parse_brf(brf_text)
    score.title = "Song"
    
    validator = BANAValidator(enabled_rules=["S11c-2"])
    result = validator.validate(score, raw_brl_text=brf_text)
    
    title_warns = [c for c in result.corrections if "Title Centering" in c.message]
    assert len(title_warns) == 1
    assert title_warns[0].rule_id == "S11c-2"
    
    # Rendering should center the title automatically
    rendered = score.to_braille()
    assert "      ⠠⠎⠕⠝⠛⠲" in rendered


def test_layout_signature_indentation():
    # Signature line has time signature but is not indented 8 spaces
    # ⠼⠉⠲ is 3/4 time signature
    brf_text = "⠼⠉⠲\n⠐⠹"
    score = parse_brf(brf_text)
    
    validator = BANAValidator(enabled_rules=["S11c-2"])
    result = validator.validate(score, raw_brl_text=brf_text)
    
    sig_warns = [c for c in result.corrections if "Signature Line Indentation" in c.message]
    assert len(sig_warns) == 1
    
    # Rendering should indent signature line by 8 spaces
    rendered = score.to_braille()
    assert "        ⠼⠉⠲" in rendered


def test_layout_heading_spacing():
    # Blank line between signature and music
    brf_text = "        ⠼⠉⠲\n\n⠐⠹"
    score = parse_brf(brf_text)
    
    validator = BANAValidator(enabled_rules=["S11c-2"])
    result = validator.validate(score, raw_brl_text=brf_text)
    
    spacing_warns = [c for c in result.corrections if "Heading Spacing" in c.message]
    assert len(spacing_warns) == 1
    
    # Rendering should not have any blank line between signatures and first music line
    rendered = score.to_braille()
    assert "        ⠼⠉⠲\n⠁ ⠐⠹" in rendered


def test_layout_running_head_centering():
    # Multipage document. Page 2 starts with uncentered running head
    brf_text = "      ⠠⠎⠕⠝⠛⠲\n⠐⠹\n\f⠠⠎⠕⠝⠛⠀⠃"
    score = parse_brf("⠐⠹\n⠐⠹")
    score.title = "Song"
    
    validator = BANAValidator(enabled_rules=["S11c-2"])
    result = validator.validate(score, raw_brl_text=brf_text)
    
    rh_warns = [c for c in result.corrections if "Running Head" in c.message]
    assert len(rh_warns) == 1
    
    # BRFWriter should center the running head on page 2
    writer = BRFWriter(line_width=40, page_height=1)
    rendered = writer.render_to_string(score)
    pages = rendered.split('\f')
    assert len(pages) > 1
    expected_header = "                 ⠠⠎⠕⠝⠛                 ⠃"
    assert pages[1].splitlines()[0] == expected_header


def test_layout_piano_parallels_have_no_blank_lines():
    # BANA chapters 28 (bar-over-bar general principles) and 29 (keyboard
    # instruments) never mention blank-line separation between parallels --
    # unlike solo/ensemble/figured-bass formats, which do. Each new
    # keyboard parallel is introduced solely by its own measure-number
    # margin marker (29.3(b)), directly following the previous one.
    brf_text = "⠁⠀⠨⠜⠐⠹\n⠀⠀⠸⠜⠐⠹\n\n⠃⠀⠨⠜⠐⠹\n⠀⠀⠸⠜⠐⠹"

    score = parse_brf(brf_text)
    score.staves[0].name = "piano right hand"
    score.staves[1].name = "piano left hand"

    # Force each measure into its own parallel (narrow line width) so
    # there's an inter-parallel boundary to check.
    rendered = BrailleRenderer(line_width=8, compression_level="none").render(score)
    assert "\n\n" not in rendered


def test_layout_organ_parallels_have_no_blank_lines():
    # Same check as test_layout_piano_parallels_have_no_blank_lines, but
    # with staff names that don't literally contain "piano"/"harp" --
    # regression test for the keyboard-family detection bug where
    # "Organ"/"Harpsichord"/etc. staves fell through to the solo layout.
    brf_text = "⠁⠀⠨⠜⠐⠹\n⠀⠀⠸⠜⠐⠹\n\n⠃⠀⠨⠜⠐⠹\n⠀⠀⠸⠜⠐⠹"

    score = parse_brf(brf_text)
    score.staves[0].name = "Organ right hand"
    score.staves[1].name = "Organ left hand"

    rendered = BrailleRenderer(line_width=8, compression_level="none").render(score)
    assert "\n\n" not in rendered
    # Exporting must not silently drop the left-hand staff either.
    assert "⠨⠜" in rendered and "⠸⠜" in rendered


def test_layout_ensemble_parallel_spacing():
    # Ensemble music with no blank lines preceding a parallel
    brf_text = (
        '⠠⠋⠇⠥⠞⠑⠀⠐⠐⠐⠐⠐⠀⠀⠜⠋⠇⠄\n'
        '⠠⠧⠊⠕⠇⠊⠝⠀⠐⠐⠀⠀⠀⠜⠧⠇⠄\n'
        '⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠣⠣⠣⠼⠙⠲\n'
        '⠁⠀⠀⠜⠋⠇⠄⠐⠹⠱⠫⠻⠀⠐⠳⠪⠺⠹\n'
        '⠀⠀⠀⠜⠧⠇⠄⠸⠳⠪⠺⠹⠀⠸⠹⠱⠫⠻\n'
        '⠃⠀⠀⠜⠋⠇⠄⠐⠹⠱⠫⠻⠀⠐⠳⠪⠺⠹\n'
        '⠀⠀⠀⠜⠧⠇⠄⠸⠳⠪⠺⠹⠀⠸⠹⠱⠫⠻\n'
    )
    
    score = EnsembleParser().parse(brf_text)
    
    validator = BANAValidator(enabled_rules=["S11c-2"])
    result = validator.validate(score, raw_brl_text=brf_text)
    
    ensemble_warns = [c for c in result.corrections if "Ensemble parallels must be preceded by at least 1 blank line" in c.message]
    assert len(ensemble_warns) == 1
    
    # Exporting should format it with exactly 1 blank line before the parallel heading
    rendered = BrailleRenderer(line_width=15, compression_level="none").render(score)
    lines = rendered.splitlines()
    blank_indices = [i for i, line in enumerate(lines) if line == ""]
    assert len(blank_indices) == 1
    assert '⠼' in lines[blank_indices[0] + 1]
