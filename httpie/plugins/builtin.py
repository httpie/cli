from base64 import b64encode

import requests.auth

from httpie.plugins.base import AuthPlugin


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

        See https://github.com/httpie/httpie/issues/212

        """
        # noinspection PyTypeChecker
        request.headers['Authorization'] = type(self).make_header(
            self.username, self.password).encode('latin1')
        return request

    @staticmethod
    def make_header(username: str, password: str) -> str:
        credentials = u'%s:%s' % (username, password)
        token = b64encode(credentials.encode('utf8')).strip().decode('latin1')
        return 'Basic %s' % token


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
