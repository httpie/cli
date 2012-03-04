import os
import json
import pygments
from pygments import token
from pygments.util import ClassNotFound
from pygments.lexers import get_lexer_for_mimetype
from pygments.formatters.terminal256 import Terminal256Formatter
from pygments.formatters.terminal import TerminalFormatter
from pygments.lexer import RegexLexer, bygroups
from pygments.styles import get_style_by_name, STYLE_MAP
from . import solarized


DEFAULT_STYLE = 'solarized'
AVAILABLE_STYLES = [DEFAULT_STYLE] + STYLE_MAP.keys()
TYPE_JS = 'application/javascript'
FORMATTER = (Terminal256Formatter
             if os.environ.get('TERM') == 'xterm-256color'
             else TerminalFormatter)


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


class PrettyHttp(object):

    def __init__(self, style_name):
        if style_name == 'solarized':
            style = solarized.SolarizedStyle
        else:
            style = get_style_by_name(style_name)
        self.formatter = FORMATTER(style=style)

    def headers(self, content):
        return pygments.highlight(content, HTTPLexer(), self.formatter)

    def body(self, content, content_type):
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
        except ClassNotFound:
            return content
        content = pygments.highlight(content, lexer, self.formatter)
        return content
