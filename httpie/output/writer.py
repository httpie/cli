import argparse
import errno
from typing import IO, TextIO, Tuple, Type, Union

from ..cli.dicts import HTTPHeadersDict
from ..context import Environment
from ..models import (
    HTTPRequest,
    HTTPResponse,
    HTTPMessage,
    RequestsMessage,
    RequestsMessageKind,
    OutputOptions
)
from .processing import Conversion, Formatting
from .streams import (
    BaseStream, BufferedPrettyStream, EncodedStream, PrettyStream, RawStream,
)


MESSAGE_SEPARATOR = '\n\n'
MESSAGE_SEPARATOR_BYTES = MESSAGE_SEPARATOR.encode()


def write_message(
    requests_message: RequestsMessage,
    env: Environment,
    args: argparse.Namespace,
    output_options: OutputOptions,
):
    if not output_options.any():
        return
    write_stream_kwargs = {
        'stream': build_output_stream_for_message(
            args=args,
            env=env,
            requests_message=requests_message,
            output_options=output_options,
        ),
        # NOTE: `env.stdout` will in fact be `stderr` with `--download`
        'outfile': env.stdout,
        'flush': env.stdout_isatty or args.stream
    }
    try:
        if env.is_windows and 'colors' in args.prettify:
            write_stream_with_colors_win(**write_stream_kwargs)
        else:
            write_stream(**write_stream_kwargs)
    except OSError as e:
        show_traceback = args.debug or args.traceback
        if not show_traceback and e.errno == errno.EPIPE:
            # Ignore broken pipes unless --traceback.
            env.stderr.write('\n')
        else:
            raise


def write_stream(
    stream: BaseStream,
    outfile: Union[IO, TextIO],
    flush: bool
):
    """Write the output stream."""
    try:
        # Writing bytes so we use the buffer interface.
        buf = outfile.buffer
    except AttributeError:
        buf = outfile

    for chunk in stream:
        buf.write(chunk)
        if flush:
            outfile.flush()


def write_stream_with_colors_win(
    stream: 'BaseStream',
    outfile: TextIO,
    flush: bool
):
    """Like `write`, but colorized chunks are written as text
    directly to `outfile` to ensure it gets processed by colorama.
    Applies only to Windows and colorized terminal output.

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


def build_output_stream_for_message(
    args: argparse.Namespace,
    env: Environment,
    requests_message: RequestsMessage,
    output_options: OutputOptions,
):
    message_type = {
        RequestsMessageKind.REQUEST: HTTPRequest,
        RequestsMessageKind.RESPONSE: HTTPResponse,
    }[output_options.kind]
    stream_class, stream_kwargs = get_stream_type_and_kwargs(
        env=env,
        args=args,
        message_type=message_type,
        headers=requests_message.headers
    )
    yield from stream_class(
        msg=message_type(requests_message),
        output_options=output_options,
        **stream_kwargs,
    )
    if (env.stdout_isatty and output_options.body and not output_options.meta
            and not getattr(requests_message, 'is_body_upload_chunk', False)):
        # Ensure a blank line after the response body.
        # For terminal output only.
        yield MESSAGE_SEPARATOR_BYTES


def get_stream_type_and_kwargs(
    env: Environment,
    args: argparse.Namespace,
    message_type: Type[HTTPMessage],
    headers: HTTPHeadersDict,
) -> Tuple[Type['BaseStream'], dict]:
    """Pick the right stream type and kwargs for it based on `env` and `args`.

    """
    is_stream = args.stream
    if not is_stream and message_type is HTTPResponse:
        # If this is a response, then check the headers for determining
        # auto-streaming.
        is_stream = headers.get('Content-Type') == 'text/event-stream'

    if not env.stdout_isatty and not args.prettify:
        stream_class = RawStream
        stream_kwargs = {
            'chunk_size': (
                RawStream.CHUNK_SIZE_BY_LINE
                if is_stream
                else RawStream.CHUNK_SIZE
            )
        }
    else:
        stream_class = EncodedStream
        stream_kwargs = {
            'env': env,
        }
        if message_type is HTTPResponse:
            stream_kwargs.update({
                'mime_overwrite': args.response_mime,
                'encoding_overwrite': args.response_charset,
            })
        if args.prettify:
            stream_class = PrettyStream if is_stream else BufferedPrettyStream
            stream_kwargs.update({
                'conversion': Conversion(),
                'formatting': Formatting(
                    env=env,
                    groups=args.prettify,
                    color_scheme=args.style,
                    explicit_json=args.json,
                    format_options=args.format_options,
                )
            })

    return stream_class, stream_kwargs
