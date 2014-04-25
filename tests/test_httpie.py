"""High-level tests."""
from tests import TestEnvironment, http, httpbin, HTTP_OK
from tests.fixtures import FILE_PATH, FILE_CONTENT
import httpie


class TestHTTPie:

    def test_debug(self):
        r = http('--debug')
        assert r.exit_status == httpie.ExitStatus.OK
        assert 'HTTPie %s' % httpie.__version__ in r.stderr
        assert 'HTTPie data:' in r.stderr

    def test_help(self):
        r = http('--help')
        assert r.exit_status == httpie.ExitStatus.ERROR
        assert 'https://github.com/jkbr/httpie/issues' in r

    def test_version(self):
        r = http('--version')
        assert r.exit_status == httpie.ExitStatus.ERROR
        # FIXME: py3 has version in stdout, py2 in stderr
        assert httpie.__version__ == r.stderr.strip() + r.strip()

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
