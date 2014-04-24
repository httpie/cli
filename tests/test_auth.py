"""HTTP authentication-related tests."""
from unittest import TestCase

import requests
import pytest

from tests import http, httpbin, HTTP_OK
import httpie.input


class AuthTest(TestCase):
    def test_basic_auth(self):
        r = http('--auth=user:password', 'GET',
                 httpbin('/basic-auth/user/password'))
        assert HTTP_OK in r
        assert '"authenticated": true' in r
        assert '"user": "user"' in r

    @pytest.mark.skipif(
        requests.__version__ == '0.13.6',
        reason='Redirects with prefetch=False are broken in Requests 0.13.6')
    def test_digest_auth(self):
        r = http('--auth-type=digest', '--auth=user:password', 'GET',
                 httpbin('/digest-auth/auth/user/password'))
        assert HTTP_OK in r
        assert r'"authenticated": true' in r
        assert r'"user": "user"', r

    def test_password_prompt(self):
        httpie.input.AuthCredentials._getpass = lambda self, prompt: 'password'
        r = http('--auth', 'user', 'GET', httpbin('/basic-auth/user/password'))
        assert HTTP_OK in r
        assert '"authenticated": true' in r
        assert '"user": "user"' in r

    def test_credentials_in_url(self):
        url = httpbin('/basic-auth/user/password')
        url = 'http://user:password@' + url.split('http://', 1)[1]
        r = http('GET', url)
        assert HTTP_OK in r
        assert '"authenticated": true' in r
        assert '"user": "user"' in r

    def test_credentials_in_url_auth_flag_has_priority(self):
        """When credentials are passed in URL and via -a at the same time,
         then the ones from -a are used."""
        url = httpbin('/basic-auth/user/password')
        url = 'http://user:wrong_password@' + url.split('http://', 1)[1]
        r = http('--auth=user:password', 'GET', url)
        assert HTTP_OK in r
        assert '"authenticated": true' in r
        assert '"user": "user"' in r
