"""
Tests for the provided defaults regarding HTTP method, and --json vs. --form.

"""
from tests import (
    BaseTestCase, TestEnvironment,
    http, httpbin,
    OK, FILE_PATH,
)


class ImplicitHTTPMethodTest(BaseTestCase):

    def test_implicit_GET(self):
        r = http(httpbin('/get'))
        self.assertIn(OK, r)

    def test_implicit_GET_with_headers(self):
        r = http(
            httpbin('/headers'),
            'Foo:bar'
        )
        self.assertIn(OK, r)
        self.assertIn('"Foo": "bar"', r)

    def test_implicit_POST_json(self):
        r = http(
            httpbin('/post'),
            'hello=world'
        )
        self.assertIn(OK, r)
        self.assertIn(r'\"hello\": \"world\"', r)

    def test_implicit_POST_form(self):
        r = http(
            '--form',
            httpbin('/post'),
            'foo=bar'
        )
        self.assertIn(OK, r)
        self.assertIn('"foo": "bar"', r)

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
        self.assertIn(OK, r)


class AutoContentTypeAndAcceptHeadersTest(BaseTestCase):
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
        self.assertIn(OK, r)
        self.assertIn('"Accept": "*/*"', r)
        self.assertNotIn('"Content-Type": "application/json', r)

    def test_POST_no_data_no_auto_headers(self):
        # JSON headers shouldn't be automatically set for POST with no data.
        r = http(
            'POST',
            httpbin('/post')
        )
        self.assertIn(OK, r)
        self.assertIn('"Accept": "*/*"', r)
        self.assertNotIn('"Content-Type": "application/json', r)

    def test_POST_with_data_auto_JSON_headers(self):
        r = http(
            'POST',
            httpbin('/post'),
            'a=b'
        )
        self.assertIn(OK, r)
        self.assertIn('"Accept": "application/json"', r)
        self.assertIn('"Content-Type": "application/json; charset=utf-8', r)

    def test_GET_with_data_auto_JSON_headers(self):
        # JSON headers should automatically be set also for GET with data.
        r = http(
            'POST',
            httpbin('/post'),
            'a=b'
        )
        self.assertIn(OK, r)
        self.assertIn('"Accept": "application/json"', r)
        self.assertIn('"Content-Type": "application/json; charset=utf-8', r)

    def test_POST_explicit_JSON_auto_JSON_accept(self):
        r = http(
            '--json',
            'POST',
            httpbin('/post')
        )
        self.assertIn(OK, r)
        self.assertEqual(r.json['headers']['Accept'], 'application/json')
        # Make sure Content-Type gets set even with no data.
        # https://github.com/jkbr/httpie/issues/137
        self.assertIn('application/json', r.json['headers']['Content-Type'])

    def test_GET_explicit_JSON_explicit_headers(self):
        r = http(
            '--json',
            'GET',
            httpbin('/headers'),
            'Accept:application/xml',
            'Content-Type:application/xml'
        )
        self.assertIn(OK, r)
        self.assertIn('"Accept": "application/xml"', r)
        self.assertIn('"Content-Type": "application/xml"', r)

    def test_POST_form_auto_Content_Type(self):
        r = http(
            '--form',
            'POST',
            httpbin('/post')
        )
        self.assertIn(OK, r)
        self.assertIn(
            '"Content-Type":'
            ' "application/x-www-form-urlencoded; charset=utf-8"',
            r
        )

    def test_POST_form_Content_Type_override(self):
        r = http(
            '--form',
            'POST',
            httpbin('/post'),
            'Content-Type:application/xml'
        )
        self.assertIn(OK, r)
        self.assertIn('"Content-Type": "application/xml"', r)

    def test_print_only_body_when_stdout_redirected_by_default(self):

        r = http(
            'GET',
            httpbin('/get'),
            env=TestEnvironment(
                stdin_isatty=True,
                stdout_isatty=False
            )
        )
        self.assertNotIn('HTTP/', r)

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
        self.assertIn(OK, r)
