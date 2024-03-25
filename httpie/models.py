from time import monotonic

import niquests

from kiss_headers.utils import prettify_header_name

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
from .compat import urllib3, SKIP_HEADER, SKIPPABLE_HEADERS, cached_property
from .utils import split_cookies, parse_content_type_header

ELAPSED_TIME_LABEL = 'Elapsed time'
ELAPSED_DNS_RESOLUTION_LABEL = 'Elapsed DNS'
ELAPSED_TLS_HANDSHAKE = 'Elapsed TLS handshake'
ELAPSED_REQUEST_SEND = 'Elapsed emitting request'
ELAPSED_ESTABLISH_CONN = 'Elapsed established connection'


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
    """A :class:`niquests.models.Response` wrapper."""

    def iter_body(self, chunk_size=1):
        return self._orig.iter_content(chunk_size=chunk_size)

    def iter_lines(self, chunk_size):
        return ((line, b'\n') for line in self._orig.iter_lines(chunk_size))

    @property
    def headers(self):
        original = self._orig
        http_headers = original.raw.headers if original.raw and hasattr(original.raw, "headers") else original.headers
        status_line = f'HTTP/{self.version} {original.status_code} {original.reason}'
        headers = [status_line]
        headers.extend(
            ': '.join([prettify_header_name(header), value])
            for header, value in http_headers.items()
            if header.lower() != 'set-cookie'
        )
        headers.extend(
            f'Set-Cookie: {cookie}'
            for header, value in http_headers.items()
            for cookie in split_cookies(value)
            if header.lower() == 'set-cookie'
        )
        return '\r\n'.join(headers)

    @property
    def metadata(self) -> str:
        data = {}
        time_to_parse_headers = self._orig.elapsed.total_seconds()

        # noinspection PyProtectedMember
        time_since_headers_parsed = monotonic() - self._orig._httpie_headers_parsed_at
        time_elapsed = time_to_parse_headers + time_since_headers_parsed

        # metrics aren't guaranteed to be there. act with caution.
        # see https://niquests.readthedocs.io/en/latest/user/advanced.html#event-hooks for more.
        if hasattr(self._orig, "conn_info") and self._orig.conn_info:
            if self._orig.conn_info.resolution_latency is not None:
                if self._orig.conn_info.resolution_latency:
                    data[ELAPSED_DNS_RESOLUTION_LABEL] = f"{round(self._orig.conn_info.resolution_latency.total_seconds(), 10):6f}s"
                else:
                    data[ELAPSED_DNS_RESOLUTION_LABEL] = "0s"
            if self._orig.conn_info.established_latency is not None:
                if self._orig.conn_info.established_latency:
                    data[ELAPSED_ESTABLISH_CONN] = f"{round(self._orig.conn_info.established_latency.total_seconds(), 10):6f}s"
                else:
                    data[ELAPSED_ESTABLISH_CONN] = "0s"
            if self._orig.conn_info.tls_handshake_latency is not None:
                if self._orig.conn_info.tls_handshake_latency:
                    data[ELAPSED_TLS_HANDSHAKE] = f"{round(self._orig.conn_info.tls_handshake_latency.total_seconds(), 10):6f}s"
                else:
                    data[ELAPSED_TLS_HANDSHAKE] = "0s"
            if self._orig.conn_info.request_sent_latency is not None:
                if self._orig.conn_info.request_sent_latency:
                    data[ELAPSED_REQUEST_SEND] = f"{round(self._orig.conn_info.request_sent_latency.total_seconds(), 10):6f}s"
                else:
                    data[ELAPSED_REQUEST_SEND] = "0s"

        data[ELAPSED_TIME_LABEL] = f"{round(time_elapsed, 10):6f}s"

        return '\n'.join(
            f'{key}: {value}'
            for key, value in data.items()
        )

    @property
    def version(self) -> str:
        """
        Return the HTTP version used by the server, e.g. '1.1'.

        Assume HTTP/1.1 if version is not available.

        """
        return self._orig.conn_info.http_version.value.replace("HTTP/", "").replace(".0", "") if self._orig.conn_info and self._orig.conn_info.http_version else "1.1"


class HTTPRequest(HTTPMessage):
    """A :class:`niquests.models.Request` wrapper."""

    def iter_body(self, chunk_size):
        yield self.body

    def iter_lines(self, chunk_size):
        yield self.body, b''

    @property
    def metadata(self) -> str:
        conn_info: urllib3.ConnectionInfo = self._orig.conn_info

        metadatum = f"Connected to: {conn_info.destination_address[0]} port {conn_info.destination_address[1]}\n"

        if conn_info.certificate_dict:
            metadatum += (
                f"Connection secured using: {conn_info.tls_version.name.replace('_', '.')} with {conn_info.cipher.replace('TLS_', '').replace('_', '-')}\n"
                f"Server certificate: "
            )

            for entry in conn_info.certificate_dict['subject']:
                if len(entry) == 2:
                    rdns, value = entry
                elif len(entry) == 1:
                    rdns, value = entry[0]
                else:
                    continue

                metadatum += f'{rdns}="{value}"; '

            if "subjectAltName" in conn_info.certificate_dict:
                for entry in conn_info.certificate_dict['subjectAltName']:
                    if len(entry) == 2:
                        rdns, value = entry
                        metadatum += f'{rdns}="{value}"; '

            metadatum = metadatum[:-2] + "\n"

            metadatum += f'Certificate validity: "{conn_info.certificate_dict["notBefore"]}" to "{conn_info.certificate_dict["notAfter"]}"\n'

            if "issuer" in conn_info.certificate_dict:
                metadatum += "Issuer: "

                for entry in conn_info.certificate_dict['issuer']:
                    if len(entry) == 2:
                        rdns, value = entry
                    elif len(entry) == 1:
                        rdns, value = entry[0]
                    else:
                        continue

                    metadatum += f'{rdns}="{value}"; '

                metadatum = metadatum[:-2] + "\n"

            if self._orig.ocsp_verified is None:
                metadatum += "Revocation status: Unverified\n"
            elif self._orig.ocsp_verified is True:
                metadatum += "Revocation status: Good\n"

        return metadatum[:-1]

    @property
    def headers(self):
        url = urlsplit(self._orig.url)

        request_line = '{method} {path}{query} {http_version}'.format(
            method=self._orig.method,
            path=url.path or '/',
            query=f'?{url.query}' if url.query else '',
            http_version=self._orig.conn_info.http_version.value.replace(".0", "") if self._orig.conn_info and self._orig.conn_info.http_version else "HTTP/1.1"
        )

        headers = self._orig.headers.copy()
        if 'Host' not in self._orig.headers:
            headers['Host'] = url.netloc.split('@')[-1]

        headers = [
            f'{name}: {value if isinstance(value, str) else value.decode()}'
            for name, value in headers.items()
            if not (name.lower() in SKIPPABLE_HEADERS and value == SKIP_HEADER)
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


RequestsMessage = Union[niquests.PreparedRequest, niquests.Response]


class RequestsMessageKind(Enum):
    REQUEST = auto()
    RESPONSE = auto()


def infer_requests_message_kind(message: RequestsMessage) -> RequestsMessageKind:
    if isinstance(message, niquests.PreparedRequest):
        return RequestsMessageKind.REQUEST
    elif isinstance(message, niquests.Response):
        return RequestsMessageKind.RESPONSE
    else:
        raise TypeError(f"Unexpected message type: {type(message).__name__}")


OPTION_TO_PARAM = {
    RequestsMessageKind.REQUEST: {
        'headers': OUT_REQ_HEAD,
        'body': OUT_REQ_BODY,
        'meta': OUT_RESP_META
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
