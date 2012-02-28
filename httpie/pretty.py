import json
from functools import partial
import pygments
from pygments.lexers import get_lexer_for_mimetype
from pygments.formatters.terminal256 import Terminal256Formatter
from pygments.lexer import RegexLexer, bygroups
from pygments import token
from pygments.styles import get_style_by_name
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


def _get_highlighter(style_name='solarized'):
    try:
        style = get_style_by_name(style_name)
    except pygments.util.ClassNotFound:
        style = solarized.SolarizedStyle
    return partial(pygments.highlight,
                   formatter=Terminal256Formatter(style=style))


def prettify_http(headers, style_name='solarized'):
    highlight = partial(_get_highlighter(style_name), lexer=HTTPLexer())
    return highlight(headers)


def prettify_body(content, content_type, style_name='solarized'):
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
        highlight = _get_highlighter(style_name)
        content = highlight(code=content, lexer=lexer)
        if content:
            content = content[:-1]
    except Exception:
        pass
    return content
