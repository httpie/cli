# coding=utf-8
"""
Various unicode handling related tests.

"""
from tests import http, httpbin


JP_SUN = u'太陽'


class TestUnicode:

    def test_unicode_headers(self):
        r = http('GET', httpbin('/headers'), u'Test:%s' % JP_SUN)
        assert r.json['headers']['Test'] == JP_SUN

    def test_unicode_form_item(self):
        r = http('--form', 'POST', httpbin('/post'), u'test=%s' % JP_SUN)
        assert r.json['form']['test'] == JP_SUN

    def test_unicode_json_item(self):
        r = http('--json', 'POST', httpbin('/post'), u'test=%s' % JP_SUN)
        assert r.json['json']['test'] == JP_SUN

    def test_unicode_raw_json_item(self):
        r = http('--json', 'POST', httpbin('/post'), u'test:=["%s"]' % JP_SUN)
        assert r.json['json']['test'] == [JP_SUN]

    def test_unicode_url(self):
        r = http(httpbin(u'/get?test=' + JP_SUN))
        assert r.json['args']['test'] == JP_SUN

    def test_unicode_basic_auth(self):
        # it doesn't really authenticate us because httpbin
        # doesn't interpret the utf8-encoded auth
        http('--verbose', '--auth', u'test:%s' % JP_SUN,
             httpbin(u'/basic-auth/test/' + JP_SUN))

    def test_unicode_digest_auth(self):
        # it doesn't really authenticate us because httpbin
        # doesn't interpret the utf8-encoded auth
        http('--auth-type=digest',
             '--auth', u'test:%s' % JP_SUN,
             httpbin(u'/digest-auth/auth/test/' + JP_SUN))
