import argparse
from itertools import chain
from typing import Callable, IO, Iterable, TextIO, Tuple, Type, Union

import requests

from httpie.cli.constants import (
    OUT_REQ_BODY, OUT_REQ_HEAD, OUT_RESP_BODY, OUT_RESP_HEAD,
)
from httpie.context import Environment
from httpie.models import HTTPMessage, HTTPRequest, HTTPResponse
from httpie.output.processing import Conversion, Formatting


BINARY_SUPPRESSED_NOTICE = (
    b'\n'
    b'+-----------------------------------------+\n'
    b'| NOTE: binary data not shown in terminal |\n'
    b'+-----------------------------------------+'
)


class BinarySuppressedError(Exception):
    """An error indicating that the body is binary and won't be written,
     e.g., for terminal output)."""

    message = BINARY_SUPPRESSED_NOTICE


def write_stream(
    stream: 'BaseStream',
    outfile: Union[IO, TextIO],
    flush: bool
):
    """Write the output stream."""
    try:
        # Writing bytes so we use the buffer interface (Python 3).
        buf = outfile.buffer
    except AttributeError:
        buf = outfile

    for chunk in stream:
        buf.write(chunk)
        if flush:
            outfile.flush()


def write_stream_with_colors_win_py3(
    stream: 'BaseStream',
    outfile: TextIO,
    flush: bool
):
    """Like `write`, but colorized chunks are written as text
    directly to `outfile` to ensure it gets processed by colorama.
    Applies only to Windows with Python 3 and colorized terminal output.

    """
    color = b'\x1b['
    encoding = outfile.encoding
    for chunk in stream:
        if color in chunk:
            outfile.write(chunk.decode(encoding))
        else:
            outfile.buffer.write(chunk)
        if flush:
            outfile.flush()


def build_output_stream(
    args: argparse.Namespace,
    env: Environment,
    request: requests.Request,
    response: requests.Response,
    output_options: str
) -> Iterable[bytes]:
    """Build and return a chain of iterators over the `request`-`response`
    exchange each of which yields `bytes` chunks.

    """
    req_h = OUT_REQ_HEAD in output_options
    req_b = OUT_REQ_BODY in output_options
    resp_h = OUT_RESP_HEAD in output_options
    resp_b = OUT_RESP_BODY in output_options
    req = req_h or req_b
    resp = resp_h or resp_b

    output = []
    stream_class, stream_kwargs = get_stream_type_and_kwargs(
        env=env, args=args)

    if req:
        output.append(
            stream_class(
                msg=HTTPRequest(request),
                with_headers=req_h,
                with_body=req_b,
                **stream_kwargs,
            )
        )

    if req_b and resp:
        # Request/Response separator.
        output.append([b'\n\n'])

    if resp:
        output.append(
            stream_class(
                msg=HTTPResponse(response),
                with_headers=resp_h,
                with_body=resp_b,
                **stream_kwargs,
            )
        )

    if env.stdout_isatty and resp_b:
        # Ensure a blank line after the response body.
        # For terminal output only.
        output.append([b'\n\n'])

    return chain(*output)


def get_stream_type_and_kwargs(
    env: Environment,
    args: argparse.Namespace
) -> Tuple[Type['BaseStream'], dict]:
    """Pick the right stream type and kwargs for it based on `env` and `args`.

    """
    if not env.stdout_isatty and not args.prettify:
        stream_class = RawStream
        stream_kwargs = {
            'chunk_size': (
                RawStream.CHUNK_SIZE_BY_LINE
                if args.stream
                else RawStream.CHUNK_SIZE
            )
        }
    elif args.prettify:
        stream_class = PrettyStream if args.stream else BufferedPrettyStream
        stream_kwargs = {
            'env': env,
            'conversion': Conversion(),
            'formatting': Formatting(
                env=env,
                groups=args.prettify,
                color_scheme=args.style,
                explicit_json=args.json,
            )
        }
    else:
        stream_class = EncodedStream
        stream_kwargs = {
            'env': env
        }

    return stream_class, stream_kwargs


class BaseStream:
    """Base HTTP message output stream class."""

    def __init__(
        self,
        msg: HTTPMessage,
        with_headers=True, with_body=True,
        on_body_chunk_downloaded: Callable[[bytes], None] = None
    ):
        """
        :param msg: a :class:`models.HTTPMessage` subclass
        :param with_headers: if `True`, headers will be included
        :param with_body: if `True`, body will be included

        """
        assert with_headers or with_body
        self.msg = msg
        self.with_headers = with_headers
        self.with_body = with_body
        self.on_body_chunk_downloaded = on_body_chunk_downloaded

    def get_headers(self) -> bytes:
        """Return the headers' bytes."""
        return self.msg.headers.encode('utf8')

    def iter_body(self) -> Iterable[bytes]:
        """Return an iterator over the message body."""
        raise NotImplementedError()

    def __iter__(self) -> Iterable[bytes]:
        """Return an iterator over `self.msg`."""
        if self.with_headers:
            yield self.get_headers()
            yield b'\r\n\r\n'

        if self.with_body:
            try:
                for chunk in self.iter_body():
                    yield chunk
                    if self.on_body_chunk_downloaded:
                        self.on_body_chunk_downloaded(chunk)
            except BinarySuppressedError as e:
                if self.with_headers:
                    yield b'\n'
                yield e.message


class RawStream(BaseStream):
    """The message is streamed in chunks with no processing."""

    CHUNK_SIZE = 1024 * 100
    CHUNK_SIZE_BY_LINE = 1

    def __init__(self, chunk_size=CHUNK_SIZE, **kwargs):
        super().__init__(**kwargs)
        self.chunk_size = chunk_size

    def iter_body(self) -> Iterable[bytes]:
        return self.msg.iter_body(self.chunk_size)


class EncodedStream(BaseStream):
    """Encoded HTTP message stream.

    The message bytes are converted to an encoding suitable for
    `self.env.stdout`. Unicode errors are replaced and binary data
    is suppressed. The body is always streamed by line.

    """
    CHUNK_SIZE = 1

    def __init__(self, env=Environment(), **kwargs):
        super().__init__(**kwargs)
        if env.stdout_isatty:
            # Use the encoding supported by the terminal.
            output_encoding = env.stdout_encoding
        else:
            # Preserve the message encoding.
            output_encoding = self.msg.encoding
        # Default to utf8 when unsure.
        self.output_encoding = output_encoding or 'utf8'

    def iter_body(self) -> Iterable[bytes]:
        for line, lf in self.msg.iter_lines(self.CHUNK_SIZE):
            if b'\0' in line:
                raise BinarySuppressedError()
            yield line.decode(self.msg.encoding) \
                      .encode(self.output_encoding, 'replace') + lf


class PrettyStream(EncodedStream):
    """In addition to :class:`EncodedStream` behaviour, this stream applies
    content processing.

    Useful for long-lived HTTP responses that stream by lines
    such as the Twitter streaming API.

    """

    CHUNK_SIZE = 1

    def __init__(
        self, conversion: Conversion,
        formatting: Formatting,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.formatting = formatting
        self.conversion = conversion
        self.mime = self.msg.content_type.split(';')[0]

    def get_headers(self) -> bytes:
        return self.formatting.format_headers(
            self.msg.headers).encode(self.output_encoding)

    def iter_body(self) -> Iterable[bytes]:
        first_chunk = True
        iter_lines = self.msg.iter_lines(self.CHUNK_SIZE)
        for line, lf in iter_lines:
            if b'\0' in line:
                if first_chunk:
                    converter = self.conversion.get_converter(self.mime)
                    if converter:
                        body = bytearray()
                        # noinspection PyAssignmentToLoopOrWithParameter
                        for line, lf in chain([(line, lf)], iter_lines):
                            body.extend(line)
                            body.extend(lf)
                        self.mime, body = converter.convert(body)
                        assert isinstance(body, str)
                        yield self.process_body(body)
                        return
                raise BinarySuppressedError()
            yield self.process_body(line) + lf
            first_chunk = False

    def process_body(self, chunk: Union[str, bytes]) -> bytes:
        if not isinstance(chunk, str):
            # Text when a converter has been used,
            # otherwise it will always be bytes.
            chunk = chunk.decode(self.msg.encoding, 'replace')
        chunk = self.formatting.format_body(content=chunk, mime=self.mime)
        return chunk.encode(self.output_encoding, 'replace')


class BufferedPrettyStream(PrettyStream):
    """The same as :class:`PrettyStream` except that the body is fully
    fetched before it's processed.

    Suitable regular HTTP responses.

    """

    CHUNK_SIZE = 1024 * 10

    def iter_body(self) -> Iterable[bytes]:
        # Read the whole body before prettifying it,
        # but bail out immediately if the body is binary.
        converter = None
        body = bytearray()

        for chunk in self.msg.iter_body(self.CHUNK_SIZE):
            if not converter and b'\0' in chunk:
                converter = self.conversion.get_converter(self.mime)
                if not converter:
                    raise BinarySuppressedError()
            body.extend(chunk)

        if converter:
            self.mime, body = converter.convert(body)

        yield self.process_body(body)
