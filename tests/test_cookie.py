from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

from .utils import http


class TestIntegration:

    def setup_mock_server(self, handler):
        """Configure mock server."""
        # Passing 0 as the port will cause a random free port to be chosen.
        self.mock_server = HTTPServer(('localhost', 0), handler)
        _, self.mock_server_port = self.mock_server.server_address

        # Start running mock server in a separate thread.
        # Daemon threads automatically shut down when the main process exits.
        self.mock_server_thread = Thread(target=self.mock_server.serve_forever)
        self.mock_server_thread.setDaemon(True)
        self.mock_server_thread.start()

    def test_cookie_parser(self):
        """Not directly testing HTTPie but `requests` to ensure their cookies handling
        is still as expected by `get_expired_cookies()`.
        """

        class MockServerRequestHandler(BaseHTTPRequestHandler):
            """"HTTP request handler."""

            def do_GET(self):
                """Handle GET requests."""
                # Craft multiple cookies
                cookie = SimpleCookie()
                cookie['hello'] = 'world'
                cookie['hello']['path'] = self.path
                cookie['oatmeal_raisin'] = 'is the best'
                cookie['oatmeal_raisin']['path'] = self.path

                # Send HTTP headers
                self.send_response(200)
                self.send_header('Set-Cookie', cookie.output())
                self.end_headers()

        self.setup_mock_server(MockServerRequestHandler)
        response = http(f'http://localhost:{self.mock_server_port}/')
        assert 'Set-Cookie: hello=world; Path=/' in response
        assert 'Set-Cookie: oatmeal_raisin="is the best"; Path=/' in response
