from time import monotonic

import requests

from enum import Enum, auto
from typing import Iterable, Union, NamedTuple
from urllib.parse import urlsplit

from .cli.constants import (
    OUT_REQ_BODY,
    OUT_REQ_HEAD,
    OUT_RESP_BODY,
    OUT_RESP_HEAD,
    OUT_RESP_META
)
from .compat import cached_property
from .utils import split_cookies, parse_content_type_header


ELAPSED_TIME_LABEL = 'Elapsed time'


class HTTPMessage:
    """Abstract class for HTTP messages."""

    def __init__(self, orig):
        self._orig = orig

    def iter_body(self, chunk_size: int) -> Iterable[bytes]:
        """Return an iterator over the body."""
        raise NotImplementedError

    def iter_lines(self, chunk_size: int) -> Iterable[bytes]:
        """Return an iterator over the body yielding (`line`, `line_feed`)."""
        raise NotImplementedError

    @property
    def headers(self) -> str:
        """Return a `str` with the message's headers."""
        raise NotImplementedError

    @property
    def metadata(self) -> str:
        """Return metadata about the current message."""
        raise NotImplementedError

    @cached_property
    def encoding(self) -> str:
        ct, params = parse_content_type_header(self.content_type)
        return params.get('charset', '')

    @property
    def content_type(self) -> str:
        """Return the message content type."""
        ct = self._orig.headers.get('Content-Type', '')
        if not isinstance(ct, str):
            ct = ct.decode()
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
            raw = self._orig.raw
            if getattr(raw, '_original_response', None):
                raw_version = raw._original_response.version
            else:
                raw_version = raw.version
        except AttributeError:
            # Assume HTTP/1.1
            raw_version = 11
        version = {
            9: '0.9',
            10: '1.0',
            11: '1.1',
            20: '2.0',
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
            for header, value in original.headers.items()
            for cookie in split_cookies(value)
            if header == 'Set-Cookie'
        )
        return '\r\n'.join(headers)

    @property
    def metadata(self) -> str:
        data = {}
        time_to_parse_headers = self._orig.elapsed.total_seconds()
        # noinspection PyProtectedMember
        time_since_headers_parsed = monotonic() - self._orig._httpie_headers_parsed_at
        time_elapsed = time_to_parse_headers + time_since_headers_parsed
        # data['Headers time'] = str(round(time_to_parse_headers, 5)) + 's'
        # data['Body time'] = str(round(time_since_headers_parsed, 5)) + 's'
        data[ELAPSED_TIME_LABEL] = str(round(time_elapsed, 10)) + 's'
        return '\n'.join(
            f'{key}: {value}'
            for key, value in data.items()
        )


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

        headers = self._orig.headers.copy()
        if 'Host' not in self._orig.headers:
            headers['Host'] = url.netloc.split('@')[-1]

        headers = [
            f'{name}: {value if isinstance(value, str) else value.decode()}'
            for name, value in headers.items()
        ]

        headers.insert(0, request_line)
        headers = '\r\n'.join(headers).strip()
        return headers

    @property
    def body(self):
        body = self._orig.body
        if isinstance(body, str):
            # Happens with JSON/form request data parsed from the command line.
            body = body.encode()
        return body or b''


RequestsMessage = Union[requests.PreparedRequest, requests.Response]


class RequestsMessageKind(Enum):
    REQUEST = auto()
    RESPONSE = auto()


def infer_requests_message_kind(message: RequestsMessage) -> RequestsMessageKind:
    if isinstance(message, requests.PreparedRequest):
        return RequestsMessageKind.REQUEST
    elif isinstance(message, requests.Response):
        return RequestsMessageKind.RESPONSE
    else:
        raise TypeError(f"Unexpected message type: {type(message).__name__}")


OPTION_TO_PARAM = {
    RequestsMessageKind.REQUEST: {
        'headers': OUT_REQ_HEAD,
        'body': OUT_REQ_BODY,
    },
    RequestsMessageKind.RESPONSE: {
        'headers': OUT_RESP_HEAD,
        'body': OUT_RESP_BODY,
        'meta': OUT_RESP_META
    }
}


class OutputOptions(NamedTuple):
    kind: RequestsMessageKind
    headers: bool
    body: bool
    meta: bool = False

    def any(self):
        return (
            self.headers
            or self.body
            or self.meta
        )

    @classmethod
    def from_message(
        cls,
        message: RequestsMessage,
        raw_args: str = '',
        **kwargs
    ):
        kind = infer_requests_message_kind(message)

        options = {
            option: param in raw_args
            for option, param in OPTION_TO_PARAM[kind].items()
        }
        options.update(kwargs)

        return cls(
            kind=kind,
            **options
        )
