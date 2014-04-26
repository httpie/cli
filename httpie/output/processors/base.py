from httpie.context import Environment


# The default number of spaces to indent when pretty printing
DEFAULT_INDENT = 4


class BaseProcessor(object):
    """Base output processor class."""

    def __init__(self, env=Environment(), **kwargs):
        """
        :param env: an class:`Environment` instance
        :param kwargs: additional keyword argument that some
                       processor might require.

        """
        self.enabled = True
        self.env = env
        self.kwargs = kwargs

    def process_headers(self, headers):
        """Return processed `headers`

        :param headers: The headers as text.

        """
        return headers

    def process_body(self, content, mime):
        """Return processed `content`.

        :param content: The body content as text
        :param mime: E.g., 'application/atom+xml'.

        """
        return content
