import os
import json
import xml.dom.minidom
import pygments
from pygments import token
from pygments.util import ClassNotFound
from pygments.lexers import get_lexer_for_mimetype
from pygments.formatters.terminal256 import Terminal256Formatter
from pygments.formatters.terminal import TerminalFormatter
from pygments.lexer import  RegexLexer, bygroups
from pygments.styles import get_style_by_name, STYLE_MAP
from .pygson import JSONLexer
from . import solarized


DEFAULT_STYLE = 'solarized'
AVAILABLE_STYLES = [DEFAULT_STYLE] + list(STYLE_MAP.keys())
FORMATTER = (Terminal256Formatter
             if '256color' in os.environ.get('TERM', '')
             else TerminalFormatter)


class HTTPLexer(RegexLexer):
    name = 'HTTP'
    aliases = ['http']
    filenames = ['*.http']
    tokens = {
        'root': [
            (r'\s+', token.Text),
            # Request-Line
            (r'([A-Z]+\s+)(/.*?)(\s+HTTP/[\d.]+)', bygroups(
             token.Keyword, token.String, token.Keyword)),
            # Status-Line
            (r'(HTTP/[\d.]+\s+)(\d+)(\s+.+)', bygroups(
             token.Keyword, token.Number, token.String)),
            # Header
            (r'(.*?:)(.+)',  bygroups(token.Name, token.Keyword))
    ]}


def xml_prettify(buf, indent_spaces=4):
    doc = xml.dom.minidom.parseString(buf)
    return doc.toprettyxml(indent=' ' * indent_spaces)

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
        prettyfiers_by_lexer = {
            JSONLexer: lambda x: json.dumps(json.loads(x),
                                    sort_keys=True, indent=4),
            pygments.lexers.XmlLexer: xml_prettify,
        }

        content_type = content_type.split(';')[0]
        try:
            lexer = get_lexer_for_mimetype(content_type)
        except ClassNotFound:
            if 'json' in content_type:
                # JSON lexer not found, use internal
                lexer = JSONLexer()
            else:
                # no lexer for mimetype
                return content

        prettyfier = prettyfiers_by_lexer.get(lexer.__class__)
        if prettyfier is not None:
            try:
                # prettify the data.
                content = prettyfier(content)
            except Exception:
                pass
        return pygments.highlight(content, lexer, self.formatter)

