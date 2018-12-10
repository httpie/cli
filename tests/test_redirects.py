"""High-level tests."""
import pytest

from httpie import ExitStatus
from httpie.compat import urlencode
from utils import http, HTTP_OK
from fixtures import FILE_CONTENT, FILE_PATH_ARG

# Some redirection tests are repeated with many combinations of METHOD & CODE
# because HTTPieRequestsSession relies on undocumented behaviour of the requests
# library, hopefully thorough test coverage will catch any problems when updating it
METHODS_TO_TEST = ['DELETE', 'GET', 'HEAD', 'PATCH', 'POST', 'PUT', 'TRACE']
REDIRECT_CODES_TO_TEST = range(300, 310)


def redirect_to(status_code, url):
    return '/redirect-to?' + urlencode([('status_code', status_code), ('url', url)])


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


def test_follow_redirect_output_options(httpbin):
    r = http('--check-status',
             '--follow',
             '--all',
             '--print=h',
             '--history-print=H',
             httpbin.url + '/redirect/2')
    assert r.count('GET /') == 2
    assert 'HTTP/1.1 302 FOUND' not in r
    assert HTTP_OK in r


@pytest.mark.parametrize('code', REDIRECT_CODES_TO_TEST)
@pytest.mark.parametrize('method', METHODS_TO_TEST)
def test_follow_default_redirect_behaviour(httpbin, code, method):
    # The various behaviours here are simply what the requests library does by default,
    # we detail them in our docs so if nothing else this test is at least checking our
    # docs are accurate

    redirected_request_is_sent = code in [301, 302, 303, 307, 308]

    use_get = (code == 301 and method == 'POST') or (code in [302, 303] and method != 'HEAD')

    times_data_is_sent = 2 if code in [307, 308] else 1

    r = http('--follow',
             '--form',
             '--verbose',
             method, httpbin.url + redirect_to(code, '/status/200'),
             'Cookie:Monster=OM NOM NOM NOM',
             'test-file@%s' % FILE_PATH_ARG,
             'foo=bar')

    if redirected_request_is_sent:
        assert ('%s /status/200 HTTP/1.1' % 'GET' if use_get else method) in r
        assert HTTP_OK in r
    else:
        assert '/status/200 HTTP/1.1' not in r

    assert r.count('Cookie: Monster=OM NOM NOM NOM') == 1
    assert r.count(FILE_CONTENT) == times_data_is_sent
    assert r.split().count('bar') == times_data_is_sent


def test_max_redirects(httpbin):
    r = http('--max-redirects=1', '--follow', httpbin.url + '/redirect/3',
             error_exit_ok=True)
    assert r.exit_status == ExitStatus.ERROR_TOO_MANY_REDIRECTS


@pytest.mark.parametrize('code', REDIRECT_CODES_TO_TEST)
@pytest.mark.parametrize('method', METHODS_TO_TEST)
def test_follow_rule(httpbin, code, method):
    r = http('--follow-rule', '%s:%s' % (code, method),
             '--form',
             '--verbose',
             method, httpbin.url + redirect_to(code, '/status/200'),
             'Cookie:Monster=OM NOM NOM NOM',
             'test-file@%s' % FILE_PATH_ARG,
             'foo=bar')
    assert '%s /status/200 HTTP/1.1' % method in r
    assert HTTP_OK in r
    assert r.count('Cookie: Monster=OM NOM NOM NOM') == 1
    assert r.count(FILE_CONTENT) == 2
    assert r.split().count('bar') == 2


def test_follow_rule_multiple(httpbin):
    r = http('--follow-rule', '307:POST',
             '--follow-rule', '301:POST',
             '--form',
             '--verbose',
             'POST', httpbin.url + redirect_to(307, redirect_to(301, '/status/200')),
             'test-file@%s' % FILE_PATH_ARG,
             'foo=bar')
    assert r.count('POST /redirect-to?status_code=307') == 1
    assert r.count('HTTP/1.1 307 TEMPORARY REDIRECT') == 1
    assert r.count('POST /redirect-to?status_code=301') == 1
    assert r.count('HTTP/1.1 301 MOVED PERMANENTLY') == 1
    assert r.count('POST /status/200') == 1
    assert r.count(HTTP_OK) == 1
    assert r.count(FILE_CONTENT) == 3
    assert r.count('bar') == 3


@pytest.mark.parametrize('code', REDIRECT_CODES_TO_TEST)
@pytest.mark.parametrize('method', METHODS_TO_TEST)
def test_follow_rule_samecookies(httpbin, code, method):
    r = http('--follow-rule', '%s:%s:samecookies' % (code, method),
             '--verbose',
             method, httpbin.url + redirect_to(code, '/status/200'),
             'Cookie:Monster=OM NOM NOM NOM')
    assert HTTP_OK in r
    assert r.count('Cookie: Monster=OM NOM NOM NOM') == 2


@pytest.mark.parametrize('code', REDIRECT_CODES_TO_TEST)
@pytest.mark.parametrize('method', METHODS_TO_TEST)
def test_follow_rule_nodata(httpbin, code, method):
    r = http('--follow-rule', '%s:%s:nodata' % (code, method),
             '--form',
             '--verbose',
             method, httpbin.url + redirect_to(code, '/status/200'),
             'test-file@%s' % FILE_PATH_ARG,
             'foo=bar')
    assert HTTP_OK in r
    assert r.count(FILE_CONTENT) == 1
    assert r.split().count('bar') == 1


@pytest.mark.parametrize('code', REDIRECT_CODES_TO_TEST)
@pytest.mark.parametrize('method', METHODS_TO_TEST)
def test_follow_rule_dont_follow(httpbin, code, method):
    r = http('--follow-rule', '999:NOTUSED',
             '--form',
             '--verbose',
             method, httpbin.url + redirect_to(code, '/status/200'),
             'test-file@%s' % FILE_PATH_ARG,
             'foo=bar')
    assert '/status/200 HTTP/1.1' not in r
    assert HTTP_OK not in r
    assert r.count(FILE_CONTENT) == 1
    assert r.split().count('bar') == 1


@pytest.mark.parametrize('code', [301, 302, 303])
def test_post30x(httpbin, code):
    r = http('--post%s' % code,
             '--verbose',
             'POST', httpbin.url + redirect_to(code, '/post'))
    assert HTTP_OK in r
