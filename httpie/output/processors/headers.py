from .base import BaseProcessor


class HeadersProcessor(BaseProcessor):

    def process_headers(self, headers):
        """
        Sorts headers by name while retaining relative
        order of multiple headers with the same name.

        """
        lines = headers.splitlines()
        headers = sorted(lines[1:], key=lambda h: h.split(':')[0])
        return '\r\n'.join(lines[:1] + headers)
