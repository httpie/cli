import argparse
import os
import platform
import sys
from typing import List, Optional, Tuple, Union

import requests
from pygments import __version__ as pygments_version
from requests import __version__ as requests_version

from httpie import __version__ as httpie_version
from httpie.cli.constants import (
    OUT_REQ_BODY, OUT_REQ_HEAD, OUT_RESP_BODY,
    OUT_RESP_HEAD,
)
from httpie.client import collect_messages
from httpie.context import Environment
from httpie.downloads import Downloader
from httpie.output.writer import (
    write_message,
    write_stream,
)
from httpie.plugins.registry import plugin_manager
from httpie.status import ExitStatus, http_status_to_exit_status

from httpie.history import EntryNotFound, get_history


# noinspection PyDefaultArgument
def main(
    args: List[Union[str, bytes]] = sys.argv,
    env=Environment(),
) -> ExitStatus:
    """
    The main function.

    Pre-process args, handle some special types of invocations,
    and run the main program with error handling.

    Return exit status code.

    """
    program_name, *args = args
    env.program_name = os.path.basename(program_name)
    args = decode_raw_args(args, env.stdin_encoding)
    plugin_manager.load_installed_plugins()

    from httpie.cli.definition import parser

    if env.config.default_options:
        args = env.config.default_options + args

    include_debug_info = '--debug' in args
    include_traceback = include_debug_info or '--traceback' in args

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
        env.history_enabled = True
        if parsed_args.history is not None:
            if parsed_args.history == 0:
                print_history(env, parsed_args)
                return ExitStatus.SUCCESS
            else:
                history = get_history(env.config.directory, host=parsed_args.headers.get('Host'), url=parsed_args.url)
                args = history.get_entry(parsed_args.history).get_args()
                env.history_enabled = False
                main(args, env)
                return ExitStatus.SUCCESS

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
    except EntryNotFound:
        if include_traceback:
            raise
        env.log_error('Entry not found.')
        exit_status = ExitStatus.ERROR
    else:
        try:
            exit_status = program(
                args=parsed_args,
                env=env,
            )

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
        except requests.Timeout:
            exit_status = ExitStatus.ERROR_TIMEOUT
            env.log_error(f'Request timed out ({parsed_args.timeout}s).')
        except requests.TooManyRedirects:
            exit_status = ExitStatus.ERROR_TOO_MANY_REDIRECTS
            env.log_error(
                f'Too many redirects'
                f' (--max-redirects={parsed_args.max_redirects}).'
            )
        except Exception as e:
            # TODO: Further distinction between expected and unexpected errors.
            msg = str(e)
            if hasattr(e, 'request'):
                request = e.request
                if hasattr(request, 'url'):
                    msg = (
                        f'{msg} while doing a {request.method}'
                        f' request to URL: {request.url}'
                    )
            env.log_error(f'{type(e).__name__}: {msg}')
            if include_traceback:
                raise
            exit_status = ExitStatus.ERROR

    return exit_status


def get_output_options(
    args: argparse.Namespace,
    message: Union[requests.PreparedRequest, requests.Response]
) -> Tuple[bool, bool]:
    return {
        requests.PreparedRequest: (
            OUT_REQ_HEAD in args.output_options,
            OUT_REQ_BODY in args.output_options,
        ),
        requests.Response: (
            OUT_RESP_HEAD in args.output_options,
            OUT_RESP_BODY in args.output_options,
        ),
    }[type(message)]


def program(
    args: argparse.Namespace,
    env: Environment,
) -> ExitStatus:
    """
    The main program without error handling.

    """
    exit_status = ExitStatus.SUCCESS
    downloader = None

    try:
        if args.download:
            args.follow = True  # --download implies --follow.
            downloader = Downloader(
                output_file=args.output_file,
                progress_file=env.stderr,
                resume=args.download_resume
            )
            downloader.pre_request(args.headers)

        needs_separator = False

        def maybe_separate():
            nonlocal needs_separator
            if env.stdout.isatty() and needs_separator:
                needs_separator = False
                getattr(env.stdout, 'buffer', env.stdout).write(b'\n\n')

        initial_request: Optional[requests.PreparedRequest] = None
        final_response: Optional[requests.Response] = None

        def request_body_read_callback(chunk: bytes):
            should_pipe_to_stdout = (
                # Request body output desired
                OUT_REQ_BODY in args.output_options
                # & not `.read()` already pre-request (e.g., for  compression)
                and initial_request
                # & non-EOF chunk
                and chunk
            )
            if should_pipe_to_stdout:
                msg = requests.PreparedRequest()
                msg.is_body_upload_chunk = True
                msg.body = chunk
                msg.headers = initial_request.headers
                write_message(
                    requests_message=msg,
                    env=env,
                    args=args,
                    with_body=True,
                    with_headers=False
                )

        messages = collect_messages(
            args=args,
            config_dir=env.config.directory,
            request_body_read_callback=request_body_read_callback
        )
        for message in messages:
            maybe_separate()
            is_request = isinstance(message, requests.PreparedRequest)
            with_headers, with_body = get_output_options(
                args=args, message=message)
            if is_request:
                if not initial_request:
                    initial_request = message
                    is_streamed_upload = not isinstance(
                        message.body, (str, bytes))
                    if with_body:
                        with_body = not is_streamed_upload
                        needs_separator = is_streamed_upload
            else:
                final_response = message
                if args.check_status or downloader:
                    exit_status = http_status_to_exit_status(
                        http_status=message.status_code,
                        follow=args.follow
                    )
                    if (not env.stdout_isatty
                            and exit_status != ExitStatus.SUCCESS):
                        env.log_error(
                            f'HTTP {message.raw.status} {message.raw.reason}',
                            level='warning'
                        )
            write_message(
                requests_message=message,
                env=env,
                args=args,
                with_headers=with_headers,
                with_body=with_body,
            )

        maybe_separate()

        if downloader and exit_status == ExitStatus.SUCCESS:
            # Last response body download.
            download_stream, download_to = downloader.start(
                initial_url=initial_request.url,
                final_response=final_response,
            )
            write_stream(
                stream=download_stream,
                outfile=download_to,
                flush=False,
            )
            downloader.finish()
            if downloader.interrupted:
                exit_status = ExitStatus.ERROR
                env.log_error(
                    'Incomplete download: size=%d; downloaded=%d' % (
                        downloader.status.total_size,
                        downloader.status.downloaded
                    ))

        if args.history is None and env.history_enabled:
            history = get_history(config_dir=env.config.directory, host=args.headers.get('Host'), url=args.url)
            history.add_entry(args=sys.argv)
            history.save()

        return exit_status

    finally:
        if downloader and not downloader.finished:
            downloader.failed()

        if (not isinstance(args, list) and args.output_file
                and args.output_file_specified):
            args.output_file.close()


def print_debug_info(env: Environment):
    env.stderr.writelines([
        f'HTTPie {httpie_version}\n',
        f'Requests {requests_version}\n',
        f'Pygments {pygments_version}\n',
        f'Python {sys.version}\n{sys.executable}\n',
        f'{platform.system()} {platform.release()}',
    ])
    env.stderr.write('\n\n')
    env.stderr.write(repr(env))
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
        if type(arg) == bytes else arg
        for arg in args
    ]


def print_history(env, args):
    history = get_history(config_dir=env.config.directory, host=args.headers.get('Host'), url=args.url)
    env.stderr.write(history.get_history_str(10))
