#!/usr/bin/env python
# coding=utf8
"""

Many of the test cases here use httpbin.org.

To make it run faster and offline you can::

    # Install `httpbin` locally
    pip install git+https://github.com/kennethreitz/httpbin.git

    # Run it
    httpbin

    # Run the tests against it
    HTTPBIN_URL=http://localhost:5000 python setup.py test

    # Test all Python environments
    HTTPBIN_URL=http://localhost:5000 tox

"""
import os
import sys
import json
import argparse
import tempfile
import unittest
try:
    from urllib.request import urlopen
except ImportError:
    from urllib2 import urlopen
try:
    from unittest import skipIf
except ImportError:

    def skipIf(cond, reason):
        def decorator(test_method):
            if cond:
                return lambda self: None
            return test_method
        return decorator


from requests.compat import is_windows, is_py26, bytes, str



#################################################################
# Utils/setup
#################################################################

# HACK: Prepend ../ to PYTHONPATH so that we can import httpie form there.
TESTS_ROOT = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, os.path.realpath(os.path.join(TESTS_ROOT, '..')))

from httpie import EXIT
from httpie import input
from httpie.models import Environment
from httpie.core import main
from httpie.output import BINARY_SUPPRESSED_NOTICE
from httpie.input import ParseError


HTTPBIN_URL = os.environ.get('HTTPBIN_URL',
                             'http://httpbin.org').rstrip('/')


OK = 'HTTP/1.1 200'
OK_COLOR = (
    'HTTP\x1b[39m\x1b[38;5;245m/\x1b[39m\x1b'
    '[38;5;37m1.1\x1b[39m\x1b[38;5;245m \x1b[39m\x1b[38;5;37m200'
    '\x1b[39m\x1b[38;5;245m \x1b[39m\x1b[38;5;136mOK'
)
COLOR = '\x1b['


def patharg(path):
    """Back slashes need to be escaped in ITEM args, even in Windows paths."""
    return path.replace('\\', '\\\\\\')

# Test files
FILE_PATH = os.path.join(TESTS_ROOT, 'fixtures', 'file.txt')
FILE2_PATH = os.path.join(TESTS_ROOT, 'fixtures', 'file2.txt')
BIN_FILE_PATH = os.path.join(TESTS_ROOT, 'fixtures', 'file.bin')

FILE_PATH_ARG = patharg(FILE_PATH)
FILE2_PATH_ARG = patharg(FILE2_PATH)
BIN_FILE_PATH_ARG = patharg(BIN_FILE_PATH)

with open(FILE_PATH) as f:
    FILE_CONTENT = f.read().strip()
with open(BIN_FILE_PATH, 'rb') as f:
    BIN_FILE_CONTENT = f.read()


def httpbin(path):
    return HTTPBIN_URL + path


class TestEnvironment(Environment):
    colors = 0
    stdin_isatty = True,
    stdout_isatty = True
    is_windows = False

    def __init__(self, **kwargs):

        if 'stdout' not in kwargs:
            kwargs['stdout'] = tempfile.TemporaryFile('w+b')

        if 'stderr' not in kwargs:
            kwargs['stderr'] = tempfile.TemporaryFile('w+t')

        super(TestEnvironment, self).__init__(**kwargs)


class BytesResponse(bytes):
    stderr = json = exit_status = None
class StrResponse(str):
    stderr = json = exit_status = None


def http(*args, **kwargs):
    """
    Invoke `httpie.core.main()` with `args` and `kwargs`,
    and return a unicode response.

    Return a `StrResponse`, or `BytesResponse` if unable to decode the output.
    The response has the following attributes:

        `stderr`: text written to stderr
        `exit_status`: the exit status
        `json`: decoded JSON (if possible) or `None`

    Exceptions are propagated except for SystemExit.

    """
    env = kwargs.get('env')
    if not env:
        env = kwargs['env'] = TestEnvironment()

    try:

        try:
            exit_status = main(args=['--debug'] + list(args), **kwargs)
        except Exception:
            sys.stderr.write(env.stderr.read())
            raise
        except SystemExit:
            exit_status = EXIT.ERROR

        env.stdout.seek(0)
        env.stderr.seek(0)

        output = env.stdout.read()

        try:
            r = StrResponse(output.decode('utf8'))
        except UnicodeDecodeError:
            r = BytesResponse(output)
        else:
            if COLOR not in r:
                # De-serialize JSON body if possible.
                if r.strip().startswith('{'):
                    #noinspection PyTypeChecker
                    r.json = json.loads(r)
                elif r.count('Content-Type:') == 1 and 'application/json' in r:
                    try:
                        j = r.strip()[r.strip().rindex('\n\n'):]
                    except ValueError:
                        pass
                    else:
                        try:
                            r.json = json.loads(j)
                        except ValueError:
                            pass

        r.stderr = env.stderr.read()
        r.exit_status = exit_status

        return r

    finally:
        env.stdout.close()
        env.stderr.close()


class BaseTestCase(unittest.TestCase):

    if is_py26:
        def assertIn(self, member, container, msg=None):
            self.assertTrue(member in container, msg)

        def assertNotIn(self, member, container, msg=None):
            self.assertTrue(member not in container, msg)

        def assertDictEqual(self, d1, d2, msg=None):
            self.assertEqual(set(d1.keys()), set(d2.keys()), msg)
            self.assertEqual(sorted(d1.values()), sorted(d2.values()), msg)


#################################################################
# High-level tests using httpbin.
#################################################################

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
        self.assertIn('"foo": "bar"', r)

    def test_POST_JSON_data(self):
        r = http(
            'POST',
            httpbin('/post'),
            'foo=bar'
        )
        self.assertIn(OK, r)
        self.assertIn('"foo": "bar"', r)

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


class QuerystringTest(BaseTestCase):

    def test_query_string_params_in_url(self):
        r = http(
            '--print=Hhb',
            'GET',
            httpbin('/get?a=1&b=2')
        )

        path = '/get?a=1&b=2'
        url = httpbin(path)

        self.assertIn(OK, r)
        self.assertIn('GET %s HTTP/1.1' % path, r)
        self.assertIn('"url": "%s"' % url, r)

    def test_query_string_params_items(self):
        r = http(
            '--print=Hhb',
            'GET',
            httpbin('/get'),
            'a==1',
            'b==2'
        )

        path = '/get?a=1&b=2'
        url = httpbin(path)

        self.assertIn(OK, r)
        self.assertIn('GET %s HTTP/1.1' % path, r)
        self.assertIn('"url": "%s"' % url, r)

    def test_query_string_params_in_url_and_items_with_duplicates(self):
        r = http(
            '--print=Hhb',
            'GET',
            httpbin('/get?a=1&a=1'),
            'a==1',
            'a==1',
            'b==2',
        )

        path = '/get?a=1&a=1&a=1&a=1&b=2'
        url = httpbin(path)

        self.assertIn(OK, r)
        self.assertIn('GET %s HTTP/1.1' % path, r)
        self.assertIn('"url": "%s"' % url, r)


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

    def test_POST_explicit_JSON_auto_JSON_headers(self):
        r = http(
            '--json',
            'POST',
            httpbin('/post')
        )
        self.assertIn(OK, r)
        self.assertIn('"Accept": "application/json"', r)
        self.assertIn('"Content-Type": "application/json; charset=utf-8', r)

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
        self.assertIn('"hello": "world"', r)

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


class PrettyFlagTest(BaseTestCase):
    """Test the --pretty / --ugly flag handling."""

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
            '--pretty',
            'GET',
            httpbin('/get'),
            env=TestEnvironment(stdout_isatty=False, colors=256),
        )
        self.assertIn(COLOR, r)

    def test_force_ugly(self):
        r = http(
            '--ugly',
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
            '--pretty',
            httpbin('/post'),
            'Content-Type:text/foo+json',
            'a=b',
            env=TestEnvironment(colors=256)
        )
        self.assertIn(COLOR, r)


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
        #noinspection PyUnresolvedReferences
        self.assertEqual(r.count('"baz": "bar"'), 2)


class MultipartFormDataFileUploadTest(BaseTestCase):

    def test_non_existent_file_raises_parse_error(self):
        self.assertRaises(ParseError, http,
            '--form',
            'POST',
            httpbin('/post'),
            'foo@/__does_not_exist__',
        )

    def test_upload_ok(self):
        r = http(
            '--form',
            '--verbose',
            'POST',
            httpbin('/post'),
            'test-file@%s' % FILE_PATH_ARG,
            'foo=bar'
        )

        self.assertIn(OK, r)
        self.assertIn('Content-Disposition: form-data; name="foo"', r)
        self.assertIn('Content-Disposition: form-data; name="test-file";'
                      ' filename="%s"' % os.path.basename(FILE_PATH), r)
        #noinspection PyUnresolvedReferences
        self.assertEqual(r.count(FILE_CONTENT), 2)
        self.assertIn('"foo": "bar"', r)


class BinaryRequestDataTest(BaseTestCase):

    def test_binary_stdin(self):
        with open(BIN_FILE_PATH, 'rb') as stdin:
            env = TestEnvironment(
                stdin=stdin,
                stdin_isatty=False,
                stdout_isatty=False
            )
            r = http(
                '--print=B',
                'POST',
                httpbin('/post'),
                env=env,
            )
            self.assertEqual(r, BIN_FILE_CONTENT)

    def test_binary_file_path(self):
        env = TestEnvironment(
            stdin_isatty=True,
            stdout_isatty=False
        )
        r = http(
            '--print=B',
            'POST',
            httpbin('/post'),
            '@' + BIN_FILE_PATH_ARG,
            env=env,
        )

        self.assertEqual(r, BIN_FILE_CONTENT)

    def test_binary_file_form(self):
        env = TestEnvironment(
            stdin_isatty=True,
            stdout_isatty=False
        )
        r = http(
            '--print=B',
            '--form',
            'POST',
            httpbin('/post'),
            'test@' + BIN_FILE_PATH_ARG,
            env=env,
        )
        self.assertIn(bytes(BIN_FILE_CONTENT), bytes(r))


class BinaryResponseDataTest(BaseTestCase):

    url = 'http://www.google.com/favicon.ico'

    @property
    def bindata(self):
        if not hasattr(self, '_bindata'):
            self._bindata = urlopen(self.url).read()
        return self._bindata

    def test_binary_suppresses_when_terminal(self):
        r = http(
            'GET',
            self.url
        )
        self.assertIn(BINARY_SUPPRESSED_NOTICE.decode(), r)

    def test_binary_suppresses_when_not_terminal_but_pretty(self):
        r = http(
            '--pretty',
            'GET',
            self.url,
            env=TestEnvironment(stdin_isatty=True,
                            stdout_isatty=False)
        )
        self.assertIn(BINARY_SUPPRESSED_NOTICE.decode(), r)

    def test_binary_included_and_correct_when_suitable(self):
        r = http(
            'GET',
            self.url,
            env=TestEnvironment(stdin_isatty=True,
                            stdout_isatty=False)
        )
        self.assertEqual(r, self.bindata)


class RequestBodyFromFilePathTest(BaseTestCase):
    """
    `http URL @file'

    """
    def test_request_body_from_file_by_path(self):
        r = http(
            'POST',
            httpbin('/post'),
            '@' + FILE_PATH_ARG
        )
        self.assertIn(OK, r)
        self.assertIn(FILE_CONTENT, r)
        self.assertIn('"Content-Type": "text/plain"', r)

    def test_request_body_from_file_by_path_with_explicit_content_type(self):
        r = http(
            'POST',
            httpbin('/post'),
            '@' + FILE_PATH_ARG,
            'Content-Type:x-foo/bar'
        )
        self.assertIn(OK, r)
        self.assertIn(FILE_CONTENT, r)
        self.assertIn('"Content-Type": "x-foo/bar"', r)

    def test_request_body_from_file_by_path_no_field_name_allowed(self):
        env = TestEnvironment(stdin_isatty=True)
        r = http(
            'POST',
            httpbin('/post'),
            'field-name@' + FILE_PATH_ARG,
            env=env
        )
        self.assertIn('perhaps you meant --form?', r.stderr)

    def test_request_body_from_file_by_path_no_data_items_allowed(self):
        r = http(
            'POST',
            httpbin('/post'),
            '@' + FILE_PATH_ARG,
            'foo=bar',
            env=TestEnvironment(stdin_isatty=False)
        )
        self.assertIn('cannot be mixed', r.stderr)


class AuthTest(BaseTestCase):

    def test_basic_auth(self):
        r = http(
            '--auth=user:password',
            'GET',
            httpbin('/basic-auth/user/password')
        )
        self.assertIn(OK, r)
        self.assertIn('"authenticated": true', r)
        self.assertIn('"user": "user"', r)

    def test_digest_auth(self):
        r = http(
            '--auth-type=digest',
            '--auth=user:password',
            'GET',
            httpbin('/digest-auth/auth/user/password')
        )
        self.assertIn(OK, r)
        self.assertIn('"authenticated": true', r)
        self.assertIn('"user": "user"', r)

    def test_password_prompt(self):

        input.AuthCredentials._getpass = lambda self, prompt: 'password'

        r = http(
            '--auth',
            'user',
            'GET',
            httpbin('/basic-auth/user/password')
        )

        self.assertIn(OK, r)
        self.assertIn('"authenticated": true', r)
        self.assertIn('"user": "user"', r)


class ExitStatusTest(BaseTestCase):

    def test_ok_response_exits_0(self):
        r = http(
            'GET',
            httpbin('/status/200')
        )
        self.assertIn(OK, r)
        self.assertEqual(r.exit_status, EXIT.OK)

    def test_error_response_exits_0_without_check_status(self):
        r = http(
            'GET',
            httpbin('/status/500')
        )
        self.assertIn('HTTP/1.1 500', r)
        self.assertEqual(r.exit_status, EXIT.OK)

    def test_3xx_check_status_exits_3_and_stderr_when_stdout_redirected(self):
        r = http(
            '--check-status',
            '--headers',  # non-terminal, force headers
            'GET',
            httpbin('/status/301'),
            env=TestEnvironment(stdout_isatty=False,)
        )
        self.assertIn('HTTP/1.1 301', r)
        self.assertEqual(r.exit_status, EXIT.ERROR_HTTP_3XX)
        self.assertIn('301 moved permanently', r.stderr.lower())

    def test_3xx_check_status_redirects_allowed_exits_0(self):
        r = http(
            '--check-status',
            '--allow-redirects',
            'GET',
            httpbin('/status/301')
        )
        # The redirect will be followed so 200 is expected.
        self.assertIn('HTTP/1.1 200 OK', r)
        self.assertEqual(r.exit_status, EXIT.OK)

    def test_4xx_check_status_exits_4(self):
        r = http(
            '--check-status',
            'GET',
            httpbin('/status/401')
        )
        self.assertIn('HTTP/1.1 401', r)
        self.assertEqual(r.exit_status, EXIT.ERROR_HTTP_4XX)
        # Also stderr should be empty since stdout isn't redirected.
        self.assertTrue(not r.stderr)

    def test_5xx_check_status_exits_5(self):
        r = http(
            '--check-status',
            'GET',
            httpbin('/status/500')
        )
        self.assertIn('HTTP/1.1 500', r)
        self.assertEqual(r.exit_status, EXIT.ERROR_HTTP_5XX)


class FakeWindowsTest(BaseTestCase):

    def test_stdout_redirect_not_supported_on_windows(self):
        env = TestEnvironment(is_windows=True, stdout_isatty=False)
        r = http(
            'GET',
            httpbin('/get'),
            env=env
        )
        self.assertNotEqual(r.exit_status, EXIT.OK)
        self.assertIn('Windows', r.stderr)
        self.assertIn('--output', r.stderr)

    def test_output_file_pretty_not_allowed_on_windows(self):

        r = http(
            '--output',
            os.path.join(tempfile.gettempdir(), '__httpie_test_output__'),
            '--pretty',
            'GET',
            httpbin('/get'),
            env=TestEnvironment(is_windows=True)
        )
        self.assertIn(
            'Only terminal output can be prettified on Windows', r.stderr)


class StreamTest(BaseTestCase):
    # GET because httpbin 500s with binary POST body.

    @skipIf(is_windows, 'Pretty redirect not supported under Windows')
    def test_pretty_redirected_stream(self):
        """Test that --stream works with prettified redirected output."""
        with open(BIN_FILE_PATH, 'rb') as f:
            r = http(
                '--verbose',
                '--pretty',
                '--stream',
                'GET',
                httpbin('/get'),
                env=TestEnvironment(
                    colors=256,
                    stdin=f,
                    stdin_isatty=False,
                    stdout_isatty=False,
                )
            )
        self.assertIn(BINARY_SUPPRESSED_NOTICE.decode(), r)
        self.assertIn(OK_COLOR, r)

    def test_encoded_stream(self):
        """Test that --stream works with non-prettified redirected terminal output."""
        with open(BIN_FILE_PATH, 'rb') as f:
            r = http(
                '--ugly',
                '--stream',
                '--verbose',
                'GET',
                httpbin('/get'),
                env=TestEnvironment(
                    stdin=f,
                    stdin_isatty=False
                ),
            )
        self.assertIn(BINARY_SUPPRESSED_NOTICE.decode(), r)
        self.assertIn(OK, r)

    def test_redirected_stream(self):
        """Test that --stream works with non-prettified redirected terminal output."""
        with open(BIN_FILE_PATH, 'rb') as f:
            r = http(
                '--ugly',
                '--stream',
                '--verbose',
                'GET',
                httpbin('/get'),
                env=TestEnvironment(
                    stdout_isatty=False,
                    stdin=f,
                    stdin_isatty=False
                )
            )
        self.assertIn(OK.encode(), r)
        self.assertIn(BIN_FILE_CONTENT, r)


#################################################################
# CLI argument parsing related tests.
#################################################################

class ItemParsingTest(BaseTestCase):

    def setUp(self):
        self.key_value_type = input.KeyValueArgType(
            input.SEP_HEADERS,
            input.SEP_QUERY,
            input.SEP_DATA,
            input.SEP_DATA_RAW_JSON,
            input.SEP_FILES,
        )

    def test_invalid_items(self):
        items = ['no-separator']
        for item in items:
            self.assertRaises(argparse.ArgumentTypeError,
                              lambda: self.key_value_type(item))

    def test_escape(self):
        headers, data, files, params = input.parse_items([
            # headers
            self.key_value_type('foo\\:bar:baz'),
            self.key_value_type('jack\\@jill:hill'),
            # data
            self.key_value_type('baz\\=bar=foo'),
            # files
            self.key_value_type('bar\\@baz@%s' % FILE_PATH_ARG)
        ])
        self.assertDictEqual(headers, {
            'foo:bar': 'baz',
            'jack@jill': 'hill',
        })
        self.assertDictEqual(data, {
            'baz=bar': 'foo',
        })
        self.assertIn('bar@baz', files)

    def test_escape_longsep(self):
        headers, data, files, params = input.parse_items([
            self.key_value_type('bob\\:==foo'),
        ])
        self.assertDictEqual(params, {
            'bob:': 'foo',
        })

    def test_valid_items(self):
        headers, data, files, params = input.parse_items([
            self.key_value_type('string=value'),
            self.key_value_type('header:value'),
            self.key_value_type('list:=["a", 1, {}, false]'),
            self.key_value_type('obj:={"a": "b"}'),
            self.key_value_type('eh:'),
            self.key_value_type('ed='),
            self.key_value_type('bool:=true'),
            self.key_value_type('test-file@%s' % FILE_PATH_ARG),
            self.key_value_type('query==value'),
        ])
        self.assertDictEqual(headers, {
            'header': 'value',
            'eh': ''
        })
        self.assertDictEqual(data, {
            "ed": "",
            "string": "value",
            "bool": True,
            "list": ["a", 1, {}, False],
            "obj": {"a": "b"},
        })
        self.assertDictEqual(params, {
            'query': 'value',
        })
        self.assertIn('test-file', files)


class ArgumentParserTestCase(unittest.TestCase):

    def setUp(self):
        self.parser = input.Parser()

    def test_guess_when_method_set_and_valid(self):
        args = argparse.Namespace()
        args.method = 'GET'
        args.url = 'http://example.com/'
        args.items = []

        self.parser._guess_method(args, TestEnvironment())

        self.assertEqual(args.method, 'GET')
        self.assertEqual(args.url, 'http://example.com/')
        self.assertEqual(args.items, [])

    def test_guess_when_method_not_set(self):
        args = argparse.Namespace()
        args.method = None
        args.url = 'http://example.com/'
        args.items = []

        self.parser._guess_method(args, TestEnvironment())

        self.assertEqual(args.method, 'GET')
        self.assertEqual(args.url, 'http://example.com/')
        self.assertEqual(args.items, [])

    def test_guess_when_method_set_but_invalid_and_data_field(self):
        args = argparse.Namespace()
        args.method = 'http://example.com/'
        args.url = 'data=field'
        args.items = []

        self.parser._guess_method(args, TestEnvironment())

        self.assertEqual(args.method, 'POST')
        self.assertEqual(args.url, 'http://example.com/')
        self.assertEqual(
            args.items,
            [input.KeyValue(
                key='data', value='field', sep='=', orig='data=field')])

    def test_guess_when_method_set_but_invalid_and_header_field(self):
        args = argparse.Namespace()
        args.method = 'http://example.com/'
        args.url = 'test:header'
        args.items = []

        self.parser._guess_method(args, TestEnvironment())

        self.assertEqual(args.method, 'GET')
        self.assertEqual(args.url, 'http://example.com/')
        self.assertEqual(
            args.items,
            [input.KeyValue(
                key='test', value='header', sep=':', orig='test:header')])

    def test_guess_when_method_set_but_invalid_and_item_exists(self):
        args = argparse.Namespace()
        args.method = 'http://example.com/'
        args.url = 'new_item=a'
        args.items = [
            input.KeyValue(
                key='old_item', value='b', sep='=', orig='old_item=b')
        ]

        self.parser._guess_method(args, TestEnvironment())

        self.assertEqual(args.items, [
            input.KeyValue(
                key='new_item', value='a', sep='=', orig='new_item=a'),
            input.KeyValue(key
                ='old_item', value='b', sep='=', orig='old_item=b'),
        ])


if __name__ == '__main__':
    #noinspection PyCallingNonCallable
    unittest.main()
