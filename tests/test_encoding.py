"""
Various unicode handling related tests.

"""
import pytest
import responses
from charset_normalizer.constant import TOO_SMALL_SEQUENCE

from httpie.cli.constants import PRETTY_MAP
from httpie.encoding import UTF8

from .utils import http, HTTP_OK, URL_EXAMPLE, MockEnvironment
from .fixtures import UNICODE


CHARSET_TEXT_PAIRS = [
    ('big5', '卷首卷首卷首卷首卷卷首卷首卷首卷首卷首卷首卷首卷首卷首卷首卷首卷首卷首'),
    ('windows-1250', 'Všichni lidé jsou si rovni. Všichni lidé jsou si rovni.'),
    (UTF8, 'Všichni lidé jsou si rovni. Všichni lidé jsou si rovni.'),
]


def test_fixtures():
    for charset, text in CHARSET_TEXT_PAIRS:
        assert len(text) > TOO_SMALL_SEQUENCE
        if charset != UTF8:
            with pytest.raises(UnicodeDecodeError):
                assert text != text.encode(charset).decode(UTF8)


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


@pytest.mark.parametrize(['charset', 'text'], CHARSET_TEXT_PAIRS)
@responses.activate
def test_response_body_encoding_detection_from_content(text, charset):
    responses.add(
        responses.POST,
        URL_EXAMPLE,
        body=text.encode(charset),
        content_type='text/plain',
    )
    r = http('--form', 'POST', URL_EXAMPLE)
    assert text in r


@pytest.mark.parametrize(['charset', 'text'], CHARSET_TEXT_PAIRS)
@responses.activate
def test_response_body_encoding_detection_from_content_type_header(charset, text):
    responses.add(
        responses.POST,
        URL_EXAMPLE,
        body=text.encode(charset),
        content_type=f'text/plain; charset={charset}',
    )
    r = http('--form', 'POST', URL_EXAMPLE)
    assert text in r


@pytest.mark.parametrize(['charset', 'text'], CHARSET_TEXT_PAIRS)
@pytest.mark.parametrize('pretty', PRETTY_MAP.keys())
@responses.activate
def test_response_body_encoding_detection_from_content_type_header_stream(charset, text, pretty):
    responses.add(
        responses.GET,
        URL_EXAMPLE,
        body=f'<?xml version="1.0"?>\n<c>{text}</c>'.encode(charset),
        stream=True,
        content_type=f'text/xml; charset={charset.upper()}',
    )
    r = http('--pretty', pretty, '--stream', URL_EXAMPLE)
    assert text in r


@pytest.mark.parametrize(['charset', 'text'], CHARSET_TEXT_PAIRS)
@pytest.mark.parametrize('pretty', PRETTY_MAP.keys())
@responses.activate
def test_response_body_encoding_override_by_option(charset, text, pretty):
    responses.add(
        responses.GET,
        URL_EXAMPLE,
        body=text.encode(charset),
        content_type='text/plain; charset=utf-8',
    )
    args = ('--pretty', pretty, URL_EXAMPLE)

    if charset != UTF8:
        # Encoding provided by Content-Type is incorrect, thus it should print something unreadable.
        r = http(*args)
        assert text not in r
    r = http('--response-charset', charset, *args)
    assert text in r


@pytest.mark.parametrize(['charset', 'text'], CHARSET_TEXT_PAIRS)
def test_request_content_type_charset_used(charset, text):
    body_bytes = text.encode(charset)

    r = http(
        '--offline',
        URL_EXAMPLE,
        f'Content-Type: text/plain; charset={charset.upper()}',
        env=MockEnvironment(stdin=body_bytes, stdin_isatty=False),
    )
    assert text in r


@pytest.mark.parametrize(['charset', 'text'], CHARSET_TEXT_PAIRS)
def test_request_charset_detected(charset, text):
    body_bytes = text.encode(charset)
    r = http(
        '--offline',
        URL_EXAMPLE,
        f'Content-Type: text/plain',
        env=MockEnvironment(stdin=body_bytes, stdin_isatty=False),
    )
    assert text in r
