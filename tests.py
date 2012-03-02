import unittest
from StringIO import StringIO
from httpie import __main__


def http(*args, **kwargs):
    stdout = StringIO()
    __main__.main(args=args, stdout=stdout, stdin_isatty=True,
                  stdout_isatty=False)
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


if __name__ == '__main__':
    unittest.main()
