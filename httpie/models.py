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
    """A :class:`requests.models.Response` wrapper."""

    def iter_body(self, chunk_size=1):
        return self._orig.iter_content(chunk_size=chunk_size)

    def iter_lines(self, chunk_size):
        return ((line, b'\n') for line in self._orig.iter_lines(chunk_size))

    # noinspection PyProtectedMember
    @property
    def headers(self):
        original = self._orig.raw._original_response

        version = {
            9: '0.9',
            10: '1.0',
            11: '1.1',
            20: '2',
        }[original.version]

        status_line = f'HTTP/{version} {original.status} {original.reason}'
        headers = [status_line]
        try:
            # `original.msg` is a `http.client.HTTPMessage` on Python 3
            # `_headers` is a 2-tuple
            headers.extend(
                '%s: %s' % header for header in original.msg._headers)
        except AttributeError:
            # and a `httplib.HTTPMessage` on Python 2.x
            # `headers` is a list of `name: val<CRLF>`.
            headers.extend(h.strip() for h in original.msg.headers)

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
    """A :class:`requests.models.Request` wrapper."""

    def iter_body(self, chunk_size):
        yield self.body

    def iter_lines(self, chunk_size):
        yield self.body, b''

    @property
    def headers(self):
        url = urlsplit(self._orig.url)

        request_line = '{method} {path}{query} HTTP/1.1'.format(
            method=self._orig.method,
            path=url.path or '/',
            query='?' + url.query if url.query else ''
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
        body = self._orig.body
        if isinstance(body, str):
            # Happens with JSON/form request data parsed from the command line.
            body = body.encode('utf8')
        return body or b''
