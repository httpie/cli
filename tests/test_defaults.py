"""
Tests for the provided defaults regarding HTTP method, and --json vs. --form.

"""
from unittest import TestCase

from tests import (
    TestEnvironment,
    http, httpbin,
    HTTP_OK, FILE_PATH,
)


class ImplicitHTTPMethodTest(TestCase):

    def test_implicit_GET(self):
        r = http(httpbin('/get'))
        assert HTTP_OK in r

    def test_implicit_GET_with_headers(self):
        r = http(
            httpbin('/headers'),
            'Foo:bar'
        )
        assert HTTP_OK in r
        assert '"Foo": "bar"' in r

    def test_implicit_POST_json(self):
        r = http(
            httpbin('/post'),
            'hello=world'
        )
        assert HTTP_OK in r
        assert r'\"hello\": \"world\"' in r

    def test_implicit_POST_form(self):
        r = http(
            '--form',
            httpbin('/post'),
            'foo=bar'
        )
        assert HTTP_OK in r
        assert '"foo": "bar"' in r

    def test_implicit_POST_stdin(self):
        with open(FILE_PATH) as f:
            env = TestEnvironment(
                stdin_isatty=False,
                stdin=f,
            )
            r = http(
                '--form',
                httpbin('/post'),
                env=env
            )
        assert HTTP_OK in r


class AutoContentTypeAndAcceptHeadersTest(TestCase):
    """
    Test that Accept and Content-Type correctly defaults to JSON,
    but can still be overridden. The same with Content-Type when --form
    -f is used.

    """
    def test_GET_no_data_no_auto_headers(self):
        # https://github.com/jkbr/httpie/issues/62
        r = http(
            'GET',
            httpbin('/headers')
        )
        assert HTTP_OK in r
        assert '"Accept": "*/*"' in r
        assert '"Content-Type": "application/json' not in r

    def test_POST_no_data_no_auto_headers(self):
        # JSON headers shouldn't be automatically set for POST with no data.
        r = http(
            'POST',
            httpbin('/post')
        )
        assert HTTP_OK in r
        assert '"Accept": "*/*"' in r
        assert '"Content-Type": "application/json' not in r

    def test_POST_with_data_auto_JSON_headers(self):
        r = http(
            'POST',
            httpbin('/post'),
            'a=b'
        )
        assert HTTP_OK in r
        assert '"Accept": "application/json"' in r
        assert '"Content-Type": "application/json; charset=utf-8' in r

    def test_GET_with_data_auto_JSON_headers(self):
        # JSON headers should automatically be set also for GET with data.
        r = http(
            'POST',
            httpbin('/post'),
            'a=b'
        )
        assert HTTP_OK in r
        assert '"Accept": "application/json"' in r
        assert '"Content-Type": "application/json; charset=utf-8' in r

    def test_POST_explicit_JSON_auto_JSON_accept(self):
        r = http(
            '--json',
            'POST',
            httpbin('/post')
        )
        assert HTTP_OK in r
        assert r.json['headers']['Accept'] == 'application/json'
        # Make sure Content-Type gets set even with no data.
        # https://github.com/jkbr/httpie/issues/137
        assert 'application/json' in r.json['headers']['Content-Type']

    def test_GET_explicit_JSON_explicit_headers(self):
        r = http(
            '--json',
            'GET',
            httpbin('/headers'),
            'Accept:application/xml',
            'Content-Type:application/xml'
        )
        assert HTTP_OK in r
        assert '"Accept": "application/xml"' in r
        assert '"Content-Type": "application/xml"' in r

    def test_POST_form_auto_Content_Type(self):
        r = http(
            '--form',
            'POST',
            httpbin('/post')
        )
        assert HTTP_OK in r
        assert '"Content-Type": "application/x-www-form-urlencoded' in r

    def test_POST_form_Content_Type_override(self):
        r = http(
            '--form',
            'POST',
            httpbin('/post'),
            'Content-Type:application/xml'
        )
        assert HTTP_OK in r
        assert '"Content-Type": "application/xml"' in r

    def test_print_only_body_when_stdout_redirected_by_default(self):

        r = http(
            'GET',
            httpbin('/get'),
            env=TestEnvironment(
                stdin_isatty=True,
                stdout_isatty=False
            )
        )
        assert 'HTTP/' not in r

    def test_print_overridable_when_stdout_redirected(self):

        r = http(
            '--print=h',
            'GET',
            httpbin('/get'),
            env=TestEnvironment(
                stdin_isatty=True,
                stdout_isatty=False
            )
        )
        assert HTTP_OK in r
