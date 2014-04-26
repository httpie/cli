# coding=utf-8
"""
Various unicode handling related tests.

"""
from tests import http, httpbin


UNICODE = u'太陽'


class TestUnicode:

    def test_unicode_headers(self):
        r = http('GET', httpbin('/headers'), u'Test:%s' % UNICODE)
        assert r.json['headers']['Test'] == UNICODE

    def test_unicode_form_item(self):
        r = http('--form', 'POST', httpbin('/post'), u'test=%s' % UNICODE)
        assert r.json['form']['test'] == UNICODE

    def test_unicode_json_item(self):
        r = http('--json', 'POST', httpbin('/post'), u'test=%s' % UNICODE)
        assert r.json['json']['test'] == UNICODE

    def test_unicode_raw_json_item(self):
        r = http('--json', 'POST', httpbin('/post'), u'test:=["%s"]' % UNICODE)
        assert r.json['json']['test'] == [UNICODE]

    def test_unicode_url(self):
        r = http(httpbin(u'/get?test=' + UNICODE))
        assert r.json['args']['test'] == UNICODE

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
