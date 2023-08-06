from base64 import b64encode

import requests.auth

from .base import AuthPlugin


# noinspection PyAbstractClass
class BuiltinAuthPlugin(AuthPlugin):
    package_name = '(builtin)'


class HTTPBasicAuth(requests.auth.HTTPBasicAuth):

    def __call__(
        self,
        request: requests.PreparedRequest
    ) -> requests.PreparedRequest:
        """
        Override username/password serialization to allow unicode.

        See https://github.com/httpie/cli/issues/212

        """
        # noinspection PyTypeChecker
        request.headers['Authorization'] = type(self).make_header(
            self.username, self.password).encode('latin1')
        return request

    @staticmethod
    def make_header(username: str, password: str) -> str:
        credentials = f'{username}:{password}'
        token = b64encode(credentials.encode()).strip().decode('latin1')
        return f'Basic {token}'


class HTTPBearerAuth(requests.auth.AuthBase):

    def __init__(self, token: str) -> None:
        self.token = token

    def __call__(self, request: requests.PreparedRequest) -> requests.PreparedRequest:
        request.headers['Authorization'] = f'Bearer {self.token}'
        return request


class BasicAuthPlugin(BuiltinAuthPlugin):
    name = 'Basic HTTP auth'
    auth_type = 'basic'
    netrc_parse = True

    # noinspection PyMethodOverriding
    def get_auth(self, username: str, password: str) -> HTTPBasicAuth:
        return HTTPBasicAuth(username, password)


class DigestAuthPlugin(BuiltinAuthPlugin):
    name = 'Digest HTTP auth'
    auth_type = 'digest'
    netrc_parse = True

    # noinspection PyMethodOverriding
    def get_auth(
        self,
        username: str,
        password: str
    ) -> requests.auth.HTTPDigestAuth:
        return requests.auth.HTTPDigestAuth(username, password)


class BearerAuthPlugin(BuiltinAuthPlugin):
    name = 'Bearer HTTP Auth'
    auth_type = 'bearer'
    netrc_parse = False
    auth_parse = False

    # noinspection PyMethodOverriding
    def get_auth(self, **kwargs) -> requests.auth.HTTPDigestAuth:
        return HTTPBearerAuth(self.raw_auth)
