"""Parsing and processing of CLI input (args, auth credentials, files, stdin).

"""
import enum
import re


URL_SCHEME_RE = re.compile(r'^[a-z][a-z0-9.+-]*://', re.IGNORECASE)

HTTP_POST = 'POST'
HTTP_GET = 'GET'

# Various separators used in args
SEPARATOR_HEADER = ':'
SEPARATOR_HEADER_EMPTY = ';'
SEPARATOR_CREDENTIALS = ':'
SEPARATOR_PROXY = ':'
SEPARATOR_DATA_STRING = '='
SEPARATOR_DATA_RAW_JSON = ':='
SEPARATOR_FILE_UPLOAD = '@'
SEPARATOR_FILE_UPLOAD_TYPE = ';type='  # in already parsed file upload path only
SEPARATOR_DATA_EMBED_FILE_CONTENTS = '=@'
SEPARATOR_DATA_EMBED_RAW_JSON_FILE = ':=@'
SEPARATOR_QUERY_PARAM = '=='

# Separators that become request data
SEPARATOR_GROUP_DATA_ITEMS = frozenset({
    SEPARATOR_DATA_STRING,
    SEPARATOR_DATA_RAW_JSON,
    SEPARATOR_FILE_UPLOAD,
    SEPARATOR_DATA_EMBED_FILE_CONTENTS,
    SEPARATOR_DATA_EMBED_RAW_JSON_FILE
})

SEPARATORS_GROUP_MULTIPART = frozenset({
    SEPARATOR_DATA_STRING,
    SEPARATOR_DATA_EMBED_FILE_CONTENTS,
    SEPARATOR_FILE_UPLOAD,
})

# Separators for items whose value is a filename to be embedded
SEPARATOR_GROUP_DATA_EMBED_ITEMS = frozenset({
    SEPARATOR_DATA_EMBED_FILE_CONTENTS,
    SEPARATOR_DATA_EMBED_RAW_JSON_FILE,
})

# Separators for raw JSON items
SEPARATOR_GROUP_RAW_JSON_ITEMS = frozenset([
    SEPARATOR_DATA_RAW_JSON,
    SEPARATOR_DATA_EMBED_RAW_JSON_FILE,
])

# Separators allowed in ITEM arguments
SEPARATOR_GROUP_ALL_ITEMS = frozenset({
    SEPARATOR_HEADER,
    SEPARATOR_HEADER_EMPTY,
    SEPARATOR_QUERY_PARAM,
    SEPARATOR_DATA_STRING,
    SEPARATOR_DATA_RAW_JSON,
    SEPARATOR_FILE_UPLOAD,
    SEPARATOR_DATA_EMBED_FILE_CONTENTS,
    SEPARATOR_DATA_EMBED_RAW_JSON_FILE,
})

# Output options
OUT_REQ_HEAD = 'H'
OUT_REQ_BODY = 'B'
OUT_RESP_HEAD = 'h'
OUT_RESP_BODY = 'b'

OUTPUT_OPTIONS = frozenset({
    OUT_REQ_HEAD,
    OUT_REQ_BODY,
    OUT_RESP_HEAD,
    OUT_RESP_BODY
})

# Pretty
PRETTY_MAP = {
    'all': ['format', 'colors'],
    'colors': ['colors'],
    'format': ['format'],
    'none': []
}
PRETTY_STDOUT_TTY_ONLY = object()


DEFAULT_FORMAT_OPTIONS = [
    'headers.sort:true',
    'json.format:true',
    'json.indent:4',
    'json.sort_keys:true',
]
SORTED_FORMAT_OPTIONS = [
    'headers.sort:true',
    'json.sort_keys:true',
]
SORTED_FORMAT_OPTIONS_STRING = ','.join(SORTED_FORMAT_OPTIONS)
UNSORTED_FORMAT_OPTIONS_STRING = ','.join(
    option.replace('true', 'false') for option in SORTED_FORMAT_OPTIONS)

# Defaults
OUTPUT_OPTIONS_DEFAULT = OUT_RESP_HEAD + OUT_RESP_BODY
OUTPUT_OPTIONS_DEFAULT_STDOUT_REDIRECTED = OUT_RESP_BODY
OUTPUT_OPTIONS_DEFAULT_OFFLINE = OUT_REQ_HEAD + OUT_REQ_BODY


class RequestType(enum.Enum):
    FORM = enum.auto()
    MULTIPART = enum.auto()
    JSON = enum.auto()
