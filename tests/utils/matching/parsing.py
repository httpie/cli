import re
from typing import Iterable
from enum import Enum, auto

from httpie.output.writer import MESSAGE_SEPARATOR
from tests.utils import CRLF


class Expect(Enum):
    """
    Predefined token types we can expect in the output.

    """
    REQUEST_HEADERS = auto()
    RESPONSE_HEADERS = auto()
    BODY = auto()
    SEPARATOR = auto()


SEPARATOR_RE = re.compile(f'^{MESSAGE_SEPARATOR}')


def make_headers_re(message_type: Expect):
    assert message_type in {Expect.REQUEST_HEADERS, Expect.RESPONSE_HEADERS}

    # language=RegExp
    crlf = r'[\r][\n]'
    non_crlf = rf'[^{CRLF}]'

    # language=RegExp
    http_version = r'HTTP/\d+\.\d+'
    if message_type is Expect.REQUEST_HEADERS:
        # POST /post HTTP/1.1
        start_line_re = fr'{non_crlf}*{http_version}{crlf}'
    else:
        # HTTP/1.1 200 OK
        start_line_re = fr'{http_version}{non_crlf}*{crlf}'

    return re.compile(
        fr'''
            ^
            {start_line_re}
            ({non_crlf}+:{non_crlf}+{crlf})+
            {crlf}
        ''',
        flags=re.VERBOSE
    )


BODY_ENDINGS = [
    MESSAGE_SEPARATOR,
    CRLF,  # Not really but useful for testing (just remember not to include it in a body).
]
TOKEN_REGEX_MAP = {
    Expect.REQUEST_HEADERS: make_headers_re(Expect.REQUEST_HEADERS),
    Expect.RESPONSE_HEADERS: make_headers_re(Expect.RESPONSE_HEADERS),
    Expect.SEPARATOR: SEPARATOR_RE,
}


class OutputMatchingError(ValueError):
    pass


def expect_tokens(tokens: Iterable[Expect], s: str):
    for token in tokens:
        s = expect_token(token, s)
    if s:
        raise OutputMatchingError(f'Unmatched remaining output for {tokens} in {s!r}')


def expect_token(token: Expect, s: str) -> str:
    if token is Expect.BODY:
        s = expect_body(s)
    else:
        s = expect_regex(token, s)
    return s


def expect_regex(token: Expect, s: str) -> str:
    match = TOKEN_REGEX_MAP[token].match(s)
    if not match:
        raise OutputMatchingError(f'No match for {token} in {s!r}')
    return s[match.end():]


def expect_body(s: str) -> str:
    """
    We require some text, and continue to read until we find an ending or until the end of the string.

    """
    if 'content-disposition:' in s.lower():
        # Multipart body heuristic.
        final_boundary_re = re.compile('\r\n--[^-]+?--\r\n')
        match = final_boundary_re.search(s)
        if match:
            return s[match.end():]

    endings = [s.index(sep) for sep in BODY_ENDINGS if sep in s]
    if not endings:
        s = ''  # Only body
    else:
        end = min(endings)
        if end == 0:
            raise OutputMatchingError(f'Empty body: {s!r}')
        s = s[end:]
    return s
