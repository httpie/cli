from utils import http, HTTP_OK
from httpie.plugins import AuthPlugin, plugin_manager

# TODO: run all these tests in session mode as well

# Basic auth encoded 'username' and 'password'
BASIC_AUTH_HEADER_VALUE = 'Basic dXNlcm5hbWU6cGFzc3dvcmQ='
BASIC_AUTH_URL = '/basic-auth/username/password'


def dummy_auth(auth_header=BASIC_AUTH_HEADER_VALUE):

    def inner(r):
        r.headers['Authorization'] = auth_header
        return r

    return inner


def test_auth_plugin_parse_false(httpbin):

    class ParseFalseAuthPlugin(AuthPlugin):
        auth_type = 'parse-false'
        auth_parse = False

        def get_auth(self, username=None, password=None):
            assert username is None
            assert password is None
            assert self.raw_auth == BASIC_AUTH_HEADER_VALUE
            return dummy_auth(self.raw_auth)

    plugin_manager.register(ParseFalseAuthPlugin)
    try:
        r = http(
            httpbin + BASIC_AUTH_URL,
            '--auth-type', 'parse-false',
            '--auth', BASIC_AUTH_HEADER_VALUE
        )
        assert HTTP_OK in r
    finally:
        plugin_manager.unregister(ParseFalseAuthPlugin)


def test_auth_plugin_require_false(httpbin):

    class RequireFalseAuthPlugin(AuthPlugin):
        auth_type = 'require-false'
        auth_require = False

        def get_auth(self, username=None, password=None):
            assert self.raw_auth is None
            assert username is None
            assert password is None
            return dummy_auth()

    plugin_manager.register(RequireFalseAuthPlugin)
    try:
        r = http(
            httpbin + BASIC_AUTH_URL,
            '--auth-type', 'require-false',
        )
        assert HTTP_OK in r
    finally:
        plugin_manager.unregister(RequireFalseAuthPlugin)


def test_auth_plugin_prompt_false(httpbin):

    class PromptFalseAuthPlugin(AuthPlugin):
        auth_type = 'prompt-false'
        prompt_password = False

        def get_auth(self, username=None, password=None):
            assert self.raw_auth == 'username:'
            assert username == 'username'
            assert password == ''
            return dummy_auth()

    plugin_manager.register(PromptFalseAuthPlugin)

    try:
        r = http(
            httpbin + BASIC_AUTH_URL,
            '--auth-type', 'prompt-false',
            '--auth', 'username:'
        )
        assert HTTP_OK in r
    finally:
        plugin_manager.unregister(PromptFalseAuthPlugin)
