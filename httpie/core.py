"""This module provides the main functionality of HTTPie.

Invocation flow:

  1. Read, validate and process the input (args, `stdin`).
  2. Create and send a request.
  3. Stream, and possibly process and format, the parts
     of the request-response exchange selected by output options.
  4. Simultaneously write to `stdout`
  5. Exit.

"""
import sys
import errno
import platform

import requests
from requests import __version__ as requests_version
from pygments import __version__ as pygments_version

from httpie import __version__ as httpie_version, ExitStatus
from httpie.compat import str, bytes, is_py3
from httpie.client import get_response
from httpie.downloads import Downloader
from httpie.context import Environment
from httpie.plugins import plugin_manager
from httpie.output.streams import (
    build_output_stream,
    write_stream,
    write_stream_with_colors_win_py3
)

from coverage_tool import has_branched, write_info

def get_exit_status(http_status, follow=False):
    """Translate HTTP status code to exit status code."""
    if 300 <= http_status <= 399 and not follow:
        # Redirect
        return ExitStatus.ERROR_HTTP_3XX
    elif 400 <= http_status <= 499:
        # Client Error
        return ExitStatus.ERROR_HTTP_4XX
    elif 500 <= http_status <= 599:
        # Server Error
        return ExitStatus.ERROR_HTTP_5XX
    else:
        return ExitStatus.OK


def print_debug_info(env):
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


def decode_args(args, stdin_encoding):
    """
    Convert all bytes args to str
    by decoding them using stdin encoding.

    """
    return [
        arg.decode(stdin_encoding)
        if type(arg) == bytes else arg
        for arg in args
    ]


def program(args, env, log_error):
    """
    The main program without error handling

    :param args: parsed args (argparse.Namespace)
    :type env: Environment
    :param log_error: error log function
    :return: status code

    """
    exit_status = ExitStatus.OK
    downloader = None
    show_traceback = args.debug or args.traceback

    try:
        if args.download:
            args.follow = True  # --download implies --follow.
            downloader = Downloader(
                output_file=args.output_file,
                progress_file=env.stderr,
                resume=args.download_resume
            )
            downloader.pre_request(args.headers)

        final_response = get_response(args, config_dir=env.config.directory)
        if args.all:
            responses = final_response.history + [final_response]
        else:
            responses = [final_response]

        for response in responses:

            if args.check_status or downloader:
                exit_status = get_exit_status(
                    http_status=response.status_code,
                    follow=args.follow
                )
                if not env.stdout_isatty and exit_status != ExitStatus.OK:
                    log_error(
                        'HTTP %s %s', response.raw.status, response.raw.reason,
                        level='warning'
                    )

            write_stream_kwargs = {
                'stream': build_output_stream(
                    args=args,
                    env=env,
                    request=response.request,
                    response=response,
                    output_options=(
                        args.output_options
                        if response is final_response
                        else args.output_options_history
                    )
                ),
                # NOTE: `env.stdout` will in fact be `stderr` with `--download`
                'outfile': env.stdout,
                'flush': env.stdout_isatty or args.stream
            }
            try:
                if env.is_windows and is_py3 and 'colors' in args.prettify:
                    write_stream_with_colors_win_py3(**write_stream_kwargs)
                else:
                    write_stream(**write_stream_kwargs)
            except IOError as e:
                if not show_traceback and e.errno == errno.EPIPE:
                    # Ignore broken pipes unless --traceback.
                    env.stderr.write('\n')
                else:
                    raise

        if downloader and exit_status == ExitStatus.OK:
            # Last response body download.
            download_stream, download_to = downloader.start(final_response)
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

        if (not isinstance(args, list) and args.output_file and
                args.output_file_specified):
            args.output_file.close()


def main(args=sys.argv[1:], env=Environment(), custom_log_error=None):
    """
    The main function.

    Pre-process args, handle some special types of invocations,
    and run the main program with error handling.

    Return exit status code.

    """
    args = decode_args(args, env.stdin_encoding)
    plugin_manager.load_installed_plugins()

    def log_error(msg, *args, **kwargs):
        msg = msg % args
        level = kwargs.get('level', 'error')
        assert level in ['error', 'warning']
        env.stderr.write('\nhttp: %s: %s\n' % (level, msg))

    from httpie.cli import parser

    write_info('main','Total: 21')
    if env.config.default_options:
        has_branched('main', 1)
        args = env.config.default_options + args

    if custom_log_error:
        has_branched('main', 2)
        log_error = custom_log_error

    include_debug_info = '--debug' in args
    include_traceback = include_debug_info or '--traceback' in args

    if include_debug_info:
        print_debug_info(env)
        has_branched('main', 3)
        if args == ['--debug']:
            has_branched('main', 4)
            return ExitStatus.OK

    exit_status = ExitStatus.OK

    try:
        parsed_args = parser.parse_args(args=args, env=env)
    except KeyboardInterrupt:
        has_branched('main', 5)
        env.stderr.write('\n')
        if include_traceback:
            has_branched('main', 6)
            raise
        exit_status = ExitStatus.ERROR_CTRL_C
    except SystemExit as e:
        has_branched('main', 7)
        if e.code != ExitStatus.OK:
            has_branched('main', 8)
            env.stderr.write('\n')
            if include_traceback:
                has_branched('main', 9)
                raise
            exit_status = ExitStatus.ERROR
    else:
        has_branched('main', 10)
        try:
            exit_status = program(
                args=parsed_args,
                env=env,
                log_error=log_error,
            )
        except KeyboardInterrupt:
            has_branched('main', 11)
            env.stderr.write('\n')
            if include_traceback:
                has_branched('main', 12)
                raise
            exit_status = ExitStatus.ERROR_CTRL_C
        except SystemExit as e:
            has_branched('main', 13)
            if e.code != ExitStatus.OK:
                has_branched('main', 14)
                env.stderr.write('\n')
                if include_traceback:
                    has_branched('main', 15)
                    raise
                exit_status = ExitStatus.ERROR
        except requests.Timeout:
            has_branched('main', 16)
            exit_status = ExitStatus.ERROR_TIMEOUT
            log_error('Request timed out (%ss).', parsed_args.timeout)
        except requests.TooManyRedirects:
            has_branched('main', 17)
            exit_status = ExitStatus.ERROR_TOO_MANY_REDIRECTS
            log_error('Too many redirects (--max-redirects=%s).',
                      parsed_args.max_redirects)
        except Exception as e:
            has_branched('main', 18)
            # TODO: Further distinction between expected and unexpected errors.
            msg = str(e)
            if hasattr(e, 'request'):
                has_branched('main', 19)
                request = e.request
                if hasattr(request, 'url'):
                    has_branched('main', 20)
                    msg += ' while doing %s request to URL: %s' % (
                        request.method, request.url)
            log_error('%s: %s', type(e).__name__, msg)
            if include_traceback:
                has_branched('main', 21)
                raise
            exit_status = ExitStatus.ERROR

    return exit_status
