"""
Various unicode handling related tests.

"""
from .utils import http, HTTP_OK
from .fixtures import UNICODE


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
