import argparse
import os
import platform
import site
import sys
from typing import Callable, List, Union

from pkg_resources import working_set
import requests
from pygments import __version__ as pygments_version
from requests import __version__ as requests_version

from httpie import __version__ as httpie_version
from httpie.status import ExitStatus, http_status_to_exit_status
from httpie.client import collect_messages
from httpie.context import Environment
from httpie.downloads import Downloader
from httpie.output.writer import write_message, write_stream
from httpie.plugins import plugin_manager


def main(
    args: List[Union[str, bytes]] = sys.argv,
    env=Environment(),
    custom_log_error: Callable = None
) -> ExitStatus:
    """
    The main function.

    Pre-process args, handle some special types of invocations,
    and run the main program with error handling.

    Return exit status code.

    """
    args = decode_raw_args(args, env.stdin_encoding)
    program_name, *args = args

    sys_path_length = len(sys.path)

    for sitedir in env.config.extra_site_dirs:
        parts = sitedir.split(os.sep)
        if parts[0].startswith('~'):
            parts[0] = os.path.expanduser(parts[0])
        site.addsitedir(os.sep.join(parts))

    for new_path in sys.path[sys_path_length:]:
        working_set.add_entry(new_path)

    include_debug_info = '--debug' in args

    if include_debug_info:
        print_debug_info(env)

    plugin_manager.load_installed_plugins(env.stderr if include_debug_info else None)

    def log_error(msg, level='error'):
        assert level in ['error', 'warning']
        env.stderr.write(f'\n{program_name}: {level}: {msg}\n')

    from httpie.cli.definition import parser

    if env.config.default_options:
        args = env.config.default_options + args

    if custom_log_error:
        log_error = custom_log_error

    include_traceback = include_debug_info or '--traceback' in args

    if args == ['--debug']:
        return ExitStatus.SUCCESS

    exit_status = ExitStatus.SUCCESS

    try:
        parsed_args = parser.parse_args(
            args=args,
            program_name=program_name,
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
                log_error=log_error,
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
            log_error(f'Request timed out ({parsed_args.timeout}s).')
        except requests.TooManyRedirects:
            exit_status = ExitStatus.ERROR_TOO_MANY_REDIRECTS
            log_error(
                f'Too many redirects'
                f' (--max-redirects=parsed_args.max_redirects).'
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
            log_error(f'{type(e).__name__}: {msg}')
            if include_traceback:
                raise
            exit_status = ExitStatus.ERROR

    return exit_status


def program(
    args: argparse.Namespace,
    env: Environment,
    log_error: Callable
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
                    if not env.stdout_isatty and exit_status != ExitStatus.SUCCESS:
                        log_error(
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
                log_error('Incomplete download: size=%d; downloaded=%d' % (
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
        'HTTPie %s\n' % httpie_version,
        'Requests %s\n' % requests_version,
        'Pygments %s\n' % pygments_version,
        'Python %s\n%s\n' % (sys.version, sys.executable),
        '%s %s' % (platform.system(), platform.release()),
    ])
    env.stderr.write('\n\n')
    env.stderr.write(repr(env))
    env.stderr.write('\n')
    env.stderr.write('Looking for plugins in these directories:\n')
    for p in sys.path:
        env.stderr.write('  %s\n' % p)
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
