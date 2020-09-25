from typing import Iterable, Optional
from urllib.parse import urlsplit


class HTTPMessage:
    """Abstract class for HTTP messages."""

    def __init__(self, orig):
        self._orig = orig

    def iter_body(self, chunk_size: int) -> Iterable[bytes]:
        """Return an iterator over the body."""
        raise NotImplementedError()

    def iter_lines(self, chunk_size: int) -> Iterable[bytes]:
        """Return an iterator over the body yielding (`line`, `line_feed`)."""
        raise NotImplementedError()

    @property
    def headers(self) -> str:
        """Return a `str` with the message's headers."""
        raise NotImplementedError()

    @property
    def encoding(self) -> Optional[str]:
        """Return a `str` with the message's encoding, if known."""
        raise NotImplementedError()

    @property
    def body(self) -> bytes:
        """Return a `bytes` with the message's body."""
        raise NotImplementedError()

    @property
    def content_type(self) -> str:
        """Return the message content type."""
        ct = self._orig.headers.get('Content-Type', '')
        if not isinstance(ct, str):
            ct = ct.decode('utf8')
        return ct


class HTTPResponse(HTTPMessage):
    """A :class:`httpx.models.Response` wrapper."""

    def iter_body(self, chunk_size=1):
        return self._orig.iter_bytes()

    def iter_lines(self, chunk_size):
        return ((line, b'\n') for line in self._orig.iter_lines())

    # noinspection PyProtectedMember
    @property
    def headers(self):
        original = self._orig

        status_line = f'{original.http_version} {original.status_code} {original.reason_phrase}'
        headers = [status_line]
        headers.extend(
            '%s: %s' % header for header in original.headers.items())

        return '\r\n'.join(headers)

    @property
    def encoding(self):
        return self._orig.encoding or 'utf8'

    @property
    def body(self):
        # Only now the response body is fetched.
        # Shouldn't be touched unless the body is actually needed.
        return self._orig.content


class HTTPRequest(HTTPMessage):
    """A :class:`httpx.models.Request` wrapper."""

    def iter_body(self, chunk_size):
        yield self.body

    def iter_lines(self, chunk_size):
        yield self.body, b''

    @property
    def headers(self):
        url = self._orig.url

        request_line = '{method} {target} HTTP/1.1'.format(
            method=self._orig.method,
            target=url.raw_path.decode("ascii")
        )

        headers = dict(self._orig.headers)
        if 'Host' not in self._orig.headers:
            headers['Host'] = url.netloc.split('@')[-1]

        headers = [
            '%s: %s' % (
                name,
                value if isinstance(value, str) else value.decode('utf8')
            )
            for name, value in headers.items()
        ]

        headers.insert(0, request_line)
        headers = '\r\n'.join(headers).strip()

        if isinstance(headers, bytes):
            # Python < 3
            headers = headers.decode('utf8')
        return headers

    @property
    def encoding(self):
        return 'utf8'

    @property
    def body(self):
        body = self._orig.content
        if isinstance(body, str):
            # Happens with JSON/form request data parsed from the command line.
            body = body.encode('utf8')
        return body or b''
