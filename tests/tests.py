import unittest
import argparse
import os
import sys
import tempfile
from requests.compat import is_py26


#################################################################
# Utils/setup
#################################################################

# HACK: Prepend ../ to PYTHONPATH so that we can import httpie form there.
TESTS_ROOT = os.path.dirname(__file__)
sys.path.insert(0, os.path.realpath(os.path.join(TESTS_ROOT, '..')))

from httpie import __main__, cliparse


TEST_FILE_PATH = os.path.join(TESTS_ROOT, 'file.txt')
TEST_FILE2_PATH = os.path.join(TESTS_ROOT, 'file2.txt')
TEST_FILE_CONTENT = open(TEST_FILE_PATH).read().strip()
TERMINAL_COLOR_PRESENCE_CHECK = '\x1b['


def http(*args, **kwargs):
    """
    Invoke `httpie.__main__.main` with `args` and `kwargs`,
    and return a unicode response.

    """
    http_kwargs = {
        'stdin_isatty': True,
        'stdout_isatty': False
    }
    http_kwargs.update(kwargs)
    stdout = http_kwargs.setdefault('stdout', tempfile.TemporaryFile())
    __main__.main(args=args, **http_kwargs)
    stdout.seek(0)
    response = stdout.read().decode('utf8')
    stdout.close()
    return response


class BaseTestCase(unittest.TestCase):

    if is_py26:
        def assertIn(self, member, container, msg=None):
            self.assert_(member in container, msg)

        def assertNotIn(self, member, container, msg=None):
            self.assert_(member not in container, msg)

        def assertDictEqual(self, d1, d2, msg=None):
            self.assertEqual(set(d1.keys()), set(d2.keys()), msg)
            self.assertEqual(sorted(d1.values()), sorted(d2.values()), msg)


#################################################################
# High-level tests using httpbin.org.
#################################################################

class HTTPieTest(BaseTestCase):

    def test_GET(self):
        r = http('GET', 'http://httpbin.org/get')
        self.assertIn('HTTP/1.1 200', r)

    def test_DELETE(self):
        r = http('DELETE', 'http://httpbin.org/delete')
        self.assertIn('HTTP/1.1 200', r)

    def test_PUT(self):
        r = http('PUT', 'http://httpbin.org/put', 'foo=bar')
        self.assertIn('HTTP/1.1 200', r)
        self.assertIn('"foo": "bar"', r)

    def test_POST_JSON_data(self):
        r = http('POST', 'http://httpbin.org/post', 'foo=bar')
        self.assertIn('HTTP/1.1 200', r)
        self.assertIn('"foo": "bar"', r)

    def test_POST_form(self):
        r = http('--form', 'POST', 'http://httpbin.org/post', 'foo=bar')
        self.assertIn('HTTP/1.1 200', r)
        self.assertIn('"foo": "bar"', r)

    def test_POST_stdin(self):
        r = http('--form', 'POST', 'http://httpbin.org/post',
                 stdin=open(TEST_FILE_PATH), stdin_isatty=False)
        self.assertIn('HTTP/1.1 200', r)
        self.assertIn(TEST_FILE_CONTENT, r)

    def test_headers(self):
        r = http('GET', 'http://httpbin.org/headers', 'Foo:bar')
        self.assertIn('HTTP/1.1 200', r)
        self.assertIn('"User-Agent": "HTTPie', r)
        self.assertIn('"Foo": "bar"', r)


class AutoContentTypeAndAcceptHeadersTest(BaseTestCase):
    """
    Test that Accept and Content-Type correctly defaults to JSON,
    but can still be overridden. The same with Content-Type when --form
    -f is used.

    """
    def test_GET_no_data_no_auto_headers(self):
        # https://github.com/jkbr/httpie/issues/62
        r = http('GET', 'http://httpbin.org/headers')
        self.assertIn('HTTP/1.1 200', r)
        self.assertIn('"Accept": "*/*"', r)
        # Although an empty header is present in the response from httpbin,
        # it's not included in the request.
        self.assertIn('"Content-Type": ""', r)

    def test_POST_no_data_no_auto_headers(self):
        # JSON headers shouldn't be automatically set for POST with no data.
        r = http('POST', 'http://httpbin.org/post')
        self.assertIn('HTTP/1.1 200', r)
        self.assertIn('"Accept": "*/*"', r)
        # Although an empty header is present in the response from httpbin,
        # it's not included in the request.
        self.assertIn(' "Content-Type": ""', r)

    def test_POST_with_data_auto_JSON_headers(self):
        r = http('POST', 'http://httpbin.org/post', 'a=b')
        self.assertIn('HTTP/1.1 200', r)
        self.assertIn('"Accept": "application/json"', r)
        self.assertIn('"Content-Type": "application/json; charset=utf-8', r)

    def test_GET_with_data_auto_JSON_headers(self):
        # JSON headers should automatically be set also for GET with data.
        r = http('POST', 'http://httpbin.org/post', 'a=b')
        self.assertIn('HTTP/1.1 200', r)
        self.assertIn('"Accept": "application/json"', r)
        self.assertIn('"Content-Type": "application/json; charset=utf-8', r)

    def test_POST_explicit_JSON_auto_JSON_headers(self):
        r = http('-j', 'POST', 'http://httpbin.org/post')
        self.assertIn('HTTP/1.1 200', r)
        self.assertIn('"Accept": "application/json"', r)
        self.assertIn('"Content-Type": "application/json; charset=utf-8', r)

    def test_GET_explicit_JSON_explicit_headers(self):
        r = http('-j', 'GET', 'http://httpbin.org/headers',
                'Accept:application/xml',
                'Content-Type:application/xml')
        self.assertIn('HTTP/1.1 200', r)
        self.assertIn('"Accept": "application/xml"', r)
        self.assertIn('"Content-Type": "application/xml"', r)

    def test_POST_form_auto_Content_Type(self):
        r = http('-f', 'POST', 'http://httpbin.org/post')
        self.assertIn('HTTP/1.1 200', r)
        self.assertIn('"Content-Type": "application/x-www-form-urlencoded; charset=utf-8"', r)

    def test_POST_form_Content_Type_override(self):
        r = http('-f', 'POST', 'http://httpbin.org/post', 'Content-Type:application/xml')
        self.assertIn('HTTP/1.1 200', r)
        self.assertIn('"Content-Type": "application/xml"', r)


class ImplicitHTTPMethodTest(BaseTestCase):

    def test_implicit_GET(self):
        r = http('http://httpbin.org/get')
        self.assertIn('HTTP/1.1 200', r)

    def test_implicit_GET_with_headers(self):
        r = http('http://httpbin.org/headers', 'Foo:bar')
        self.assertIn('HTTP/1.1 200', r)
        self.assertIn('"Foo": "bar"', r)

    def test_implicit_POST_json(self):
        r = http('http://httpbin.org/post', 'hello=world')
        self.assertIn('HTTP/1.1 200', r)
        self.assertIn('"hello": "world"', r)

    def test_implicit_POST_form(self):
        r = http('--form', 'http://httpbin.org/post', 'foo=bar')
        self.assertIn('HTTP/1.1 200', r)
        self.assertIn('"foo": "bar"', r)

    def test_implicit_POST_stdin(self):
        r = http('--form', 'http://httpbin.org/post',
                 stdin=open(TEST_FILE_PATH), stdin_isatty=False)
        self.assertIn('HTTP/1.1 200', r)


class PrettyFlagTest(BaseTestCase):
    """Test the --pretty / --ugly flag handling."""

    def test_pretty_enabled_by_default(self):
        r = http('GET', 'http://httpbin.org/get', stdout_isatty=True)
        self.assertIn(TERMINAL_COLOR_PRESENCE_CHECK, r)

    def test_pretty_enabled_by_default_unless_stdin_redirected(self):
        r = http('GET', 'http://httpbin.org/get', stdout_isatty=False)
        self.assertNotIn(TERMINAL_COLOR_PRESENCE_CHECK, r)

    def test_force_pretty(self):
        r = http('--pretty', 'GET', 'http://httpbin.org/get', stdout_isatty=False)
        self.assertIn(TERMINAL_COLOR_PRESENCE_CHECK, r)

    def test_force_ugly(self):
        r = http('--ugly', 'GET', 'http://httpbin.org/get', stdout_isatty=True)
        self.assertNotIn(TERMINAL_COLOR_PRESENCE_CHECK, r)


class VerboseFlagTest(BaseTestCase):

    def test_verbose(self):
        r = http('--verbose', 'GET', 'http://httpbin.org/get', 'test-header:__test__')
        self.assertIn('HTTP/1.1 200', r)
        self.assertEqual(r.count('__test__'), 2)

    def test_verbose_form(self):
        # https://github.com/jkbr/httpie/issues/53
        r = http('--verbose', '--form', 'POST', 'http://httpbin.org/post', 'foo=bar', 'baz=bar')
        self.assertIn('HTTP/1.1 200', r)
        self.assertIn('foo=bar&baz=bar', r)


class MultipartFormDataFileUploadTest(BaseTestCase):

    def test_non_existent_file_raises_parse_error(self):
        self.assertRaises(cliparse.ParseError, http,
            '--form', '--traceback',
            'POST', 'http://httpbin.org/post',
            'foo@/__does_not_exist__')

    def test_upload_ok(self):
        r = http('--form', 'POST', 'http://httpbin.org/post',
             'test-file@%s' % TEST_FILE_PATH, 'foo=bar')
        self.assertIn('HTTP/1.1 200', r)
        self.assertIn('"test-file": "%s' % TEST_FILE_CONTENT, r)
        self.assertIn('"foo": "bar"', r)


class RequestBodyFromFilePathTest(BaseTestCase):
    """
    `http URL @file'

    """
    def test_request_body_from_file_by_path(self):
        r = http('POST', 'http://httpbin.org/post', '@' + TEST_FILE_PATH)
        self.assertIn('HTTP/1.1 200', r)
        self.assertIn(TEST_FILE_CONTENT, r)
        self.assertIn('"Content-Type": "text/plain"', r)

    def test_request_body_from_file_by_path_with_explicit_content_type(self):
        r = http('POST', 'http://httpbin.org/post', '@' + TEST_FILE_PATH, 'Content-Type:x-foo/bar')
        self.assertIn('HTTP/1.1 200', r)
        self.assertIn(TEST_FILE_CONTENT, r)
        self.assertIn('"Content-Type": "x-foo/bar"', r)

    def test_request_body_from_file_by_path_only_one_file_allowed(self):
        self.assertRaises(SystemExit, lambda: http(
            'POST',
                'http://httpbin.org/post',
                '@' + TEST_FILE_PATH,
                '@' + TEST_FILE2_PATH))

    def test_request_body_from_file_by_path_no_data_items_allowed(self):
        self.assertRaises(SystemExit, lambda: http(
            'POST',
                'http://httpbin.org/post',
                '@' + TEST_FILE_PATH,
                'foo=bar'))


class AuthTest(BaseTestCase):

    def test_basic_auth(self):
        r = http('--auth', 'user:password',
                 'GET', 'httpbin.org/basic-auth/user/password')
        self.assertIn('HTTP/1.1 200', r)
        self.assertIn('"authenticated": true', r)
        self.assertIn('"user": "user"', r)

    def test_digest_auth(self):
        r = http('--auth-type=digest', '--auth', 'user:password',
                 'GET', 'httpbin.org/digest-auth/auth/user/password')
        self.assertIn('HTTP/1.1 200', r)
        self.assertIn('"authenticated": true', r)
        self.assertIn('"user": "user"', r)

    def test_password_prompt(self):
        cliparse.AuthCredentials._getpass = lambda self, prompt: 'password'

        r = http('--auth', 'user',
                 'GET', 'httpbin.org/basic-auth/user/password')

        self.assertIn('HTTP/1.1 200', r)
        self.assertIn('"authenticated": true', r)
        self.assertIn('"user": "user"', r)


#################################################################
# CLI argument parsing related tests.
#################################################################

class ItemParsingTest(BaseTestCase):

    def setUp(self):
        self.key_value_type = cliparse.KeyValueType(
            cliparse.SEP_HEADERS,
            cliparse.SEP_DATA,
            cliparse.SEP_DATA_RAW_JSON,
            cliparse.SEP_FILES,
        )

    def test_invalid_items(self):
        items = ['no-separator']
        for item in items:
            self.assertRaises(argparse.ArgumentTypeError,
                              lambda: self.key_value_type(item))

    def test_escape(self):
        headers, data, files = cliparse.parse_items([
            # headers
            self.key_value_type('foo\\:bar:baz'),
            self.key_value_type('jack\\@jill:hill'),
            # data
            self.key_value_type('baz\\=bar=foo'),
            # files
            self.key_value_type('bar\\@baz@%s' % TEST_FILE_PATH)
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
        headers, data, files = cliparse.parse_items([
            self.key_value_type('bob\\:==foo'),
        ])
        self.assertDictEqual(data, {
            'bob:=': 'foo',
        })

    def test_valid_items(self):
        headers, data, files = cliparse.parse_items([
            self.key_value_type('string=value'),
            self.key_value_type('header:value'),
            self.key_value_type('list:=["a", 1, {}, false]'),
            self.key_value_type('obj:={"a": "b"}'),
            self.key_value_type('eh:'),
            self.key_value_type('ed='),
            self.key_value_type('bool:=true'),
            self.key_value_type('test-file@%s' % TEST_FILE_PATH),
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
            "obj": {"a": "b"}
        })
        self.assertIn('test-file', files)


class ArgumentParserTestCase(unittest.TestCase):

    def setUp(self):
        self.parser = cliparse.Parser()

    def test_guess_when_method_set_and_valid(self):
        args = argparse.Namespace()
        args.method = 'GET'
        args.url = 'http://example.com/'
        args.items = []

        self.parser._guess_method(args)

        self.assertEquals(args.method, 'GET')
        self.assertEquals(args.url, 'http://example.com/')
        self.assertEquals(args.items, [])

    def test_guess_when_method_not_set(self):
        args = argparse.Namespace()
        args.method = None
        args.url = 'http://example.com/'
        args.items = []

        self.parser._guess_method(args)

        self.assertEquals(args.method, 'GET')
        self.assertEquals(args.url, 'http://example.com/')
        self.assertEquals(args.items, [])

    def test_guess_when_method_set_but_invalid_and_data_field(self):
        args = argparse.Namespace()
        args.method = 'http://example.com/'
        args.url = 'data=field'
        args.items = []

        self.parser._guess_method(args)

        self.assertEquals(args.method, 'POST')
        self.assertEquals(args.url, 'http://example.com/')
        self.assertEquals(
            args.items,
            [cliparse.KeyValue(key='data', value='field', sep='=', orig='data=field')])

    def test_guess_when_method_set_but_invalid_and_header_field(self):
        args = argparse.Namespace()
        args.method = 'http://example.com/'
        args.url = 'test:header'
        args.items = []

        self.parser._guess_method(args)

        self.assertEquals(args.method, 'GET')
        self.assertEquals(args.url, 'http://example.com/')
        self.assertEquals(
            args.items,
            [cliparse.KeyValue(key='test', value='header', sep=':', orig='test:header')])

    def test_guess_when_method_set_but_invalid_and_item_exists(self):
        args = argparse.Namespace()
        args.method = 'http://example.com/'
        args.url = 'new_item=a'
        args.items = [
            cliparse.KeyValue(key='old_item', value='b', sep='=', orig='old_item=b')
        ]

        self.parser._guess_method(args)

        self.assertEquals(args.items, [
            cliparse.KeyValue(key='new_item', value='a', sep='=', orig='new_item=a'),
            cliparse.KeyValue(key='old_item', value='b', sep='=', orig='old_item=b'),
        ])


if __name__ == '__main__':
    unittest.main()
