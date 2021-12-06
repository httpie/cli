"""
The ideas behind these test and the named templates is to ensure consistent output
across all supported different scenarios:

TODO: cover more scenarios
 * terminal vs. redirect stdout
 * different combinations of `--print=HBhb` (request/response headers/body)
 * multipart requests
 * streamed uploads

"""
from .utils.matching import assert_output_matches, Expect, ExpectSequence
from .utils import http, HTTP_OK, MockEnvironment


def test_headers():
    r = http('--print=H', '--offline', 'pie.dev')
    assert_output_matches(r, [Expect.REQUEST_HEADERS])


def test_redirected_headers():
    r = http('--print=H', '--offline', 'pie.dev', env=MockEnvironment(stdout_isatty=False))
    assert_output_matches(r, [Expect.REQUEST_HEADERS])


def test_terminal_headers_and_body():
    r = http('--print=HB', '--offline', 'pie.dev', 'AAA=BBB')
    assert_output_matches(r, ExpectSequence.TERMINAL_REQUEST)


def test_terminal_request_headers_response_body(httpbin):
    r = http('--print=Hb', httpbin + '/get')
    assert_output_matches(r, ExpectSequence.TERMINAL_REQUEST)


def test_raw_request_headers_response_body(httpbin):
    r = http('--print=Hb', httpbin + '/get', env=MockEnvironment(stdout_isatty=False))
    assert_output_matches(r, ExpectSequence.RAW_REQUEST)


def test_terminal_request_headers_response_headers(httpbin):
    r = http('--print=Hh', httpbin + '/get')
    assert_output_matches(r, [Expect.REQUEST_HEADERS, Expect.RESPONSE_HEADERS])


def test_raw_request_headers_response_headers(httpbin):
    r = http('--print=Hh', httpbin + '/get', env=MockEnvironment(stdout_isatty=False))
    assert_output_matches(r, [Expect.REQUEST_HEADERS, Expect.RESPONSE_HEADERS])


def test_terminal_request_body_response_body(httpbin):
    r = http('--print=Hh', httpbin + '/get')
    assert_output_matches(r, [Expect.REQUEST_HEADERS, Expect.RESPONSE_HEADERS])


def test_raw_headers_and_body():
    r = http(
        '--print=HB', '--offline', 'pie.dev', 'AAA=BBB',
        env=MockEnvironment(stdout_isatty=False),
    )
    assert_output_matches(r, ExpectSequence.RAW_REQUEST)


def test_raw_body():
    r = http('--print=B', '--offline', 'pie.dev', 'AAA=BBB', env=MockEnvironment(stdout_isatty=False))
    assert_output_matches(r, ExpectSequence.RAW_BODY)


def test_raw_exchange(httpbin):
    r = http('--verbose', httpbin + '/post', 'a=b', env=MockEnvironment(stdout_isatty=False))
    assert HTTP_OK in r
    assert_output_matches(r, ExpectSequence.RAW_EXCHANGE)


def test_terminal_exchange(httpbin):
    r = http('--verbose', httpbin + '/post', 'a=b')
    assert HTTP_OK in r
    assert_output_matches(r, ExpectSequence.TERMINAL_EXCHANGE)


def test_headers_multipart_body_separator():
    r = http('--print=HB', '--multipart', '--offline', 'pie.dev', 'AAA=BBB')
    assert_output_matches(r, ExpectSequence.TERMINAL_REQUEST)


def test_redirected_headers_multipart_no_separator():
    r = http(
        '--print=HB', '--multipart', '--offline', 'pie.dev', 'AAA=BBB',
        env=MockEnvironment(stdout_isatty=False),
    )
    assert_output_matches(r, ExpectSequence.RAW_REQUEST)


def test_verbose_chunked(httpbin_with_chunked_support):
    r = http('--verbose', '--chunked', httpbin_with_chunked_support + '/post', 'hello=world')
    assert HTTP_OK in r
    assert 'Transfer-Encoding: chunked' in r
    assert_output_matches(r, ExpectSequence.TERMINAL_EXCHANGE)


def test_request_headers_response_body(httpbin):
    r = http('--print=Hb', httpbin + '/get')
    assert_output_matches(r, ExpectSequence.TERMINAL_REQUEST)
