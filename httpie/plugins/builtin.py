from base64 import b64encode

import httpx
import requests.auth

from httpie.plugins.base import AuthPlugin


# noinspection PyAbstractClass
class BuiltinAuthPlugin(AuthPlugin):
    package_name = '(builtin)'


class BasicAuthPlugin(BuiltinAuthPlugin):
    name = 'Basic HTTP auth'
    auth_type = 'basic'
    netrc_parse = True

    # noinspection PyMethodOverriding
    def get_auth(self, username: str, password: str) -> httpx.BasicAuth:
        return httpx.BasicAuth(username, password)


class DigestAuthPlugin(BuiltinAuthPlugin):
    name = 'Digest HTTP auth'
    auth_type = 'digest'
    netrc_parse = True

    # noinspection PyMethodOverriding
    def get_auth(
        self,
        username: str,
        password: str
    ) -> httpx.DigestAuth:
        return httpx.DigestAuth(username, password)
