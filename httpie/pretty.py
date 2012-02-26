import json
from functools import partial
import pygments
from pygments.lexers import get_lexer_for_mimetype
from pygments.formatters.terminal256 import Terminal256Formatter
from pygments.lexer import RegexLexer, bygroups
from pygments import token
from . import solarized


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
                    formatter=Terminal256Formatter(
                        style=solarized.SolarizedStyle))
highlight_http = partial(highlight, lexer=HTTPLexer())


def prettify_http(headers):
    return highlight_http(headers)


def prettify_body(content, content_type):
    content_type = content_type.split(';')[0]
    if 'json' in content_type:
        content_type = TYPE_JS
        try:
            # Indent JSON
            content = json.dumps(json.loads(content),
                                sort_keys=True, indent=4)
        except Exception:
            pass
    try:
        lexer = get_lexer_for_mimetype(content_type)
        content = highlight(code=content, lexer=lexer)
        if content:
            content = content[:-1]
    except Exception:
        pass
    return content

