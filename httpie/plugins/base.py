from typing import Tuple


class BasePlugin:
    # The name of the plugin, eg. "My auth".
    name = None

    # Optional short description. It will be shown in the help
    # under --auth-type.
    description = None

    # This be set automatically once the plugin has been loaded.
    package_name = None


class AuthPlugin(BasePlugin):
    """
    Base auth plugin class.

    See httpie-ntlm for an example auth plugin:

        <https://github.com/httpie/httpie-ntlm>

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

    # Set to `True` to make it possible for this auth
    # plugin to acquire credentials from the user’s netrc file(s).
    # It is used as a fallback when the credentials are not provided explicitly
    # through `--auth, -a`. Enabling this will allow skipping `--auth, -a`
    # even when `auth_require` is set `True` (provided that netrc provides
    # credential for a given host).
    netrc_parse = False

    # If both `auth_parse` and `prompt_password` are set to `True`,
    # and the value of `-a` lacks the password part,
    # then the user will be prompted to type the password in.
    prompt_password = True

    # Will be set to the raw value of `-a` (if provided) before
    # `get_auth()` gets called. If the credentials came from a netrc file,
    # then this is `None`.
    raw_auth = None

    def get_auth(self, username: str = None, password: str = None):
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
    Requests transport adapter docs:

        <https://requests.readthedocs.io/en/latest/user/advanced/#transport-adapters>

    See httpie-unixsocket for an example transport plugin:

        <https://github.com/httpie/httpie-unixsocket>

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
    """
    Possibly converts binary response data for prettified terminal display.

    See httpie-msgpack for an example converter plugin:

        <https://github.com/rasky/httpie-msgpack>.

    """

    def __init__(self, mime: str):
        self.mime = mime

    def convert(self, body: bytes) -> Tuple[str, str]:
        """
        Convert a binary body to a textual representation for the terminal
        and return a tuple containing the new Content-Type and content, e.g.:

        ('application/json', '{}')

        """
        raise NotImplementedError

    @classmethod
    def supports(cls, mime: str) -> bool:
        raise NotImplementedError


class FormatterPlugin(BasePlugin):
    """
    Possibly formats response body & headers for prettified terminal display.

    """
    group_name = 'format'

    def __init__(self, **kwargs):
        """
        :param env: an class:`Environment` instance
        :param kwargs: additional keyword argument that some
                       formatters might require.

        """
        self.enabled = True
        self.kwargs = kwargs
        self.format_options = kwargs['format_options']

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

    def format_metadata(self, metadata: str) -> str:
        """Return processed `metadata`.

        :param metadata: The metadata as text.

        """
        return metadata
