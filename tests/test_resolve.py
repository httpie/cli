import pytest
import socket
import threading
import time

from httpie.resolve import CustomResolver

try:
    from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
except:
    from http.server import BaseHTTPRequestHandler, HTTPServer
from utils import http


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


@pytest.mark.parametrize('arg,expected', [
    (
        'a:80:127.0.0.1',
        ('a', 80, ['127.0.0.1']),
    ),
    (
        'a:127.0.0.1',
        ('a', None, ['127.0.0.1']),
    ),
    (
        'a:::1',
        ('a', None, ['::1']),
    ),
])
def test_resolve_arg_parse(arg, expected):
    assert CustomResolver.parse_resolve_entry(arg) == expected


class TestResolve:
    def test_resolve_ipv4(self):
        with MockHTTPServer(4) as mock_http_server:
            r = http('http://httpbin.org:%s/' % mock_http_server.port,
                     '--resolve', 'httpbin.org:%s:%s' % (mock_http_server.port, mock_http_server.host))
            assert '200 GOOD' in r

    def test_resolve_ipv6(self):
        with MockHTTPServer(6) as mock_http_server:
            r = http('http://httpbin.org:%s/' % mock_http_server.port,
                     '--resolve', 'httpbin.org:%s:%s' % (mock_http_server.port, mock_http_server.host))
            assert '200 GOOD' in r

    def test_resolve_ipv6_and_ipv6(self):
        with MockHTTPServer(6) as mock_http_server:
            r = http('http://httpbin.org:%s/' % mock_http_server.port,
                     '--resolve', 'httpbin.org:%s:[::2],%s' % (mock_http_server.port, mock_http_server.host))
            assert '200 GOOD' in r

    def test_resolve_ipv6_and_ipv4(self):
        with MockHTTPServer(4) as mock_http_server:
            r = http('http://httpbin.org:%s/' % mock_http_server.port,
                     '--resolve', 'httpbin.org:%s:[::2],%s' % (mock_http_server.port, mock_http_server.host))
            assert '200 GOOD' in r
