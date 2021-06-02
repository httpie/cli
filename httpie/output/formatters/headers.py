from ...plugins import FormatterPlugin


class HeadersFormatter(FormatterPlugin):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.enabled = self.format_options['headers']['sort']

    def format_headers(self, headers: str) -> str:
        """
        Sorts headers by name while retaining relative
        order of multiple headers with the same name.

        """
        lines = headers.splitlines()
        headers = sorted(lines[1:], key=lambda h: h.split(':')[0])
        return '\r\n'.join(lines[:1] + headers)
