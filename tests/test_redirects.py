"""High-level tests."""
import pytest

from httpie.compat import is_windows
from httpie.status import ExitStatus
from .fixtures import FILE_PATH_ARG, FILE_CONTENT
from .utils import http, HTTP_OK
from .utils.matching import assert_output_matches, Expect, ExpectSequence


# <https://developer.mozilla.org/en-US/docs/Web/HTTP/Redirections>
REDIRECTS_WITH_METHOD_BODY_PRESERVED = [307, 308]


def test_follow_all_redirects_shown(httpbin):
    r = http('--follow', '--all', httpbin + '/redirect/2')
    assert r.count('HTTP/1.1') == 3
    assert r.count('HTTP/1.1 302 FOUND', 2)
    assert HTTP_OK in r


@pytest.mark.parametrize('follow_flag', ['--follow', '-F'])
def test_follow_without_all_redirects_hidden(httpbin, follow_flag):
    r = http(follow_flag, httpbin + '/redirect/2')
    assert r.count('HTTP/1.1') == 1
    assert HTTP_OK in r


@pytest.mark.xfail(True, reason="https://github.com/httpie/cli/issues/1082")
def test_follow_output_options_used_for_redirects(httpbin):
    r = http('--follow', '--print=H', httpbin + '/redirect/2')
    assert r.count('GET /') == 1
    assert HTTP_OK not in r


def test_follow_all_output_options_used_for_redirects(httpbin):
    r = http('--check-status',
             '--follow',
             '--all',
             '--print=H',
             httpbin + '/redirect/2')
    assert r.count('GET /') == 3
    assert HTTP_OK not in r


#
# def test_follow_redirect_output_options(httpbin):
#     r = http('--check-status',
#              '--follow',
#              '--all',
#              '--print=h',
#              '--history-print=H',
#              httpbin + '/redirect/2')
#     assert r.count('GET /') == 2
#     assert 'HTTP/1.1 302 FOUND' not in r
#     assert HTTP_OK in r
#


def test_max_redirects(httpbin):
    r = http(
        '--max-redirects=1',
        '--follow',
        httpbin + '/redirect/3',
        tolerate_error_exit_status=True,
    )
    assert r.exit_status == ExitStatus.ERROR_TOO_MANY_REDIRECTS


@pytest.mark.skipif(is_windows, reason='occasionally fails w/ ConnectionError for no apparent reason')
@pytest.mark.parametrize('status_code', REDIRECTS_WITH_METHOD_BODY_PRESERVED)
def test_follow_redirect_with_repost(httpbin, status_code):
    r = http(
        '--follow',
        httpbin + '/redirect-to',
        'A:A',
        'A:B',
        'B:B',
        f'url=={httpbin}/post',
        f'status_code=={status_code}',
        '@' + FILE_PATH_ARG,
    )
    assert HTTP_OK in r
    assert FILE_CONTENT in r
    assert r.json['headers']['A'] == 'A,B'
    assert r.json['headers']['B'] == 'B'


@pytest.mark.skipif(is_windows, reason='occasionally fails w/ ConnectionError for no apparent reason')
@pytest.mark.parametrize('status_code', REDIRECTS_WITH_METHOD_BODY_PRESERVED)
def test_verbose_follow_redirect_with_repost(httpbin, status_code):
    r = http(
        '--follow',
        '--verbose',
        httpbin + '/redirect-to',
        'A:A',
        'A:B',
        'B:B',
        f'url=={httpbin}/post',
        f'status_code=={status_code}',
        '@' + FILE_PATH_ARG,
    )
    assert f'HTTP/1.1 {status_code}' in r
    assert 'A: A' in r
    assert 'A: B' in r
    assert 'B: B' in r
    assert r.count('POST /redirect-to') == 1
    assert r.count('POST /post') == 1
    assert r.count(FILE_CONTENT) == 3  # two requests + final response contain it
    assert HTTP_OK in r
    assert_output_matches(r, [
        *ExpectSequence.TERMINAL_REQUEST,
        Expect.RESPONSE_HEADERS,
        Expect.SEPARATOR,
        *ExpectSequence.TERMINAL_EXCHANGE,
    ])
