"""High-level tests."""
import pytest

from httpie.status import ExitStatus
from .fixtures import FILE_PATH_ARG
from .utils import http, HTTP_OK


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


@pytest.mark.xfail(True, reason="https://github.com/httpie/httpie/issues/1082")
def test_follow_output_options_used_for_redirects(httpbin):
    r = http('--follow', '--print=H', httpbin.url + '/redirect/2')
    assert r.count('GET /') == 1
    assert HTTP_OK not in r


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


def test_http_307_allow_redirect_post(httpbin):
    r = http('--follow', 'POST', httpbin.url + '/redirect-to',
             f'url=={httpbin.url}/post', 'status_code==307',
             '@' + FILE_PATH_ARG)
    assert HTTP_OK in r


def test_http_307_allow_redirect_post_verbose(httpbin):
    r = http('--follow', '--verbose', 'POST', httpbin.url + '/redirect-to',
             f'url=={httpbin.url}/post', 'status_code==307',
             '@' + FILE_PATH_ARG)
    assert r.count('POST /redirect-to') == 1
    assert r.count('POST /post') == 1
    assert HTTP_OK in r
