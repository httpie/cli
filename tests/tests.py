# coding:utf-8
import os
import sys
import unittest
import argparse
try:
    from requests.compat import is_py26
except ImportError:
    is_py26 = (sys.version_info[0] == 2 and sys.version_info[1] == 6)
import tempfile
try:
    from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
except:
    from http.server import BaseHTTPRequestHandler, HTTPServer
import socket
import threading
import time

TESTS_ROOT = os.path.dirname(__file__)
sys.path.insert(0, os.path.realpath(os.path.join(TESTS_ROOT, '..')))
from httpie import __main__
from httpie import cliparse


TEST_FILE = os.path.join(TESTS_ROOT, 'file.txt')
TERMINAL_COLOR_PRESENCE_CHECK = '\x1b['


def http(*args, **kwargs):
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
            self.key_value_type('bar\\@baz@%s' % TEST_FILE)
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
            self.key_value_type('test-file@%s' % TEST_FILE),
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

    def test_verbose_form(self):
        # https://github.com/jkbr/httpie/issues/53
        r = http('--verbose', '--form', 'POST', 'http://httpbin.org/post', 'foo=bar', 'baz=bar')
        self.assertIn('foo=bar&baz=bar', r)

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



class TestHTTPieSuggestion(BaseTest):
    def test_get(self):
        http('http://httpbin.org/get')

    def test_post(self):
        r = http('http://httpbin.org/post', 'hello=world')
        self.assertIn('"hello": "world"', r)

    def test_verbose(self):
        r = http('--verbose', 'http://httpbin.org/get', 'test-header:__test__')
        self.assertEqual(r.count('__test__'), 2)

    def test_verbose_form(self):
        r = http('--verbose', '--form', 'http://httpbin.org/post', 'foo=bar', 'baz=bar')
        self.assertIn('foo=bar&baz=bar', r)

    def test_json(self):
        response = http('http://httpbin.org/post', 'foo=bar')
        self.assertIn('"foo": "bar"', response)
        response2 = http('-j', 'GET', 'http://httpbin.org/headers')
        self.assertIn('"Accept": "application/json"', response2)
        response3 = http('-j', 'GET', 'http://httpbin.org/headers', 'Accept:application/xml')
        self.assertIn('"Accept": "application/xml"', response3)

    def test_form(self):
        response = http('--form', 'http://httpbin.org/post', 'foo=bar')
        self.assertIn('"foo": "bar"', response)

    def test_headers(self):
        response = http('http://httpbin.org/headers', 'Foo:bar')
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
        self.assertRaises(cliparse.ParseError, http,
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


class MockHTTPServer:
    class MockHTTPRequestHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200, 'GOOD')

    def __init__(self, ipv):
        if ipv == 4:
            self.host = '127.0.0.1'
            self.address_family = socket.AF_INET
        elif ipv == 6:
            self.host = '::1'
            self.address_family = socket.AF_INET6
        else:
            raise ValueError('Invalid ipv (%s), expected 4 or 6' % ipv)
        self.port = self.get_free_port()

        class _HTTPServer(HTTPServer):
            address_family = self.address_family

        self.mock_server = _HTTPServer((self.host, self.port), self.MockHTTPRequestHandler)
        self.thread = threading.Thread(target=self._start)

    def _start(self):
        self.mock_server.serve_forever()

    def get_free_port(self):
        s = socket.socket(self.address_family, type=socket.SOCK_STREAM)
        s.bind(('localhost', 0))
        r = s.getsockname()
        s.close()
        return r[1]

    def __enter__(self):
        self.thread.setDaemon(True)
        self.thread.start()
        time.sleep(1.0)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.thread:
            self.thread.join(1.0)


class TestResolve(BaseTest):
    def test_resolve_ipv4(self):
        with MockHTTPServer(4) as mock_http_server:
            r = http('http://httpbin.org:%s/' % mock_http_server.port,
                     '--resolve', 'httpbin.org:%s:%s' % (mock_http_server.port, mock_http_server.host))
            self.assertIn('200 GOOD', r)

    def test_resolve_ipv6(self):
        with MockHTTPServer(6) as mock_http_server:
            r = http('http://httpbin.org:%s/' % mock_http_server.port,
                     '--resolve', 'httpbin.org:%s:%s' % (mock_http_server.port, mock_http_server.host))
            self.assertIn('200 GOOD', r)

    def test_resolve_ipv6_and_ipv6(self):
        with MockHTTPServer(6) as mock_http_server:
            r = http('http://httpbin.org:%s/' % mock_http_server.port,
                     '--resolve', 'httpbin.org:%s:[::2],%s' % (mock_http_server.port, mock_http_server.host))
            self.assertIn('200 GOOD', r)

    def test_resolve_ipv6_and_ipv4(self):
        with MockHTTPServer(4) as mock_http_server:
            r = http('http://httpbin.org:%s/' % mock_http_server.port,
                     '--resolve', 'httpbin.org:%s:[::2],%s' % (mock_http_server.port, mock_http_server.host))
            self.assertIn('200 GOOD', r)



if __name__ == '__main__':
    unittest.main()
