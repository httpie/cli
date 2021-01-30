from typing import Iterable

import pytest

from tests.utils.matching.parsing import OutputMatchingError, expect_tokens, Expect


__all__ = [
    'assert_output_matches',
    'assert_output_does_not_match',
    'Expect',
]


def assert_output_matches(output: str, tokens: Iterable[Expect]):
    r"""
    Check the command `output` for an exact full sequence of `tokens`.

    >>> out = 'GET / HTTP/1.1\r\nAAA:BBB\r\n\r\nCCC\n\n'
    >>> assert_output_matches(out, [Expect.REQUEST_HEADERS, Expect.BODY, Expect.SEPARATOR])

    """
    # TODO: auto-remove ansi colors to allow for testing of colorized output as well.
    expect_tokens(tokens=tokens, s=output)


def assert_output_does_not_match(output: str, tokens: Iterable[Expect]):
    r"""
    >>> assert_output_does_not_match('\r\n', [Expect.BODY])
    """
    with pytest.raises(OutputMatchingError):
        assert_output_matches(output=output, tokens=tokens)
