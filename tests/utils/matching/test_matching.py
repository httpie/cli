"""
Here we test our output parsing and matching implementation, not HTTPie itself.

"""
from httpie.output.writer import MESSAGE_SEPARATOR
from tests.utils import CRLF
from tests.utils.matching import assert_output_does_not_match, assert_output_matches, Expect


def test_assert_matches_headers_incomplete():
    assert_output_does_not_match(f'HTTP/1.1{CRLF}', [Expect.RESPONSE_HEADERS])


def test_assert_matches_headers_unterminated():
    assert_output_does_not_match(
        (
            f'HTTP/1.1{CRLF}'
            f'AAA:BBB'
            f'{CRLF}'
        ),
        [Expect.RESPONSE_HEADERS],
    )


def test_assert_matches_response_headers():
    assert_output_matches(
        (
            f'HTTP/1.1 200 OK{CRLF}'
            f'AAA:BBB{CRLF}'
            f'{CRLF}'
        ),
        [Expect.RESPONSE_HEADERS],
    )


def test_assert_matches_request_headers():
    assert_output_matches(
        (
            f'GET / HTTP/1.1{CRLF}'
            f'AAA:BBB{CRLF}'
            f'{CRLF}'
        ),
        [Expect.REQUEST_HEADERS],
    )


def test_assert_matches_headers_and_separator():
    assert_output_matches(
        (
            f'HTTP/1.1{CRLF}'
            f'AAA:BBB{CRLF}'
            f'{CRLF}'
            f'{MESSAGE_SEPARATOR}'
        ),
        [Expect.RESPONSE_HEADERS, Expect.SEPARATOR],
    )


def test_assert_matches_body_unmatched_crlf():
    assert_output_does_not_match(f'AAA{CRLF}', [Expect.BODY])


def test_assert_matches_body_unmatched_message_separator():
    assert_output_does_not_match(f'AAA{MESSAGE_SEPARATOR}', [Expect.BODY])


def test_assert_matches_body_and_separator():
    assert_output_matches(f'AAA{MESSAGE_SEPARATOR}', [Expect.BODY, Expect.SEPARATOR])


def test_assert_matches_body_r():
    assert_output_matches(f'AAA\r', [Expect.BODY])


def test_assert_matches_body_n():
    assert_output_matches(f'AAA\n', [Expect.BODY])


def test_assert_matches_body_r_body():
    assert_output_matches(f'AAA\rBBB', [Expect.BODY])


def test_assert_matches_body_n_body():
    assert_output_matches(f'AAA\nBBB', [Expect.BODY])


def test_assert_matches_headers_and_body():
    assert_output_matches(
        (
            f'HTTP/1.1{CRLF}'
            f'AAA:BBB{CRLF}'
            f'{CRLF}'
            f'CCC'
        ),
        [Expect.RESPONSE_HEADERS, Expect.BODY]
    )


def test_assert_matches_headers_body_separator():
    assert_output_matches(
        (
            f'HTTP/1.1 {CRLF}'
            f'AAA:BBB{CRLF}{CRLF}'
            f'CCC{MESSAGE_SEPARATOR}'
        ),
        [Expect.RESPONSE_HEADERS, Expect.BODY, Expect.SEPARATOR]
    )


def test_assert_matches_multiple_messages():
    assert_output_matches(
        (
            f'POST / HTTP/1.1{CRLF}'
            f'AAA:BBB{CRLF}'
            f'{CRLF}'

            f'CCC'
            f'{MESSAGE_SEPARATOR}'

            f'HTTP/1.1 200 OK{CRLF}'
            f'EEE:FFF{CRLF}'
            f'{CRLF}'

            f'GGG'
            f'{MESSAGE_SEPARATOR}'
        ), [
            Expect.REQUEST_HEADERS,
            Expect.BODY,
            Expect.SEPARATOR,
            Expect.RESPONSE_HEADERS,
            Expect.BODY,
            Expect.SEPARATOR,
        ]
    )
