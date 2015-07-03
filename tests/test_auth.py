"""HTTP authentication-related tests."""
import requests
import pytest

from utils import http, add_auth, HTTP_OK, TestEnvironment
import httpie.input
import httpie.cli


class TestAuth:
    def test_basic_auth(self, httpbin):
        r = http('--auth=user:password',
                 'GET', httpbin.url + '/basic-auth/user/password')
        assert HTTP_OK in r
        assert r.json == {'authenticated': True, 'user': 'user'}

    @pytest.mark.skipif(
        requests.__version__ == '0.13.6',
        reason='Redirects with prefetch=False are broken in Requests 0.13.6')
    def test_digest_auth(self, httpbin):
        r = http('--auth-type=digest', '--auth=user:password',
                 'GET', httpbin.url + '/digest-auth/auth/user/password')
        assert HTTP_OK in r
        assert r.json == {'authenticated': True, 'user': 'user'}

    def test_password_prompt(self, httpbin):
        httpie.input.AuthCredentials._getpass = lambda self, prompt: 'password'
        r = http('--auth', 'user',
                 'GET', httpbin.url + '/basic-auth/user/password')
        assert HTTP_OK in r
        assert r.json == {'authenticated': True, 'user': 'user'}

    def test_credentials_in_url(self, httpbin):
        url = add_auth(httpbin.url + '/basic-auth/user/password',
                       auth='user:password')
        r = http('GET', url)
        assert HTTP_OK in r
        assert r.json == {'authenticated': True, 'user': 'user'}

    def test_credentials_in_url_auth_flag_has_priority(self, httpbin):
        """When credentials are passed in URL and via -a at the same time,
         then the ones from -a are used."""
        url = add_auth(httpbin.url + '/basic-auth/user/password',
                       auth='user:wrong')
        r = http('--auth=user:password', 'GET', url)
        assert HTTP_OK in r
        assert r.json == {'authenticated': True, 'user': 'user'}

    @pytest.mark.parametrize('url', [
        'username@example.org',
        'username:@example.org',
    ])
    def test_only_username_in_url(self, url):
        """
        https://github.com/jkbrzt/httpie/issues/242

        """
        args = httpie.cli.parser.parse_args(args=[url], env=TestEnvironment())
        assert args.auth
        assert args.auth.key == 'username'
        assert args.auth.value == ''

