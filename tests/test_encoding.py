"""
Various unicode handling related tests.

"""
import pytest
import responses
from charset_normalizer.constant import TOO_SMALL_SEQUENCE

from httpie.cli.constants import PRETTY_MAP
from httpie.encoding import UTF8

from .utils import http, HTTP_OK, URL_EXAMPLE, MockEnvironment, StdinBytesIO
from .fixtures import UNICODE


CZECH_TEXT = 'Všichni lidé jsou si rovni. Všichni lidé jsou si rovni.'
assert len(CZECH_TEXT) > TOO_SMALL_SEQUENCE
CZECH_TEXT_SPECIFIC_CHARSET = 'windows-1250'
ENCODINGS = [UTF8, CZECH_TEXT_SPECIFIC_CHARSET]


def test_unicode_headers(httpbin):
    # httpbin doesn't interpret UFT-8 headers
    r = http(httpbin.url + '/headers', f'Test:{UNICODE}')
    assert HTTP_OK in r


def test_unicode_headers_verbose(httpbin):
    # httpbin doesn't interpret UTF-8 headers
    r = http('--verbose', httpbin.url + '/headers', f'Test:{UNICODE}')
    assert HTTP_OK in r
    assert UNICODE in r


def test_unicode_raw(httpbin):
    r = http('--raw', f'test {UNICODE}', 'POST', httpbin.url + '/post')
    assert HTTP_OK in r
    assert r.json['data'] == f'test {UNICODE}'


def test_unicode_raw_verbose(httpbin):
    r = http('--verbose', '--raw', f'test {UNICODE}',
             'POST', httpbin.url + '/post')
    assert HTTP_OK in r
    assert UNICODE in r


def test_unicode_form_item(httpbin):
    r = http('--form', 'POST', httpbin.url + '/post', f'test={UNICODE}')
    assert HTTP_OK in r
    assert r.json['form'] == {'test': UNICODE}


def test_unicode_form_item_verbose(httpbin):
    r = http('--verbose', '--form',
             'POST', httpbin.url + '/post', f'test={UNICODE}')
    assert HTTP_OK in r
    assert UNICODE in r


def test_unicode_json_item(httpbin):
    r = http('--json', 'POST', httpbin.url + '/post', f'test={UNICODE}')
    assert HTTP_OK in r
    assert r.json['json'] == {'test': UNICODE}


def test_unicode_json_item_verbose(httpbin):
    r = http('--verbose', '--json',
             'POST', httpbin.url + '/post', f'test={UNICODE}')
    assert HTTP_OK in r
    assert UNICODE in r


def test_unicode_raw_json_item(httpbin):
    r = http('--json', 'POST', httpbin.url + '/post',
             f'test:={{ "{UNICODE}" : [ "{UNICODE}" ] }}')
    assert HTTP_OK in r
    assert r.json['json'] == {'test': {UNICODE: [UNICODE]}}


def test_unicode_raw_json_item_verbose(httpbin):
    r = http('--json', 'POST', httpbin.url + '/post',
             f'test:={{ "{UNICODE}" : [ "{UNICODE}" ] }}')
    assert HTTP_OK in r
    assert r.json['json'] == {'test': {UNICODE: [UNICODE]}}


def test_unicode_url_query_arg_item(httpbin):
    r = http(httpbin.url + '/get', f'test=={UNICODE}')
    assert HTTP_OK in r
    assert r.json['args'] == {'test': UNICODE}, r


def test_unicode_url_query_arg_item_verbose(httpbin):
    r = http('--verbose', httpbin.url + '/get', f'test=={UNICODE}')
    assert HTTP_OK in r
    assert UNICODE in r


def test_unicode_url(httpbin):
    r = http(f'{httpbin.url}/get?test={UNICODE}')
    assert HTTP_OK in r
    assert r.json['args'] == {'test': UNICODE}


def test_unicode_url_verbose(httpbin):
    r = http('--verbose', f'{httpbin.url}/get?test={UNICODE}')
    assert HTTP_OK in r
    assert r.json['args'] == {'test': UNICODE}


def test_unicode_basic_auth(httpbin):
    # it doesn't really authenticate us because httpbin
    # doesn't interpret the UTF-8-encoded auth
    http('--verbose', '--auth', f'test:{UNICODE}',
         f'{httpbin.url}/basic-auth/test/{UNICODE}')


def test_unicode_digest_auth(httpbin):
    # it doesn't really authenticate us because httpbin
    # doesn't interpret the UTF-8-encoded auth
    http('--auth-type=digest',
         '--auth', f'test:{UNICODE}',
         f'{httpbin.url}/digest-auth/auth/test/{UNICODE}')


@pytest.mark.parametrize('encoding', ENCODINGS)
@responses.activate
def test_response_encoding_detection_from_content(encoding):
    responses.add(
        responses.POST,
        URL_EXAMPLE,
        body=CZECH_TEXT.encode(encoding),
        content_type='text/plain',
    )
    r = http('--form', 'POST', URL_EXAMPLE)
    assert CZECH_TEXT in r


@pytest.mark.parametrize('encoding', ENCODINGS)
@responses.activate
def test_response_encoding_detection_from_content_xml(encoding):
    body = f'<?xml version="1.0" encoding="{encoding.upper()}"?>\n<c>{CZECH_TEXT}</c>'
    responses.add(
        responses.GET,
        URL_EXAMPLE,
        body=body.encode(encoding),
        content_type='text/xml',
    )
    r = http(URL_EXAMPLE)
    assert CZECH_TEXT in r


@pytest.mark.parametrize('encoding', ENCODINGS)
@responses.activate
def test_response_encoding_detection_from_content_type_header(encoding):
    responses.add(
        responses.POST,
        URL_EXAMPLE,
        body=CZECH_TEXT.encode(encoding),
        content_type=f'text/plain; charset={encoding.upper()}',
    )
    r = http('--form', 'POST', URL_EXAMPLE)
    assert CZECH_TEXT in r


@pytest.mark.parametrize('pretty', PRETTY_MAP.keys())
@responses.activate
def test_response_encoding_provided_by_option(pretty):
    responses.add(
        responses.GET,
        URL_EXAMPLE,
        body='卷首'.encode('big5'),
        content_type='text/plain; charset=utf-8',
    )
    args = ('--pretty', pretty, URL_EXAMPLE)

    # Encoding provided by Content-Type is incorrect, thus it should print something unreadable.
    r = http(*args)
    assert '卷首' not in r
    r = http('--response-charset=big5', *args)
    assert '卷首' in r


@pytest.mark.parametrize('encoding', ENCODINGS)
@pytest.mark.parametrize('pretty', PRETTY_MAP.keys())
@responses.activate
def test_streamed_response_encoding_detection_from_content_type_header(encoding, pretty):
    responses.add(
        responses.GET,
        URL_EXAMPLE,
        body=f'<?xml version="1.0"?>\n<c>{CZECH_TEXT}</c>'.encode(encoding),
        stream=True,
        content_type=f'text/xml; charset={encoding.upper()}',
    )
    r = http('--pretty', pretty, '--stream', URL_EXAMPLE)
    assert CZECH_TEXT in r


@pytest.mark.parametrize('encoding', ENCODINGS)
def test_request_body_content_type_charset_used(encoding):
    body_str = CZECH_TEXT
    body_bytes = body_str.encode(encoding)
    if encoding != UTF8:
        with pytest.raises(UnicodeDecodeError):
            assert body_str != body_bytes.decode()

    r = http(
        '--offline',
        URL_EXAMPLE,
        f'Content-Type: text/plain; charset={encoding.upper()}',
        env=MockEnvironment(
            stdin=StdinBytesIO(body_bytes),
            stdin_isatty=False,
        )
    )
    assert body_str in r
