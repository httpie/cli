"""CLI arguments definition.

NOTE: the CLI interface may change before reaching v1.0.
TODO: make the options config friendly, i.e., no mutually exclusive groups to
      allow options overwriting.

"""
from argparse import FileType, OPTIONAL, ZERO_OR_MORE, SUPPRESS

from requests.compat import is_windows

from . import __doc__
from . import __version__
from .sessions import DEFAULT_SESSIONS_DIR
from .output import AVAILABLE_STYLES, DEFAULT_STYLE
from .input import (Parser, AuthCredentialsArgType, KeyValueArgType,
                    SEP_PROXY, SEP_CREDENTIALS, SEP_GROUP_ITEMS,
                    OUT_REQ_HEAD, OUT_REQ_BODY, OUT_RESP_HEAD,
                    OUT_RESP_BODY, OUTPUT_OPTIONS,
                    PRETTY_MAP, PRETTY_STDOUT_TTY_ONLY)


def _(text):
    """Normalize whitespace."""
    return ' '.join(text.strip().split())


parser = Parser(
    description='%s <http://httpie.org>' % __doc__.strip(),
    epilog=_('''
        Suggestions and bug reports are greatly appreciated:
        https://github.com/jkbr/httpie/issues
    ''')
)



###############################################################################
# Positional arguments.
###############################################################################

positional = parser.add_argument_group(
    title='Positional arguments',
    description=_('''
        These arguments come after any flags and in the
        order they are listed here. Only URL is required.'''
    )
)
positional.add_argument(
    'method', metavar='METHOD',
    nargs=OPTIONAL,
    default=None,
    help=_('''
        The HTTP method to be used for the request
        (GET, POST, PUT, DELETE, PATCH, ...).
        If this argument is omitted, then HTTPie
        will guess the HTTP method. If there is some
        data to be sent, then it will be POST, otherwise GET.
    ''')
)
positional.add_argument(
    'url', metavar='URL',
    help=_('''
        The protocol defaults to http:// if the
        URL does not include one.
    ''')
)
positional.add_argument(
    'items', metavar='REQUEST ITEM',
    nargs=ZERO_OR_MORE,
    type=KeyValueArgType(*SEP_GROUP_ITEMS),
    help=_('''
        A key-value pair whose type is defined by the
        separator used. It can be an HTTP header (header:value),
        a data field to be used in the request body (field_name=value),
        a raw JSON data field (field_name:=value),
        a query parameter (name==value),
        or a file field (field_name@/path/to/file).
        You can use a backslash to escape a colliding
        separator in the field name.
    ''')
)


###############################################################################
# Content type.
###############################################################################

content_type = parser.add_argument_group(
    title='Predefined content types',
    description=None
).add_mutually_exclusive_group(required=False)

content_type.add_argument(
    '--json', '-j', action='store_true',
    help=_('''
        (default) Data items from the command
        line are serialized as a JSON object.
        The Content-Type and Accept headers
        are set to application/json (if not specified).
    ''')
)
content_type.add_argument(
    '--form', '-f', action='store_true',
    help=_('''
        Data items from the command line are serialized as form fields.
        The Content-Type is set to application/x-www-form-urlencoded
        (if not specified).
        The presence of any file fields results
        in a multipart/form-data request.
     ''')
)


###############################################################################
# Output processing
###############################################################################

output_processing = parser.add_argument_group(title='Output processing')

output_processing.add_argument(
    '--output', '-o', type=FileType('w+b'),
    metavar='FILE',
    help= SUPPRESS if not is_windows else _(
        '''
        Save output to FILE.
        This option is a replacement for piping output to FILE,
        which would on Windows result in corrupted data
        being saved.

        '''
    )
)
output_processing.add_argument(
    '--pretty', dest='prettify', default=PRETTY_STDOUT_TTY_ONLY,
    choices=sorted(PRETTY_MAP.keys()),
    help=_('''
        Controls output processing. The value can be "none" to not prettify
        the output (default for redirected output), "all" to apply both colors
        and formatting
        (default for terminal output), "colors", or "format".
    ''')
)
output_processing.add_argument(
    '--style', '-s', dest='style', default=DEFAULT_STYLE, metavar='STYLE',
    choices=AVAILABLE_STYLES,
    help=_('''
        Output coloring style. One of %s. Defaults to "%s".
        For this option to work properly, please make sure that the
        $TERM environment variable is set to "xterm-256color" or similar
        (e.g., via `export TERM=xterm-256color' in your ~/.bashrc).
    ''') % (', '.join(sorted(AVAILABLE_STYLES)), DEFAULT_STYLE)
)



###############################################################################
# Output options
###############################################################################
output_options = parser.add_argument_group(title='Output options')

output_print = output_options.add_mutually_exclusive_group(required=False)
output_print.add_argument('--print', '-p', dest='output_options',
    metavar='WHAT',
    help=_('''
        String specifying what the output should contain:
        "{request_headers}" stands for the request headers,  and
        "{request_body}" for the request body.
        "{response_headers}" stands for the response headers and
        "{response_body}" for response the body.
        The default behaviour is "hb" (i.e., the response
        headers and body is printed), if standard output is not redirected.
        If the output is piped to another program or to a file,
        then only the body is printed by default.
    '''.format(
        request_headers=OUT_REQ_HEAD,
        request_body=OUT_REQ_BODY,
        response_headers=OUT_RESP_HEAD,
        response_body=OUT_RESP_BODY,
    ))
)
output_print.add_argument(
    '--verbose', '-v', dest='output_options',
    action='store_const', const=''.join(OUTPUT_OPTIONS),
    help=_('''
        Print the whole request as well as the response.
        Shortcut for --print={0}.
    '''.format(''.join(OUTPUT_OPTIONS)))
)
output_print.add_argument(
    '--headers', '-h', dest='output_options',
    action='store_const', const=OUT_RESP_HEAD,
    help=_('''
        Print only the response headers.
        Shortcut for --print={0}.
    '''.format(OUT_RESP_HEAD))
)
output_print.add_argument(
    '--body', '-b', dest='output_options',
    action='store_const', const=OUT_RESP_BODY,
    help=_('''
        Print only the response body.
        Shortcut for --print={0}.
    '''.format(OUT_RESP_BODY))
)

output_options.add_argument('--stream', '-S', action='store_true', default=False,
    help=_('''
    Always stream the output by line, i.e., behave like `tail -f'.

    Without --stream and with --pretty (either set or implied),
    HTTPie fetches the whole response before it outputs the processed data.

    Set this option when you want to continuously display a prettified
    long-lived response, such as one from the Twitter streaming API.

    It is useful also without --pretty: It ensures that the output is flushed
    more often and in smaller chunks.

    '''
))


###############################################################################
# Sessions
###############################################################################
sessions = parser.add_argument_group(title='Sessions')\
                 .add_mutually_exclusive_group(required=False)

sessions.add_argument(
    '--session', metavar='SESSION_NAME',
    help=_('''
    Create, or reuse and update a session.
    Withing a session, custom headers, auth credential, as well as any
    cookies sent by the server persist between requests.
    Session files are stored in %s/<HOST>/<SESSION_NAME>.json.
    ''' % DEFAULT_SESSIONS_DIR)
)
sessions.add_argument(
    '--session-read-only', metavar='SESSION_NAME',
    help=_('''
        Create or read a session without updating it form the
        request/response exchange.
    ''')
)


###############################################################################
# Authentication
###############################################################################
# ``requests.request`` keyword arguments.
auth = parser.add_argument_group(title='Authentication')
auth.add_argument(
    '--auth', '-a', metavar='USER[:PASS]',
    type=AuthCredentialsArgType(SEP_CREDENTIALS),
    help=_('''
        If only the username is provided (-a username),
        HTTPie will prompt for the password.
    '''),
)

auth.add_argument(
    '--auth-type', choices=['basic', 'digest'], default='basic',
    help=_('''
        The authentication mechanism to be used.
        Defaults to "basic".
    ''')
)



# Network
#############################################

network = parser.add_argument_group(title='Network')

network.add_argument(
    '--proxy', default=[], action='append', metavar='PROTOCOL:HOST',
    type=KeyValueArgType(SEP_PROXY),
    help=_('''
        String mapping protocol to the URL of the proxy
        (e.g. http:foo.bar:3128). You can specify multiple
        proxies with different protocols.
    ''')
)
network.add_argument(
    '--follow', default=False, action='store_true',
    help=_('''
        Set this flag if full redirects are allowed
        (e.g. re-POST-ing of data at new ``Location``)
    ''')
)
network.add_argument(
    '--verify', default='yes',
    help=_('''
        Set to "no" to skip checking the host\'s SSL certificate.
        You can also pass the  path to a CA_BUNDLE
        file for private certs. You can also set
        the REQUESTS_CA_BUNDLE  environment variable.
        Defaults to "yes".
    ''')
)

network.add_argument(
    '--timeout', type=float, default=30, metavar='SECONDS',
    help=_('''
        The connection timeout of the request in seconds.
        The default value is 30 seconds.
    ''')
)
network.add_argument(
    '--check-status', default=False, action='store_true',
    help=_('''
        By default, HTTPie exits with 0 when no network or other fatal
        errors occur.

        This flag instructs HTTPie to also check the HTTP status code and
        exit with an error if the status indicates one.

        When the server replies with a 4xx (Client Error) or 5xx
        (Server Error) status code, HTTPie exits with 4 or 5 respectively.
        If the response is a 3xx (Redirect) and --follow
        hasn't been set, then the exit status is 3.

        Also an error message is written to stderr if stdout is redirected.

    ''')
)


###############################################################################
# Troubleshooting
###############################################################################

troubleshooting = parser.add_argument_group(title='Troubleshooting')

troubleshooting.add_argument(
    '--help',
    action='help', default=SUPPRESS,
    help='Show this help message and exit'
)
troubleshooting.add_argument('--version', action='version', version=__version__)
troubleshooting.add_argument(
    '--traceback', action='store_true', default=False,
    help='Prints exception traceback should one occur.'
)
troubleshooting.add_argument(
    '--debug', action='store_true', default=False,
    help=_('''
        Prints exception traceback should one occur, and also other
        information that is useful for debugging HTTPie itself and
        for bug reports.
    ''')
)
