import json
import argparse
from collections import namedtuple
from . import pretty
from . import __doc__ as doc
from . import __version__ as version


SEP_COMMON = ':'
SEP_HEADERS = SEP_COMMON
SEP_DATA = '='
SEP_DATA_RAW_JSON = ':='
PRETTIFY_STDOUT_TTY_ONLY = object()


class ParseError(Exception):
    pass


KeyValue = namedtuple('KeyValue', ['key', 'value', 'sep', 'orig'])


class KeyValueType(object):
    """A type used with `argparse`."""
    def __init__(self, *separators):
        self.separators = separators

    def __call__(self, string):
        found = dict((string.find(sep), sep)
                     for sep in self.separators
                     if string.find(sep) != -1)

        if not found:
            #noinspection PyExceptionInherit
            raise argparse.ArgumentTypeError(
                '"%s" is not a valid value' % string)
        sep = found[min(found.keys())]
        key, value = string.split(sep, 1)
        return KeyValue(key=key, value=value, sep=sep, orig=string)


def parse_items(items, data=None, headers=None):
    """Parse `KeyValueType` `items` into `data` and `headers`."""
    if headers is None:
        headers = {}
    if data is None:
        data = {}
    for item in items:
        value = item.value
        if item.sep == SEP_HEADERS:
            target = headers
        elif item.sep in [SEP_DATA, SEP_DATA_RAW_JSON]:
            if item.sep == SEP_DATA_RAW_JSON:
                try:
                    value = json.loads(item.value)
                except ValueError:
                    raise ParseError('%s is not valid JSON' % item.orig)
            target = data
        else:
            raise ParseError('%s is not valid item' % item.orig)

        if item.key in target:
            ParseError('duplicate item %s (%s)' % (item.key, item.orig))

        target[item.key] = value

    return headers, data


def _(text):
    """Normalize white space."""
    return ' '.join(text.strip().split())


parser = argparse.ArgumentParser(description=doc.strip(),)
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
        Serialize data items as form values and set
        Content-Type to application/x-www-form-urlencoded,
         if not specified.
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
    '--pretty', '-p', dest='prettify', action='store_true',
    default=PRETTIFY_STDOUT_TTY_ONLY,
    help=_('''
        If stdout is a terminal,
        the response is prettified by default (colorized and
        indented if it is JSON). This flag ensures
        prettifying even when stdout is redirected.
    ''')
)
prettify.add_argument(
    '--ugly', '-u', dest='prettify', action='store_false',
    help=_('''
        Do not prettify the response.
    ''')
)

only = parser.add_mutually_exclusive_group(required=False)
only.add_argument(
    '--headers', '-t', dest='print_body',
    action='store_false', default=True,
    help=('''
        Print only the response headers.
    ''')
)
only.add_argument(
    '--body', '-b', dest='print_headers',
    action='store_false', default=True,
    help=('''
        Print only the response body.
    ''')
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
    '--verify',
    help=_('''
        Set to "yes" to check the host\'s SSL certificate.
        You can also pass the  path to a CA_BUNDLE
        file for private certs. You can also set
        the REQUESTS_CA_BUNDLE  environment variable.
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
    '--file', metavar='PATH', type=argparse.FileType(),
    default=[], action='append',
    help='File to multipart upload'
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
    type=KeyValueType(SEP_COMMON, SEP_DATA, SEP_DATA_RAW_JSON),
    help=_('''
        HTTP header (key:value), data field (key=value)
        or raw JSON field (field:=value).
    ''')
)
