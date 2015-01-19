"""High-level tests."""
from utils import TestEnvironment, http, HTTP_OK
from fixtures import FILE_PATH, FILE_CONTENT
import httpie


class TestHTTPie:

    def test_debug(self):
        r = http('--debug')
        assert r.exit_status == httpie.ExitStatus.OK
        assert 'HTTPie %s' % httpie.__version__ in r.stderr
        assert 'HTTPie data:' in r.stderr

    def test_help(self):
        r = http('--help', error_exit_ok=True)
        assert r.exit_status == httpie.ExitStatus.OK
        assert 'https://github.com/jakubroztocil/httpie/issues' in r

    def test_version(self):
        r = http('--version', error_exit_ok=True)
        assert r.exit_status == httpie.ExitStatus.OK
        # FIXME: py3 has version in stdout, py2 in stderr
        assert httpie.__version__ == r.stderr.strip() + r.strip()

    def test_GET(self, httpbin):
        r = http('GET', httpbin.url + '/get')
        assert HTTP_OK in r

    def test_DELETE(self, httpbin):
        r = http('DELETE', httpbin.url + '/delete')
        assert HTTP_OK in r

    def test_PUT(self, httpbin):
        r = http('PUT', httpbin.url + '/put', 'foo=bar')
        assert HTTP_OK in r
        assert r.json['json']['foo'] == 'bar'

    def test_POST_JSON_data(self, httpbin):
        r = http('POST', httpbin.url + '/post', 'foo=bar')
        assert HTTP_OK in r
        assert r.json['json']['foo'] == 'bar'

    def test_POST_form(self, httpbin):
        r = http('--form', 'POST', httpbin.url + '/post', 'foo=bar')
        assert HTTP_OK in r
        assert '"foo": "bar"' in r

    def test_POST_form_multiple_values(self, httpbin):
        r = http('--form', 'POST', httpbin.url + '/post', 'foo=bar', 'foo=baz')
        assert HTTP_OK in r
        assert r.json['form'] == {'foo': ['bar', 'baz']}

    def test_POST_stdin(self, httpbin):
        with open(FILE_PATH) as f:
            env = TestEnvironment(stdin=f, stdin_isatty=False)
            r = http('--form', 'POST', httpbin.url + '/post', env=env)
        assert HTTP_OK in r
        assert FILE_CONTENT in r

    def test_headers(self, httpbin):
        r = http('GET', httpbin.url + '/headers', 'Foo:bar')
        assert HTTP_OK in r
        assert '"User-Agent": "HTTPie' in r, r
        assert '"Foo": "bar"' in r
