from abc import ABCMeta, abstractmethod
from itertools import chain
from typing import Any, Callable, Iterable, Tuple, Union

from ..cli.constants import EMPTY_FORMAT_OPTION
from ..codec import TextDecoderStrategy
from ..context import Environment
from ..constants import UTF8
from ..models import HTTPMessage, HTTPResponse
from .processing import Conversion, Formatting
from .utils import parse_header_content_type

BINARY_SUPPRESSED_NOTICE = (
    b'\n'
    b'+-----------------------------------------+\n'
    b'| NOTE: binary data not shown in terminal |\n'
    b'+-----------------------------------------+'
)


class DataSuppressedError(Exception):
    message = None


class BinarySuppressedError(DataSuppressedError):
    """An error indicating that the body is binary and won't be written,
     e.g., for terminal output)."""
    message = BINARY_SUPPRESSED_NOTICE


class BaseStream(metaclass=ABCMeta):
    """Base HTTP message output stream class."""

    def __init__(
        self,
        msg: HTTPMessage,
        with_headers=True,
        with_body=True,
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
        return self.msg.headers.encode()

    @abstractmethod
    def iter_body(self) -> Iterable[bytes]:
        """Return an iterator over the message body."""

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
            except DataSuppressedError as e:
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
        # Default to UTF-8 when unsure.
        self.output_encoding = output_encoding or UTF8

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
        self.mime, mime_options = self._get_mime_and_options()
        self.charset = mime_options.get('charset') or ''

    def _get_mime_and_options(self) -> Tuple[str, dict[str, Any]]:
        # Defaults from the message `Content-Type`.
        mime, options = parse_header_content_type(self.msg.content_type)
        if not isinstance(self.msg, HTTPResponse):
            return mime, options

        # The response `Content-Type` could be overridden from the CLI.
        forced_content_type = self.formatting.options['response']['as']
        if forced_content_type == EMPTY_FORMAT_OPTION:
            return mime, options

        forced_mime, forced_options = parse_header_content_type(forced_content_type)
        return (forced_mime or mime, forced_options or options)

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

        # Decode the body using the most appropriate encoding.
        # This is a no-op if it is already a string (likely altered by a converter).
        body = TextDecoderStrategy(self.charset).decode(body)

        yield self.process_body(body)
