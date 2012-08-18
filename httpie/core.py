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
from requests.compat import str, is_py3
from httpie import __version__ as httpie_version
from requests import __version__ as requests_version
from pygments import __version__ as pygments_version

from .cli import parser
from .client import get_response
from .models import Environment
from .output import output_stream, write, write_with_colors_win_p3k
from .config import CONFIG_DIR
from . import EXIT


def get_exist_status(code, allow_redirects=False):
    """Translate HTTP status code to exit status."""
    if 300 <= code <= 399 and not allow_redirects:
        # Redirect
        return EXIT.ERROR_HTTP_3XX
    elif 400 <= code <= 499:
        # Client Error
        return EXIT.ERROR_HTTP_4XX
    elif 500 <= code <= 599:
        # Server Error
        return EXIT.ERROR_HTTP_5XX
    else:
        return EXIT.OK


def print_debug_info():
    sys.stderr.writelines([
        'HTTPie %s\n' % httpie_version,
        'HTTPie data: %s\n' % CONFIG_DIR,
        'Requests %s\n' % requests_version,
        'Pygments %s\n' % pygments_version,
        'Python %s %s\n' % (sys.version, sys.platform)
    ])


def main(args=sys.argv[1:], env=Environment()):
    """Run the main program and write the output to ``env.stdout``.

    Return exit status.

    """

    def error(msg, *args):
        msg = msg % args
        env.stderr.write('\nhttp: error: %s\n' % msg)

    debug = '--debug' in args
    traceback = debug or '--traceback' in args
    status = EXIT.OK

    if debug:
        print_debug_info()
        if args == ['--debug']:
            sys.exit(EXIT.OK)

    try:
        args = parser.parse_args(args=args, env=env)
        response = get_response(args)

        if args.check_status:
            status = get_exist_status(response.status_code,
                                      args.allow_redirects)
            if status and not env.stdout_isatty:
                error('%s %s', response.raw.status, response.raw.reason)

        stream = output_stream(args, env, response.request, response)

        write_kwargs = {
            'stream': stream,
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
        status = EXIT.ERROR
    except requests.Timeout:
        status = EXIT.ERROR_TIMEOUT
        error('Request timed out (%ss).', args.timeout)
    except Exception as e:
        # TODO: distinguish between expected and unexpected errors.
        #       network errors vs. bugs, etc.
        if traceback:
            raise
        error('%s: %s', type(e).__name__, str(e))
        status = EXIT.ERROR

    return status
