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

import requests
from requests import __version__ as requests_version
from pygments import __version__ as pygments_version

from httpie import __version__ as httpie_version, ExitStatus
from httpie.compat import str, bytes, is_py3
from httpie.client import get_response
from httpie.downloads import Download
from httpie.context import Environment
from httpie.plugins import plugin_manager
from httpie.output.streams import (
    build_output_stream,
    write, write_with_colors_win_py3
)


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
        'HTTPie data: %s\n' % env.config.directory,
        'Requests %s\n' % requests_version,
        'Pygments %s\n' % pygments_version,
        'Python %s %s\n' % (sys.version, sys.platform)
    ])


def decode_args(args, stdin_encoding):
    """
    Convert all bytes ags to str
    by decoding them using stdin encoding.

    """
    return [
        arg.decode(stdin_encoding)
        if type(arg) == bytes else arg
        for arg in args
    ]


def main(args=sys.argv[1:], env=Environment(), error=None):
    """Run the main program and write the output to ``env.stdout``.

    Return exit status code.

    """
    args = decode_args(args, env.stdin_encoding)
    plugin_manager.load_installed_plugins()

    from httpie.cli import parser

    if env.config.default_options:
        args = env.config.default_options + args

    def _error(msg, *args, **kwargs):
        msg = msg % args
        level = kwargs.get('level', 'error')
        env.stderr.write('\nhttp: %s: %s\n' % (level, msg))

    if error is None:
        error = _error

    debug = '--debug' in args
    traceback = debug or '--traceback' in args
    exit_status = ExitStatus.OK

    if debug:
        print_debug_info(env)
        if args == ['--debug']:
            return exit_status

    download = None

    try:
        args = parser.parse_args(args=args, env=env)

        if args.download:
            args.follow = True  # --download implies --follow.
            download = Download(
                output_file=args.output_file,
                progress_file=env.stderr,
                resume=args.download_resume
            )
            download.pre_request(args.headers)

        response = get_response(args, config_dir=env.config.directory)

        if args.check_status or download:

            exit_status = get_exit_status(
                http_status=response.status_code,
                follow=args.follow
            )

            if not env.stdout_isatty and exit_status != ExitStatus.OK:
                error('HTTP %s %s',
                      response.raw.status,
                      response.raw.reason,
                      level='warning')

        write_kwargs = {
            'stream': build_output_stream(
                args, env, response.request, response),

            # This will in fact be `stderr` with `--download`
            'outfile': env.stdout,

            'flush': env.stdout_isatty or args.stream
        }

        try:

            if env.is_windows and is_py3 and 'colors' in args.prettify:
                write_with_colors_win_py3(**write_kwargs)
            else:
                write(**write_kwargs)

            if download and exit_status == ExitStatus.OK:
                # Response body download.
                download_stream, download_to = download.start(response)
                write(
                    stream=download_stream,
                    outfile=download_to,
                    flush=False,
                )
                download.finish()
                if download.interrupted:
                    exit_status = ExitStatus.ERROR
                    error('Incomplete download: size=%d; downloaded=%d' % (
                        download.status.total_size,
                        download.status.downloaded
                    ))

        except IOError as e:
            if not traceback and e.errno == errno.EPIPE:
                # Ignore broken pipes unless --traceback.
                env.stderr.write('\n')
            else:
                raise
    except KeyboardInterrupt:
        if traceback:
            raise
        env.stderr.write('\n')
        exit_status = ExitStatus.ERROR
    except SystemExit as e:
        if e.code != ExitStatus.OK:
            if traceback:
                raise
            env.stderr.write('\n')
            exit_status = ExitStatus.ERROR
    except requests.Timeout:
        exit_status = ExitStatus.ERROR_TIMEOUT
        error('Request timed out (%ss).', args.timeout)

    except Exception as e:
        # TODO: Better distinction between expected and unexpected errors.
        #       Network errors vs. bugs, etc.
        if traceback:
            raise
        msg = str(e)
        if hasattr(e, 'request'):
            request = e.request
            if hasattr(request, 'url'):
                msg += ' while doing %s request to URL: %s' % (
                    request.method, request.url)
        error('%s: %s', type(e).__name__, msg)
        exit_status = ExitStatus.ERROR

    finally:
        if download and not download.finished:
            download.failed()

    return exit_status
