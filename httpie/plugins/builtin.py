from base64 import b64encode

import requests.auth

from httpie.plugins.base import AuthPlugin


# noinspection PyAbstractClass
class BuiltinAuthPlugin(AuthPlugin):

    package_name = '(builtin)'


class HTTPBasicAuth(requests.auth.HTTPBasicAuth):

    def __call__(self, r):
        """
        Override username/password serialization to allow unicode.

        See https://github.com/jkbrzt/httpie/issues/212

        """
        r.headers['Authorization'] = type(self).make_header(
            self.username, self.password).encode('latin1')
        return r

    @staticmethod
    def make_header(username, password):
        credentials = u'%s:%s' % (username, password)
        token = b64encode(credentials.encode('utf8')).strip().decode('latin1')
        return 'Basic %s' % token


class BasicAuthPlugin(BuiltinAuthPlugin):

    name = 'Basic HTTP auth'
    auth_type = 'basic'

    # noinspection PyMethodOverriding
    def get_auth(self, username, password):
        return HTTPBasicAuth(username, password)


class DigestAuthPlugin(BuiltinAuthPlugin):

    name = 'Digest HTTP auth'
    auth_type = 'digest'

    # noinspection PyMethodOverriding
    def get_auth(self, username, password):
        return requests.auth.HTTPDigestAuth(username, password)
