"""CLI arguments definition.

NOTE: the CLI interface may change before reaching v1.0.

"""
# noinspection PyCompatibility
from argparse import (
    RawDescriptionHelpFormatter, FileType,
    OPTIONAL, ZERO_OR_MORE, SUPPRESS
)
from textwrap import dedent, wrap

from httpie import __doc__, __version__
from httpie.input import (
    FollowRule, HTTPieArgumentParser, KeyValueArgType,
    SEP_PROXY, SEP_GROUP_ALL_ITEMS,
    OUT_REQ_HEAD, OUT_REQ_BODY, OUT_RESP_HEAD,
    OUT_RESP_BODY, OUTPUT_OPTIONS,
    OUTPUT_OPTIONS_DEFAULT, PRETTY_MAP,
    PRETTY_STDOUT_TTY_ONLY, SessionNameValidator,
    readable_file_arg, SSL_VERSION_ARG_MAPPING
)
from httpie.output.formatters.colors import (
    AVAILABLE_STYLES, DEFAULT_STYLE, AUTO_STYLE
)
from httpie.plugins import plugin_manager
from httpie.plugins.builtin import BuiltinAuthPlugin
from httpie.sessions import DEFAULT_SESSIONS_DIR


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


parser = HTTPieArgumentParser(
    prog='http',
    formatter_class=HTTPieHelpFormatter,
    description='%s <http://httpie.org>' % __doc__.strip(),
    epilog=dedent("""
    For every --OPTION there is also a --no-OPTION that reverts OPTION
    to its default value.

    Suggestions and bug reports are greatly appreciated:

        https://github.com/jakubroztocil/httpie/issues

    """),
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
    (You can override this with: --default-scheme=https)

    You can also use a shorthand for localhost

        $ http :3000                    # => http://localhost:3000
        $ http :/foo                    # => http://localhost/foo

    """
)
positional.add_argument(
    'items',
    metavar='REQUEST_ITEM',
    nargs=ZERO_OR_MORE,
    default=None,
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

{available_styles}

    The "{auto_style}" style follows your terminal's ANSI color styles.

    For non-{auto_style} styles to work properly, please make sure that the
    $TERM environment variable is set to "xterm-256color" or similar
    (e.g., via `export TERM=xterm-256color' in your ~/.bashrc).

    """.format(
        default=DEFAULT_STYLE,
        available_styles='\n'.join(
            '{0}{1}'.format(8 * ' ', line.strip())
            for line in wrap(', '.join(sorted(AVAILABLE_STYLES)), 60)
        ).rstrip(),
        auto_style=AUTO_STYLE,
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
    '--verbose', '-v',
    dest='verbose',
    action='store_true',
    help="""
    Verbose output. Print the whole request as well as the response. Also print
    any intermediary requests/responses (such as redirects).
    It's a shortcut for: --all --print={0}

    """
    .format(''.join(OUTPUT_OPTIONS))
)
output_options.add_argument(
    '--all',
    default=False,
    action='store_true',
    help="""
    By default, only the final request/response is shown. Use this flag to show
    any intermediary requests/responses as well. Intermediary requests include
    followed redirects (with --follow), the first unauthorized request when
    Digest auth is used (--auth=digest), etc.

    """
)
output_options.add_argument(
    '--history-print', '-P',
    dest='output_options_history',
    metavar='WHAT',
    help="""
    The same as --print, -p but applies only to intermediary requests/responses
    (such as redirects) when their inclusion is enabled with --all. If this
    options is not specified, then they are formatted the same way as the final
    response.

    """
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
    Save output to FILE instead of stdout. If --download is also set, then only
    the response body is saved to FILE. Other parts of the HTTP exchange are
    printed to stderr.

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
    default=None,
    metavar='USER[:PASS]',
    help="""
    If only the username is provided (-a username), HTTPie will prompt
    for the password.

    """,
)


class _AuthTypeLazyChoices(object):
    # Needed for plugin testing

    def __contains__(self, item):
        return item in plugin_manager.get_auth_plugin_mapping()

    def __iter__(self):
        return iter(sorted(plugin_manager.get_auth_plugin_mapping().keys()))


_auth_plugins = plugin_manager.get_auth_plugins()
auth.add_argument(
    '--auth-type', '-A',
    choices=_AuthTypeLazyChoices(),
    default=None,
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
    '--follow', '-F',
    default=False,
    action='store_true',
    help="""
    Follow 30x Location redirects.

    Unless overridden via --follow-rule, HTTPie will:
    * Follow only 301, 302, 303, 307 and 308.
    * Resend request data only for 307 and 308.
    * Never resend cookies specified on the command line.
    * Use the original request method in the follow request except for these
      cases which will use GET:
          - The response was 301 and the original request was POST.
          - The response was 302 or 303 and the original request was not HEAD.

    """
)
network.add_argument(
    '--follow-rule',
    action='append',
    # Maybe nicer to put the exact syntax in metavar but we cannot because of a Python bug that is
    # not fixed in all the versions we support (https://github.com/python/cpython/pull/1826)
    metavar='RULE',
    type=FollowRule,
    default=None,
    help="""
    String specifying how to follow a Location redirect:

        CODE:METHOD[:nodata][:samecookies]

    e.g. "301:POST" means a POST will be sent after receiving a 301.

        "nodata":   Do not resend the request data (by default it is resent).
        "samecookies":  Send exactly the same cookies as the original request.

    You can specify multiple rules with different codes. When this option is
    used, --follow is implied and HTTPie will only follow codes that have a
    matching rule.

    """
)
network.add_argument(
    '--post301',
    action='store_true',
    default=False,
    help="""
    Shorthand for --follow-rule 301:POST

    """
)
network.add_argument(
    '--post302',
    action='store_true',
    default=False,
    help="""
    Shorthand for --follow-rule 302:POST

    """
)
network.add_argument(
    '--post303',
    action='store_true',
    default=False,
    help="""
    Shorthand for --follow-rule 303:POST

    """
)
network.add_argument(
    '--max-redirects',
    type=int,
    default=30,
    help="""
    By default, requests have a limit of 30 redirects (works with --follow).

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
# SSL
#######################################################################

ssl = parser.add_argument_group(title='SSL')
ssl.add_argument(
    '--verify',
    default='yes',
    help="""
    Set to "no" (or "false") to skip checking the host's SSL certificate.
    Defaults to "yes" ("true"). You can also pass the path to a CA_BUNDLE file
    for private certs. (Or you can set the REQUESTS_CA_BUNDLE environment
    variable instead.)
    """
)
ssl.add_argument(
    '--ssl',  # TODO: Maybe something more general, such as --secure-protocol?
    dest='ssl_version',
    choices=list(sorted(SSL_VERSION_ARG_MAPPING.keys())),
    help="""
    The desired protocol version to use. This will default to
    SSL v2.3 which will negotiate the highest protocol that both
    the server and your installation of OpenSSL support. Available protocols
    may vary depending on OpenSSL installation (only the supported ones
    are shown here).

    """
)
ssl.add_argument(
    '--cert',
    default=None,
    type=readable_file_arg,
    help="""
    You can specify a local cert to use as client side SSL certificate.
    This file may either contain both private key and certificate or you may
    specify --cert-key separately.

    """
)

ssl.add_argument(
    '--cert-key',
    default=None,
    type=readable_file_arg,
    help="""
    The private key to use with SSL. Only needed if --cert is given and the
    certificate file does not contain the private key.

    """
)

#######################################################################
# Troubleshooting
#######################################################################

troubleshooting = parser.add_argument_group(title='Troubleshooting')

troubleshooting.add_argument(
    '--ignore-stdin', '-I',
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
    Prints the exception traceback should one occur.

    """
)
troubleshooting.add_argument(
    '--default-scheme',
    default="http",
    help="""
    The default scheme to use if not specified in the URL.

    """
)
troubleshooting.add_argument(
    '--debug',
    action='store_true',
    default=False,
    help="""
    Prints the exception traceback should one occur, as well as other
    information useful for debugging HTTPie itself and for reporting bugs.

    """
)
