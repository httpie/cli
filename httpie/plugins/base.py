class BasePlugin(object):

    # The name of the plugin, eg. "My auth".
    name = None

    # Optional short description. Will be be shown in the help
    # under --auth-type.
    description = None

    # This be set automatically once the plugin has been loaded.
    package_name = None


class AuthPlugin(BasePlugin):
    """
    Base auth plugin class.

    See <https://github.com/jkbrzt/httpie-ntlm> for an example auth plugin.

    """
    # The value that should be passed to --auth-type
    # to use this auth plugin. Eg. "my-auth"
    auth_type = None

    def get_auth(self, username, password):
        """
        Return a ``requests.auth.AuthBase`` subclass instance.

        """
        raise NotImplementedError()


class TransportPlugin(BasePlugin):
    """

    http://docs.python-requests.org/en/latest/user/advanced/#transport-adapters

    """

    # The URL prefix the adapter should be mount to.
    prefix = None

    def get_adapter(self):
        """
        Return a ``requests.adapters.BaseAdapter`` subclass instance to be
        mounted to ``self.prefix``.

        """
        raise NotImplementedError()


class ConverterPlugin(object):

    def __init__(self, mime):
        self.mime = mime

    def convert(self, content_bytes):
        raise NotImplementedError

    @classmethod
    def supports(cls, mime):
        raise NotImplementedError


class FormatterPlugin(object):

    def __init__(self, **kwargs):
        """
        :param env: an class:`Environment` instance
        :param kwargs: additional keyword argument that some
                       processor might require.

        """
        self.enabled = True
        self.kwargs = kwargs

    def format_headers(self, headers):
        """Return processed `headers`

        :param headers: The headers as text.

        """
        return headers

    def format_body(self, content, mime):
        """Return processed `content`.

        :param mime: E.g., 'application/atom+xml'.
        :param content: The body content as text

        """
        return content
