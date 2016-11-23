"""Parsing and processing of CLI input (args, auth credentials, files, stdin).

"""
import os
import ssl
import sys
import re
import errno
import mimetypes
import getpass
from io import BytesIO
from collections import namedtuple, Iterable
# noinspection PyCompatibility
from argparse import ArgumentParser, ArgumentTypeError, ArgumentError

# TODO: Use MultiDict for headers once added to `requests`.
# https://github.com/jkbrzt/httpie/issues/130
from httpie.plugins import plugin_manager
from requests.structures import CaseInsensitiveDict

from httpie.compat import OrderedDict, urlsplit, str, is_pypy, is_py27
from httpie.sessions import VALID_SESSION_NAME_PATTERN
from httpie.utils import load_json_preserve_order


# ALPHA *( ALPHA / DIGIT / "+" / "-" / "." )
# <http://tools.ietf.org/html/rfc3986#section-3.1>
URL_SCHEME_RE = re.compile(r'^[a-z][a-z0-9.+-]*://', re.IGNORECASE)

HTTP_POST = 'POST'
HTTP_GET = 'GET'


# Various separators used in args
SEP_HEADERS = ':'
SEP_HEADERS_EMPTY = ';'
SEP_CREDENTIALS = ':'
SEP_PROXY = ':'
SEP_DATA = '='
SEP_DATA_RAW_JSON = ':='
SEP_FILES = '@'
SEP_DATA_EMBED_FILE = '=@'
SEP_DATA_EMBED_RAW_JSON_FILE = ':=@'
SEP_QUERY = '=='

# Separators that become request data
SEP_GROUP_DATA_ITEMS = frozenset([
    SEP_DATA,
    SEP_DATA_RAW_JSON,
    SEP_FILES,
    SEP_DATA_EMBED_FILE,
    SEP_DATA_EMBED_RAW_JSON_FILE
])

# Separators for items whose value is a filename to be embedded
SEP_GROUP_DATA_EMBED_ITEMS = frozenset([
    SEP_DATA_EMBED_FILE,
    SEP_DATA_EMBED_RAW_JSON_FILE,
])

# Separators for raw JSON items
SEP_GROUP_RAW_JSON_ITEMS = frozenset([
    SEP_DATA_RAW_JSON,
    SEP_DATA_EMBED_RAW_JSON_FILE,
])

# Separators allowed in ITEM arguments
SEP_GROUP_ALL_ITEMS = frozenset([
    SEP_HEADERS,
    SEP_HEADERS_EMPTY,
    SEP_QUERY,
    SEP_DATA,
    SEP_DATA_RAW_JSON,
    SEP_FILES,
    SEP_DATA_EMBED_FILE,
    SEP_DATA_EMBED_RAW_JSON_FILE,
])


# Output options
OUT_REQ_HEAD = 'H'
OUT_REQ_BODY = 'B'
OUT_RESP_HEAD = 'h'
OUT_RESP_BODY = 'b'

OUTPUT_OPTIONS = frozenset([
    OUT_REQ_HEAD,
    OUT_REQ_BODY,
    OUT_RESP_HEAD,
    OUT_RESP_BODY
])

# Pretty
PRETTY_MAP = {
    'all': ['format', 'colors'],
    'colors': ['colors'],
    'format': ['format'],
    'none': []
}
PRETTY_STDOUT_TTY_ONLY = object()


# Defaults
OUTPUT_OPTIONS_DEFAULT = OUT_RESP_HEAD + OUT_RESP_BODY
OUTPUT_OPTIONS_DEFAULT_STDOUT_REDIRECTED = OUT_RESP_BODY


SSL_VERSION_ARG_MAPPING = {
    'ssl2.3': 'PROTOCOL_SSLv23',
    'ssl3': 'PROTOCOL_SSLv3',
    'tls1': 'PROTOCOL_TLSv1',
    'tls1.1': 'PROTOCOL_TLSv1_1',
    'tls1.2': 'PROTOCOL_TLSv1_2',
}
SSL_VERSION_ARG_MAPPING = dict(
    (cli_arg, getattr(ssl, ssl_constant))
    for cli_arg, ssl_constant in SSL_VERSION_ARG_MAPPING.items()
    if hasattr(ssl, ssl_constant)
)


class HTTPieArgumentParser(ArgumentParser):
    """Adds additional logic to `argparse.ArgumentParser`.

    Handles all input (CLI args, file args, stdin), applies defaults,
    and performs extra validation.

    """

    def __init__(self, *args, **kwargs):
        kwargs['add_help'] = False
        super(HTTPieArgumentParser, self).__init__(*args, **kwargs)

    # noinspection PyMethodOverriding
    def parse_args(self, env, args=None, namespace=None):

        self.env = env
        self.args, no_options = super(HTTPieArgumentParser, self)\
            .parse_known_args(args, namespace)

        if self.args.debug:
            self.args.traceback = True

        # Arguments processing and environment setup.
        self._apply_no_options(no_options)
        self._validate_download_options()
        self._setup_standard_streams()
        self._process_output_options()
        self._process_pretty_options()
        self._guess_method()
        self._parse_items()
        if not self.args.ignore_stdin and not env.stdin_isatty:
            self._body_from_file(self.env.stdin)
        if not URL_SCHEME_RE.match(self.args.url):
            scheme = self.args.default_scheme + "://"

            # See if we're using curl style shorthand for localhost (:3000/foo)
            shorthand = re.match(r'^:(?!:)(\d*)(/?.*)$', self.args.url)
            if shorthand:
                port = shorthand.group(1)
                rest = shorthand.group(2)
                self.args.url = scheme + 'localhost'
                if port:
                    self.args.url += ':' + port
                self.args.url += rest
            else:
                self.args.url = scheme + self.args.url
        self._process_auth()

        return self.args

    # noinspection PyShadowingBuiltins
    def _print_message(self, message, file=None):
        # Sneak in our stderr/stdout.
        file = {
            sys.stdout: self.env.stdout,
            sys.stderr: self.env.stderr,
            None: self.env.stderr
        }.get(file, file)
        if not hasattr(file, 'buffer') and isinstance(message, str):
            message = message.encode(self.env.stdout_encoding)
        super(HTTPieArgumentParser, self)._print_message(message, file)

    def _setup_standard_streams(self):
        """
        Modify `env.stdout` and `env.stdout_isatty` based on args, if needed.

        """
        self.args.output_file_specified = bool(self.args.output_file)
        if self.args.download:
            # FIXME: Come up with a cleaner solution.
            if not self.args.output_file and not self.env.stdout_isatty:
                # Use stdout as the download output file.
                self.args.output_file = self.env.stdout
            # With `--download`, we write everything that would normally go to
            # `stdout` to `stderr` instead. Let's replace the stream so that
            # we don't have to use many `if`s throughout the codebase.
            # The response body will be treated separately.
            self.env.stdout = self.env.stderr
            self.env.stdout_isatty = self.env.stderr_isatty
        elif self.args.output_file:
            # When not `--download`ing, then `--output` simply replaces
            # `stdout`. The file is opened for appending, which isn't what
            # we want in this case.
            self.args.output_file.seek(0)
            try:
                self.args.output_file.truncate()
            except IOError as e:
                if e.errno == errno.EINVAL:
                    # E.g. /dev/null on Linux.
                    pass
                else:
                    raise
            self.env.stdout = self.args.output_file
            self.env.stdout_isatty = False

    def _process_auth(self):
        # TODO: refactor
        self.args.auth_plugin = None
        default_auth_plugin = plugin_manager.get_auth_plugins()[0]
        auth_type_set = self.args.auth_type is not None
        url = urlsplit(self.args.url)

        if self.args.auth is None and not auth_type_set:
            if url.username is not None:
                # Handle http://username:password@hostname/
                username = url.username
                password = url.password or ''
                self.args.auth = AuthCredentials(
                    key=username,
                    value=password,
                    sep=SEP_CREDENTIALS,
                    orig=SEP_CREDENTIALS.join([username, password])
                )

        if self.args.auth is not None or auth_type_set:
            if not self.args.auth_type:
                self.args.auth_type = default_auth_plugin.auth_type
            plugin = plugin_manager.get_auth_plugin(self.args.auth_type)()

            if plugin.auth_require and self.args.auth is None:
                self.error('--auth required')

            plugin.raw_auth = self.args.auth
            self.args.auth_plugin = plugin
            already_parsed = isinstance(self.args.auth, AuthCredentials)

            if self.args.auth is None or not plugin.auth_parse:
                self.args.auth = plugin.get_auth()
            else:
                if already_parsed:
                    # from the URL
                    credentials = self.args.auth
                else:
                    credentials = parse_auth(self.args.auth)

                if (not credentials.has_password() and
                        plugin.prompt_password):
                    if self.args.ignore_stdin:
                        # Non-tty stdin read by now
                        self.error(
                            'Unable to prompt for passwords because'
                            ' --ignore-stdin is set.'
                        )
                    credentials.prompt_password(url.netloc)
                self.args.auth = plugin.get_auth(
                    username=credentials.key,
                    password=credentials.value,
                )

    def _apply_no_options(self, no_options):
        """For every `--no-OPTION` in `no_options`, set `args.OPTION` to
        its default value. This allows for un-setting of options, e.g.,
        specified in config.

        """
        invalid = []

        for option in no_options:
            if not option.startswith('--no-'):
                invalid.append(option)
                continue

            # --no-option => --option
            inverted = '--' + option[5:]
            for action in self._actions:
                if inverted in action.option_strings:
                    setattr(self.args, action.dest, action.default)
                    break
            else:
                invalid.append(option)

        if invalid:
            msg = 'unrecognized arguments: %s'
            self.error(msg % ' '.join(invalid))

    def _body_from_file(self, fd):
        """There can only be one source of request data.

        Bytes are always read.

        """
        if self.args.data:
            self.error('Request body (from stdin or a file) and request '
                       'data (key=value) cannot be mixed.')
        self.args.data = getattr(fd, 'buffer', fd).read()

    def _guess_method(self):
        """Set `args.method` if not specified to either POST or GET
        based on whether the request has data or not.

        """
        if self.args.method is None:
            # Invoked as `http URL'.
            assert not self.args.items
            if not self.args.ignore_stdin and not self.env.stdin_isatty:
                self.args.method = HTTP_POST
            else:
                self.args.method = HTTP_GET

        # FIXME: False positive, e.g., "localhost" matches but is a valid URL.
        elif not re.match('^[a-zA-Z]+$', self.args.method):
            # Invoked as `http URL item+'. The URL is now in `args.method`
            # and the first ITEM is now incorrectly in `args.url`.
            try:
                # Parse the URL as an ITEM and store it as the first ITEM arg.
                self.args.items.insert(0, KeyValueArgType(
                    *SEP_GROUP_ALL_ITEMS).__call__(self.args.url))

            except ArgumentTypeError as e:
                if self.args.traceback:
                    raise
                self.error(e.args[0])

            else:
                # Set the URL correctly
                self.args.url = self.args.method
                # Infer the method
                has_data = (
                    (not self.args.ignore_stdin and
                     not self.env.stdin_isatty) or
                    any(item.sep in SEP_GROUP_DATA_ITEMS
                        for item in self.args.items)
                )
                self.args.method = HTTP_POST if has_data else HTTP_GET

    def _parse_items(self):
        """Parse `args.items` into `args.headers`, `args.data`, `args.params`,
         and `args.files`.

        """
        try:
            items = parse_items(
                items=self.args.items,
                data_class=ParamsDict if self.args.form else OrderedDict
            )
        except ParseError as e:
            if self.args.traceback:
                raise
            self.error(e.args[0])
        else:
            self.args.headers = items.headers
            self.args.data = items.data
            self.args.files = items.files
            self.args.params = items.params

        if self.args.files and not self.args.form:
            # `http url @/path/to/file`
            file_fields = list(self.args.files.keys())
            if file_fields != ['']:
                self.error(
                    'Invalid file fields (perhaps you meant --form?): %s'
                    % ','.join(file_fields))

            fn, fd, ct = self.args.files['']
            self.args.files = {}

            self._body_from_file(fd)

            if 'Content-Type' not in self.args.headers:
                content_type = get_content_type(fn)
                if content_type:
                    self.args.headers['Content-Type'] = content_type

    def _process_output_options(self):
        """Apply defaults to output options, or validate the provided ones.

        The default output options are stdout-type-sensitive.

        """
        def check_options(value, option):
            unknown = set(value) - OUTPUT_OPTIONS
            if unknown:
                self.error('Unknown output options: {0}={1}'.format(
                    option,
                    ','.join(unknown)
                ))

        if self.args.verbose:
            self.args.all = True

        if self.args.output_options is None:
            if self.args.verbose:
                self.args.output_options = ''.join(OUTPUT_OPTIONS)
            else:
                self.args.output_options = (
                    OUTPUT_OPTIONS_DEFAULT
                    if self.env.stdout_isatty
                    else OUTPUT_OPTIONS_DEFAULT_STDOUT_REDIRECTED
                )

        if self.args.output_options_history is None:
            self.args.output_options_history = self.args.output_options

        check_options(self.args.output_options, '--print')
        check_options(self.args.output_options_history, '--history-print')

        if self.args.download and OUT_RESP_BODY in self.args.output_options:
            # Response body is always downloaded with --download and it goes
            # through a different routine, so we remove it.
            self.args.output_options = str(
                set(self.args.output_options) - set(OUT_RESP_BODY))

    def _process_pretty_options(self):
        if self.args.prettify == PRETTY_STDOUT_TTY_ONLY:
            self.args.prettify = PRETTY_MAP[
                'all' if self.env.stdout_isatty else 'none']
        elif (self.args.prettify and self.env.is_windows and
              self.args.output_file):
            self.error('Only terminal output can be colorized on Windows.')
        else:
            # noinspection PyTypeChecker
            self.args.prettify = PRETTY_MAP[self.args.prettify]

    def _validate_download_options(self):
        if not self.args.download:
            if self.args.download_resume:
                self.error('--continue only works with --download')
        if self.args.download_resume and not (
                self.args.download and self.args.output_file):
            self.error('--continue requires --output to be specified')


class ParseError(Exception):
    pass


class KeyValue(object):
    """Base key-value pair parsed from CLI."""

    def __init__(self, key, value, sep, orig):
        self.key = key
        self.value = value
        self.sep = sep
        self.orig = orig

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __repr__(self):
        return repr(self.__dict__)


class SessionNameValidator(object):

    def __init__(self, error_message):
        self.error_message = error_message

    def __call__(self, value):
        # Session name can be a path or just a name.
        if (os.path.sep not in value and
                not VALID_SESSION_NAME_PATTERN.search(value)):
            raise ArgumentError(None, self.error_message)
        return value


class KeyValueArgType(object):
    """A key-value pair argument type used with `argparse`.

    Parses a key-value arg and constructs a `KeyValue` instance.
    Used for headers, form data, and other key-value pair types.

    """

    key_value_class = KeyValue

    def __init__(self, *separators):
        self.separators = separators
        self.special_characters = set('\\')
        for separator in separators:
            self.special_characters.update(separator)

    def __call__(self, string):
        """Parse `string` and return `self.key_value_class()` instance.

        The best of `self.separators` is determined (first found, longest).
        Back slash escaped characters aren't considered as separators
        (or parts thereof). Literal back slash characters have to be escaped
        as well (r'\\').

        """

        class Escaped(str):
            """Represents an escaped character."""

        def tokenize(string):
            """Tokenize `string`. There are only two token types - strings
            and escaped characters:

            tokenize(r'foo\=bar\\baz')
            => ['foo', Escaped('='), 'bar', Escaped('\\'), 'baz']

            """
            tokens = ['']
            characters = iter(string)
            for char in characters:
                if char == '\\':
                    char = next(characters, '')
                    if char not in self.special_characters:
                        tokens[-1] += '\\' + char
                    else:
                        tokens.extend([Escaped(char), ''])
                else:
                    tokens[-1] += char
            return tokens

        tokens = tokenize(string)

        # Sorting by length ensures that the longest one will be
        # chosen as it will overwrite any shorter ones starting
        # at the same position in the `found` dictionary.
        separators = sorted(self.separators, key=len)

        for i, token in enumerate(tokens):

            if isinstance(token, Escaped):
                continue

            found = {}
            for sep in separators:
                pos = token.find(sep)
                if pos != -1:
                    found[pos] = sep

            if found:
                # Starting first, longest separator found.
                sep = found[min(found.keys())]

                key, value = token.split(sep, 1)

                # Any preceding tokens are part of the key.
                key = ''.join(tokens[:i]) + key

                # Any following tokens are part of the value.
                value += ''.join(tokens[i + 1:])

                break

        else:
            raise ArgumentTypeError(
                u'"%s" is not a valid value' % string)

        return self.key_value_class(
            key=key, value=value, sep=sep, orig=string)


class AuthCredentials(KeyValue):
    """Represents parsed credentials."""

    def _getpass(self, prompt):
        # To allow mocking.
        return getpass.getpass(str(prompt))

    def has_password(self):
        return self.value is not None

    def prompt_password(self, host):
        try:
            self.value = self._getpass(
                'http: password for %s@%s: ' % (self.key, host))
        except (EOFError, KeyboardInterrupt):
            sys.stderr.write('\n')
            sys.exit(0)


class AuthCredentialsArgType(KeyValueArgType):
    """A key-value arg type that parses credentials."""

    key_value_class = AuthCredentials

    def __call__(self, string):
        """Parse credentials from `string`.

        ("username" or "username:password").

        """
        try:
            return super(AuthCredentialsArgType, self).__call__(string)
        except ArgumentTypeError:
            # No password provided, will prompt for it later.
            return self.key_value_class(
                key=string,
                value=None,
                sep=SEP_CREDENTIALS,
                orig=string
            )


parse_auth = AuthCredentialsArgType(SEP_CREDENTIALS)


class RequestItemsDict(OrderedDict):
    """Multi-value dict for URL parameters and form data."""

    if is_pypy and is_py27:
        # Manually set keys when initialized with an iterable as PyPy
        # doesn't call __setitem__ in such case (pypy3 does).
        def __init__(self, *args, **kwargs):
            if len(args) == 1 and isinstance(args[0], Iterable):
                super(RequestItemsDict, self).__init__(**kwargs)
                for k, v in args[0]:
                    self[k] = v
            else:
                super(RequestItemsDict, self).__init__(*args, **kwargs)

    # noinspection PyMethodOverriding
    def __setitem__(self, key, value):
        """ If `key` is assigned more than once, `self[key]` holds a
        `list` of all the values.

        This allows having multiple fields with the same name in form
        data and URL params.

        """
        assert not isinstance(value, list)
        if key not in self:
            super(RequestItemsDict, self).__setitem__(key, value)
        else:
            if not isinstance(self[key], list):
                super(RequestItemsDict, self).__setitem__(key, [self[key]])
            self[key].append(value)


class ParamsDict(RequestItemsDict):
    pass


class DataDict(RequestItemsDict):

    def items(self):
        for key, values in super(RequestItemsDict, self).items():
            if not isinstance(values, list):
                values = [values]
            for value in values:
                yield key, value


RequestItems = namedtuple('RequestItems',
                          ['headers', 'data', 'files', 'params'])


def get_content_type(filename):
    """
    Return the content type for ``filename`` in format appropriate
    for Content-Type headers, or ``None`` if the file type is unknown
    to ``mimetypes``.

    """
    mime, encoding = mimetypes.guess_type(filename, strict=False)
    if mime:
        content_type = mime
        if encoding:
            content_type = '%s; charset=%s' % (mime, encoding)
        return content_type


def parse_items(items,
                headers_class=CaseInsensitiveDict,
                data_class=OrderedDict,
                files_class=DataDict,
                params_class=ParamsDict):
    """Parse `KeyValue` `items` into `data`, `headers`, `files`,
    and `params`.

    """
    headers = []
    data = []
    files = []
    params = []
    for item in items:
        value = item.value
        if item.sep == SEP_HEADERS:
            if value == '':
                # No value => unset the header
                value = None
            target = headers
        elif item.sep == SEP_HEADERS_EMPTY:
            if item.value:
                raise ParseError(
                    'Invalid item "%s" '
                    '(to specify an empty header use `Header;`)'
                    % item.orig
                )
            target = headers
        elif item.sep == SEP_QUERY:
            target = params
        elif item.sep == SEP_FILES:
            try:
                with open(os.path.expanduser(value), 'rb') as f:
                    value = (os.path.basename(value),
                             BytesIO(f.read()),
                             get_content_type(value))
            except IOError as e:
                raise ParseError('"%s": %s' % (item.orig, e))
            target = files

        elif item.sep in SEP_GROUP_DATA_ITEMS:

            if item.sep in SEP_GROUP_DATA_EMBED_ITEMS:
                try:
                    with open(os.path.expanduser(value), 'rb') as f:
                        value = f.read().decode('utf8')
                except IOError as e:
                    raise ParseError('"%s": %s' % (item.orig, e))
                except UnicodeDecodeError:
                    raise ParseError(
                        '"%s": cannot embed the content of "%s",'
                        ' not a UTF8 or ASCII-encoded text file'
                        % (item.orig, item.value)
                    )

            if item.sep in SEP_GROUP_RAW_JSON_ITEMS:
                try:
                    value = load_json_preserve_order(value)
                except ValueError as e:
                    raise ParseError('"%s": %s' % (item.orig, e))
            target = data

        else:
            raise TypeError(item)

        target.append((item.key, value))

    return RequestItems(headers_class(headers),
                        data_class(data),
                        files_class(files),
                        params_class(params))


def readable_file_arg(filename):
    try:
        open(filename, 'rb')
    except IOError as ex:
        raise ArgumentTypeError('%s: %s' % (filename, ex.args[1]))
    return filename
