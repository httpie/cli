# coding:utf-8
import os
import sys
import unittest
import argparse
from requests.compat import StringIO, is_py26, str


TESTS_ROOT = os.path.dirname(__file__)
sys.path.insert(0, os.path.realpath(os.path.join(TESTS_ROOT, '..')))
from httpie import __main__
from httpie import cli


TEST_FILE = os.path.join(TESTS_ROOT, 'file.txt')
TERMINAL_COLOR_PRESENCE_CHECK = '\x1b['


def http(*args, **kwargs):
    http_kwargs = {
        'stdin_isatty': True,
        'stdout_isatty': False
    }
    http_kwargs.update(kwargs)
    stdout = http_kwargs.setdefault('stdout', StringIO())
    __main__.main(args=args, **http_kwargs)
    return stdout.getvalue()


class BaseTest(unittest.TestCase):

    if is_py26:
        def assertIn(self, member, container, msg=None):
            self.assert_(member in container, msg)

        def assertNotIn(self, member, container, msg=None):
            self.assert_(member not in container, msg)

        def assertDictEqual(self, d1, d2, msg=None):
            self.assertEqual(set(d1.keys()), set(d2.keys()), msg)
            self.assertEqual(sorted(d1.values()), sorted(d2.values()), msg)


class TestItemParsing(BaseTest):

    def setUp(self):
        self.kv = cli.KeyValueType(
            cli.SEP_HEADERS,
            cli.SEP_DATA,
            cli.SEP_DATA_RAW_JSON,
            cli.SEP_FILES,
        )

    def test_invalid_items(self):
        items = ['no-separator']
        for item in items:
            self.assertRaises(argparse.ArgumentTypeError,
                              lambda: self.kv(item))

    def test_escape(self):
        headers, data, files = cli.parse_items([
            # headers
            self.kv('foo\\:bar:baz'),
            self.kv('jack\\@jill:hill'),
            # data
            self.kv('baz\\=bar=foo'),
            # files
            self.kv('bar\\@baz@%s' % TEST_FILE)
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
        headers, data, files = cli.parse_items([
            self.kv('bob\\:==foo'),
        ])
        self.assertDictEqual(data, {
            'bob:=': 'foo',
        })
    
    def test_valid_items(self):
        headers, data, files = cli.parse_items([
            self.kv('string=value'),
            self.kv('header:value'),
            self.kv('list:=["a", 1, {}, false]'),
            self.kv('obj:={"a": "b"}'),
            self.kv('eh:'),
            self.kv('ed='),
            self.kv('bool:=true'),
            self.kv('test-file@%s' % TEST_FILE),
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


class TestHTTPie(BaseTest):

    def test_get(self):
        http('GET', 'http://httpbin.org/get')

    def test_verbose(self):
        r = http('--verbose', 'GET', 'http://httpbin.org/get', 'test-header:__test__')
        self.assertEqual(r.count('__test__'), 2)

    def test_json(self):
        response = http('POST', 'http://httpbin.org/post', 'foo=bar')
        self.assertIn('"foo": "bar"', response)
        response2 = http('-j', 'GET', 'http://httpbin.org/headers')
        self.assertIn('"Accept": "application/json"', response2)
        response3 = http('-j', 'GET', 'http://httpbin.org/headers', 'Accept:application/xml')
        self.assertIn('"Accept": "application/xml"', response3)

    def test_form(self):
        response = http('--form', 'POST', 'http://httpbin.org/post', 'foo=bar')
        self.assertIn('"foo": "bar"', response)

    def test_headers(self):
        response = http('GET', 'http://httpbin.org/headers', 'Foo:bar')
        self.assertIn('"User-Agent": "HTTPie', response)
        self.assertIn('"Foo": "bar"', response)


class TestPrettyFlag(BaseTest):
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


class TestFileUpload(BaseTest):

    def test_non_existent_file_raises_parse_error(self):
        self.assertRaises(cli.ParseError, http,
            '--form', '--traceback',
            'POST', 'http://httpbin.org/post',
            'foo@/__does_not_exist__')

    def test_upload_ok(self):
        r = http('--form', 'POST', 'http://httpbin.org/post',
             'test-file@%s' % TEST_FILE)
        self.assertIn('"test-file": "__test_file_content__', r)


class TestAuth(BaseTest):

    def test_basic_auth(self):
        r = http('--auth', 'user:password',
                 'GET', 'httpbin.org/basic-auth/user/password')
        self.assertIn('"authenticated": true', r)
        self.assertIn('"user": "user"', r)

    def test_digest_auth(self):
        r = http('--auth-type=digest', '--auth', 'user:password',
                 'GET', 'httpbin.org/digest-auth/auth/user/password')
        self.assertIn('"authenticated": true', r)
        self.assertIn('"user": "user"', r)


if __name__ == '__main__':
    unittest.main()
