from tests.utils.matching import assert_output_matches, Expect
from utils import http, HTTP_OK

# TODO: Test for all the many scenarios: pretty/non-pretty, streamed uploads, multipart, etc.


def test_headers():
    r = http('--print=HB', '--offline', 'pie.dev', )
    assert_output_matches(r, [Expect.REQUEST_HEADERS, Expect.SEPARATOR])


def test_headers_body():
    r = http('--print=HB', '--offline', 'pie.dev', 'a=b')
    assert_output_matches(r, [Expect.REQUEST_HEADERS, Expect.BODY, Expect.SEPARATOR])


def test_verbose(httpbin):
    r = http('--verbose', httpbin + '/post', 'a=b')
    assert HTTP_OK in r
    assert_output_matches(r, [
        Expect.REQUEST_HEADERS,
        Expect.BODY,
        Expect.SEPARATOR,
        Expect.SEPARATOR,
        Expect.RESPONSE_HEADERS,
        Expect.BODY,
        Expect.SEPARATOR,
    ])
