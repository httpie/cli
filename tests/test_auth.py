"""HTTP authentication-related tests."""
import requests
import pytest

from tests import http, httpbin, HTTP_OK
import httpie.input


class TestAuth:
    def test_basic_auth(self):
        r = http('--auth=user:password',
                 'GET', httpbin('/basic-auth/user/password'))
        assert HTTP_OK in r
        assert r.json == {'authenticated': True, 'user': 'user'}

    @pytest.mark.skipif(
        requests.__version__ == '0.13.6',
        reason='Redirects with prefetch=False are broken in Requests 0.13.6')
    def test_digest_auth(self):
        r = http('--auth-type=digest', '--auth=user:password',
                 'GET', httpbin('/digest-auth/auth/user/password'))
        assert HTTP_OK in r
        assert r.json == {'authenticated': True, 'user': 'user'}

    def test_password_prompt(self):
        httpie.input.AuthCredentials._getpass = lambda self, prompt: 'password'
        r = http('--auth', 'user', 'GET', httpbin('/basic-auth/user/password'))
        assert HTTP_OK in r
        assert r.json == {'authenticated': True, 'user': 'user'}

    def test_credentials_in_url(self):
        r = http('GET', httpbin('/basic-auth/user/password',
                                auth='user:password'))
        assert HTTP_OK in r
        assert r.json == {'authenticated': True, 'user': 'user'}

    def test_credentials_in_url_auth_flag_has_priority(self):
        """When credentials are passed in URL and via -a at the same time,
         then the ones from -a are used."""
        r = http('--auth=user:password', 'GET',
                 httpbin('/basic-auth/user/password', auth='user:wrong'))
        assert HTTP_OK in r
        assert r.json == {'authenticated': True, 'user': 'user'}
