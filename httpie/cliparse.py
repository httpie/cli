"""
CLI argument parsing logic.

"""
import os
import json
import re
from collections import namedtuple
try:
    from collections import OrderedDict
except ImportError:
    OrderedDict = dict
import argparse
from requests.structures import CaseInsensitiveDict
from . import __version__


SEP_COMMON = ':'
SEP_HEADERS = SEP_COMMON
SEP_DATA = '='
SEP_DATA_RAW_JSON = ':='
SEP_FILES = '@'


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

    def parse_args(self, args=None, namespace=None):
        args = super(HTTPieArgumentParser, self).parse_args(args, namespace)
        self._validate_output_options(args)
        self._validate_auth_options(args)
        self._parse_items(args)
        return args

    def _parse_items(self, args):
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
