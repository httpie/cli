"""HTTP authentication-related tests."""
import mock
import pytest

from httpie.plugins.builtin import HTTPBasicAuth
from httpie.utils import ExplicitNullAuth
from utils import http, add_auth, HTTP_OK, MockEnvironment
import httpie.cli.constants
import httpie.cli.definition


def test_basic_auth(httpbin_both):
    r = http('--auth=user:password',
             'GET', httpbin_both + '/basic-auth/user/password')
    assert HTTP_OK in r
    assert r.json == {'authenticated': True, 'user': 'user'}


@pytest.mark.parametrize('argument_name', ['--auth-type', '-A'])
def test_digest_auth(httpbin_both, argument_name):
    r = http(argument_name + '=digest', '--auth=user:password',
             'GET', httpbin_both.url + '/digest-auth/auth/user/password')
    assert HTTP_OK in r
    assert r.json == {'authenticated': True, 'user': 'user'}


@mock.patch('httpie.cli.argtypes.AuthCredentials._getpass',
            new=lambda self, prompt: 'password')
def test_password_prompt(httpbin):
    r = http('--auth', 'user',
             'GET', httpbin.url + '/basic-auth/user/password')
    assert HTTP_OK in r
    assert r.json == {'authenticated': True, 'user': 'user'}


def test_credentials_in_url(httpbin_both):
    url = add_auth(httpbin_both.url + '/basic-auth/user/password',
                   auth='user:password')
    r = http('GET', url)
    assert HTTP_OK in r
    assert r.json == {'authenticated': True, 'user': 'user'}


def test_credentials_in_url_auth_flag_has_priority(httpbin_both):
    """When credentials are passed in URL and via -a at the same time,
     then the ones from -a are used."""
    url = add_auth(httpbin_both.url + '/basic-auth/user/password',
                   auth='user:wrong')
    r = http('--auth=user:password', 'GET', url)
    assert HTTP_OK in r
    assert r.json == {'authenticated': True, 'user': 'user'}


@pytest.mark.parametrize('url', [
    'username@example.org',
    'username:@example.org',
])
def test_only_username_in_url(url):
    """
    https://github.com/jakubroztocil/httpie/issues/242

    """
    args = httpie.cli.definition.parser.parse_args(args=[url], env=MockEnvironment())
    assert args.auth
    assert args.auth.username == 'username'
    assert args.auth.password == ''


def test_missing_auth(httpbin):
    r = http(
        '--auth-type=basic',
        'GET',
        httpbin + '/basic-auth/user/password',
        error_exit_ok=True
    )
    assert HTTP_OK not in r
    assert '--auth required' in r.stderr


def test_netrc(httpbin_both):
    with mock.patch('requests.sessions.get_netrc_auth') as get_netrc_auth:
        get_netrc_auth.return_value = ('httpie', 'password')
        r = http(httpbin_both + '/basic-auth/httpie/password')
        assert get_netrc_auth.call_count == 1
        assert HTTP_OK in r


def test_ignore_netrc(httpbin_both):
    with mock.patch('requests.sessions.get_netrc_auth') as get_netrc_auth:
        get_netrc_auth.return_value = ('httpie', 'password')
        r = http('--ignore-netrc', httpbin_both + '/basic-auth/httpie/password')
        assert get_netrc_auth.call_count == 0
        assert 'HTTP/1.1 401 UNAUTHORIZED' in r


def test_ignore_netrc_null_auth():
    args = httpie.cli.definition.parser.parse_args(
        args=['--ignore-netrc', 'example.org'],
        env=MockEnvironment(),
    )
    assert isinstance(args.auth, ExplicitNullAuth)


def test_ignore_netrc_together_with_auth():
    args = httpie.cli.definition.parser.parse_args(
        args=['--ignore-netrc', '--auth=username:password', 'example.org'],
        env=MockEnvironment(),
    )
    assert isinstance(args.auth, HTTPBasicAuth)
