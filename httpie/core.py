"""This module provides the main functionality of HTTPie.

Invocation flow:

    1. Read, validate and process the input (args, `stdin`).
    2. Create and send a request.
    3. Stream, and possibly process and format, the requested parts
       of the request-response exchange.
    4. Simultaneously write to `stdout`
    5. Exit.

"""
import sys
import errno

import requests
from httpie import __version__ as httpie_version
from requests import __version__ as requests_version
from pygments import __version__ as pygments_version

from .cli import parser
from .compat import str, is_py3
from .client import get_response
from .models import Environment
from .output import build_output_stream, write, write_with_colors_win_p3k
from . import ExitStatus


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
    sys.stderr.writelines([
        'HTTPie %s\n' % httpie_version,
        'HTTPie data: %s\n' % env.config.directory,
        'Requests %s\n' % requests_version,
        'Pygments %s\n' % pygments_version,
        'Python %s %s\n' % (sys.version, sys.platform)
    ])


def main(args=sys.argv[1:], env=Environment()):
    """Run the main program and write the output to ``env.stdout``.

    Return exit status code.

    """
    if env.config.default_options:
        args = env.config.default_options + args

    def error(msg, *args, **kwargs):
        msg = msg % args
        level = kwargs.get('level', 'error')
        env.stderr.write('http: %s: %s\n' % (level, msg))

    debug = '--debug' in args
    traceback = debug or '--traceback' in args
    exit_status = ExitStatus.OK

    if debug:
        print_debug_info(env)
        if args == ['--debug']:
            return exit_status

    try:
        args = parser.parse_args(args=args, env=env)

        response = get_response(args, config_dir=env.config.directory)

        if args.check_status:
            exit_status = get_exit_status(response.status_code, args.follow)

            if not env.stdout_isatty and exit_status != ExitStatus.OK:
                error('HTTP %s %s',
                      response.raw.status,
                      response.raw.reason,
                      level='warning')

        write_kwargs = {
            'stream': build_output_stream(args, env,
                                          response.request,
                                          response),
            'outfile': env.stdout,
            'flush': env.stdout_isatty or args.stream
        }
        try:
            if env.is_windows and is_py3 and 'colors' in args.prettify:
                write_with_colors_win_p3k(**write_kwargs)
            else:
                write(**write_kwargs)

        except IOError as e:
            if not traceback and e.errno == errno.EPIPE:
                # Ignore broken pipes unless --traceback.
                env.stderr.write('\n')
            else:
                raise

    except (KeyboardInterrupt, SystemExit):
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
        error('%s: %s', type(e).__name__, str(e))
        exit_status = ExitStatus.ERROR

    return exit_status
