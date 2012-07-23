"""
CLI argument parsing logic.

"""
import os
import sys
import re
import json
import argparse
import mimetypes
import getpass

try:
    from collections import OrderedDict
except ImportError:
    OrderedDict = dict

from requests.structures import CaseInsensitiveDict

from . import __version__


SEP_COMMON = ':'
SEP_HEADERS = SEP_COMMON
SEP_DATA = '='
SEP_DATA_RAW_JSON = ':='
SEP_FILES = '@'
SEP_QUERY = '=:'
DATA_ITEM_SEPARATORS = [
    SEP_DATA,
    SEP_DATA_RAW_JSON,
    SEP_FILES
]


OUT_REQ_HEAD = 'H'
OUT_REQ_BODY = 'B'
OUT_RESP_HEAD = 'h'
OUT_RESP_BODY = 'b'
OUTPUT_OPTIONS = [OUT_REQ_HEAD,
                  OUT_REQ_BODY,
                  OUT_RESP_HEAD,
                  OUT_RESP_BODY]


PRETTIFY_STDOUT_TTY_ONLY = object()

DEFAULT_UA = 'HTTPie/%s' % __version__


class Parser(argparse.ArgumentParser):

    def parse_args(self, env, args=None, namespace=None):

        args = super(Parser, self).parse_args(args, namespace)

        self._process_output_options(args, env)
        self._validate_auth_options(args)
        self._guess_method(args, env)
        self._parse_items(args)

        if not env.stdin_isatty:
            self._body_from_file(args, env.stdin)

        if args.auth and not args.auth.has_password():
            # stdin has already been read (if not a tty) so
            # it's save to prompt now.
            args.auth.prompt_password()

        return args

    def _body_from_file(self, args, f):
        if args.data:
            self.error('Request body (from stdin or a file) and request '
                       'data (key=value) cannot be mixed.')
        args.data = f.read()

    def _guess_method(self, args, env):
        """
        Set `args.method`, if not specified, to either POST or GET
        based on whether the request has data or not.

        """
        if args.method is None:
            # Invoked as `http URL'.
            assert not args.items
            if not env.stdin_isatty:
                args.method = 'POST'
            else:
                args.method = 'GET'
        # FIXME: False positive, e.g., "localhost" matches but is a valid URL.
        elif not re.match('^[a-zA-Z]+$', args.method):
            # Invoked as `http URL item+':
            # - The URL is now in `args.method`.
            # - The first item is now in `args.url`.
            #
            # So we need to:
            # - Guess the HTTP method.
            # - Set `args.url` correctly.
            # - Parse the first item and move it to `args.items[0]`.

            item = KeyValueType(
                SEP_COMMON,
                SEP_QUERY,
                SEP_DATA,
                SEP_DATA_RAW_JSON,
                SEP_FILES).__call__(args.url)

            args.url = args.method
            args.items.insert(0, item)

            has_data = not env.stdin_isatty or any(
                item.sep in DATA_ITEM_SEPARATORS for item in args.items)
            if has_data:
                args.method = 'POST'
            else:
                args.method = 'GET'

    def _parse_items(self, args):
        """
        Parse `args.items` into `args.headers`,
        `args.data`, `args.queries`, and `args.files`.

        """
        args.headers = CaseInsensitiveDict()
        args.headers['User-Agent'] = DEFAULT_UA
        args.data = OrderedDict()
        args.files = OrderedDict()
        args.queries = CaseInsensitiveDict()
        try:
            parse_items(items=args.items,
                        headers=args.headers,
                        data=args.data,
                        files=args.files,
                        queries=args.queries)
        except ParseError as e:
            if args.traceback:
                raise
            self.error(e.message)

        if args.files and not args.form:
            # `http url @/path/to/file`
            # It's not --form so the file contents will be used as the
            # body of the requests. Also, we try to detect the appropriate
            # Content-Type.
            if len(args.files) > 1:
                self.error(
                    'Only one file can be specified unless'
                    ' --form is used. File fields: %s'
                    % ','.join(args.files.keys()))
            f = list(args.files.values())[0]
            self._body_from_file(args, f)
            args.files = {}
            if 'Content-Type' not in args.headers:
                mime, encoding = mimetypes.guess_type(f.name, strict=False)
                if mime:
                    content_type = mime
                    if encoding:
                        content_type = '%s; charset=%s' % (mime, encoding)
                    args.headers['Content-Type'] = content_type

    def _process_output_options(self, args, env):
        if not args.output_options:
            if env.stdout_isatty:
                args.output_options = OUT_RESP_HEAD + OUT_RESP_BODY
            else:
                args.output_options = OUT_RESP_BODY

        unknown = set(args.output_options) - set(OUTPUT_OPTIONS)
        if unknown:
            self.error(
                'Unknown output options: %s' %
                ','.join(unknown)
            )

    def _validate_auth_options(self, args):
        if args.auth_type and not args.auth:
            self.error('--auth-type can only be used with --auth')


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


class KeyValueType(object):
    """A type used with `argparse`."""

    key_value_class = KeyValue

    def __init__(self, *separators):
        self.separators = separators
        self.escapes = ['\\\\' + sep for sep in separators]

    def __call__(self, string):
        found = {}
        found_escapes = []
        for esc in self.escapes:
            found_escapes += [m.span() for m in re.finditer(esc, string)]
        for sep in self.separators:
            matches = re.finditer(sep, string)
            for match in matches:
                start, end = match.span()
                inside_escape = False
                for estart, eend in found_escapes:
                    if start >= estart and end <= eend:
                        inside_escape = True
                        break
                if start in found and len(found[start]) > len(sep):
                    break
                if not inside_escape:
                    found[start] = sep

        if not found:
            raise argparse.ArgumentTypeError(
                '"%s" is not a valid value' % string)

        # split the string at the earliest non-escaped separator.
        seploc = min(found.keys())
        sep = found[seploc]
        key = string[:seploc]
        value = string[seploc + len(sep):]

        # remove escape chars
        for sepstr in self.separators:
            key = key.replace('\\' + sepstr, sepstr)
            value = value.replace('\\' + sepstr, sepstr)
        return self.key_value_class(key=key, value=value, sep=sep, orig=string)


class AuthCredentials(KeyValue):
    """
    Represents parsed credentials.

    """
    def _getpass(self, prompt):
        # To allow mocking.
        return getpass.getpass(prompt)

    def has_password(self):
        return self.value is not None

    def prompt_password(self):
        try:
            self.value = self._getpass("Password for user '%s': " % self.key)
        except (EOFError, KeyboardInterrupt):
            sys.stderr.write('\n')
            sys.exit(0)


class AuthCredentialsType(KeyValueType):

    key_value_class = AuthCredentials

    def __call__(self, string):
        try:
            return super(AuthCredentialsType, self).__call__(string)
        except argparse.ArgumentTypeError:
            # No password provided, will prompt for it later.
            return self.key_value_class(
                key=string,
                value=None,
                sep=SEP_COMMON,
                orig=string
            )


def parse_items(items, data=None, headers=None, files=None, queries=None):
    """
    Parse `KeyValueType` `items` into `data`, `headers`, `files`,
    and `queries`.

    """
    if headers is None:
        headers = {}
    if data is None:
        data = {}
    if files is None:
        files = {}
    if queries is None:
        queries = {}
    for item in items:
        value = item.value
        key = item.key
        if item.sep == SEP_HEADERS:
            target = headers
        elif item.sep == SEP_QUERY:
            target = queries
        elif item.sep == SEP_FILES:
            try:
                value = open(os.path.expanduser(item.value), 'r')
            except IOError as e:
                raise ParseError(
                    'Invalid argument %r. %s' % (item.orig, e))
            if not key:
                key = os.path.basename(value.name)
            target = files
        elif item.sep in [SEP_DATA, SEP_DATA_RAW_JSON]:
            if item.sep == SEP_DATA_RAW_JSON:
                try:
                    value = json.loads(item.value)
                except ValueError:
                    raise ParseError('%s is not valid JSON' % item.orig)
            target = data
        else:
            raise ParseError('%s is not valid item' % item.orig)

        if key in target:
            ParseError('duplicate item %s (%s)' % (item.key, item.orig))

        target[key] = value

    return headers, data, files, queries
