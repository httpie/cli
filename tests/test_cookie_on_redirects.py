import pytest
from .utils import http


@pytest.mark.parametrize('target_httpbin', [
    'httpbin',
    'remote_httpbin',
])
def test_explicit_user_set_cookie(httpbin, target_httpbin, request):
    """User set cookies ARE NOT persisted within redirects when there is no session, even on the same domain."""
    target_httpbin = request.getfixturevalue(target_httpbin)
    r = http(
        '--follow',
        httpbin + '/redirect-to',
        f'url=={target_httpbin}/cookies',
        'Cookie:a=b'
    )
    assert r.json == {'cookies': {}}


@pytest.mark.parametrize('target_httpbin', [
    'httpbin',
    'remote_httpbin',
])
def test_explicit_user_set_cookie_in_session(tmp_path, httpbin, target_httpbin, request):
    """User set cookies ARE persisted within redirects when there is A session, even on the same domain."""
    target_httpbin = request.getfixturevalue(target_httpbin)
    r = http(
        '--follow',
        '--session',
        str(tmp_path / 'session.json'),
        httpbin + '/redirect-to',
        f'url=={target_httpbin}/cookies',
        'Cookie:a=b'
    )
    assert r.json == {'cookies': {'a': 'b'}}


@pytest.mark.parametrize('target_httpbin', [
    'httpbin',
    'remote_httpbin',
])
def test_saved_user_set_cookie_in_session(tmp_path, httpbin, target_httpbin, request):
    """User set cookies ARE persisted within redirects when there is A session, even on the same domain."""
    target_httpbin = request.getfixturevalue(target_httpbin)
    http(
        '--follow',
        '--session',
        str(tmp_path / 'session.json'),
        httpbin + '/get',
        'Cookie:a=b'
    )
    r = http(
        '--follow',
        '--session',
        str(tmp_path / 'session.json'),
        httpbin + '/redirect-to',
        f'url=={target_httpbin}/cookies',
    )
    assert r.json == {'cookies': {'a': 'b'}}


@pytest.mark.parametrize('target_httpbin', [
    'httpbin',
    'remote_httpbin',
])
@pytest.mark.parametrize('session', [True, False])
def test_explicit_user_set_headers(httpbin, tmp_path, target_httpbin, session, request):
    """
    User set headers ARE persisted within redirects even on different domains domain with or without an active session.

    """
    target_httpbin = request.getfixturevalue(target_httpbin)
    session_args = []
    if session:
        session_args.extend([
            '--session',
            str(tmp_path / 'session.json')
        ])
    r = http(
        '--follow',
        *session_args,
        httpbin + '/redirect-to',
        f'url=={target_httpbin}/get',
        'X-Custom-Header:value'
    )
    assert 'X-Custom-Header' in r.json['headers']


@pytest.mark.parametrize('session', [True, False])
def test_server_set_cookie_on_redirect_same_domain(tmp_path, httpbin, session):
    """Server set cookies ARE persisted on the same domain when they are forwarded."""
    session_args = []
    if session:
        session_args.extend([
            '--session',
            str(tmp_path / 'session.json')
        ])
    r = http(
        '--follow',
        *session_args,
        httpbin + '/cookies/set/a/b',
    )
    assert r.json['cookies'] == {'a': 'b'}


@pytest.mark.parametrize('session', [True, False])
def test_server_set_cookie_on_redirect_different_domain(tmp_path, http_server, httpbin, session):
    # Server set cookies ARE persisted on different domains
    # when they are forwarded.

    session_args = []
    if session:
        session_args.extend([
            '--session',
            str(tmp_path / 'session.json')
        ])

    r = http(
        '--follow',
        *session_args,
        http_server + '/cookies/set-and-redirect',
        f"X-Redirect-To:{httpbin + '/cookies'}",
        'X-Cookies:a=b'
    )
    assert r.json['cookies'] == {'a': 'b'}


def test_saved_session_cookies_on_same_domain(tmp_path, httpbin):
    """Saved session cookies ARE persisted when making a new request to the same domain."""
    http(
        '--session',
        str(tmp_path / 'session.json'),
        httpbin + '/cookies/set/a/b'
    )
    r = http(
        '--session',
        str(tmp_path / 'session.json'),
        httpbin + '/cookies'
    )
    assert r.json == {'cookies': {'a': 'b'}}


def test_saved_session_cookies_on_different_domain(tmp_path, httpbin, remote_httpbin):
    """Saved session cookies ARE persisted when making a new request to a different domain."""
    http(
        '--session',
        str(tmp_path / 'session.json'),
        httpbin + '/cookies/set/a/b'
    )
    r = http(
        '--session',
        str(tmp_path / 'session.json'),
        remote_httpbin + '/cookies'
    )
    assert r.json == {'cookies': {}}


@pytest.mark.parametrize(['initial_domain', 'first_request_domain', 'second_request_domain', 'expect_cookies'], [
    (
        # Cookies are set by    Domain A
        # Initial domain is     Domain A
        # Redirected domain is  Domain A
        'httpbin',
        'httpbin',
        'httpbin',
        True,
    ),
    (
        # Cookies are set by    Domain A
        # Initial domain is     Domain B
        # Redirected domain is  Domain B
        'httpbin',
        'remote_httpbin',
        'remote_httpbin',
        False,
    ),
    (
        # Cookies are set by    Domain A
        # Initial domain is     Domain A
        # Redirected domain is  Domain B
        'httpbin',
        'httpbin',
        'remote_httpbin',
        False,
    ),
    (
        # Cookies are set by    Domain A
        # Initial domain is     Domain B
        # Redirected domain is  Domain A
        'httpbin',
        'remote_httpbin',
        'httpbin',
        True,
    ),
])
def test_saved_session_cookies_on_redirect(
        tmp_path, initial_domain, first_request_domain, second_request_domain, expect_cookies, request):
    initial_domain = request.getfixturevalue(initial_domain)
    first_request_domain = request.getfixturevalue(first_request_domain)
    second_request_domain = request.getfixturevalue(second_request_domain)
    http(
        '--session',
        str(tmp_path / 'session.json'),
        initial_domain + '/cookies/set/a/b'
    )
    r = http(
        '--session',
        str(tmp_path / 'session.json'),
        '--follow',
        first_request_domain + '/redirect-to',
        f'url=={second_request_domain}/cookies'
    )
    if expect_cookies:
        expected_data = {'cookies': {'a': 'b'}}
    else:
        expected_data = {'cookies': {}}
    assert r.json == expected_data


def test_saved_session_cookie_pool(tmp_path, httpbin, remote_httpbin):
    http(
        '--session',
        str(tmp_path / 'session.json'),
        httpbin + '/cookies/set/a/b'
    )
    http(
        '--session',
        str(tmp_path / 'session.json'),
        remote_httpbin + '/cookies/set/a/c'
    )
    http(
        '--session',
        str(tmp_path / 'session.json'),
        remote_httpbin + '/cookies/set/b/d'
    )

    response = http(
        '--session',
        str(tmp_path / 'session.json'),
        httpbin + '/cookies'
    )
    assert response.json['cookies'] == {'a': 'b'}

    response = http(
        '--session',
        str(tmp_path / 'session.json'),
        remote_httpbin + '/cookies'
    )
    assert response.json['cookies'] == {'a': 'c', 'b': 'd'}
