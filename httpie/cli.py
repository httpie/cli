import os
import json
import argparse
import re
from collections import namedtuple
from . import pretty
from . import __doc__ as doc
from . import __version__ as version


SEP_COMMON = ':'
SEP_HEADERS = SEP_COMMON
SEP_DATA = '='
SEP_DATA_RAW_JSON = ':='
SEP_FILES = '@'
PRETTIFY_STDOUT_TTY_ONLY = object()

OUT_REQUEST_HEADERS = 'H'
OUT_REQUEST_BODY = 'B'
OUT_RESPONSE_HEADERS = 'h'
OUT_RESPONSE_BODY = 'b'

OUTPUT_OPTIONS = [OUT_REQUEST_HEADERS,
                  OUT_REQUEST_BODY,
                  OUT_RESPONSE_HEADERS,
                  OUT_RESPONSE_BODY]


class ParseError(Exception):
    pass


KeyValue = namedtuple('KeyValue', ['key', 'value', 'sep', 'orig'])

class KeyValueType(object):
    """A type used with `argparse`."""
    def __init__(self, *separators):
        self.separators = separators

    def __call__(self, string):
        found = {}
        for sep in self.separators:
            regex = '[^\\\\]' + sep
            match = re.search(regex, string)
            if match:
                found[match.start() + 1] = sep

        if not found:
            #noinspection PyExceptionInherit
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


def _(text):
    """Normalize white space."""
    return ' '.join(text.strip().split())


class HTTPieArgumentParser(argparse.ArgumentParser):
    def parse_args(self, args=None, namespace=None):
        args = super(HTTPieArgumentParser, self).parse_args(args, namespace)
        self._validate_output_options(args)
        self._validate_auth_options(args)
        return args

    def _validate_output_options(self, args):
        unknown_output_options = set(args.output_options) - set(OUTPUT_OPTIONS)
        if unknown_output_options:
            self.error('Unknown output options: %s' % ','.join(unknown_output_options))

    def _validate_auth_options(self, args):
        if args.auth_type and not args.auth:
            self.error('--auth-type can only be used with --auth')



parser = HTTPieArgumentParser(description=doc.strip(),)
parser.add_argument('--version', action='version', version=version)

# Content type.
#############################################

group_type = parser.add_mutually_exclusive_group(required=False)
group_type.add_argument(
    '--json', '-j', action='store_true',
    help=_('''
        Serialize data items as a JSON object and set
        Content-Type to application/json, if not specified.
    ''')
)
group_type.add_argument(
    '--form', '-f', action='store_true',
    help=_('''
        Serialize fields as form values. The Content-Type is set to application/x-www-form-urlencoded.
        The presence of any file fields results into a multipart/form-data request.
        Note that Content-Type is not automatically set if explicitely specified.
     ''')
)


# output_options options.
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
    default=OUT_RESPONSE_HEADERS + OUT_RESPONSE_BODY,
    help=_('''
        String specifying what should the output contain.
        "{request_headers}" stands for request headers and
        "{request_body}" for request body.
        "{response_headers}" stands for response headers and
        "{response_body}" for response body.
        Defaults to "hb" which means that the whole response
        (headers and body) is printed.
    '''.format(
        request_headers=OUT_REQUEST_HEADERS,
        request_body=OUT_REQUEST_BODY,
        response_headers=OUT_RESPONSE_HEADERS,
        response_body=OUT_RESPONSE_BODY,
    ))
)
output_options.add_argument(
    '--verbose', '-v', dest='output_options',
    action='store_const', const=''.join(OUTPUT_OPTIONS),
    help=_('''
        Print the whole request as well as response.
        Shortcut for --print={0}.
    '''.format(''.join(OUTPUT_OPTIONS)))
)
output_options.add_argument(
    '--headers', '-t', dest='output_options',
    action='store_const', const=OUT_RESPONSE_HEADERS,
    help=_('''
        Print only the response headers.
        Shortcut for --print={0}.
    '''.format(OUT_RESPONSE_HEADERS))
)
output_options.add_argument(
    '--body', '-b', dest='output_options',
    action='store_const', const=OUT_RESPONSE_BODY,
    help=_('''
        Print only the response body.
        Shortcut for --print={0}.
    '''.format(OUT_RESPONSE_BODY))
)

parser.add_argument(
    '--style', '-s', dest='style', default='solarized', metavar='STYLE',
    choices=pretty.AVAILABLE_STYLES,
    help=_('''
        Output coloring style, one of %s. Defaults to solarized.
    ''') % ', '.join(sorted(pretty.AVAILABLE_STYLES))
)

# ``requests.request`` keyword arguments.
parser.add_argument(
    '--auth', '-a', help='username:password',
    type=KeyValueType(SEP_COMMON)
)

parser.add_argument(
    '--auth-type', choices=['basic', 'digest'],
    help=_('The type of authentication ("basic" or "digest"). Defaults to "basic".')
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
    type=KeyValueType(SEP_COMMON),
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
        HTTP method to be used for the request
        (GET, POST, PUT, DELETE, PATCH, ...).
    ''')
)
parser.add_argument(
    'url', metavar='URL',
    help=_('''
        Protocol defaults to http:// if the
        URL does not include it.
    ''')
)
parser.add_argument(
    'items', nargs='*',
    type=KeyValueType(SEP_COMMON, SEP_DATA, SEP_DATA_RAW_JSON, SEP_FILES),
    help=_('''
        HTTP header (header:value), data field (field=value),
        raw JSON field (field:=value)
        or file field (field@/path/to/file).
    ''')
)
