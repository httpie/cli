"""CLI arguments definition.

NOTE: the CLI interface may change before reaching v1.0.

"""
import argparse

from requests.compat import is_windows

from . import __doc__
from . import __version__
from .output import AVAILABLE_STYLES, DEFAULT_STYLE
from .input import (Parser, AuthCredentialsArgType, KeyValueArgType,
                    PRETTIFY_STDOUT_TTY_ONLY,
                    SEP_PROXY, SEP_CREDENTIALS, SEP_GROUP_ITEMS,
                    OUT_REQ_HEAD, OUT_REQ_BODY, OUT_RESP_HEAD,
                    OUT_RESP_BODY, OUTPUT_OPTIONS)


def _(text):
    """Normalize whitespace."""
    return ' '.join(text.strip().split())


parser = Parser(description='%s <http://httpie.org>' % __doc__.strip())
parser.add_argument('--version', action='version', version=__version__)


# Content type.
#############################################

group_type = parser.add_mutually_exclusive_group(required=False)
group_type.add_argument(
    '--json', '-j', action='store_true',
    help=_('''
        (default) Data items from the command
        line are serialized as a JSON object.
        The Content-Type and Accept headers
        are set to application/json (if not specified).
    ''')
)
group_type.add_argument(
    '--form', '-f', action='store_true',
    help=_('''
        Data items from the command line are serialized as form fields.
        The Content-Type is set to application/x-www-form-urlencoded
        (if not specified).
        The presence of any file fields results
        into a multipart/form-data request.
     ''')
)


# Output options.
#############################################


parser.add_argument(
    '--output', '-o', type=argparse.FileType('w+b'),
    metavar='FILE',
    help= argparse.SUPPRESS if not is_windows else _(
        '''
        Save output to FILE.
        This option is a replacement for piping output to FILE,
        which would on Windows result into corrupted data
        being saved.

        '''
    )
)

prettify = parser.add_mutually_exclusive_group(required=False)
prettify.add_argument(
    '--pretty', dest='prettify', action='store_true',
    default=PRETTIFY_STDOUT_TTY_ONLY,
    help=_('''
        If stdout is a terminal, the response is prettified
        by default (colorized and indented if it is JSON).
        This flag ensures prettifying even when stdout is redirected.
    ''')
)
prettify.add_argument(
    '--ugly', '-u', dest='prettify', action='store_false',
    help=_('''
        Do not prettify the response.
    ''')
)

output_options = parser.add_mutually_exclusive_group(required=False)
output_options.add_argument('--print', '-p', dest='output_options',
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
output_options.add_argument(
    '--verbose', '-v', dest='output_options',
    action='store_const', const=''.join(OUTPUT_OPTIONS),
    help=_('''
        Print the whole request as well as the response.
        Shortcut for --print={0}.
    '''.format(''.join(OUTPUT_OPTIONS)))
)
output_options.add_argument(
    '--headers', '-h', dest='output_options',
    action='store_const', const=OUT_RESP_HEAD,
    help=_('''
        Print only the response headers.
        Shortcut for --print={0}.
    '''.format(OUT_RESP_HEAD))
)
output_options.add_argument(
    '--body', '-b', dest='output_options',
    action='store_const', const=OUT_RESP_BODY,
    help=_('''
        Print only the response body.
        Shortcut for --print={0}.
    '''.format(OUT_RESP_BODY))
)

parser.add_argument(
    '--style', '-s', dest='style', default=DEFAULT_STYLE, metavar='STYLE',
    choices=AVAILABLE_STYLES,
    help=_('''
        Output coloring style, one of %s. Defaults to "%s".
        For this option to work properly, please make sure that the
        $TERM environment variable is set to "xterm-256color" or similar
        (e.g., via `export TERM=xterm-256color' in your ~/.bashrc).
    ''') % (', '.join(sorted(AVAILABLE_STYLES)), DEFAULT_STYLE)
)

parser.add_argument('--stream', '-S', action='store_true', default=False, help=_(
    '''
    Always stream the output by line, i.e., behave like `tail -f'.

    Without --stream and with --pretty (either set or implied),
    HTTPie fetches the whole response before it outputs the processed data.

    Set this option when you want to continuously display a prettified
    long-lived response, such as one from the Twitter streaming API.

    It is useful also without --pretty: It ensures that the output is flushed
    more often and in smaller chunks.

    '''
))
parser.add_argument(
    '--check-status', default=False, action='store_true',
    help=_('''
        By default, HTTPie exits with 0 when no network or other fatal
        errors occur.

        This flag instructs HTTPie to also check the HTTP status code and
        exit with an error if the status indicates one.

        When the server replies with a 4xx (Client Error) or 5xx
        (Server Error) status code, HTTPie exits with 4 or 5 respectively.
        If the response is a 3xx (Redirect) and --allow-redirects
        hasn't been set, then the exit status is 3.

        Also an error message is written to stderr if stdout is redirected.

    ''')
)

# ``requests.request`` keyword arguments.
parser.add_argument(
    '--auth', '-a',
    type=AuthCredentialsArgType(SEP_CREDENTIALS),
    help=_('''
        username:password.
        If only the username is provided (-a username),
        HTTPie will prompt for the password.
    '''),
)

parser.add_argument(
    '--auth-type', choices=['basic', 'digest'], default='basic',
    help=_('''
        The authentication mechanism to be used.
        Defaults to "basic".
    ''')
)

parser.add_argument(
    '--verify', default='yes',
    help=_('''
        Set to "no" to skip checking the host\'s SSL certificate.
        You can also pass the  path to a CA_BUNDLE
        file for private certs. You can also set
        the REQUESTS_CA_BUNDLE  environment variable.
        Defaults to "yes".
    ''')
)
parser.add_argument(
    '--proxy', default=[], action='append',
    type=KeyValueArgType(SEP_PROXY),
    help=_('''
        String mapping protocol to the URL of the proxy
        (e.g. http:foo.bar:3128).
    ''')
)
parser.add_argument(
    '--allow-redirects', default=False, action='store_true',
    help=_('''
        Set this flag if full redirects are allowed
        (e.g. re-POST-ing of data at new ``Location``)
    ''')
)
parser.add_argument(
    '--timeout', type=float,
    help=_('''
        Float describes the timeout of the request
        (Use socket.setdefaulttimeout() as fallback).
    ''')
)
parser.add_argument(
    '--debug', action='store_true', default=False,
    help=_('''
        Prints exception traceback should one occur and other
        information useful for debugging HTTPie itself.
    ''')
)


# Positional arguments.
#############################################

parser.add_argument(
    'method', metavar='METHOD',
    nargs='?',
    default=None,
    help=_('''
        The HTTP method to be used for the request
        (GET, POST, PUT, DELETE, PATCH, ...).
        If this argument is omitted, then HTTPie
        will guess the HTTP method. If there is some
        data to be sent, then it will be POST, otherwise GET.
    ''')
)
parser.add_argument(
    'url', metavar='URL',
    help=_('''
        The protocol defaults to http:// if the
        URL does not include one.
    ''')
)
parser.add_argument(
    'items', nargs='*',
    metavar='ITEM',
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
