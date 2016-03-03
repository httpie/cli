from httpie import ExitStatus
from utils import TestEnvironment, http, HTTP_OK


def test_ok_response_exits_0(httpbin):
    r = http('GET', httpbin.url + '/status/200')
    assert HTTP_OK in r
    assert r.exit_status == ExitStatus.OK


def test_error_response_exits_0_without_check_status(httpbin):
    r = http('GET', httpbin.url + '/status/500')
    assert '500 INTERNAL SERVER ERRO' in r
    assert r.exit_status == ExitStatus.OK
    assert not r.stderr


def test_timeout_exit_status(httpbin):

    r = http('--timeout=0.01', 'GET', httpbin.url + '/delay/0.02',
             error_exit_ok=True)
    assert r.exit_status == ExitStatus.ERROR_TIMEOUT


def test_3xx_check_status_exits_3_and_stderr_when_stdout_redirected(
        httpbin):
    env = TestEnvironment(stdout_isatty=False)
    r = http('--check-status', '--headers',
             'GET', httpbin.url + '/status/301',
             env=env, error_exit_ok=True)
    assert '301 MOVED PERMANENTLY' in r
    assert r.exit_status == ExitStatus.ERROR_HTTP_3XX
    assert '301 moved permanently' in r.stderr.lower()


def test_3xx_check_status_redirects_allowed_exits_0(httpbin):
    r = http('--check-status', '--follow',
             'GET', httpbin.url + '/status/301',
             error_exit_ok=True)
    # The redirect will be followed so 200 is expected.
    assert HTTP_OK in r
    assert r.exit_status == ExitStatus.OK


def test_4xx_check_status_exits_4(httpbin):
    r = http('--check-status', 'GET', httpbin.url + '/status/401',
             error_exit_ok=True)
    assert '401 UNAUTHORIZED' in r
    assert r.exit_status == ExitStatus.ERROR_HTTP_4XX
    # Also stderr should be empty since stdout isn't redirected.
    assert not r.stderr


def test_5xx_check_status_exits_5(httpbin):
    r = http('--check-status', 'GET', httpbin.url + '/status/500',
             error_exit_ok=True)
    assert '500 INTERNAL SERVER ERROR' in r
    assert r.exit_status == ExitStatus.ERROR_HTTP_5XX
