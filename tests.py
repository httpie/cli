import unittest
from StringIO import StringIO
from httpie import __main__


TERMINAL_COLOR_END = '\x1b[39m'


def http(*args, **kwargs):
    http_kwargs = {
        'stdin_isatty': True,
        'stdout_isatty': False
    }
    http_kwargs.update(kwargs)
    stdout = http_kwargs.setdefault('stdout', StringIO())
    __main__.main(args=args, **http_kwargs)
    return stdout.getvalue()


# TODO: moar!

class TestHTTPie(unittest.TestCase):

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


class TestPrettyFlag(unittest.TestCase):
    """Test the --pretty / --ugly flag handling."""

    def test_pretty_enabled_by_default(self):
        r = http('GET', 'http://httpbin.org/get', stdout_isatty=True)
        self.assertIn(TERMINAL_COLOR_END, r)

    def test_pretty_enabled_by_default_unless_stdin_redirected(self):
        r = http('GET', 'http://httpbin.org/get', stdout_isatty=False)
        self.assertNotIn(TERMINAL_COLOR_END, r)

    def test_force_pretty(self):
        r = http('GET', '--pretty', 'http://httpbin.org/get', stdout_isatty=False)
        self.assertIn(TERMINAL_COLOR_END, r)

    def test_force_ugly(self):
        r = http('GET', '--ugly', 'http://httpbin.org/get', stdout_isatty=True)
        self.assertNotIn(TERMINAL_COLOR_END, r)


if __name__ == '__main__':
    unittest.main()
