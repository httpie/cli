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
from io import BytesIO
import subprocess
import os
import sys
import json
import argparse
import tempfile
import unittest
import shutil
import time
from requests.structures import CaseInsensitiveDict

try:
    from urllib.request import urlopen
except ImportError:
    # noinspection PyUnresolvedReferences
    from urllib2 import urlopen
try:
    from unittest import skipIf, skip
except ImportError:
    skip = lambda msg: lambda self: None

    # noinspection PyUnusedLocal
    def skipIf(cond, reason):
        def decorator(test_method):
            if cond:
                return lambda self: None
            return test_method
        return decorator

from requests import __version__ as requests_version


#################################################################
# Utils/setup
#################################################################

# HACK: Prepend ../ to PYTHONPATH so that we can import httpie form there.
TESTS_ROOT = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, os.path.realpath(os.path.join(TESTS_ROOT, '..')))

from httpie import ExitStatus
from httpie import input
from httpie.models import Environment
from httpie.core import main
from httpie.output import BINARY_SUPPRESSED_NOTICE
from httpie.input import ParseError
from httpie.compat import is_windows, is_py26, bytes, str
from httpie.downloads import (
    parse_content_range,
    filename_from_content_disposition,
    filename_from_url,
    get_unique_filename,
    ContentRangeError,
    Download,
)


CRLF = '\r\n'
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


def mk_config_dir():
    return tempfile.mkdtemp(prefix='httpie_test_config_dir_')


class TestEnvironment(Environment):
    colors = 0
    stdin_isatty = True,
    stdout_isatty = True
    is_windows = False
    _shutil = shutil  # we need it in __del__ (would get gc'd)

    def __init__(self, **kwargs):

        if 'stdout' not in kwargs:
            kwargs['stdout'] = tempfile.TemporaryFile('w+b')

        if 'stderr' not in kwargs:
            kwargs['stderr'] = tempfile.TemporaryFile('w+t')

        self.delete_config_dir = False
        if 'config_dir' not in kwargs:
            kwargs['config_dir'] = mk_config_dir()
            self.delete_config_dir = True

        super(TestEnvironment, self).__init__(**kwargs)

    def __del__(self):
        if self.delete_config_dir:
            self._shutil.rmtree(self.config_dir)


def has_docutils():
    try:
        #noinspection PyUnresolvedReferences
        import docutils
        return True
    except ImportError:
        return False


def get_readme_errors():
    p = subprocess.Popen([
        'rst2pseudoxml.py',
        '--report=1',
        '--exit-status=1',
        os.path.join(TESTS_ROOT, '..', 'README.rst')
    ], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    err = p.communicate()[1]
    if p.returncode:
        return err


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

    stdout = env.stdout
    stderr = env.stderr
    try:

        try:
            exit_status = main(args=['--traceback'] + list(args), **kwargs)
            if '--download' in args:
                # Let the progress reporter thread finish.
                time.sleep(.5)
        except Exception:
            sys.stderr.write(stderr.read())
            raise
        except SystemExit:
            exit_status = ExitStatus.ERROR

        stdout.seek(0)
        stderr.seek(0)

        output = stdout.read()
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
                        j = r.strip()[r.strip().rindex('\r\n\r\n'):]
                    except ValueError:
                        pass
                    else:
                        try:
                            r.json = json.loads(j)
                        except ValueError:
                            pass

        r.stderr = stderr.read()
        r.exit_status = exit_status

        return r

    finally:
        stdout.close()
        stderr.close()


class BaseTestCase(unittest.TestCase):

    maxDiff = 100000

    if is_py26:
        def assertIn(self, member, container, msg=None):
            self.assertTrue(member in container, msg)

        def assertNotIn(self, member, container, msg=None):
            self.assertTrue(member not in container, msg)

        def assertDictEqual(self, d1, d2, msg=None):
            self.assertEqual(set(d1.keys()), set(d2.keys()), msg)
            self.assertEqual(sorted(d1.values()), sorted(d2.values()), msg)

    def assertIsNone(self, obj, msg=None):
        self.assertEqual(obj, None, msg=msg)


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
            '--pretty=all',
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
        # FIXME: *sometimes* fails on py33, the content-type is form.
        # https://github.com/jkbr/httpie/issues/140
        r = http(
            'POST',
            httpbin('/post'),
            '@' + FILE_PATH_ARG
        )
        self.assertIn(OK, r)
        self.assertIn(FILE_CONTENT, r)
        self.assertIn('"Content-Type": "text/plain"', r)

    def test_request_body_from_file_by_path_with_explicit_content_type(self):
        # FIXME: *sometimes* fails on py33, the content-type is form.
        # https://github.com/jkbr/httpie/issues/140
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

    @skipIf(requests_version == '0.13.6',
            'Redirects with prefetch=False are broken in Requests 0.13.6')
    def test_digest_auth(self):
        r = http(
            '--auth-type=digest',
            '--auth=user:password',
            'GET',
            httpbin('/digest-auth/auth/user/password')
        )
        self.assertIn(OK, r)
        self.assertIn(r'"authenticated": true', r)
        self.assertIn(r'"user": "user"', r)

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

    def test_credentials_in_url(self):
        url = httpbin('/basic-auth/user/password')
        url = 'http://user:password@' + url.split('http://', 1)[1]
        r = http(
            'GET',
            url
        )
        self.assertIn(OK, r)
        self.assertIn('"authenticated": true', r)
        self.assertIn('"user": "user"', r)

    def test_credentials_in_url_auth_flag_has_priority(self):
        """When credentials are passed in URL and via -a at the same time,
         then the ones from -a are used."""
        url = httpbin('/basic-auth/user/password')
        url = 'http://user:wrong_password@' + url.split('http://', 1)[1]
        r = http(
            '--auth=user:password',
            'GET',
            url
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
        self.assertEqual(r.exit_status, ExitStatus.OK)

    def test_error_response_exits_0_without_check_status(self):
        r = http(
            'GET',
            httpbin('/status/500')
        )
        self.assertIn('HTTP/1.1 500', r)
        self.assertEqual(r.exit_status, ExitStatus.OK)
        self.assertTrue(not r.stderr)

    def test_timeout_exit_status(self):
        r = http(
            '--timeout=0.5',
            'GET',
            httpbin('/delay/1')
        )
        self.assertEqual(r.exit_status, ExitStatus.ERROR_TIMEOUT)

    def test_3xx_check_status_exits_3_and_stderr_when_stdout_redirected(self):
        r = http(
            '--check-status',
            '--headers',  # non-terminal, force headers
            'GET',
            httpbin('/status/301'),
            env=TestEnvironment(stdout_isatty=False,)
        )
        self.assertIn('HTTP/1.1 301', r)
        self.assertEqual(r.exit_status, ExitStatus.ERROR_HTTP_3XX)
        self.assertIn('301 moved permanently', r.stderr.lower())

    @skipIf(requests_version == '0.13.6',
            'Redirects with prefetch=False are broken in Requests 0.13.6')
    def test_3xx_check_status_redirects_allowed_exits_0(self):
        r = http(
            '--check-status',
            '--follow',
            'GET',
            httpbin('/status/301')
        )
        # The redirect will be followed so 200 is expected.
        self.assertIn('HTTP/1.1 200 OK', r)
        self.assertEqual(r.exit_status, ExitStatus.OK)

    def test_4xx_check_status_exits_4(self):
        r = http(
            '--check-status',
            'GET',
            httpbin('/status/401')
        )
        self.assertIn('HTTP/1.1 401', r)
        self.assertEqual(r.exit_status, ExitStatus.ERROR_HTTP_4XX)
        # Also stderr should be empty since stdout isn't redirected.
        self.assertTrue(not r.stderr)

    def test_5xx_check_status_exits_5(self):
        r = http(
            '--check-status',
            'GET',
            httpbin('/status/500')
        )
        self.assertIn('HTTP/1.1 500', r)
        self.assertEqual(r.exit_status, ExitStatus.ERROR_HTTP_5XX)


class WindowsOnlyTests(BaseTestCase):

    @skip('FIXME: kills the runner')
    #@skipIf(not is_windows, 'windows-only')
    def test_windows_colorized_output(self):
        # Spits out the colorized output.
        http(httpbin('/get'), env=Environment())


class FakeWindowsTest(BaseTestCase):

    def test_output_file_pretty_not_allowed_on_windows(self):

        r = http(
            '--output',
            os.path.join(tempfile.gettempdir(), '__httpie_test_output__'),
            '--pretty=all',
            'GET',
            httpbin('/get'),
            env=TestEnvironment(is_windows=True)
        )
        self.assertIn(
            'Only terminal output can be colorized on Windows', r.stderr)


class StreamTest(BaseTestCase):
    # GET because httpbin 500s with binary POST body.

    @skipIf(is_windows, 'Pretty redirect not supported under Windows')
    def test_pretty_redirected_stream(self):
        """Test that --stream works with prettified redirected output."""
        with open(BIN_FILE_PATH, 'rb') as f:
            r = http(
                '--verbose',
                '--pretty=all',
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
        # We get 'Bad Request' but it's okay.
        #self.assertIn(OK_COLOR, r)

    def test_encoded_stream(self):
        """Test that --stream works with non-prettified
        redirected terminal output."""
        with open(BIN_FILE_PATH, 'rb') as f:
            r = http(
                '--pretty=none',
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
        # We get 'Bad Request' but it's okay.
        #self.assertIn(OK, r)

    def test_redirected_stream(self):
        """Test that --stream works with non-prettified
        redirected terminal output."""
        with open(BIN_FILE_PATH, 'rb') as f:
            r = http(
                '--pretty=none',
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
        # We get 'Bad Request' but it's okay.
        #self.assertIn(OK.encode(), r)
        self.assertIn(BIN_FILE_CONTENT, r)


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
        self.parser.args = argparse.Namespace()
        self.parser.args.method = 'GET'
        self.parser.args.url = 'http://example.com/'
        self.parser.args.items = []

        self.parser.env = TestEnvironment()

        self.parser._guess_method()

        self.assertEqual(self.parser.args.method, 'GET')
        self.assertEqual(self.parser.args.url, 'http://example.com/')
        self.assertEqual(self.parser.args.items, [])

    def test_guess_when_method_not_set(self):

        self.parser.args = argparse.Namespace()
        self.parser.args.method = None
        self.parser.args.url = 'http://example.com/'
        self.parser.args.items = []
        self.parser.env = TestEnvironment()

        self.parser._guess_method()

        self.assertEqual(self.parser.args.method, 'GET')
        self.assertEqual(self.parser.args.url, 'http://example.com/')
        self.assertEqual(self.parser.args.items, [])

    def test_guess_when_method_set_but_invalid_and_data_field(self):
        self.parser.args = argparse.Namespace()
        self.parser.args.method = 'http://example.com/'
        self.parser.args.url = 'data=field'
        self.parser.args.items = []
        self.parser.env = TestEnvironment()
        self.parser._guess_method()

        self.assertEqual(self.parser.args.method, 'POST')
        self.assertEqual(self.parser.args.url, 'http://example.com/')
        self.assertEqual(
            self.parser.args.items,
            [input.KeyValue(
                key='data', value='field', sep='=', orig='data=field')])

    def test_guess_when_method_set_but_invalid_and_header_field(self):
        self.parser.args = argparse.Namespace()
        self.parser.args.method = 'http://example.com/'
        self.parser.args.url = 'test:header'
        self.parser.args.items = []

        self.parser.env = TestEnvironment()

        self.parser._guess_method()

        self.assertEqual(self.parser.args.method, 'GET')
        self.assertEqual(self.parser.args.url, 'http://example.com/')
        self.assertEqual(
            self.parser.args.items,
            [input.KeyValue(
                key='test', value='header', sep=':', orig='test:header')])

    def test_guess_when_method_set_but_invalid_and_item_exists(self):
        self.parser.args = argparse.Namespace()
        self.parser.args.method = 'http://example.com/'
        self.parser.args.url = 'new_item=a'
        self.parser.args.items = [
            input.KeyValue(
                key='old_item', value='b', sep='=', orig='old_item=b')
        ]

        self.parser.env = TestEnvironment()

        self.parser._guess_method()

        self.assertEqual(self.parser.args.items, [
            input.KeyValue(
                key='new_item', value='a', sep='=', orig='new_item=a'),
            input.KeyValue(
                key='old_item', value='b', sep='=', orig='old_item=b'),
        ])


class TestNoOptions(BaseTestCase):

    def test_valid_no_options(self):
        r = http(
            '--verbose',
            '--no-verbose',
            'GET',
            httpbin('/get')
        )
        self.assertNotIn('GET /get HTTP/1.1', r)

    def test_invalid_no_options(self):
        r = http(
            '--no-war',
            'GET',
            httpbin('/get')
        )
        self.assertEqual(r.exit_status, 1)
        self.assertIn('unrecognized arguments: --no-war', r.stderr)
        self.assertNotIn('GET /get HTTP/1.1', r)


class READMETest(BaseTestCase):

    @skipIf(not has_docutils(), 'docutils not installed')
    def test_README_reStructuredText_valid(self):
        errors = get_readme_errors()
        self.assertFalse(errors, msg=errors)


class SessionTest(BaseTestCase):

    @property
    def env(self):
        return TestEnvironment(config_dir=self.config_dir)

    def setUp(self):
        # Start a full-blown session with a custom request header,
        # authorization, and response cookies.
        self.config_dir = mk_config_dir()
        r = http(
            '--follow',
            '--session=test',
            '--auth=username:password',
            'GET',
            httpbin('/cookies/set?hello=world'),
            'Hello:World',
            env=self.env
        )
        self.assertIn(OK, r)

    def tearDown(self):
        shutil.rmtree(self.config_dir)

    def test_session_create(self):
        # Verify that the session has been created.
        r = http(
            '--session=test',
            'GET',
            httpbin('/get'),
            env=self.env
        )
        self.assertIn(OK, r)

        self.assertEqual(r.json['headers']['Hello'], 'World')
        self.assertEqual(r.json['headers']['Cookie'], 'hello=world')
        self.assertIn('Basic ', r.json['headers']['Authorization'])

    def test_session_update(self):
        # Get a response to a request from the original session.
        r1 = http(
            '--session=test',
            'GET',
            httpbin('/get'),
            env=self.env
        )
        self.assertIn(OK, r1)

        # Make a request modifying the session data.
        r2 = http(
            '--follow',
            '--session=test',
            '--auth=username:password2',
            'GET',
            httpbin('/cookies/set?hello=world2'),
            'Hello:World2',
            env=self.env
        )
        self.assertIn(OK, r2)

        # Get a response to a request from the updated session.
        r3 = http(
            '--session=test',
            'GET',
            httpbin('/get'),
            env=self.env
        )
        self.assertIn(OK, r3)

        self.assertEqual(r3.json['headers']['Hello'], 'World2')
        self.assertEqual(r3.json['headers']['Cookie'], 'hello=world2')
        self.assertNotEqual(r1.json['headers']['Authorization'],
                            r3.json['headers']['Authorization'])

    def test_session_read_only(self):
        # Get a response from the original session.
        r1 = http(
            '--session=test',
            'GET',
            httpbin('/get'),
            env=self.env
        )
        self.assertIn(OK, r1)

        # Make a request modifying the session data but
        # with --session-read-only.
        r2 = http(
            '--follow',
            '--session-read-only=test',
            '--auth=username:password2',
            'GET',
            httpbin('/cookies/set?hello=world2'),
            'Hello:World2',
            env=self.env
        )
        self.assertIn(OK, r2)

        # Get a response from the updated session.
        r3 = http(
            '--session=test',
            'GET',
            httpbin('/get'),
            env=self.env
        )
        self.assertIn(OK, r3)

        # Origin can differ on Travis.
        del r1.json['origin'], r3.json['origin']

        # Should be the same as before r2.
        self.assertDictEqual(r1.json, r3.json)


class DownloadUtilsTest(BaseTestCase):

    def test_Content_Range_parsing(self):

        parse = parse_content_range

        self.assertEqual(parse('bytes 100-199/200', 100), 200)
        self.assertEqual(parse('bytes 100-199/*', 100), 200)

        # missing
        self.assertRaises(ContentRangeError, parse, None, 100)

        # syntax error
        self.assertRaises(ContentRangeError, parse, 'beers 100-199/*', 100)

        # unexpected range
        self.assertRaises(ContentRangeError, parse, 'bytes 100-199/*', 99)

        # invalid instance-length
        self.assertRaises(ContentRangeError, parse, 'bytes 100-199/199', 100)

        # invalid byte-range-resp-spec
        self.assertRaises(ContentRangeError, parse, 'bytes 100-99/199', 100)

        # invalid byte-range-resp-spec
        self.assertRaises(ContentRangeError, parse, 'bytes 100-100/*', 100)

    def test_Content_Disposition_parsing(self):
        parse = filename_from_content_disposition
        self.assertEqual(
            parse('attachment; filename=hello-WORLD_123.txt'),
            'hello-WORLD_123.txt'
        )
        self.assertEqual(
            parse('attachment; filename=".hello-WORLD_123.txt"'),
            'hello-WORLD_123.txt'
        )
        self.assertIsNone(parse('attachment; filename='))
        self.assertIsNone(parse('attachment; filename=/etc/hosts'))
        self.assertIsNone(parse('attachment; filename=hello@world'))

    def test_filename_from_url(self):
        self.assertEqual(filename_from_url(
            url='http://example.org/foo',
            content_type='text/plain'
        ), 'foo.txt')
        self.assertEqual(filename_from_url(
            url='http://example.org/foo',
            content_type='text/html; charset=utf8'
        ), 'foo.html')
        self.assertEqual(filename_from_url(
            url='http://example.org/foo',
            content_type=None
        ), 'foo')
        self.assertEqual(filename_from_url(
            url='http://example.org/foo',
            content_type='x-foo/bar'
        ), 'foo')

    def test_unique_filename(self):

        def make_exists(unique_on_attempt=0):
            # noinspection PyUnresolvedReferences,PyUnusedLocal
            def exists(filename):
                if exists.attempt == unique_on_attempt:
                    return False
                exists.attempt += 1
                return True
            exists.attempt = 0
            return exists

        self.assertEqual(
            get_unique_filename('foo.bar', exists=make_exists()),
            'foo.bar'
        )
        self.assertEqual(
            get_unique_filename('foo.bar', exists=make_exists(1)),
            'foo.bar-1'
        )
        self.assertEqual(
            get_unique_filename('foo.bar', exists=make_exists(10)),
            'foo.bar-10'
        )


class Response(object):

    # noinspection PyDefaultArgument
    def __init__(self, url, headers={}, status_code=200):
        self.url = url
        self.headers = CaseInsensitiveDict(headers)
        self.status_code = status_code


# noinspection PyTypeChecker
class DownloadTest(BaseTestCase):
    # TODO: Download tests.

    def test_actual_download(self):
        url = httpbin('/robots.txt')
        body = urlopen(url).read().decode()
        r = http(
            '--download',
            url,
            env=TestEnvironment(
                stdin_isatty=True,
                stdout_isatty=False
            )
        )
        self.assertIn('Downloading', r.stderr)
        self.assertIn('[K', r.stderr)
        self.assertIn('Done', r.stderr)
        self.assertEqual(body, r)

    def test_download_no_Content_Length(self):
        download = Download(output_file=open(os.devnull, 'w'))
        download.start(Response(url=httpbin('/')))
        download._chunk_downloaded(b'12345')
        download.finish()
        self.assertFalse(download.interrupted)

    def test_download_interrupted(self):
        download = Download(
            output_file=open(os.devnull, 'w')
        )
        download.start(Response(
            url=httpbin('/'),
            headers={'Content-Length': 5}
        ))
        download._chunk_downloaded(b'1234')
        download.finish()
        self.assertTrue(download.interrupted)


if __name__ == '__main__':
    unittest.main()
