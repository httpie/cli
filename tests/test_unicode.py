# coding=utf-8
"""
Various unicode handling related tests.

"""
from utils import http, httpbin, HTTP_OK
from fixtures import UNICODE


class TestUnicode:

    def test_unicode_headers(self):
        # httpbin doesn't interpret utf8 headers
        r = http(httpbin('/headers'), u'Test:%s' % UNICODE)
        assert HTTP_OK in r

    def test_unicode_headers_verbose(self):
        # httpbin doesn't interpret utf8 headers
        r = http('--verbose', httpbin('/headers'), u'Test:%s' % UNICODE)
        assert HTTP_OK in r
        assert UNICODE in r

    def test_unicode_form_item(self):
        r = http('--form', 'POST', httpbin('/post'), u'test=%s' % UNICODE)
        assert HTTP_OK in r
        assert r.json['form'] == {'test': UNICODE}

    def test_unicode_form_item_verbose(self):
        r = http('--verbose', '--form',
                 'POST', httpbin('/post'), u'test=%s' % UNICODE)
        assert HTTP_OK in r
        assert UNICODE in r

    def test_unicode_json_item(self):
        r = http('--json', 'POST', httpbin('/post'), u'test=%s' % UNICODE)
        assert HTTP_OK in r
        assert r.json['json'] == {'test': UNICODE}

    def test_unicode_json_item_verbose(self):
        r = http('--verbose', '--json',
                 'POST', httpbin('/post'), u'test=%s' % UNICODE)
        assert HTTP_OK in r
        assert UNICODE in r

    def test_unicode_raw_json_item(self):
        r = http('--json', 'POST', httpbin('/post'),
                 u'test:={ "%s" : [ "%s" ] }' % (UNICODE, UNICODE))
        assert HTTP_OK in r
        assert r.json['json'] == {'test': {UNICODE: [UNICODE]}}

    def test_unicode_raw_json_item_verbose(self):
        r = http('--json', 'POST', httpbin('/post'),
                 u'test:={ "%s" : [ "%s" ] }' % (UNICODE, UNICODE))
        assert HTTP_OK in r
        assert r.json['json'] == {'test': {UNICODE: [UNICODE]}}

    def test_unicode_url_query_arg_item(self):
        r = http(httpbin('/get'), u'test==%s' % UNICODE)
        assert HTTP_OK in r
        assert r.json['args'] == {'test': UNICODE}, r

    def test_unicode_url_query_arg_item_verbose(self):
        r = http('--verbose', httpbin('/get'), u'test==%s' % UNICODE)
        assert HTTP_OK in r
        assert UNICODE in r

    def test_unicode_url(self):
        r = http(httpbin(u'/get?test=' + UNICODE))
        assert HTTP_OK in r
        assert r.json['args'] == {'test': UNICODE}

    # def test_unicode_url_verbose(self):
    #     r = http(httpbin('--verbose', u'/get?test=' + UNICODE))
    #     assert HTTP_OK in r

    def test_unicode_basic_auth(self):
        # it doesn't really authenticate us because httpbin
        # doesn't interpret the utf8-encoded auth
        http('--verbose', '--auth', u'test:%s' % UNICODE,
             httpbin(u'/basic-auth/test/' + UNICODE))

    def test_unicode_digest_auth(self):
        # it doesn't really authenticate us because httpbin
        # doesn't interpret the utf8-encoded auth
        http('--auth-type=digest',
             '--auth', u'test:%s' % UNICODE,
             httpbin(u'/digest-auth/auth/test/' + UNICODE))
