from unittest import TestCase

from httpie import ExitStatus
from tests import (
    TestEnvironment,
    http, httpbin,
    HTTP_OK, COLOR, CRLF
)


class VerboseFlagTest(TestCase):

    def test_verbose(self):
        r = http(
            '--verbose',
            'GET',
            httpbin('/get'),
            'test-header:__test__'
        )
        assert HTTP_OK in r
        assert r.count('__test__') == 2

    def test_verbose_form(self):
        # https://github.com/jkbr/httpie/issues/53
        r = http(
            '--verbose',
            '--form',
            'POST',
            httpbin('/post'),
            'foo=bar',
            'baz=bar'
        )
        assert HTTP_OK in r
        assert 'foo=bar&baz=bar' in r

    def test_verbose_json(self):
        r = http(
            '--verbose',
            'POST',
            httpbin('/post'),
            'foo=bar',
            'baz=bar'
        )
        assert HTTP_OK in r
        assert '"baz": "bar"' in r  # request
        assert r'\"baz\": \"bar\"' in r  # response


class PrettyOptionsTest(TestCase):
    """Test the --pretty flag handling."""

    def test_pretty_enabled_by_default(self):
        r = http(
            'GET',
            httpbin('/get'),
            env=TestEnvironment(colors=256),
        )
        assert COLOR in r

    def test_pretty_enabled_by_default_unless_stdout_redirected(self):
        r = http(
            'GET',
            httpbin('/get')
        )
        assert COLOR not in r

    def test_force_pretty(self):
        r = http(
            '--pretty=all',
            'GET',
            httpbin('/get'),
            env=TestEnvironment(stdout_isatty=False, colors=256),
        )
        assert COLOR in r

    def test_force_ugly(self):
        r = http(
            '--pretty=none',
            'GET',
            httpbin('/get'),
        )
        assert COLOR not in r

    def test_subtype_based_pygments_lexer_match(self):
        """Test that media subtype is used if type/subtype doesn't
        match any lexer.

        """
        r = http(
            '--print=B',
            '--pretty=all',
            httpbin('/post'),
            'Content-Type:text/foo+json',
            'a=b',
            env=TestEnvironment(colors=256)
        )
        assert COLOR in r

    def test_colors_option(self):
        r = http(
            '--print=B',
            '--pretty=colors',
            'GET',
            httpbin('/get'),
            'a=b',
            env=TestEnvironment(colors=256),
        )
        #noinspection PyUnresolvedReferences
        # Tests that the JSON data isn't formatted.
        assert not r.strip().count('\n')
        assert COLOR in r

    def test_format_option(self):
        r = http(
            '--print=B',
            '--pretty=format',
            'GET',
            httpbin('/get'),
            'a=b',
            env=TestEnvironment(colors=256),
        )
        #noinspection PyUnresolvedReferences
        # Tests that the JSON data is formatted.
        assert r.strip().count('\n') == 2
        assert COLOR not in r


class LineEndingsTest(TestCase):
    """Test that CRLF is properly used in headers and
    as the headers/body separator."""

    def _validate_crlf(self, msg):
        lines = iter(msg.splitlines(True))
        for header in lines:
            if header == CRLF:
                break
            assert header.endswith(CRLF), repr(header)
        else:
            self.fail('CRLF between headers and body not found in %r' % msg)
        body = ''.join(lines)
        assert CRLF not in body
        return body

    def test_CRLF_headers_only(self):
        r = http(
            '--headers',
            'GET',
            httpbin('/get')
        )
        body = self._validate_crlf(r)
        assert not body, 'Garbage after headers: %r' % r

    def test_CRLF_ugly_response(self):
        r = http(
            '--pretty=none',
            'GET',
            httpbin('/get')
        )
        self._validate_crlf(r)

    def test_CRLF_formatted_response(self):
        r = http(
            '--pretty=format',
            'GET',
            httpbin('/get')
        )
        assert r.exit_status == ExitStatus.OK
        self._validate_crlf(r)

    def test_CRLF_ugly_request(self):
        r = http(
            '--pretty=none',
            '--print=HB',
            'GET',
            httpbin('/get')
        )
        self._validate_crlf(r)

    def test_CRLF_formatted_request(self):
        r = http(
            '--pretty=format',
            '--print=HB',
            'GET',
            httpbin('/get')
        )
        self._validate_crlf(r)
