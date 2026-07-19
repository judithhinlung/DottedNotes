import os
from pathlib import Path
from typing import Union
from dottednotes.models.score import Score
from dottednotes.renderers.braille_renderer import BrailleRenderer, encode_literary_braille

# Invert ASCII_TO_DOTS from input_pipeline
from dottednotes.parser.input_pipeline import ASCII_TO_DOTS
_DOTS_TO_ASCII = {v: k for k, v in ASCII_TO_DOTS.items()}
_DOTS_TO_ASCII[0] = ' '  # space maps to space


def unicode_to_ascii_braille(text: str) -> str:
    """Convert Unicode braille text to North American Braille ASCII."""
    result = []
    for char in text:
        if char in ('\n', '\r', '\f', '\t'):
            result.append(char)
        else:
            offset = ord(char) - 0x2800
            if 0 <= offset <= 255:
                # Mask with 0x3f to get 6-bit offset
                mask_offset = offset & 0x3f
                result.append(_DOTS_TO_ASCII.get(mask_offset, '?'))
            else:
                result.append(char)
    return "".join(result)


class BRFWriter:
    def __init__(self, line_width: int = 40, page_height: int = 25, show_measure_numbers: bool = True, compression_level: str = "full"):
        self.line_width = line_width
        self.page_height = page_height
        self.show_measure_numbers = show_measure_numbers
        self.compression_level = compression_level

    def write(self, score: Score, filepath: Union[str, Path]) -> None:
        """Render a score and write it to a BRF file in ASCII braille."""
        brl_content = self.render_to_string(score)
        ascii_content = unicode_to_ascii_braille(brl_content)
        Path(filepath).write_text(ascii_content, encoding="utf-8")

    def write_unicode(self, score: Score, filepath: Union[str, Path]) -> None:
        """Render a score and write it to a BRL file in Unicode braille."""
        brl_content = self.render_to_string(score)
        Path(filepath).write_text(brl_content, encoding="utf-8")

    def render_to_string(self, score: Score) -> str:
        """Render the score to a paginated Unicode braille string."""
        renderer = BrailleRenderer(
            line_width=self.line_width,
            show_measure_numbers=self.show_measure_numbers,
            compression_level=self.compression_level
        )
        raw_music = renderer.render(score)
        music_lines = [line.rstrip() for line in raw_music.splitlines()]

        pages = []
        current_page_lines = []
        page_num = 1

        title_brl = ""
        if score.title:
            # Strip the one trailing period `encode_literary_braille`
            # always appends, for header use -- exactly one trailing
            # character, not `.rstrip('⠲')`: the digit '4' encodes to
            # that same dots-2,5,6 cell, so a title actually ending in
            # "4" (e.g. "Symphony No. 4") would lose that digit too.
            title_brl = encode_literary_braille(score.title)[:-1]

        # We will iterate through lines and paginate
        # If the page height is exceeded, start a new page
        i = 0
        while i < len(music_lines):
            # Check if this is a new page and we need a header
            if not current_page_lines and page_num > 1 and title_brl:
                from dottednotes.renderers.braille_renderer import _INT_TO_LITERARY_DIGIT
                page_str = "".join(_INT_TO_LITERARY_DIGIT[int(d)] for d in str(page_num))
                
                start_idx = (self.line_width - len(title_brl)) // 2
                end_idx = start_idx + len(title_brl)
                left_space = start_idx
                right_space = self.line_width - end_idx - len(page_str)
                
                if left_space >= 3 and right_space >= 3:
                    header_line = " " * start_idx + title_brl + " " * (self.line_width - end_idx - len(page_str)) + page_str
                else:
                    max_title_len = self.line_width - len(page_str) - 6
                    if max_title_len > 0:
                        header_line = "   " + title_brl[:max_title_len] + "   " + page_str
                    else:
                        space_len = self.line_width - len(title_brl) - len(page_str)
                        if space_len < 1:
                            space_len = 1
                        header_line = title_brl + " " * space_len + page_str
                current_page_lines.append(header_line)

            current_page_lines.append(music_lines[i])
            i += 1

            if len(current_page_lines) >= self.page_height:
                pages.append("\n".join(current_page_lines))
                current_page_lines = []
                page_num += 1

        if current_page_lines:
            pages.append("\n".join(current_page_lines))

        # The form feed sits on its own line: a raw embosser/terminal
        # doesn't reset its column to 0 on \f the way it does on \n, so
        # \f immediately followed by text (the old "\f".join behavior)
        # shifted that text's indentation by however many columns the
        # previous page's last line had already used.
        return "\n\f\n".join(pages) + "\n"
