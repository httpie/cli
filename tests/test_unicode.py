# coding=utf-8
"""
Various unicode handling related tests.

"""
from utils import http, HTTP_OK
from fixtures import UNICODE


def test_unicode_headers(httpbin):
    # httpbin doesn't interpret utf8 headers
    r = http(httpbin.url + '/headers', u'Test:%s' % UNICODE)
    assert HTTP_OK in r


def test_unicode_headers_verbose(httpbin):
    # httpbin doesn't interpret utf8 headers
    r = http('--verbose', httpbin.url + '/headers', u'Test:%s' % UNICODE)
    assert HTTP_OK in r
    assert UNICODE in r


def test_unicode_form_item(httpbin):
    r = http('--form', 'POST', httpbin.url + '/post', u'test=%s' % UNICODE)
    assert HTTP_OK in r
    assert r.json['form'] == {'test': UNICODE}


def test_unicode_form_item_verbose(httpbin):
    r = http('--verbose', '--form',
             'POST', httpbin.url + '/post', u'test=%s' % UNICODE)
    assert HTTP_OK in r
    assert UNICODE in r


def test_unicode_json_item(httpbin):
    r = http('--json', 'POST', httpbin.url + '/post', u'test=%s' % UNICODE)
    assert HTTP_OK in r
    assert r.json['json'] == {'test': UNICODE}


def test_unicode_json_item_verbose(httpbin):
    r = http('--verbose', '--json',
             'POST', httpbin.url + '/post', u'test=%s' % UNICODE)
    assert HTTP_OK in r
    assert UNICODE in r


def test_unicode_raw_json_item(httpbin):
    r = http('--json', 'POST', httpbin.url + '/post',
             u'test:={ "%s" : [ "%s" ] }' % (UNICODE, UNICODE))
    assert HTTP_OK in r
    assert r.json['json'] == {'test': {UNICODE: [UNICODE]}}


def test_unicode_raw_json_item_verbose(httpbin):
    r = http('--json', 'POST', httpbin.url + '/post',
             u'test:={ "%s" : [ "%s" ] }' % (UNICODE, UNICODE))
    assert HTTP_OK in r
    assert r.json['json'] == {'test': {UNICODE: [UNICODE]}}


def test_unicode_url_query_arg_item(httpbin):
    r = http(httpbin.url + '/get', u'test==%s' % UNICODE)
    assert HTTP_OK in r
    assert r.json['args'] == {'test': UNICODE}, r


def test_unicode_url_query_arg_item_verbose(httpbin):
    r = http('--verbose', httpbin.url + '/get', u'test==%s' % UNICODE)
    assert HTTP_OK in r
    assert UNICODE in r


def test_unicode_url(httpbin):
    r = http(httpbin.url + u'/get?test=' + UNICODE)
    assert HTTP_OK in r
    assert r.json['args'] == {'test': UNICODE}

# def test_unicode_url_verbose(self):
#     r = http(httpbin.url + '--verbose', u'/get?test=' + UNICODE)
#     assert HTTP_OK in r


def test_unicode_basic_auth(httpbin):
    # it doesn't really authenticate us because httpbin
    # doesn't interpret the utf8-encoded auth
    http('--verbose', '--auth', u'test:%s' % UNICODE,
         httpbin.url + u'/basic-auth/test/' + UNICODE)


def test_unicode_digest_auth(httpbin):
    # it doesn't really authenticate us because httpbin
    # doesn't interpret the utf8-encoded auth
    http('--auth-type=digest',
         '--auth', u'test:%s' % UNICODE,
         httpbin.url + u'/digest-auth/auth/test/' + UNICODE)


def test_punycode_url():
    r = http("--verbose", "👻", "--offline")
    assert "Host: xn--9q8h" in r


def test_punycode_url_with_tld():
    r = http("--verbose", "test.👻", "--offline")
    assert "Host: test.xn--9q8h" in r


def test_multiple_punycode_in_url():
    r = http("--verbose", "👻.👻.com", "--offline")
    assert "Host: xn--9q8h.xn--9q8h.com" in r
