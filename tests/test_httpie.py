"""High-level tests."""
from unittest import TestCase

from tests import TestEnvironment, http, httpbin, HTTP_OK
from tests.fixtures import FILE_PATH, FILE_CONTENT


class HTTPieTest(TestCase):

    def test_GET(self):
        r = http('GET', httpbin('/get'))
        assert HTTP_OK in r

    def test_DELETE(self):
        r = http('DELETE', httpbin('/delete'))
        assert HTTP_OK in r

    def test_PUT(self):
        r = http('PUT', httpbin('/put'), 'foo=bar')
        assert HTTP_OK in r
        assert r'\"foo\": \"bar\"' in r

    def test_POST_JSON_data(self):
        r = http('POST', httpbin('/post'), 'foo=bar')
        assert HTTP_OK in r
        assert r'\"foo\": \"bar\"' in r

    def test_POST_form(self):
        r = http('--form', 'POST', httpbin('/post'), 'foo=bar')
        assert HTTP_OK in r
        assert '"foo": "bar"' in r

    def test_POST_form_multiple_values(self):
        r = http('--form', 'POST', httpbin('/post'), 'foo=bar', 'foo=baz')
        assert HTTP_OK in r
        assert r.json['form'] == {'foo': ['bar', 'baz']}

    def test_POST_stdin(self):

        with open(FILE_PATH) as f:
            env = TestEnvironment(stdin=f, stdin_isatty=False)
            r = http('--form', 'POST', httpbin('/post'), env=env)
        assert HTTP_OK in r
        assert FILE_CONTENT in r

    def test_headers(self):
        r = http('GET', httpbin('/headers'), 'Foo:bar')
        assert HTTP_OK in r
        assert '"User-Agent": "HTTPie' in r
        assert '"Foo": "bar"' in r
