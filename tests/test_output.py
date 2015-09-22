import pytest

from utils import TestEnvironment, http, HTTP_OK, COLOR, CRLF
from httpie import ExitStatus
from httpie.output.formatters.colors import get_lexer
from httpie.output.formatters.xml import XMLFormatter


class TestVerboseFlag:
    def test_verbose(self, httpbin):
        r = http('--verbose',
                 'GET', httpbin.url + '/get', 'test-header:__test__')
        assert HTTP_OK in r
        assert r.count('__test__') == 2

    def test_verbose_form(self, httpbin):
        # https://github.com/jkbrzt/httpie/issues/53
        r = http('--verbose', '--form', 'POST', httpbin.url + '/post',
                 'A=B', 'C=D')
        assert HTTP_OK in r
        assert 'A=B&C=D' in r

    def test_verbose_json(self, httpbin):
        r = http('--verbose',
                 'POST', httpbin.url + '/post', 'foo=bar', 'baz=bar')
        assert HTTP_OK in r
        assert '"baz": "bar"' in r


class TestColors:

    @pytest.mark.parametrize('mime', [
        'application/json',
        'application/json+foo',
        'application/foo+json',
        'application/json-foo',
        'application/x-json',
        'foo/json',
        'foo/json+bar',
        'foo/bar+json',
        'foo/json-foo',
        'foo/x-json',
    ])
    def test_get_lexer(self, mime):
        lexer = get_lexer(mime)
        assert lexer is not None
        assert lexer.name == 'JSON'

    def test_get_lexer_not_found(self):
        assert get_lexer('xxx/yyy') is None


class TestPrettyOptions:
    """Test the --pretty flag handling."""

    def test_pretty_enabled_by_default(self, httpbin):
        env = TestEnvironment(colors=256)
        r = http('GET', httpbin.url + '/get', env=env)
        assert COLOR in r

    def test_pretty_enabled_by_default_unless_stdout_redirected(self, httpbin):
        r = http('GET', httpbin.url + '/get')
        assert COLOR not in r

    def test_force_pretty(self, httpbin):
        env = TestEnvironment(stdout_isatty=False, colors=256)
        r = http('--pretty=all', 'GET', httpbin.url + '/get', env=env, )
        assert COLOR in r

    def test_force_ugly(self, httpbin):
        r = http('--pretty=none', 'GET', httpbin.url + '/get')
        assert COLOR not in r

    def test_subtype_based_pygments_lexer_match(self, httpbin):
        """Test that media subtype is used if type/subtype doesn't
        match any lexer.

        """
        env = TestEnvironment(colors=256)
        r = http('--print=B', '--pretty=all', httpbin.url + '/post',
                 'Content-Type:text/foo+json', 'a=b', env=env)
        assert COLOR in r

    def test_colors_option(self, httpbin):
        env = TestEnvironment(colors=256)
        r = http('--print=B', '--pretty=colors',
                 'GET', httpbin.url + '/get', 'a=b',
                 env=env)
        # Tests that the JSON data isn't formatted.
        assert not r.strip().count('\n')
        assert COLOR in r

    def test_format_option(self, httpbin):
        env = TestEnvironment(colors=256)
        r = http('--print=B', '--pretty=format',
                 'GET', httpbin.url + '/get', 'a=b',
                 env=env)
        # Tests that the JSON data is formatted.
        assert r.strip().count('\n') == 2
        assert COLOR not in r


class TestLineEndings:
    """
    Test that CRLF is properly used in headers
    and as the headers/body separator.

    """
    def _validate_crlf(self, msg):
        lines = iter(msg.splitlines(True))
        for header in lines:
            if header == CRLF:
                break
            assert header.endswith(CRLF), repr(header)
        else:
            assert 0, 'CRLF between headers and body not found in %r' % msg
        body = ''.join(lines)
        assert CRLF not in body
        return body

    def test_CRLF_headers_only(self, httpbin):
        r = http('--headers', 'GET', httpbin.url + '/get')
        body = self._validate_crlf(r)
        assert not body, 'Garbage after headers: %r' % r

    def test_CRLF_ugly_response(self, httpbin):
        r = http('--pretty=none', 'GET', httpbin.url + '/get')
        self._validate_crlf(r)

    def test_CRLF_formatted_response(self, httpbin):
        r = http('--pretty=format', 'GET', httpbin.url + '/get')
        assert r.exit_status == ExitStatus.OK
        self._validate_crlf(r)

    def test_CRLF_ugly_request(self, httpbin):
        r = http('--pretty=none', '--print=HB', 'GET', httpbin.url + '/get')
        self._validate_crlf(r)

    def test_CRLF_formatted_request(self, httpbin):
        r = http('--pretty=format', '--print=HB', 'GET', httpbin.url + '/get')
        self._validate_crlf(r)


class TestXmlFormatter:

    @pytest.fixture
    def formatter(self):
        return XMLFormatter()

    def test_it_does_not_parse_non_xml_body(self, formatter):
        body = 'foo'
        formatted_body = formatter.format_body(body=body, mime='text/html')
        assert body == body

    def test_it_parses_xml_body(self, formatter):
        xml_body = '''<body>Some text</body>'''
        formatted_body = formatter.format_body(body=xml_body, mime='text/xml')
        assert xml_body == formatted_body

    def test_it_ignores_invalid_xml_body(self, formatter):
        invalid_body = '''<body>Hello!'''
        formatted_body = formatter.format_body(body=invalid_body, mime='xml')
        assert invalid_body == formatted_body

    def test_it_returns_xml_body_when_parsing_xml_bomb(self, formatter):
        xmlbomb = '''
        <!DOCTYPE xmlbomb [
        <!ENTITY a "1234567890" >
        <!ENTITY b "&a;&a;&a;&a;&a;&a;&a;&a;">
        <!ENTITY c "&b;&b;&b;&b;&b;&b;&b;&b;">
        <!ENTITY d "&c;&c;&c;&c;&c;&c;&c;&c;">
        <!ENTITY e "&d;&d;&d;&d;&d;&d;&d;&d;">
        ]>
        <bomb>&e;</bomb>
        '''
        formatted_body = formatter.format_body(body=xmlbomb, mime='xml')
        assert formatted_body == xmlbomb
