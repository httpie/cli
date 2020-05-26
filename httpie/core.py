import argparse
import os
import platform
import sys
from typing import List, Union

import requests
from pygments import __version__ as pygments_version
from requests import __version__ as requests_version

from httpie import __version__ as httpie_version
from httpie.client import collect_messages
from httpie.context import Environment
from httpie.downloads import Downloader
from httpie.output.writer import write_message, write_stream
from httpie.plugins.registry import plugin_manager
from httpie.status import ExitStatus, http_status_to_exit_status


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

        initial_request = None
        final_response = None

        for message in collect_messages(args, env.config.directory):
            write_message(
                requests_message=message,
                env=env,
                args=args,
            )
            if isinstance(message, requests.PreparedRequest):
                if not initial_request:
                    initial_request = message
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
