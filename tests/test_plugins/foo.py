from httpie.plugins import AuthPlugin
from httpie.plugins.builtin import HTTPBasicAuth


class FooPlugin(AuthPlugin):
    auth_type = 'foo'
    name = 'foo HTTP auth'

    def get_auth(self, username=None, password=None):
        return HTTPBasicAuth(username, password + '-foo')
