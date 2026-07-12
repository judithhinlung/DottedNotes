import pytest

from dottednotes.exceptions import DottedNotesError, BrailleParseError, LilyPondCompileError


def test_braille_parse_error_is_a_dottednotes_error():
    assert issubclass(BrailleParseError, DottedNotesError)


def test_braille_parse_error_is_still_a_value_error():
    # Several existing parser errors (TripletDurationError, MeasureRepeatError)
    # already subclassed ValueError before S7-3; BrailleParseError keeps that
    # true so any pre-existing `except ValueError`/`pytest.raises(ValueError)`
    # call site keeps working unchanged.
    assert issubclass(BrailleParseError, ValueError)
    with pytest.raises(ValueError):
        raise BrailleParseError("malformed input")


def test_lilypond_compile_error_is_a_dottednotes_error():
    assert issubclass(LilyPondCompileError, DottedNotesError)


def test_lilypond_compile_error_carries_stderr():
    err = LilyPondCompileError("lilypond compilation failed", stderr="line 3: unexpected token")
    assert str(err) == "lilypond compilation failed"
    assert err.stderr == "line 3: unexpected token"


def test_lilypond_compile_error_stderr_defaults_to_empty():
    err = LilyPondCompileError("the 'lilypond' program is not installed")
    assert err.stderr == ""


def test_dottednotes_error_is_a_plain_exception_not_a_value_error():
    # The base class itself makes no promises about being a ValueError --
    # only BrailleParseError does, for the backward-compatibility reason
    # above. A generic DottedNotesError subclass should not silently be
    # catchable by an unrelated `except ValueError:`.
    assert issubclass(DottedNotesError, Exception)
    assert not issubclass(DottedNotesError, ValueError)
