"""Parsing and processing of CLI input (args, auth credentials, files, stdin).

"""
import os
import sys
import re
import json
import mimetypes
import getpass
from io import BytesIO
from argparse import ArgumentParser, ArgumentTypeError

try:
    from collections import OrderedDict
except ImportError:
    OrderedDict = dict

from requests.structures import CaseInsensitiveDict
from requests.compat import str, urlparse


HTTP_POST = 'POST'
HTTP_GET = 'GET'
HTTP = 'http://'
HTTPS = 'https://'


# Various separators used in args
SEP_HEADERS = ':'
SEP_CREDENTIALS = ':'
SEP_PROXY = ':'
SEP_DATA = '='
SEP_DATA_RAW_JSON = ':='
SEP_FILES = '@'
SEP_QUERY = '=='

# Separators that become request data
SEP_GROUP_DATA_ITEMS = frozenset([
    SEP_DATA,
    SEP_DATA_RAW_JSON,
    SEP_FILES
])

# Separators allowed in ITEM arguments
SEP_GROUP_ITEMS = frozenset([
    SEP_HEADERS,
    SEP_QUERY,
    SEP_DATA,
    SEP_DATA_RAW_JSON,
    SEP_FILES
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


class Parser(ArgumentParser):
    """Adds additional logic to `argparse.ArgumentParser`.

    Handles all input (CLI args, file args, stdin), applies defaults,
    and performs extra validation.

    """

    def __init__(self, *args, **kwargs):
        kwargs['add_help'] = False
        super(Parser, self).__init__(*args, **kwargs)

    #noinspection PyMethodOverriding
    def parse_args(self, env, args=None, namespace=None):

        self.env = env

        args = super(Parser, self).parse_args(args, namespace)

        if not args.json and env.config.implicit_content_type == 'form':
            args.form = True

        if args.debug:
            args.traceback = True

        if args.output:
            env.stdout = args.output
            env.stdout_isatty = False

        self._process_output_options(args, env)
        self._process_pretty_options(args, env)
        self._guess_method(args, env)
        self._parse_items(args)

        if not env.stdin_isatty:
            self._body_from_file(args, env.stdin)

        if not (args.url.startswith(HTTP) or args.url.startswith(HTTPS)):
            scheme = HTTPS if env.progname == 'https' else HTTP
            args.url = scheme + args.url

        if args.auth and not args.auth.has_password():
            # Stdin already read (if not a tty) so it's save to prompt.
            args.auth.prompt_password(urlparse(args.url).netloc)

        return args

    def _print_message(self, message, file=None):
        # Sneak in our stderr/stdout.
        file = {
            sys.stdout: self.env.stdout,
            sys.stderr: self.env.stderr,
            None: self.env.stderr
        }.get(file, file)

        super(Parser, self)._print_message(message, file)

    def _body_from_file(self, args, fd):
        """There can only be one source of request data.

        Bytes are always read.

        """
        if args.data:
            self.error('Request body (from stdin or a file) and request '
                       'data (key=value) cannot be mixed.')
        args.data = getattr(fd, 'buffer', fd).read()

    def _guess_method(self, args, env):
        """Set `args.method` if not specified to either POST or GET
        based on whether the request has data or not.

        """
        if args.method is None:
            # Invoked as `http URL'.
            assert not args.items
            if not env.stdin_isatty:
                args.method = HTTP_POST
            else:
                args.method = HTTP_GET

        # FIXME: False positive, e.g., "localhost" matches but is a valid URL.
        elif not re.match('^[a-zA-Z]+$', args.method):
            # Invoked as `http URL item+'. The URL is now in `args.method`
            # and the first ITEM is now incorrectly in `args.url`.
            try:
                # Parse the URL as an ITEM and store it as the first ITEM arg.
                args.items.insert(
                    0, KeyValueArgType(*SEP_GROUP_ITEMS).__call__(args.url))

            except ArgumentTypeError as e:
                if args.traceback:
                    raise
                self.error(e.message)

            else:
                # Set the URL correctly
                args.url = args.method
                # Infer the method
                has_data = not env.stdin_isatty or any(
                    item.sep in SEP_GROUP_DATA_ITEMS for item in args.items)
                args.method = HTTP_POST if has_data else HTTP_GET

    def _parse_items(self, args):
        """Parse `args.items` into `args.headers`, `args.data`,
        `args.`, and `args.files`.

        """
        args.headers = CaseInsensitiveDict()
        args.data = ParamDict() if args.form else OrderedDict()
        args.files = OrderedDict()
        args.params = ParamDict()

        try:
            parse_items(items=args.items,
                        headers=args.headers,
                        data=args.data,
                        files=args.files,
                        params=args.params)
        except ParseError as e:
            if args.traceback:
                raise
            self.error(e.message)

        if args.files and not args.form:
            # `http url @/path/to/file`
            file_fields = list(args.files.keys())
            if file_fields != ['']:
                self.error(
                    'Invalid file fields (perhaps you meant --form?): %s'
                    % ','.join(file_fields))

            fn, fd = args.files['']
            args.files = {}
            self._body_from_file(args, fd)
            if 'Content-Type' not in args.headers:
                mime, encoding = mimetypes.guess_type(fn, strict=False)
                if mime:
                    content_type = mime
                    if encoding:
                        content_type = '%s; charset=%s' % (mime, encoding)
                    args.headers['Content-Type'] = content_type

    def _process_output_options(self, args, env):
        """Apply defaults to output options or validate the provided ones.

        The default output options are stdout-type-sensitive.

        """
        if not args.output_options:
            args.output_options = (OUTPUT_OPTIONS_DEFAULT if env.stdout_isatty
                                else OUTPUT_OPTIONS_DEFAULT_STDOUT_REDIRECTED)

        unknown = set(args.output_options) - OUTPUT_OPTIONS
        if unknown:
            self.error('Unknown output options: %s' % ','.join(unknown))

    def _process_pretty_options(self, args, env):
        if args.prettify == PRETTY_STDOUT_TTY_ONLY:
            args.prettify = PRETTY_MAP['all' if env.stdout_isatty else 'none']
        elif args.prettify and env.is_windows:
            self.error('Only terminal output can be colorized on Windows.')
        else:
            args.prettify = PRETTY_MAP[args.prettify]


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


class KeyValueArgType(object):
    """A key-value pair argument type used with `argparse`.

    Parses a key-value arg and constructs a `KeyValue` instance.
    Used for headers, form data, and other key-value pair types.

    """

    key_value_class = KeyValue

    def __init__(self, *separators):
        self.separators = separators

    def __call__(self, string):
        """Parse `string` and return `self.key_value_class()` instance.

        The best of `self.separators` is determined (first found, longest).
        Back slash escaped characters aren't considered as separators
        (or parts thereof). Literal back slash characters have to be escaped
        as well (r'\\').

        """

        class Escaped(str):
            """Represents an escaped character."""

        def tokenize(s):
            """Tokenize `s`. There are only two token types - strings
            and escaped characters:

            >>> tokenize(r'foo\=bar\\baz')
            ['foo', Escaped('='), 'bar', Escaped('\\'), 'baz']

            """
            tokens = ['']
            esc = False
            for c in s:
                if esc:
                    tokens.extend([Escaped(c), ''])
                    esc = False
                else:
                    if c == '\\':
                        esc = True
                    else:
                        tokens[-1] += c
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
                '"%s" is not a valid value' % string)

        return self.key_value_class(
            key=key, value=value, sep=sep, orig=string)


class AuthCredentials(KeyValue):
    """Represents parsed credentials."""

    def _getpass(self, prompt):
        # To allow mocking.
        return getpass.getpass(prompt)

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


class ParamDict(OrderedDict):
    """Multi-value dict for URL parameters and form data."""

    #noinspection PyMethodOverriding
    def __setitem__(self, key, value):
        """ If `key` is assigned more than once, `self[key]` holds a
        `list` of all the values.

        This allows having multiple fields with the same name in form
        data and URL params.

        """
        # NOTE: Won't work when used for form data with multiple values
        # for a field and a file field is present:
        # https://github.com/kennethreitz/requests/issues/737
        if key not in self:
            super(ParamDict, self).__setitem__(key, value)
        else:
            if not isinstance(self[key], list):
                super(ParamDict, self).__setitem__(key, [self[key]])
            self[key].append(value)


def parse_items(items, data=None, headers=None, files=None, params=None):
    """Parse `KeyValue` `items` into `data`, `headers`, `files`,
    and `params`.

    """
    if headers is None:
        headers = CaseInsensitiveDict()
    if data is None:
        data = OrderedDict()
    if files is None:
        files = OrderedDict()
    if params is None:
        params = ParamDict()

    for item in items:

        value = item.value
        key = item.key

        if item.sep == SEP_HEADERS:
            target = headers
        elif item.sep == SEP_QUERY:
            target = params
        elif item.sep == SEP_FILES:
            try:
                with open(os.path.expanduser(value), 'rb') as f:
                    value = (os.path.basename(value),
                             BytesIO(f.read()))
            except IOError as e:
                raise ParseError(
                    'Invalid argument "%s": %s' % (item.orig, e))
            target = files

        elif item.sep in [SEP_DATA, SEP_DATA_RAW_JSON]:
            if item.sep == SEP_DATA_RAW_JSON:
                try:
                    value = json.loads(item.value)
                except ValueError:
                    raise ParseError('"%s" is not valid JSON' % item.orig)
            target = data

        else:
            raise TypeError(item)

        target[key] = value

    return headers, data, files, params
