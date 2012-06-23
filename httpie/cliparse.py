"""
CLI argument parsing logic.

"""
import os
import sys
import re
import json
import argparse

from collections import namedtuple

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
DATA_ITEM_SEPARATORS = {
    SEP_DATA,
    SEP_DATA_RAW_JSON,
    SEP_FILES
}


OUT_REQ_HEADERS = 'H'
OUT_REQ_BODY = 'B'
OUT_RESP_HEADERS = 'h'
OUT_RESP_BODY = 'b'
OUTPUT_OPTIONS = [OUT_REQ_HEADERS,
                  OUT_REQ_BODY,
                  OUT_RESP_HEADERS,
                  OUT_RESP_BODY]


PRETTIFY_STDOUT_TTY_ONLY = object()

DEFAULT_UA = 'HTTPie/%s' % __version__


class HTTPieArgumentParser(argparse.ArgumentParser):

    def parse_args(self, args=None, namespace=None,
                   stdin=sys.stdin,
                   stdin_isatty=sys.stdin.isatty()):
        args = super(HTTPieArgumentParser, self).parse_args(args, namespace)
        self._validate_output_options(args)
        self._validate_auth_options(args)
        self._guess_method(args, stdin_isatty)
        self._parse_items(args)
        if not stdin_isatty:
            self._process_stdin(args, stdin)
        return args

    def _process_stdin(self, args, stdin):
        if args.data:
            self.error('Request body (stdin) and request '
                       'data (key=value) cannot be mixed.')
        args.data = stdin.read()

    def _guess_method(self, args, stdin_isatty=sys.stdin.isatty()):
        """Suggests HTTP method by positional argument values.

        In following description by data item it means one of:
        * simple data item (key=value)
        * JSON raw item (key:=value)
        * file item (key@value)

        If METHOD argument is omitted and no data ITEM is given then method is GET:
        http http://example.com/
            - is shortcut for -
        http GET http://example.com.

        If METHOD argument is omitted but at least one data ITEM
        is present then method is POST:
        http http://example.com/ hello=world
            - is shortcut for -
        http POST http://example.com hello=world.

        If METHOD is specified then http behaves as it is now.

        The first argument should be treated as method
        if it matches ^[a-zA-Z]+$ regexp. Otherwise it is url.

        """
        if args.method is None:
            # Invoked as `http URL'.
            assert not args.items
            if not stdin_isatty:
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
                SEP_DATA,
                SEP_DATA_RAW_JSON,
                SEP_FILES).__call__(args.url)

            args.url = args.method
            args.items.insert(0, item)

            has_data = not stdin_isatty or any(
                item.sep in DATA_ITEM_SEPARATORS for item in args.items)
            if has_data:
                args.method = 'POST'
            else:
                args.method = 'GET'

    def _parse_items(self, args):
        """
        Parse `args.items` into `args.headers`, `args.data` and `args.files`.

        """
        args.headers = CaseInsensitiveDict()
        args.headers['User-Agent'] = DEFAULT_UA
        args.data = OrderedDict()
        args.files = OrderedDict()
        try:
            parse_items(items=args.items, headers=args.headers,
                        data=args.data, files=args.files)
        except ParseError as e:
            if args.traceback:
                raise
            self.error(e.message)

        if args.files and not args.form:
            # We could just switch to --form automatically here,
            # but I think it's better to make it explicit.
            self.error(
                ' You need to set the --form / -f flag to'
                ' to issue a multipart request. File fields: %s'
                % ','.join(args.files.keys()))

    def _validate_output_options(self, args):
        unknown_output_options = set(args.output_options) - set(OUTPUT_OPTIONS)
        if unknown_output_options:
            self.error('Unknown output options: %s' % ','.join(unknown_output_options))

    def _validate_auth_options(self, args):
        if args.auth_type and not args.auth:
            self.error('--auth-type can only be used with --auth')


class ParseError(Exception):
    pass


KeyValue = namedtuple('KeyValue', ['key', 'value', 'sep', 'orig'])


class KeyValueType(object):
    """A type used with `argparse`."""

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
        return KeyValue(key=key, value=value, sep=sep, orig=string)


def parse_items(items, data=None, headers=None, files=None):
    """Parse `KeyValueType` `items` into `data`, `headers` and `files`."""
    if headers is None:
        headers = {}
    if data is None:
        data = {}
    if files is None:
        files = {}
    for item in items:
        value = item.value
        key = item.key
        if item.sep == SEP_HEADERS:
            target = headers
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

    return headers, data, files
