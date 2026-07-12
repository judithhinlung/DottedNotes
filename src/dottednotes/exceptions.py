class DottedNotesError(Exception):
    """Base class for expected, user-facing failure conditions -- malformed
    braille input or a failed LilyPond compile -- as opposed to an internal
    programmer error. The CLI catches this (and only this, plus a narrow
    set of OSError cases) to print a single plain-text, screen-reader-
    friendly message instead of a Python traceback. Anything else (a
    TypeError, an unhandled internal assertion, ...) is a real bug and
    should keep failing loudly during development.
    """


class BrailleParseError(DottedNotesError, ValueError):
    """Raised when braille music input cannot be parsed because it is
    malformed BANA notation, not because of an internal bug. Subclasses
    ValueError too, since several existing parser errors already did and
    are still allowed to be caught that way.
    """


class LilyPondCompileError(DottedNotesError):
    """Raised when `--compile` can't produce a PDF/MIDI file: the
    `lilypond` binary isn't installed, or it exited non-zero. `stderr`
    carries the compiler's own error output, if any.
    """

    def __init__(self, message: str, stderr: str = "") -> None:
        super().__init__(message)
        self.stderr = stderr
