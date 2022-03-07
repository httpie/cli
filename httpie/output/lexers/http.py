import re
import pygments
from httpie.output.lexers.common import precise

RE_STATUS_LINE = re.compile(r'(\d{3})( +)?(.+)?')

STATUS_TYPES = {
    '1': pygments.token.Number.HTTP.INFO,
    '2': pygments.token.Number.HTTP.OK,
    '3': pygments.token.Number.HTTP.REDIRECT,
    '4': pygments.token.Number.HTTP.CLIENT_ERR,
    '5': pygments.token.Number.HTTP.SERVER_ERR,
}

RESPONSE_TYPES = {
    'GET': pygments.token.Name.Function.HTTP.GET,
    'HEAD': pygments.token.Name.Function.HTTP.HEAD,
    'POST': pygments.token.Name.Function.HTTP.POST,
    'PUT': pygments.token.Name.Function.HTTP.PUT,
    'PATCH': pygments.token.Name.Function.HTTP.PATCH,
    'DELETE': pygments.token.Name.Function.HTTP.DELETE,
}


def http_response_type(lexer, match, ctx):
    status_match = RE_STATUS_LINE.match(match.group())
    if status_match is None:
        return None

    status_code, text, reason = status_match.groups()
    status_type = precise(
        lexer,
        STATUS_TYPES.get(status_code[0]),
        pygments.token.Number
    )

    groups = pygments.lexer.bygroups(
        status_type,
        pygments.token.Text,
        status_type
    )
    yield from groups(lexer, status_match, ctx)


def request_method(lexer, match, ctx):
    response_type = precise(
        lexer,
        RESPONSE_TYPES.get(match.group()),
        pygments.token.Name.Function
    )
    yield match.start(), response_type, match.group()


class SimplifiedHTTPLexer(pygments.lexer.RegexLexer):
    """Simplified HTTP lexer for Pygments.

    It only operates on headers and provides a stronger contrast between
    their names and values than the original one bundled with Pygments
    (:class:`pygments.lexers.text import HttpLexer`), especially when
    Solarized color scheme is used.

    """
    name = 'HTTP'
    aliases = ['http']
    filenames = ['*.http']
    tokens = {
        'root': [
            # Request-Line
            (r'([A-Z]+)( +)([^ ]+)( +)(HTTP)(/)(\d+\.\d+)',
             pygments.lexer.bygroups(
                 request_method,
                 pygments.token.Text,
                 pygments.token.Name.Namespace,
                 pygments.token.Text,
                 pygments.token.Keyword.Reserved,
                 pygments.token.Operator,
                 pygments.token.Number
             )),
            # Response Status-Line
            (r'(HTTP)(/)(\d+\.\d+)( +)(.+)',
             pygments.lexer.bygroups(
                 pygments.token.Keyword.Reserved,  # 'HTTP'
                 pygments.token.Operator,  # '/'
                 pygments.token.Number,  # Version
                 pygments.token.Text,
                 http_response_type,  # Status code and Reason
             )),
            # Header
            (r'(.*?)( *)(:)( *)(.+)', pygments.lexer.bygroups(
                pygments.token.Name.Attribute,  # Name
                pygments.token.Text,
                pygments.token.Operator,  # Colon
                pygments.token.Text,
                pygments.token.String  # Value
            ))
        ]
    }
