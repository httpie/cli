"""CLI arguments definition.

NOTE: the CLI interface may change before reaching v1.0.

"""
from textwrap import dedent, wrap
#noinspection PyCompatibility
from argparse import (RawDescriptionHelpFormatter, FileType,
                      OPTIONAL, ZERO_OR_MORE, SUPPRESS)

from httpie import __doc__, __version__
from httpie.plugins.builtin import BuiltinAuthPlugin
from httpie.plugins import plugin_manager
from httpie.sessions import DEFAULT_SESSIONS_DIR
from httpie.output.formatters.colors import AVAILABLE_STYLES, DEFAULT_STYLE
from httpie.input import (Parser, AuthCredentialsArgType, KeyValueArgType,
                          SEP_PROXY, SEP_CREDENTIALS, SEP_GROUP_ALL_ITEMS,
                          OUT_REQ_HEAD, OUT_REQ_BODY, OUT_RESP_HEAD,
                          OUT_RESP_BODY, OUTPUT_OPTIONS,
                          OUTPUT_OPTIONS_DEFAULT, PRETTY_MAP,
                          PRETTY_STDOUT_TTY_ONLY, SessionNameValidator,
                          readable_file_arg)

class HTTPieHelpFormatter(RawDescriptionHelpFormatter):
    """A nicer help formatter.

    Help for arguments can be indented and contain new lines.
    It will be de-dented and arguments in the help
    will be separated by a blank line for better readability.


    """
    def __init__(self, max_help_position=6, *args, **kwargs):
        # A smaller indent for args help.
        kwargs['max_help_position'] = max_help_position
        super(HTTPieHelpFormatter, self).__init__(*args, **kwargs)

    def _split_lines(self, text, width):
        text = dedent(text).strip() + '\n\n'
        return text.splitlines()

parser = Parser(
    formatter_class=HTTPieHelpFormatter,
    description='%s <http://httpie.org>' % __doc__.strip(),
    epilog=dedent("""
    For every --OPTION there is also a --no-OPTION that reverts OPTION
    to its default value.

    Suggestions and bug reports are greatly appreciated:

        https://github.com/jakubroztocil/httpie/issues

    """)
)


#######################################################################
# Positional arguments.
#######################################################################

positional = parser.add_argument_group(
    title='Positional Arguments',
    description=dedent("""
    These arguments come after any flags and in the order they are listed here.
    Only URL is required.

    """)
)
positional.add_argument(
    'method',
    metavar='METHOD',
    nargs=OPTIONAL,
    default=None,
    choices=('GET', 'PUT', 'POST', 'HEAD', 'CONNECT'),
    help="""
    The HTTP method to be used for the request (GET, POST, PUT, DELETE, ...).

    This argument can be omitted in which case HTTPie will use POST if there
    is some data to be sent, otherwise GET:

        $ http example.org               # => GET
        $ http example.org hello=world   # => POST

    """
)
positional.add_argument(
    'url',
    metavar='URL',
    help="""
    The scheme defaults to 'http://' if the URL does not include one.

    You can also use a shorthand for localhost

        $ http :3000                    # => http://localhost:3000
        $ http :/foo                    # => http://localhost/foo

    """
)
positional.add_argument(
    'items',
    metavar='REQUEST_ITEM',
    nargs=ZERO_OR_MORE,
    type=KeyValueArgType(*SEP_GROUP_ALL_ITEMS),
    help=r"""
    Optional key-value pairs to be included in the request. The separator used
    determines the type:

    ':' HTTP headers:

        Referer:http://httpie.org  Cookie:foo=bar  User-Agent:bacon/1.0

    '==' URL parameters to be appended to the request URI:

        search==httpie

    '=' Data fields to be serialized into a JSON object (with --json, -j)
        or form data (with --form, -f):

        name=HTTPie  language=Python  description='CLI HTTP client'

    ':=' Non-string JSON data fields (only with --json, -j):

        awesome:=true  amount:=42  colors:='["red", "green", "blue"]'

    '@' Form file fields (only with --form, -f):

        cs@~/Documents/CV.pdf

    '=@' A data field like '=', but takes a file path and embeds its content:

         essay=@Documents/essay.txt

    ':=@' A raw JSON field like ':=', but takes a file path and embeds its content:

        package:=@./package.json

    You can use a backslash to escape a colliding separator in the field name:

        field-name-with\:colon=value

    """
)


#######################################################################
# Content type.
#######################################################################

content_type = parser.add_argument_group(
    title='Predefined Content Types',
    description=None
)

content_type.add_argument(
    '--json', '-j',
    action='store_true',
    help="""
    (default) Data items from the command line are serialized as a JSON object.
    The Content-Type and Accept headers are set to application/json
    (if not specified).

    """
)
content_type.add_argument(
    '--form', '-f',
    action='store_true',
    help="""
    Data items from the command line are serialized as form fields.

    The Content-Type is set to application/x-www-form-urlencoded (if not
    specified). The presence of any file fields results in a
    multipart/form-data request.

    """
)


#######################################################################
# Output processing
#######################################################################

output_processing = parser.add_argument_group(title='Output Processing')

output_processing.add_argument(
    '--pretty',
    dest='prettify',
    default=PRETTY_STDOUT_TTY_ONLY,
    choices=sorted(PRETTY_MAP.keys()),
    help="""
    Controls output processing. The value can be "none" to not prettify
    the output (default for redirected output), "all" to apply both colors
    and formatting (default for terminal output), "colors", or "format".

    """
)
output_processing.add_argument(
    '--style', '-s',
    dest='style',
    metavar='STYLE',
    default=DEFAULT_STYLE,
    choices=AVAILABLE_STYLES,
    help="""
    Output coloring style (default is "{default}"). One of:

{available}

    For this option to work properly, please make sure that the $TERM
    environment variable is set to "xterm-256color" or similar
    (e.g., via `export TERM=xterm-256color' in your ~/.bashrc).

    """.format(
        default=DEFAULT_STYLE,
        available='\n'.join(
            '{0}{1}'.format(8*' ', line.strip())
            for line in wrap(', '.join(sorted(AVAILABLE_STYLES)), 60)
        ).rstrip(),
    )
)


#######################################################################
# Output options
#######################################################################
output_options = parser.add_argument_group(title='Output Options')

output_options.add_argument(
    '--print', '-p',
    dest='output_options',
    metavar='WHAT',
    help="""
    String specifying what the output should contain:

        '{req_head}' request headers
        '{req_body}' request body
        '{res_head}' response headers
        '{res_body}' response body

    The default behaviour is '{default}' (i.e., the response headers and body
    is printed), if standard output is not redirected. If the output is piped
    to another program or to a file, then only the response body is printed
    by default.

    """
    .format(
        req_head=OUT_REQ_HEAD,
        req_body=OUT_REQ_BODY,
        res_head=OUT_RESP_HEAD,
        res_body=OUT_RESP_BODY,
        default=OUTPUT_OPTIONS_DEFAULT,
    )
)
output_options.add_argument(
    '--verbose', '-v',
    dest='output_options',
    action='store_const',
    const=''.join(OUTPUT_OPTIONS),
    help="""
    Print the whole request as well as the response. Shortcut for --print={0}.

    """
    .format(''.join(OUTPUT_OPTIONS))
)
output_options.add_argument(
    '--headers', '-h',
    dest='output_options',
    action='store_const',
    const=OUT_RESP_HEAD,
    help="""
    Print only the response headers. Shortcut for --print={0}.

    """
    .format(OUT_RESP_HEAD)
)
output_options.add_argument(
    '--body', '-b',
    dest='output_options',
    action='store_const',
    const=OUT_RESP_BODY,
    help="""
    Print only the response body. Shortcut for --print={0}.

    """
    .format(OUT_RESP_BODY)
)

output_options.add_argument(
    '--stream', '-S',
    action='store_true',
    default=False,
    help="""
    Always stream the output by line, i.e., behave like `tail -f'.

    Without --stream and with --pretty (either set or implied),
    HTTPie fetches the whole response before it outputs the processed data.

    Set this option when you want to continuously display a prettified
    long-lived response, such as one from the Twitter streaming API.

    It is useful also without --pretty: It ensures that the output is flushed
    more often and in smaller chunks.

    """
)
output_options.add_argument(
    '--output', '-o',
    type=FileType('a+b'),
    dest='output_file',
    metavar='FILE',
    help="""
    Save output to FILE. If --download is set, then only the response body is
    saved to the file. Other parts of the HTTP exchange are printed to stderr.

    """

)

output_options.add_argument(
    '--download', '-d',
    action='store_true',
    default=False,
    help="""
    Do not print the response body to stdout. Rather, download it and store it
    in a file. The filename is guessed unless specified with --output
    [filename]. This action is similar to the default behaviour of wget.

    """
)

output_options.add_argument(
    '--continue', '-c',
    dest='download_resume',
    action='store_true',
    default=False,
    help="""
    Resume an interrupted download. Note that the --output option needs to be
    specified as well.

    """
)


#######################################################################
# Sessions
#######################################################################

sessions = parser.add_argument_group(title='Sessions')\
                 .add_mutually_exclusive_group(required=False)

session_name_validator = SessionNameValidator(
    'Session name contains invalid characters.'
)

sessions.add_argument(
    '--session',
    metavar='SESSION_NAME_OR_PATH',
    type=session_name_validator,
    help="""
    Create, or reuse and update a session. Within a session, custom headers,
    auth credential, as well as any cookies sent by the server persist between
    requests.

    Session files are stored in:

        {session_dir}/<HOST>/<SESSION_NAME>.json.

    """
    .format(session_dir=DEFAULT_SESSIONS_DIR)
)
sessions.add_argument(
    '--session-read-only',
    metavar='SESSION_NAME_OR_PATH',
    type=session_name_validator,
    help="""
    Create or read a session without updating it form the request/response
    exchange.

    """
)


#######################################################################
# Authentication
#######################################################################

# ``requests.request`` keyword arguments.
auth = parser.add_argument_group(title='Authentication')
auth.add_argument(
    '--auth', '-a',
    metavar='USER[:PASS]',
    type=AuthCredentialsArgType(SEP_CREDENTIALS),
    help="""
    If only the username is provided (-a username), HTTPie will prompt
    for the password.

    """,
)

_auth_plugins = plugin_manager.get_auth_plugins()
auth.add_argument(
    '--auth-type',
    choices=[plugin.auth_type for plugin in _auth_plugins],
    default=_auth_plugins[0].auth_type,
    help="""
    The authentication mechanism to be used. Defaults to "{default}".

    {types}

    """
    .format(default=_auth_plugins[0].auth_type, types='\n    '.join(
        '"{type}": {name}{package}{description}'.format(
            type=plugin.auth_type,
            name=plugin.name,
            package=(
                '' if issubclass(plugin, BuiltinAuthPlugin)
                else ' (provided by %s)' % plugin.package_name
            ),
            description=(
                '' if not plugin.description else
                '\n      ' + ('\n      '.join(wrap(plugin.description)))
            )
        )
        for plugin in _auth_plugins
    )),
)


#######################################################################
# Network
#######################################################################

network = parser.add_argument_group(title='Network')

network.add_argument(
    '--proxy',
    default=[],
    action='append',
    metavar='PROTOCOL:PROXY_URL',
    type=KeyValueArgType(SEP_PROXY),
    help="""
    String mapping protocol to the URL of the proxy
    (e.g. http:http://foo.bar:3128). You can specify multiple proxies with
    different protocols.

    """
)
network.add_argument(
    '--follow',
    default=False,
    action='store_true',
    help="""
    Set this flag if full redirects are allowed (e.g. re-POST-ing of data at
    new Location).

    """
)
network.add_argument(
    '--verify',
    default='yes',
    help="""
    Set to "no" to skip checking the host's SSL certificate. You can also pass
    the path to a CA_BUNDLE file for private certs. You can also set the
    REQUESTS_CA_BUNDLE environment variable. Defaults to "yes".

    """
)

network.add_argument(
    '--cert',
    default=None,
    type=readable_file_arg,
    help="""
    You can specify a local cert to use as client side SSL certificate.
    This file may either contain both private key and certificate or you may
    specify --cert-key separately.

    """
)

network.add_argument(
    '--cert-key',
    default=None,
    type=readable_file_arg,
    help="""
    The private key to use with SSL. Only needed if --cert is given and the
    certificate file does not contain the private key.

    """
)

network.add_argument(
    '--timeout',
    type=float,
    default=30,
    metavar='SECONDS',
    help="""
    The connection timeout of the request in seconds. The default value is
    30 seconds.

    """
)
network.add_argument(
    '--check-status',
    default=False,
    action='store_true',
    help="""
    By default, HTTPie exits with 0 when no network or other fatal errors
    occur. This flag instructs HTTPie to also check the HTTP status code and
    exit with an error if the status indicates one.

    When the server replies with a 4xx (Client Error) or 5xx (Server Error)
    status code, HTTPie exits with 4 or 5 respectively. If the response is a
    3xx (Redirect) and --follow hasn't been set, then the exit status is 3.
    Also an error message is written to stderr if stdout is redirected.

    """
)


#######################################################################
# Troubleshooting
#######################################################################

troubleshooting = parser.add_argument_group(title='Troubleshooting')

troubleshooting.add_argument(
    '--ignore-stdin',
    action='store_true',
    default=False,
    help="""
    Do not attempt to read stdin.

    """
)
troubleshooting.add_argument(
    '--help',
    action='help',
    default=SUPPRESS,
    help="""
    Show this help message and exit.

    """
)
troubleshooting.add_argument(
    '--version',
    action='version',
    version=__version__,
    help="""
    Show version and exit.

    """
)
troubleshooting.add_argument(
    '--traceback',
    action='store_true',
    default=False,
    help="""
    Prints exception traceback should one occur.

    """
)
troubleshooting.add_argument(
    '--debug',
    action='store_true',
    default=False,
    help="""
    Prints exception traceback should one occur, and also other information
    that is useful for debugging HTTPie itself and for reporting bugs.

    """
)
