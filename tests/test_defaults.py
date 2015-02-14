"""
Tests for the provided defaults regarding HTTP method, and --json vs. --form.

"""
from utils import TestEnvironment, http, HTTP_OK, no_content_type
from fixtures import FILE_PATH


class TestImplicitHTTPMethod:
    def test_implicit_GET(self, httpbin):
        r = http(httpbin.url + '/get')
        assert HTTP_OK in r

    def test_implicit_GET_with_headers(self, httpbin):
        r = http(httpbin.url + '/headers', 'Foo:bar')
        assert HTTP_OK in r
        assert r.json['headers']['Foo'] == 'bar'

    def test_implicit_POST_json(self, httpbin):
        r = http(httpbin.url + '/post', 'hello=world')
        assert HTTP_OK in r
        assert r.json['json'] == {'hello': 'world'}

    def test_implicit_POST_form(self, httpbin):
        r = http('--form', httpbin.url + '/post', 'foo=bar')
        assert HTTP_OK in r
        assert r.json['form'] == {'foo': 'bar'}

    def test_implicit_POST_stdin(self, httpbin):
        with open(FILE_PATH) as f:
            env = TestEnvironment(stdin_isatty=False, stdin=f)
            r = http('--form', httpbin.url + '/post', env=env)
        assert HTTP_OK in r


class TestAutoContentTypeAndAcceptHeaders:
    """
    Test that Accept and Content-Type correctly defaults to JSON,
    but can still be overridden. The same with Content-Type when --form
    -f is used.

    """

    def test_GET_no_data_no_auto_headers(self, httpbin):
        # https://github.com/jakubroztocil/httpie/issues/62
        r = http('GET', httpbin.url + '/headers')
        assert HTTP_OK in r
        assert r.json['headers']['Accept'] == '*/*'
        assert no_content_type(r.json['headers'])

    def test_POST_no_data_no_auto_headers(self, httpbin):
        # JSON headers shouldn't be automatically set for POST with no data.
        r = http('POST', httpbin.url + '/post')
        assert HTTP_OK in r
        assert '"Accept": "*/*"' in r
        assert '"Content-Type": "application/json' not in r

    def test_POST_with_data_auto_JSON_headers(self, httpbin):
        r = http('POST', httpbin.url + '/post', 'a=b')
        assert HTTP_OK in r
        assert '"Accept": "application/json"' in r
        assert '"Content-Type": "application/json' in r

    def test_GET_with_data_auto_JSON_headers(self, httpbin):
        # JSON headers should automatically be set also for GET with data.
        r = http('POST', httpbin.url + '/post', 'a=b')
        assert HTTP_OK in r
        assert '"Accept": "application/json"' in r, r
        assert '"Content-Type": "application/json' in r

    def test_POST_explicit_JSON_auto_JSON_accept(self, httpbin):
        r = http('--json', 'POST', httpbin.url + '/post')
        assert HTTP_OK in r
        assert r.json['headers']['Accept'] == 'application/json'
        # Make sure Content-Type gets set even with no data.
        # https://github.com/jakubroztocil/httpie/issues/137
        assert 'application/json' in r.json['headers']['Content-Type']

    def test_GET_explicit_JSON_explicit_headers(self, httpbin):
        r = http('--json', 'GET', httpbin.url + '/headers',
                 'Accept:application/xml',
                 'Content-Type:application/xml')
        assert HTTP_OK in r
        assert '"Accept": "application/xml"' in r
        assert '"Content-Type": "application/xml"' in r

    def test_POST_form_auto_Content_Type(self, httpbin):
        r = http('--form', 'POST', httpbin.url + '/post')
        assert HTTP_OK in r
        assert '"Content-Type": "application/x-www-form-urlencoded' in r

    def test_POST_form_Content_Type_override(self, httpbin):
        r = http('--form', 'POST', httpbin.url + '/post',
                 'Content-Type:application/xml')
        assert HTTP_OK in r
        assert '"Content-Type": "application/xml"' in r

    def test_print_only_body_when_stdout_redirected_by_default(self, httpbin):
        env = TestEnvironment(stdin_isatty=True, stdout_isatty=False)
        r = http('GET', httpbin.url + '/get', env=env)
        assert 'HTTP/' not in r

    def test_print_overridable_when_stdout_redirected(self, httpbin):
        env = TestEnvironment(stdin_isatty=True, stdout_isatty=False)
        r = http('--print=h', 'GET', httpbin.url + '/get', env=env)
        assert HTTP_OK in r
