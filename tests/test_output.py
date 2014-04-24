from tests import (
    BaseTestCase, TestEnvironment,
    http, httpbin,
    OK, COLOR, CRLF
)


class VerboseFlagTest(BaseTestCase):

    def test_verbose(self):
        r = http(
            '--verbose',
            'GET',
            httpbin('/get'),
            'test-header:__test__'
        )
        self.assertIn(OK, r)
        #noinspection PyUnresolvedReferences
        self.assertEqual(r.count('__test__'), 2)

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
        self.assertIn(OK, r)
        self.assertIn('foo=bar&baz=bar', r)

    def test_verbose_json(self):
        r = http(
            '--verbose',
            'POST',
            httpbin('/post'),
            'foo=bar',
            'baz=bar'
        )
        self.assertIn(OK, r)
        self.assertIn('"baz": "bar"', r)  # request
        self.assertIn(r'\"baz\": \"bar\"', r)  # response


class PrettyOptionsTest(BaseTestCase):
    """Test the --pretty flag handling."""

    def test_pretty_enabled_by_default(self):
        r = http(
            'GET',
            httpbin('/get'),
            env=TestEnvironment(colors=256),
        )
        self.assertIn(COLOR, r)

    def test_pretty_enabled_by_default_unless_stdout_redirected(self):
        r = http(
            'GET',
            httpbin('/get')
        )
        self.assertNotIn(COLOR, r)

    def test_force_pretty(self):
        r = http(
            '--pretty=all',
            'GET',
            httpbin('/get'),
            env=TestEnvironment(stdout_isatty=False, colors=256),
        )
        self.assertIn(COLOR, r)

    def test_force_ugly(self):
        r = http(
            '--pretty=none',
            'GET',
            httpbin('/get'),
        )
        self.assertNotIn(COLOR, r)

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
        self.assertIn(COLOR, r)

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
        self.assertEqual(r.strip().count('\n'), 0)
        self.assertIn(COLOR, r)

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
        self.assertEqual(r.strip().count('\n'), 2)
        self.assertNotIn(COLOR, r)


class LineEndingsTest(BaseTestCase):
    """Test that CRLF is properly used in headers and
    as the headers/body separator."""

    def _validate_crlf(self, msg):
        lines = iter(msg.splitlines(True))
        for header in lines:
            if header == CRLF:
                break
            self.assertTrue(header.endswith(CRLF), repr(header))
        else:
            self.fail('CRLF between headers and body not found in %r' % msg)
        body = ''.join(lines)
        self.assertNotIn(CRLF, body)
        return body

    def test_CRLF_headers_only(self):
        r = http(
            '--headers',
            'GET',
            httpbin('/get')
        )
        body = self._validate_crlf(r)
        self.assertFalse(body, 'Garbage after headers: %r' % r)

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
        self.assertEqual(r.exit_status, 0)
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
