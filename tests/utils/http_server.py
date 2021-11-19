import threading

from collections import defaultdict
from http import HTTPStatus
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

import pytest


class TestHandler(BaseHTTPRequestHandler):
    handlers = defaultdict(dict)

    @classmethod
    def handler(cls, method, path):
        def inner(func):
            cls.handlers[method][path] = func
            return func
        return inner

    def do_GET(self):
        parse_result = urlparse(self.path)
        func = self.handlers['GET'].get(parse_result.path)
        if func is None:
            return self.send_error(HTTPStatus.NOT_FOUND)

        return func(self)


@TestHandler.handler('GET', '/headers')
def get_headers(handler):
    handler.send_response(200)
    for key, value in handler.headers.items():
        handler.send_header(key, value)
    handler.send_header("Content-Length", 0)
    handler.end_headers()


@pytest.fixture(scope="function")
def http_server():
    """A custom HTTP server implementation for our tests, that is
    built on top of the http.server module. Handy when we need to
    deal with details which httpbin can not capture."""

    server = HTTPServer(('localhost', 0), TestHandler)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    yield "{}:{}".format(*server.socket.getsockname())
    server.shutdown()
    thread.join(timeout=0.5)
