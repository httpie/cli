import argparse
import os
import platform
import sys
import socket
from typing import List, Optional, Union, Callable

import niquests
from pygments import __version__ as pygments_version
from niquests import __version__ as requests_version

from . import __version__ as httpie_version
from .cli.argparser import HTTPieArgumentParser
from .cli.constants import OUT_REQ_BODY
from .cli.nested_json import NestedJSONSyntaxError
from .client import collect_messages
from .context import Environment, LogLevel
from .downloads import Downloader
from .models import (
    RequestsMessageKind,
    OutputOptions
)
from .output.models import ProcessingOptions
from .output.writer import write_message, write_stream, write_raw_data, MESSAGE_SEPARATOR_BYTES
from .plugins.registry import plugin_manager
from .status import ExitStatus, http_status_to_exit_status
from .utils import unwrap_context
from .internal.update_warnings import check_updates
from .internal.daemon_runner import is_daemon_mode, run_daemon_task


# noinspection PyDefaultArgument
def raw_main(
    parser: HTTPieArgumentParser,
    main_program: Callable[[argparse.Namespace, Environment], ExitStatus],
    args: List[Union[str, bytes]] = sys.argv,
    env: Environment = Environment(),
    use_default_options: bool = True,
) -> ExitStatus:
    program_name, *args = args
    env.program_name = os.path.basename(program_name)
    args = decode_raw_args(args, env.stdin_encoding)

    if is_daemon_mode(args):
        return run_daemon_task(env, args)

    plugin_manager.load_installed_plugins(env.config.plugins_dir)

    if use_default_options and env.config.default_options:
        args = env.config.default_options + args

    include_debug_info = '--debug' in args
    include_traceback = include_debug_info or '--traceback' in args

    def handle_generic_error(e, annotation=None):
        msg = str(e)
        if hasattr(e, 'request'):
            request = e.request
            if hasattr(request, 'url'):
                msg = (
                    f'{msg} while doing a {request.method}'
                    f' request to URL: {request.url}'
                )
        if annotation:
            msg += annotation
        env.log_error(f'{type(e).__name__}: {msg}')
        if include_traceback:
            raise

    if include_debug_info:
        print_debug_info(env)
        if args == ['--debug']:
            return ExitStatus.SUCCESS

    exit_status = ExitStatus.SUCCESS

    try:
        parsed_args = parser.parse_args(
            args=args,
            env=env,
        )
    except NestedJSONSyntaxError as exc:
        env.stderr.write(str(exc) + "\n")
        if include_traceback:
            raise
        exit_status = ExitStatus.ERROR
    except KeyboardInterrupt:
        env.stderr.write('\n')
        if include_traceback:
            raise
        exit_status = ExitStatus.ERROR_CTRL_C
    except SystemExit as e:
        if e.code != ExitStatus.SUCCESS:
            env.stderr.write('\n')
            if include_traceback:
                raise
            exit_status = ExitStatus.ERROR
    else:
        check_updates(env)
        try:
            exit_status = main_program(parsed_args, env)
        except KeyboardInterrupt:
            env.stderr.write('\n')
            if include_traceback:
                raise
            exit_status = ExitStatus.ERROR_CTRL_C
        except SystemExit as e:
            if e.code != ExitStatus.SUCCESS:
                env.stderr.write('\n')
                if include_traceback:
                    raise
                exit_status = ExitStatus.ERROR
        except niquests.Timeout:
            exit_status = ExitStatus.ERROR_TIMEOUT
            # this detects if we tried to connect with HTTP/3 when the remote isn't compatible anymore.
            if hasattr(parsed_args, "_failsafe_http3"):
                env.log_error(
                    f'Unable to connect. Was the remote specified HTTP/3 compatible but is not anymore? '
                    f'Remove "{env.config.quic_file}" to clear it out. Or set --disable-http3 flag.'
                )
            else:
                env.log_error(f'Request timed out ({parsed_args.timeout}s).')
        except niquests.TooManyRedirects:
            exit_status = ExitStatus.ERROR_TOO_MANY_REDIRECTS
            env.log_error(
                f'Too many redirects'
                f' (--max-redirects={parsed_args.max_redirects}).'
            )
        except niquests.exceptions.ConnectionError as exc:
            annotation = None
            original_exc = unwrap_context(exc)
            if isinstance(original_exc, socket.gaierror):
                if original_exc.errno == socket.EAI_AGAIN:
                    annotation = '\nCouldn’t connect to a DNS server. Please check your connection and try again.'
                elif original_exc.errno == socket.EAI_NONAME:
                    annotation = '\nCouldn’t resolve the given hostname. Please check the URL and try again.'
                propagated_exc = original_exc
            else:
                propagated_exc = exc

            handle_generic_error(propagated_exc, annotation=annotation)
            exit_status = ExitStatus.ERROR
        except Exception as e:
            # TODO: Further distinction between expected and unexpected errors.
            handle_generic_error(e)
            exit_status = ExitStatus.ERROR

    return exit_status


# noinspection PyDefaultArgument
def main(
    args: List[Union[str, bytes]] = sys.argv,
    env: Environment = Environment()
) -> ExitStatus:
    """
    The main function.

    Pre-process args, handle some special types of invocations,
    and run the main program with error handling.

    Return exit status code.

    """

    from .cli.definition import parser

    return raw_main(
        parser=parser,
        main_program=program,
        args=args,
        env=env
    )


def program(args: argparse.Namespace, env: Environment) -> ExitStatus:
    """
    The main program without error handling.

    """
    # TODO: Refactor and drastically simplify, especially so that the separator logic is elsewhere.
    exit_status = ExitStatus.SUCCESS
    downloader = None
    initial_request: Optional[niquests.PreparedRequest] = None
    final_response: Optional[niquests.Response] = None
    processing_options = ProcessingOptions.from_raw_args(args)

    def separate():
        getattr(env.stdout, 'buffer', env.stdout).write(MESSAGE_SEPARATOR_BYTES)

    def request_body_read_callback(chunk: bytes):
        should_pipe_to_stdout = bool(
            # Request body output desired
            OUT_REQ_BODY in args.output_options
            # & not `.read()` already pre-request (e.g., for  compression)
            and initial_request
            # & non-EOF chunk
            and chunk
        )
        if should_pipe_to_stdout:
            return write_raw_data(
                env,
                chunk,
                processing_options=processing_options,
                headers=initial_request.headers
            )

    try:
        if args.download:
            args.follow = True  # --download implies --follow.
            downloader = Downloader(env, output_file=args.output_file, resume=args.download_resume)
            downloader.pre_request(args.headers)

        def prepared_request_readiness(pr):
            """This callback is meant to output the request part. It is triggered by
            the underlying Niquests library just after establishing the connection."""

            oo = OutputOptions.from_message(
                pr,
                args.output_options
            )

            oo = oo._replace(
                body=isinstance(pr.body, (str, bytes)) and (args.verbose or oo.body)
            )

            write_message(
                requests_message=pr,
                env=env,
                output_options=oo,
                processing_options=processing_options
            )

            if oo.body > 1:
                separate()

        messages = collect_messages(
            env,
            args=args,
            request_body_read_callback=request_body_read_callback,
            prepared_request_readiness=prepared_request_readiness
        )

        force_separator = False
        prev_with_body = False

        # Process messages as they’re generated
        for message in messages:
            output_options = OutputOptions.from_message(message, args.output_options)

            do_write_body = output_options.body
            if prev_with_body and output_options.any() and (force_separator or not env.stdout_isatty):
                # Separate after a previous message with body, if needed. See test_tokens.py.
                separate()
            force_separator = False
            if output_options.kind is RequestsMessageKind.REQUEST:
                if not initial_request:
                    initial_request = message
                if output_options.body:
                    is_streamed_upload = not isinstance(message.body, (str, bytes))
                    do_write_body = not is_streamed_upload
                    force_separator = is_streamed_upload and env.stdout_isatty
                # We're in a REQUEST message, we rather output the message
                # in prepared_request_readiness because we want "message.conn_info"
                # to be set appropriately. (e.g. know about HTTP protocol version, etc...)
                if message.conn_info is None and not args.offline:
                    # bellow variable will be accessed by prepared_request_readiness just after.
                    prev_with_body = output_options.body
                    continue
            else:
                final_response = message
                if args.check_status or downloader:
                    exit_status = http_status_to_exit_status(http_status=message.status_code, follow=args.follow)
                    if exit_status != ExitStatus.SUCCESS and (not env.stdout_isatty or args.quiet == 1):
                        env.log_error(f'HTTP {message.raw.status} {message.raw.reason}', level=LogLevel.WARNING)
            write_message(
                requests_message=message,
                env=env,
                output_options=output_options._replace(
                    body=do_write_body
                ),
                processing_options=processing_options
            )
            prev_with_body = output_options.body

        # Cleanup
        if force_separator:
            separate()
        if downloader and exit_status == ExitStatus.SUCCESS:
            # Last response body download.
            download_stream, download_to = downloader.start(
                initial_url=initial_request.url,
                final_response=final_response,
            )
            write_stream(stream=download_stream, outfile=download_to, flush=False)
            downloader.finish()
            if downloader.is_interrupted:
                exit_status = ExitStatus.ERROR
                env.log_error(
                    f'Incomplete download: size={downloader.status.total_size};'
                    f' downloaded={downloader.status.downloaded}'
                )
        return exit_status

    finally:
        if args.data and hasattr(args.data, "close"):
            args.data.close()
        if args.files and hasattr(args.files, "items"):
            for fd in args.files.items():
                fd[1][1].close()
        if downloader and not downloader.finished:
            downloader.failed()
        if args.output_file and args.output_file_specified:
            args.output_file.close()


def print_debug_info(env: Environment):
    env.stderr.writelines([
        f'HTTPie {httpie_version}\n',
        f'Niquests {requests_version}\n',
        f'Pygments {pygments_version}\n',
        f'Python {sys.version}\n{sys.executable}\n',
        f'{platform.system()} {platform.release()}',
    ])
    env.stderr.write('\n\n')
    env.stderr.write(repr(env))
    env.stderr.write('\n\n')
    env.stderr.write(repr(plugin_manager))
    env.stderr.write('\n')


def decode_raw_args(
    args: List[Union[str, bytes]],
    stdin_encoding: str
) -> List[str]:
    """
    Convert all bytes args to str
    by decoding them using stdin encoding.

    """
    return [
        arg.decode(stdin_encoding)
        if type(arg) is bytes else arg
        for arg in args
    ]
