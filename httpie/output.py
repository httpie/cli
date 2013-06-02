"""Output streaming, processing and formatting.

"""
import json
import xml.dom.minidom
from functools import partial
from itertools import chain

import pygments
from pygments import token, lexer
from pygments.styles import get_style_by_name, STYLE_MAP
from pygments.lexers import get_lexer_for_mimetype, get_lexer_by_name
from pygments.formatters.terminal import TerminalFormatter
from pygments.formatters.terminal256 import Terminal256Formatter
from pygments.util import ClassNotFound

from .compat import is_windows
from .solarized import Solarized256Style
from .models import HTTPRequest, HTTPResponse, Environment
from .input import (OUT_REQ_BODY, OUT_REQ_HEAD,
                    OUT_RESP_HEAD, OUT_RESP_BODY)


# The default number of spaces to indent when pretty printing
DEFAULT_INDENT = 4

# Colors on Windows via colorama don't look that
# great and fruity seems to give the best result there.
AVAILABLE_STYLES = set(STYLE_MAP.keys())
AVAILABLE_STYLES.add('solarized')
DEFAULT_STYLE = 'solarized' if not is_windows else 'fruity'


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


###############################################################################
# Output Streams
###############################################################################


def write(stream, outfile, flush):
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


def write_with_colors_win_py3(stream, outfile, flush):
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


def build_output_stream(args, env, request, response):
    """Build and return a chain of iterators over the `request`-`response`
    exchange each of which yields `bytes` chunks.

    """

    req_h = OUT_REQ_HEAD in args.output_options
    req_b = OUT_REQ_BODY in args.output_options
    resp_h = OUT_RESP_HEAD in args.output_options
    resp_b = OUT_RESP_BODY in args.output_options
    req = req_h or req_b
    resp = resp_h or resp_b

    output = []
    Stream = get_stream_type(env, args)

    if req:
        output.append(Stream(
            msg=HTTPRequest(request),
            with_headers=req_h,
            with_body=req_b))

    if req_b and resp:
        # Request/Response separator.
        output.append([b'\n\n'])

    if resp:
        output.append(Stream(
            msg=HTTPResponse(response),
            with_headers=resp_h,
            with_body=resp_b))

    if env.stdout_isatty and resp_b:
        # Ensure a blank line after the response body.
        # For terminal output only.
        output.append([b'\n\n'])

    return chain(*output)


def get_stream_type(env, args):
    """Pick the right stream type based on `env` and `args`.
    Wrap it in a partial with the type-specific args so that
    we don't need to think what stream we are dealing with.

    """
    if not env.stdout_isatty and not args.prettify:
        Stream = partial(
            RawStream,
            chunk_size=RawStream.CHUNK_SIZE_BY_LINE
                       if args.stream
                       else RawStream.CHUNK_SIZE
        )
    elif args.prettify:
        Stream = partial(
            PrettyStream if args.stream else BufferedPrettyStream,
            env=env,
            processor=OutputProcessor(
                env=env, groups=args.prettify, pygments_style=args.style),
        )
    else:
        Stream = partial(EncodedStream, env=env)

    return Stream


class BaseStream(object):
    """Base HTTP message output stream class."""

    def __init__(self, msg, with_headers=True, with_body=True,
                 on_body_chunk_downloaded=None):
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

    def _get_headers(self):
        """Return the headers' bytes."""
        return self.msg.headers.encode('ascii')

    def _iter_body(self):
        """Return an iterator over the message body."""
        raise NotImplementedError()

    def __iter__(self):
        """Return an iterator over `self.msg`."""
        if self.with_headers:
            yield self._get_headers()
            yield b'\r\n\r\n'

        if self.with_body:
            try:
                for chunk in self._iter_body():
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
        super(RawStream, self).__init__(**kwargs)
        self.chunk_size = chunk_size

    def _iter_body(self):
        return self.msg.iter_body(self.chunk_size)


class EncodedStream(BaseStream):
    """Encoded HTTP message stream.

    The message bytes are converted to an encoding suitable for
    `self.env.stdout`. Unicode errors are replaced and binary data
    is suppressed. The body is always streamed by line.

    """
    CHUNK_SIZE = 1

    def __init__(self, env=Environment(), **kwargs):

        super(EncodedStream, self).__init__(**kwargs)

        if env.stdout_isatty:
            # Use the encoding supported by the terminal.
            output_encoding = getattr(env.stdout, 'encoding', None)
        else:
            # Preserve the message encoding.
            output_encoding = self.msg.encoding

        # Default to utf8 when unsure.
        self.output_encoding = output_encoding or 'utf8'

    def _iter_body(self):

        for line, lf in self.msg.iter_lines(self.CHUNK_SIZE):

            if b'\0' in line:
                raise BinarySuppressedError()

            yield line.decode(self.msg.encoding)\
                      .encode(self.output_encoding, 'replace') + lf


class PrettyStream(EncodedStream):
    """In addition to :class:`EncodedStream` behaviour, this stream applies
    content processing.

    Useful for long-lived HTTP responses that stream by lines
    such as the Twitter streaming API.

    """

    CHUNK_SIZE = 1

    def __init__(self, processor, **kwargs):
        super(PrettyStream, self).__init__(**kwargs)
        self.processor = processor

    def _get_headers(self):
        return self.processor.process_headers(
            self.msg.headers).encode(self.output_encoding)

    def _iter_body(self):
        for line, lf in self.msg.iter_lines(self.CHUNK_SIZE):
            if b'\0' in line:
                raise BinarySuppressedError()
            yield self._process_body(line) + lf

    def _process_body(self, chunk):
        return (self.processor
                    .process_body(
                        content=chunk.decode(self.msg.encoding, 'replace'),
                        content_type=self.msg.content_type,
                        encoding=self.msg.encoding)
                    .encode(self.output_encoding, 'replace'))


class BufferedPrettyStream(PrettyStream):
    """The same as :class:`PrettyStream` except that the body is fully
    fetched before it's processed.

    Suitable regular HTTP responses.

    """

    CHUNK_SIZE = 1024 * 10

    def _iter_body(self):

        # Read the whole body before prettifying it,
        # but bail out immediately if the body is binary.
        body = bytearray()
        for chunk in self.msg.iter_body(self.CHUNK_SIZE):
            if b'\0' in chunk:
                raise BinarySuppressedError()
            body.extend(chunk)

        yield self._process_body(body)


###############################################################################
# Processing
###############################################################################

class HTTPLexer(lexer.RegexLexer):
    """Simplified HTTP lexer for Pygments.

    It only operates on headers and provides a stronger contrast between
    their names and values than the original one bundled with Pygments
    (:class:`pygments.lexers.text import HttpLexer`), especially when
    Solarized color scheme is used.

    """
    name = 'HTTP'
    aliases = ['http']
    filenames = ['*.http']
    tokens = {
        'root': [
            # Request-Line
            (r'([A-Z]+)( +)([^ ]+)( +)(HTTP)(/)(\d+\.\d+)',
             lexer.bygroups(
                 token.Name.Function,
                 token.Text,
                 token.Name.Namespace,
                 token.Text,
                 token.Keyword.Reserved,
                 token.Operator,
                 token.Number
             )),
            # Response Status-Line
            (r'(HTTP)(/)(\d+\.\d+)( +)(\d{3})( +)(.+)',
             lexer.bygroups(
                 token.Keyword.Reserved,  # 'HTTP'
                 token.Operator,  # '/'
                 token.Number,  # Version
                 token.Text,
                 token.Number,  # Status code
                 token.Text,
                 token.Name.Exception,  # Reason
             )),
            # Header
            (r'(.*?)( *)(:)( *)(.+)', lexer.bygroups(
                token.Name.Attribute,  # Name
                token.Text,
                token.Operator,  # Colon
                token.Text,
                token.String  # Value
            ))
        ]
    }


class BaseProcessor(object):
    """Base, noop output processor class."""

    enabled = True

    def __init__(self, env=Environment(), **kwargs):
        """
        :param env: an class:`Environment` instance
        :param kwargs: additional keyword argument that some
                       processor might require.

        """
        self.env = env
        self.kwargs = kwargs

    def process_headers(self, headers):
        """Return processed `headers`

        :param headers: The headers as text.

        """
        return headers

    def process_body(self, content, content_type, subtype, encoding):
        """Return processed `content`.

        :param content: The body content as text
        :param content_type: Full content type, e.g., 'application/atom+xml'.
        :param subtype: E.g. 'xml'.
        :param encoding: The original content encoding.

        """
        return content


class JSONProcessor(BaseProcessor):
    """JSON body processor."""

    def process_body(self, content, content_type, subtype, encoding):
        if subtype == 'json':
            try:
                # Indent the JSON data, sort keys by name, and
                # avoid unicode escapes to improve readability.
                content = json.dumps(json.loads(content),
                                     sort_keys=True,
                                     ensure_ascii=False,
                                     indent=DEFAULT_INDENT)
            except ValueError:
                # Invalid JSON but we don't care.
                pass
        return content


class XMLProcessor(BaseProcessor):
    """XML body processor."""
    # TODO: tests

    def process_body(self, content, content_type, subtype, encoding):
        if subtype == 'xml':
            try:
                # Pretty print the XML
                doc = xml.dom.minidom.parseString(content.encode(encoding))
                content = doc.toprettyxml(indent=' ' * DEFAULT_INDENT)
            except xml.parsers.expat.ExpatError:
                # Ignore invalid XML errors (skips attempting to pretty print)
                pass
        return content


class PygmentsProcessor(BaseProcessor):
    """A processor that applies syntax-highlighting using Pygments
    to the headers, and to the body as well if its content type is recognized.

    """
    def __init__(self, *args, **kwargs):
        super(PygmentsProcessor, self).__init__(*args, **kwargs)

        # Cache that speeds up when we process streamed body by line.
        self.lexers_by_type = {}

        if not self.env.colors:
            self.enabled = False
            return

        try:
            style = get_style_by_name(
                self.kwargs.get('pygments_style', DEFAULT_STYLE))
        except ClassNotFound:
            style = Solarized256Style

        if self.env.is_windows or self.env.colors == 256:
            fmt_class = Terminal256Formatter
        else:
            fmt_class = TerminalFormatter
        self.formatter = fmt_class(style=style)

    def process_headers(self, headers):
        return pygments.highlight(
            headers, HTTPLexer(), self.formatter).strip()

    def process_body(self, content, content_type, subtype, encoding):
        try:
            lexer = self.lexers_by_type.get(content_type)
            if not lexer:
                try:
                    lexer = get_lexer_for_mimetype(content_type)
                except ClassNotFound:
                    lexer = get_lexer_by_name(subtype)
                self.lexers_by_type[content_type] = lexer
        except ClassNotFound:
            pass
        else:
            content = pygments.highlight(content, lexer, self.formatter)
        return content.strip()


class HeadersProcessor(BaseProcessor):
    """Sorts headers by name retaining relative order of multiple headers
    with the same name.

    """
    def process_headers(self, headers):
        lines = headers.splitlines()
        headers = sorted(lines[1:], key=lambda h: h.split(':')[0])
        return '\r\n'.join(lines[:1] + headers)


class OutputProcessor(object):
    """A delegate class that invokes the actual processors."""

    installed_processors = {
        'format': [
            HeadersProcessor,
            JSONProcessor,
            XMLProcessor
        ],
        'colors': [
            PygmentsProcessor
        ]
    }

    def __init__(self, groups, env=Environment(), **kwargs):
        """
        :param env: a :class:`models.Environment` instance
        :param groups: the groups of processors to be applied
        :param kwargs: additional keyword arguments for processors

        """
        self.processors = []
        for group in groups:
            for cls in self.installed_processors[group]:
                processor = cls(env, **kwargs)
                if processor.enabled:
                    self.processors.append(processor)

    def process_headers(self, headers):
        for processor in self.processors:
            headers = processor.process_headers(headers)
        return headers

    def process_body(self, content, content_type, encoding):
        # e.g., 'application/atom+xml'
        content_type = content_type.split(';')[0]
        # e.g., 'xml'
        subtype = content_type.split('/')[-1].split('+')[-1]

        for processor in self.processors:
            content = processor.process_body(
                content,
                content_type,
                subtype,
                encoding
            )

        return content
