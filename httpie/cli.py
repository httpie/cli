"""
CLI definition.

"""
from . import pretty
from . import __doc__
from . import __version__
from . import cliparse


def _(text):
    """Normalize white space."""
    return ' '.join(text.strip().split())


desc = '%s <http://httpie.org>'
parser = cliparse.HTTPieArgumentParser(description=desc % __doc__.strip(),)
parser.add_argument('--version', action='version', version=__version__)


# Content type.
#############################################

group_type = parser.add_mutually_exclusive_group(required=False)
group_type.add_argument(
    '--json', '-j', action='store_true',
    help=_('''
        (default) Data items are serialized as a JSON object.
        The Content-Type and Accept headers
        are set to application/json (if not set via the command line).
    ''')
)
group_type.add_argument(
    '--form', '-f', action='store_true',
    help=_('''
        Data items are serialized as form fields.
        The Content-Type is set to application/x-www-form-urlencoded (if not specifid).
        The presence of any file fields results into a multipart/form-data request.
     ''')
)


# Output options.
#############################################

parser.add_argument(
    '--traceback', action='store_true', default=False,
    help=_('''
        Print exception traceback should one occur.
    ''')
)

prettify = parser.add_mutually_exclusive_group(required=False)
prettify.add_argument(
    '--pretty', dest='prettify', action='store_true',
    default=cliparse.PRETTIFY_STDOUT_TTY_ONLY,
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
    default=cliparse.OUT_RESP_HEADERS + cliparse.OUT_RESP_BODY,
    help=_('''
        String specifying what should the output contain.
        "{request_headers}" stands for the request headers and
        "{request_body}" for the request body.
        "{response_headers}" stands for the response headers and
        "{response_body}" for response the body.
        Defaults to "hb" which means that the whole response
        (headers and body) is printed.
    '''.format(
        request_headers=cliparse.OUT_REQ_HEADERS,
        request_body=cliparse.OUT_REQ_BODY,
        response_headers=cliparse.OUT_RESP_HEADERS,
        response_body=cliparse.OUT_RESP_BODY,
    ))
)
output_options.add_argument(
    '--verbose', '-v', dest='output_options',
    action='store_const', const=''.join(cliparse.OUTPUT_OPTIONS),
    help=_('''
        Print the whole request as well as the response.
        Shortcut for --print={0}.
    '''.format(''.join(cliparse.OUTPUT_OPTIONS)))
)
output_options.add_argument(
    '--headers', '-t', dest='output_options',
    action='store_const', const=cliparse.OUT_RESP_HEADERS,
    help=_('''
        Print only the response headers.
        Shortcut for --print={0}.
    '''.format(cliparse.OUT_RESP_HEADERS))
)
output_options.add_argument(
    '--body', '-b', dest='output_options',
    action='store_const', const=cliparse.OUT_RESP_BODY,
    help=_('''
        Print only the response body.
        Shortcut for --print={0}.
    '''.format(cliparse.OUT_RESP_BODY))
)

parser.add_argument(
    '--style', '-s', dest='style', default='solarized', metavar='STYLE',
    choices=pretty.AVAILABLE_STYLES,
    help=_('''
        Output coloring style, one of %s. Defaults to solarized.
        For this option to work properly, please make sure that the
        $TERM environment variable is set to "xterm-256color" or similar
        (e.g., via `export TERM=xterm-256color' in your ~/.bashrc).
    ''') % ', '.join(sorted(pretty.AVAILABLE_STYLES))
)

# ``requests.request`` keyword arguments.
parser.add_argument(
    '--auth', '-a', help='username:password',
    type=cliparse.KeyValueType(cliparse.SEP_COMMON)
)

parser.add_argument(
    '--auth-type', choices=['basic', 'digest'],
    help=_('The authentication mechanism to be used. Defaults to "basic".')
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
    type=cliparse.KeyValueType(cliparse.SEP_COMMON),
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


# Positional arguments.
#############################################

parser.add_argument(
    'method', metavar='METHOD',
    help=_('''
        The HTTP method to be used for the request
        (GET, POST, PUT, DELETE, PATCH, ...).
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
    type=cliparse.KeyValueType(
        cliparse.SEP_COMMON,
        cliparse.SEP_DATA,
        cliparse.SEP_DATA_RAW_JSON,
        cliparse.SEP_FILES
    ),
    help=_('''
        A key-value pair whose type is defined by the separator used. It can be an
        HTTP header (header:value),
        a data field to be used in the request body (field_name=value),
        a raw JSON data field (field_name:=value)
        or a file field (field_name@/path/to/file).
        You can use a backslash to escape a colliding separator in the field name.
    ''')
)
