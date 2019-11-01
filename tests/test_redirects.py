"""High-level tests."""
import pytest

from httpie.status import ExitStatus
from utils import http, HTTP_OK


def test_follow_all_redirects_shown(httpbin):
    r = http('--follow', '--all', httpbin.url + '/redirect/2')
    assert r.count('HTTP/1.1') == 3
    assert r.count('HTTP/1.1 302 FOUND', 2)
    assert HTTP_OK in r


@pytest.mark.parametrize('follow_flag', ['--follow', '-F'])
def test_follow_without_all_redirects_hidden(httpbin, follow_flag):
    r = http(follow_flag, httpbin.url + '/redirect/2')
    assert r.count('HTTP/1.1') == 1
    assert HTTP_OK in r


def test_follow_all_output_options_used_for_redirects(httpbin):
    r = http('--check-status',
             '--follow',
             '--all',
             '--print=H',
             httpbin.url + '/redirect/2')
    assert r.count('GET /') == 3
    assert HTTP_OK not in r

#
# def test_follow_redirect_output_options(httpbin):
#     r = http('--check-status',
#              '--follow',
#              '--all',
#              '--print=h',
#              '--history-print=H',
#              httpbin.url + '/redirect/2')
#     assert r.count('GET /') == 2
#     assert 'HTTP/1.1 302 FOUND' not in r
#     assert HTTP_OK in r
#


def test_max_redirects(httpbin):
    r = http(
        '--max-redirects=1',
        '--follow',
        httpbin.url + '/redirect/3',
        tolerate_error_exit_status=True,
    )
    assert r.exit_status == ExitStatus.ERROR_TOO_MANY_REDIRECTS
