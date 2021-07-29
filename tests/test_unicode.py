"""
Various unicode handling related tests.

"""
import pytest
import responses

from httpie.cli.constants import PRETTY_MAP
from httpie.constants import UTF8

from .utils import http, HTTP_OK, URL_EXAMPLE
from .fixtures import UNICODE

ENCODINGS = [UTF8, 'windows-1250']


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
def test_GET_encoding_detection_from_content_type_header(encoding):
    responses.add(responses.GET,
                  URL_EXAMPLE,
                  body='<?xml version="1.0"?>\n<c>Financiën</c>'.encode(encoding),
                  content_type=f'text/xml; charset={encoding.upper()}')
    r = http('GET', URL_EXAMPLE)
    assert 'Financiën' in r


@pytest.mark.parametrize('encoding', ENCODINGS)
@responses.activate
def test_GET_encoding_detection_from_content(encoding):
    body = f'<?xml version="1.0" encoding="{encoding.upper()}"?>\n<c>Financiën</c>'
    responses.add(responses.GET,
                  URL_EXAMPLE,
                  body=body.encode(encoding),
                  content_type='text/xml')
    r = http('GET', URL_EXAMPLE)
    assert 'Financiën' in r


@responses.activate
def test_GET_encoding_provided_by_format_options_argument():
    responses.add(responses.GET,
                  URL_EXAMPLE,
                  body='▒▒▒'.encode('johab'),
                  content_type='text/plain')
    r = http('--format-options', 'response.as:text/plain; charset=johab',
             'GET', URL_EXAMPLE)
    assert '▒▒▒' in r


@responses.activate
def test_GET_encoding_provided_by_charset_argument():
    responses.add(responses.GET,
                  URL_EXAMPLE,
                  body='▒▒▒'.encode('johab'),
                  content_type='text/plain')
    r = http('--response-as', 'text/plain; charset=johab',
             'GET', URL_EXAMPLE)
    assert '▒▒▒' in r


@pytest.mark.parametrize('encoding', ENCODINGS)
@responses.activate
def test_GET_encoding_provided_by_empty_charset_argument_should_use_content_detection(encoding):
    body = f'<?xml version="1.0" encoding="{encoding.upper()}"?>\n<c>Financiën</c>'
    responses.add(responses.GET,
                  URL_EXAMPLE,
                  body=body.encode(encoding),
                  content_type='text/xml')
    r = http('--response-as', 's', 'GET', URL_EXAMPLE)
    assert 'Financiën' in r


@pytest.mark.parametrize('encoding', ENCODINGS)
@responses.activate
def test_POST_encoding_detection_from_content_type_header(encoding):
    responses.add(responses.POST,
                  URL_EXAMPLE,
                  body='Všichni lidé jsou si rovni.'.encode(encoding),
                  content_type=f'text/plain; charset={encoding.upper()}')
    r = http('--form', 'POST', URL_EXAMPLE)
    assert 'Všichni lidé jsou si rovni.' in r


@pytest.mark.parametrize('encoding', ENCODINGS)
@responses.activate
def test_POST_encoding_detection_from_content(encoding):
    responses.add(responses.POST,
                  URL_EXAMPLE,
                  body='Všichni lidé jsou si rovni.'.encode(encoding),
                  content_type='text/plain')
    r = http('--form', 'POST', URL_EXAMPLE)
    assert 'Všichni lidé jsou si rovni.' in r


@pytest.mark.parametrize('encoding', ENCODINGS)
@pytest.mark.parametrize('pretty', PRETTY_MAP.keys())
@responses.activate
def test_stream_encoding_detection_from_content_type_header(encoding, pretty):
    responses.add(responses.GET,
                  URL_EXAMPLE,
                  body='<?xml version="1.0"?>\n<c>Financiën</c>'.encode(encoding),
                  stream=True,
                  content_type=f'text/xml; charset={encoding.upper()}')
    r = http('--pretty=' + pretty, '--stream', 'GET', URL_EXAMPLE)
    assert 'Financiën' in r
