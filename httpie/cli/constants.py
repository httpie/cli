"""Parsing and processing of CLI input (args, auth credentials, files, stdin).

"""
import re
import ssl


# TODO: Use MultiDict for headers once added to `requests`.
# <https://github.com/jakubroztocil/httpie/issues/130>


# ALPHA *( ALPHA / DIGIT / "+" / "-" / "." )
# <https://tools.ietf.org/html/rfc3986#section-3.1>
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

# Defaults
OUTPUT_OPTIONS_DEFAULT = OUT_RESP_HEAD + OUT_RESP_BODY
OUTPUT_OPTIONS_DEFAULT_STDOUT_REDIRECTED = OUT_RESP_BODY
OUTPUT_OPTIONS_DEFAULT_OFFLINE = OUT_REQ_HEAD + OUT_REQ_BODY

SSL_VERSION_ARG_MAPPING = {
    'ssl2.3': 'PROTOCOL_SSLv23',
    'ssl3': 'PROTOCOL_SSLv3',
    'tls1': 'PROTOCOL_TLSv1',
    'tls1.1': 'PROTOCOL_TLSv1_1',
    'tls1.2': 'PROTOCOL_TLSv1_2',
    'tls1.3': 'PROTOCOL_TLSv1_3',
}
SSL_VERSION_ARG_MAPPING = {
    cli_arg: getattr(ssl, ssl_constant)
    for cli_arg, ssl_constant in SSL_VERSION_ARG_MAPPING.items()
    if hasattr(ssl, ssl_constant)
}
