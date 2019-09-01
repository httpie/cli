class BasePlugin:

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

    See <https://github.com/httpie/httpie-ntlm> for an example auth plugin.

    See also `test_auth_plugins.py`

    """
    # The value that should be passed to --auth-type
    # to use this auth plugin. Eg. "my-auth"
    auth_type = None

    # Set to `False` to make it possible to invoke this auth
    # plugin without requiring the user to specify credentials
    # through `--auth, -a`.
    auth_require = True

    # By default the `-a` argument is parsed for `username:password`.
    # Set this to `False` to disable the parsing and error handling.
    auth_parse = True

    # If both `auth_parse` and `prompt_password` are set to `True`,
    # and the value of `-a` lacks the password part,
    # then the user will be prompted to type the password in.
    prompt_password = True

    # Will be set to the raw value of `-a` (if provided) before
    # `get_auth()` gets called.
    raw_auth = None

    def get_auth(self, username=None, password=None):
        """
        If `auth_parse` is set to `True`, then `username`
        and `password` contain the parsed credentials.

        Use `self.raw_auth` to access the raw value passed through
        `--auth, -a`.

        Return a ``requests.auth.AuthBase`` subclass instance.

        """
        raise NotImplementedError()


class TransportPlugin(BasePlugin):
    """

    https://2.python-requests.org/en/latest/user/advanced/#transport-adapters

    """

    # The URL prefix the adapter should be mount to.
    prefix = None

    def get_adapter(self):
        """
        Return a ``requests.adapters.BaseAdapter`` subclass instance to be
        mounted to ``self.prefix``.

        """
        raise NotImplementedError()


class ConverterPlugin(BasePlugin):

    def __init__(self, mime):
        self.mime = mime

    def convert(self, content_bytes):
        raise NotImplementedError

    @classmethod
    def supports(cls, mime):
        raise NotImplementedError


class FormatterPlugin(BasePlugin):
    group_name = 'format'

    def __init__(self, **kwargs):
        """
        :param env: an class:`Environment` instance
        :param kwargs: additional keyword argument that some
                       processor might require.

        """
        self.enabled = True
        self.kwargs = kwargs

    def format_headers(self, headers: str) -> str:
        """Return processed `headers`

        :param headers: The headers as text.

        """
        return headers

    def format_body(self, content: str, mime: str) -> str:
        """Return processed `content`.

        :param mime: E.g., 'application/atom+xml'.
        :param content: The body content as text

        """
        return content
