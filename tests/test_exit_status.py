import requests

from httpie import ExitStatus
from tests import (
    BaseTestCase, TestEnvironment,
    http, httpbin, OK, skip, skipIf
)


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

    @skip('timeout broken in requests'
          ' (https://github.com/jkbr/httpie/issues/185)')
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

    @skipIf(requests.__version__ == '0.13.6',
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
