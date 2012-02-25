import json
from functools import partial
import pygments
from pygments.lexers import get_lexer_for_mimetype
from pygments.formatters.terminal256 import Terminal256Formatter
from pygments.lexer import RegexLexer, bygroups
from pygments import token


TYPE_JS = 'application/javascript'


class HTTPLexer(RegexLexer):
    name = 'HTTP'
    aliases = ['http']
    filenames = ['*.http']
    tokens = {
        'root': [
            (r'\s+', token.Text),
            (r'(HTTP/[\d.]+\s+)(\d+)(\s+.+)', bygroups(
             token.Operator, token.Number, token.String)),
            (r'(.*?:)(.+)',  bygroups(token.Name, token.String))
    ]}


highlight = partial(pygments.highlight,
                    formatter=Terminal256Formatter(style='native'))
highlight_http = partial(highlight, lexer=HTTPLexer())


def prettify(content_type, status_line, headers, body):
    content_type = content_type.split(';')[0]

    if 'json' in content_type:
        content_type = TYPE_JS
        try:
            # Indent JSON
            body = json.dumps(json.loads(body), sort_keys=True, indent=4)
        except Exception:
            pass

    try:
        body = highlight(code=body, lexer=get_lexer_for_mimetype(content_type))
    except Exception:
        pass

    return (highlight_http(code=status_line).strip(),
            highlight_http(code=headers),
            body)
