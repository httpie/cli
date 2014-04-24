"""HTTP authentication-related tests."""
import requests

from tests import BaseTestCase, http, httpbin, OK, skipIf
import httpie.input


class AuthTest(BaseTestCase):

    def test_basic_auth(self):
        r = http(
            '--auth=user:password',
            'GET',
            httpbin('/basic-auth/user/password')
        )
        self.assertIn(OK, r)
        self.assertIn('"authenticated": true', r)
        self.assertIn('"user": "user"', r)

    @skipIf(requests.__version__ == '0.13.6',
            'Redirects with prefetch=False are broken in Requests 0.13.6')
    def test_digest_auth(self):
        r = http(
            '--auth-type=digest',
            '--auth=user:password',
            'GET',
            httpbin('/digest-auth/auth/user/password')
        )
        self.assertIn(OK, r)
        self.assertIn(r'"authenticated": true', r)
        self.assertIn(r'"user": "user"', r)

    def test_password_prompt(self):

        httpie.input.AuthCredentials._getpass = lambda self, prompt: 'password'

        r = http(
            '--auth',
            'user',
            'GET',
            httpbin('/basic-auth/user/password')
        )

        self.assertIn(OK, r)
        self.assertIn('"authenticated": true', r)
        self.assertIn('"user": "user"', r)

    def test_credentials_in_url(self):
        url = httpbin('/basic-auth/user/password')
        url = 'http://user:password@' + url.split('http://', 1)[1]
        r = http(
            'GET',
            url
        )
        self.assertIn(OK, r)
        self.assertIn('"authenticated": true', r)
        self.assertIn('"user": "user"', r)

    def test_credentials_in_url_auth_flag_has_priority(self):
        """When credentials are passed in URL and via -a at the same time,
         then the ones from -a are used."""
        url = httpbin('/basic-auth/user/password')
        url = 'http://user:wrong_password@' + url.split('http://', 1)[1]
        r = http(
            '--auth=user:password',
            'GET',
            url
        )
        self.assertIn(OK, r)
        self.assertIn('"authenticated": true', r)
        self.assertIn('"user": "user"', r)
