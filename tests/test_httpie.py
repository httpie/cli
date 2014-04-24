"""High-level tests."""
from tests import (
    BaseTestCase, TestEnvironment,
    http, httpbin, OK,
    FILE_PATH, FILE_CONTENT
)


class HTTPieTest(BaseTestCase):

    def test_GET(self):
        r = http(
            'GET',
            httpbin('/get')
        )
        self.assertIn(OK, r)

    def test_DELETE(self):
        r = http(
            'DELETE',
            httpbin('/delete')
        )
        self.assertIn(OK, r)

    def test_PUT(self):
        r = http(
            'PUT',
            httpbin('/put'),
            'foo=bar'
        )
        self.assertIn(OK, r)
        self.assertIn(r'\"foo\": \"bar\"', r)

    def test_POST_JSON_data(self):
        r = http(
            'POST',
            httpbin('/post'),
            'foo=bar'
        )
        self.assertIn(OK, r)
        self.assertIn(r'\"foo\": \"bar\"', r)

    def test_POST_form(self):
        r = http(
            '--form',
            'POST',
            httpbin('/post'),
            'foo=bar'
        )
        self.assertIn(OK, r)
        self.assertIn('"foo": "bar"', r)

    def test_POST_form_multiple_values(self):
        r = http(
            '--form',
            'POST',
            httpbin('/post'),
            'foo=bar',
            'foo=baz',
        )
        self.assertIn(OK, r)
        self.assertDictEqual(r.json['form'], {
            'foo': ['bar', 'baz']
        })

    def test_POST_stdin(self):

        with open(FILE_PATH) as f:
            env = TestEnvironment(
                stdin=f,
                stdin_isatty=False,
            )

            r = http(
                '--form',
                'POST',
                httpbin('/post'),
                env=env
            )
        self.assertIn(OK, r)
        self.assertIn(FILE_CONTENT, r)

    def test_headers(self):
        r = http(
            'GET',
            httpbin('/headers'),
            'Foo:bar'
        )
        self.assertIn(OK, r)
        self.assertIn('"User-Agent": "HTTPie', r)
        self.assertIn('"Foo": "bar"', r)
