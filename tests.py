import sys
import unittest
import argparse
from StringIO import StringIO
from httpie import __main__
from httpie import cli


TERMINAL_COLOR_CHECK = '\x1b['


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

    if sys.version < (2, 7):
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
            cli.SEP_DATA_RAW_JSON
        )

    def test_invalid_items(self):
        items = ['no-separator']
        for item in items:
            self.assertRaises(argparse.ArgumentTypeError,
                              lambda: self.kv(item))

    def test_valid_items(self):
        headers, data = cli.parse_items([
            self.kv('string=value'),
            self.kv('header:value'),
            self.kv('list:=["a", 1, {}, false]'),
            self.kv('obj:={"a": "b"}'),
            self.kv('eh:'),
            self.kv('ed='),
            self.kv('bool:=true'),
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


class TestHTTPie(BaseTest):

    def test_get(self):
        http('GET', 'http://httpbin.org/get')

    def test_json(self):
        response = http('POST', 'http://httpbin.org/post', 'foo=bar')
        self.assertIn('"foo": "bar"', response)

    def test_form(self):
        response = http('POST', '--form', 'http://httpbin.org/post', 'foo=bar')
        self.assertIn('"foo": "bar"', response)

    def test_headers(self):
        response = http('GET', 'http://httpbin.org/headers', 'Foo:bar')
        self.assertIn('"User-Agent": "HTTPie', response)
        self.assertIn('"Foo": "bar"', response)


class TestPrettyFlag(BaseTest):
    """Test the --pretty / --ugly flag handling."""

    def test_pretty_enabled_by_default(self):
        r = http('GET', 'http://httpbin.org/get', stdout_isatty=True)
        self.assertIn(TERMINAL_COLOR_CHECK, r)

    def test_pretty_enabled_by_default_unless_stdin_redirected(self):
        r = http('GET', 'http://httpbin.org/get', stdout_isatty=False)
        self.assertNotIn(TERMINAL_COLOR_CHECK, r)

    def test_force_pretty(self):
        r = http('GET', '--pretty', 'http://httpbin.org/get', stdout_isatty=False)
        self.assertIn(TERMINAL_COLOR_CHECK, r)

    def test_force_ugly(self):
        r = http('GET', '--ugly', 'http://httpbin.org/get', stdout_isatty=True)
        self.assertNotIn(TERMINAL_COLOR_CHECK, r)


if __name__ == '__main__':
    unittest.main()
