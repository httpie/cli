from base64 import b64encode

import requests.auth

from .base import AuthPlugin


class BuiltinAuthPlugin(AuthPlugin):

    package_name = '(builtin)'


class HTTPBasicAuth(requests.auth.HTTPBasicAuth):

    def __call__(self, r):
        """
        Override username/password serialization to allow unicode.

        See https://github.com/jkbr/httpie/issues/212

        """
        credentials = u'%s:%s' % (self.username, self.password)
        token = b64encode(credentials.encode('utf8')).strip()
        r.headers['Authorization'] = 'Basic %s' % token
        return r


class BasicAuthPlugin(BuiltinAuthPlugin):

    name = 'Basic HTTP auth'
    auth_type = 'basic'

    def get_auth(self, username, password):
        return HTTPBasicAuth(username, password)


class DigestAuthPlugin(BuiltinAuthPlugin):

    name = 'Digest HTTP auth'
    auth_type = 'digest'

    def get_auth(self, username, password):
        return requests.auth.HTTPDigestAuth(username, password)
