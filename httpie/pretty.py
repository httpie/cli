import os
import json
import pygments
import re
from pygments import token
from pygments.util import ClassNotFound
from pygments.lexers import get_lexer_for_mimetype
from pygments.formatters.terminal256 import Terminal256Formatter
from pygments.formatters.terminal import TerminalFormatter
from pygments.lexer import include, RegexLexer, bygroups
from pygments.styles import get_style_by_name, STYLE_MAP
from . import solarized


DEFAULT_STYLE = 'solarized'
AVAILABLE_STYLES = [DEFAULT_STYLE] + STYLE_MAP.keys()
TYPE_JS = 'application/javascript'
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
            (r'(HTTP/[\d.]+\s+)(\d+)(\s+.+)', bygroups(
             token.Operator, token.Number, token.String)),
            (r'(.*?:)(.+)',  bygroups(token.Name, token.String))
    ]}

# Stolen from https://github.com/orb/pygments-json
class JSONLexer(RegexLexer):
    name = 'JSON Lexer'
    aliases = ['json']
    filenames = ['*.json']
    mimetypes = []


    flags = re.DOTALL
    tokens = {
        'whitespace': [
            (r'\s+', token.Text),
        ],

        # represents a simple terminal value
        'simplevalue':[
            (r'(true|false|null)\b', token.Keyword.Constant),
            (r'-?[0-9]+', token.Number.Integer),
            (r'"(\\\\|\\"|[^"])*"', token.String.Double),
        ],


        # the right hand side of an object, after the attribute name
        'objectattribute': [
            include('value'),
            (r':', token.Punctuation),
            # comma terminates the attribute but expects more
            (r',', token.Punctuation, '#pop'),
            # a closing bracket terminates the entire object, so pop twice
            (r'}', token.Punctuation, ('#pop', '#pop')),
        ],

        # a json object - { attr, attr, ... }
        'objectvalue': [
            include('whitespace'),
            (r'"(\\\\|\\"|[^"])*"', token.Name.Tag, 'objectattribute'),
            (r'}', token.Punctuation, '#pop'),
        ],

        # json array - [ value, value, ... }
        'arrayvalue': [
            include('whitespace'),
            include('value'),
            (r',', token.Punctuation),
            (r']', token.Punctuation, '#pop'),
        ],

        # a json value - either a simple value or a complex value (object or array)
        'value': [
            include('whitespace'),
            include('simplevalue'),
            (r'{', token.Punctuation, 'objectvalue'),
            (r'\[', token.Punctuation, 'arrayvalue'),
        ],


        # the root of a json document would be a value
        'root': [
            include('value'),
        ],

    }

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
                lexer = JSONLexer()
            except Exception:
                pass
        else:
            try:
                lexer = get_lexer_for_mimetype(content_type)
            except ClassNotFound:
                return content
        content = pygments.highlight(content, lexer, self.formatter)
        return content
