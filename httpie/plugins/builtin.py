import requests.auth

from .base import AuthPlugin


class BuiltinAuthPlugin(AuthPlugin):

    package_name = '(builtin)'


class BasicAuthPlugin(BuiltinAuthPlugin):

    name = 'Basic HTTP auth'
    auth_type = 'basic'

    def get_auth(self, username, password):
        return requests.auth.HTTPBasicAuth(username, password)


class DigestAuthPlugin(BuiltinAuthPlugin):

    name = 'Digest HTTP auth'
    auth_type = 'digest'

    def get_auth(self, username, password):
        return requests.auth.HTTPDigestAuth(username, password)
