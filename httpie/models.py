from typing import Iterable, Optional
from urllib.parse import urlsplit

from httpie.utils import split_cookies


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
        try:
            raw_version = self._orig.raw._original_response.version
        except AttributeError:
            # Assume HTTP/1.1
            raw_version = 11
        version = {
            9: '0.9',
            10: '1.0',
            11: '1.1',
            20: '2',
        }[raw_version]

        original = self._orig
        status_line = f'HTTP/{version} {original.status_code} {original.reason}'
        headers = [status_line]
        headers.extend(
            ': '.join(header)
            for header in original.headers.items()
            if header[0] != 'Set-Cookie'
        )
        headers.extend(
            f'Set-Cookie: {cookie}'
            for cookie in split_cookies(original.headers.get('Set-Cookie'))
        )
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
            query=f'?{url.query}' if url.query else ''
        )

        headers = dict(self._orig.headers)
        if 'Host' not in self._orig.headers:
            headers['Host'] = url.netloc.split('@')[-1]

        headers = [
            f'{name}: {value if isinstance(value, str) else value.decode("utf-8")}'
            for name, value in headers.items()
        ]

        headers.insert(0, request_line)
        headers = '\r\n'.join(headers).strip()
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
