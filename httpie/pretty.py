"""
Colorizing of HTTP messages and content processing.

"""
import os
import re
import json
import pygments
from pygments import token, lexer
from pygments.styles import get_style_by_name, STYLE_MAP
from pygments.lexers import get_lexer_for_mimetype
from pygments.formatters.terminal import TerminalFormatter
from pygments.formatters.terminal256 import Terminal256Formatter
from pygments.util import ClassNotFound
from requests.compat import is_windows
from . import solarized


DEFAULT_STYLE = 'solarized'
AVAILABLE_STYLES = [DEFAULT_STYLE] + list(STYLE_MAP.keys())
if is_windows:
    import colorama
    colorama.init()
    # 256 looks better on Windows
    formatter_class = Terminal256Formatter
else:
    formatter_class = (
        Terminal256Formatter
        if '256color' in os.environ.get('TERM', '')
        else TerminalFormatter
    )


class HTTPLexer(lexer.RegexLexer):
    """
    Simplified HTTP lexer for Pygments.

    It only operates on headers and provides a stronger contrast between
    their names and values than the original one bundled with Pygments
    (`pygments.lexers.text import HttpLexer`), especially when
    Solarized color scheme is used.

    """
    name = 'HTTP'
    aliases = ['http']
    filenames = ['*.http']
    tokens = {
        'root': [

            # Request-Line
            (r'([A-Z]+)( +)([^ ]+)( +)(HTTP)(/)(\d+\.\d+)',
             lexer.bygroups(
                token.Name.Function,
                token.Text,
                token.Name.Namespace,
                token.Text,
                token.Keyword.Reserved,
                token.Operator,
                token.Number
             )),

            # Response Status-Line
            (r'(HTTP)(/)(\d+\.\d+)( +)(\d{3})( +)(.+)',
             lexer.bygroups(
                 token.Keyword.Reserved,  # 'HTTP'
                 token.Operator,  # '/'
                 token.Number,  # Version
                 token.Text,
                 token.Number,  # Status code
                 token.Text,
                 token.Name.Exception,  # Reason
             )),

            # Header
            (r'(.*?)( *)(:)( *)(.+)', lexer.bygroups(
                token.Name.Attribute, # Name
                token.Text,
                token.Operator,  # Colon
                token.Text,
                token.String  # Value
            ))
    ]}


class PrettyHttp(object):
    """HTTP headers & body prettyfier."""

    def __init__(self, style_name):
        try:
            style = get_style_by_name(style_name)
        except ClassNotFound:
            style = solarized.SolarizedStyle
        self.formatter = formatter_class(style=style)

    def headers(self, content):
        """Pygmentize HTTP headers."""
        return pygments.highlight(content, HTTPLexer(), self.formatter)

    def body(self, content, content_type):
        """Pygmentize `content` based on `content_type`."""

        content_type = content_type.split(';')[0]

        application_match = re.match(
            r'application/(.+\+)(json|xml)$',
            content_type
        )
        if application_match:
            # Strip vendor and extensions from Content-Type
            vendor, extension = application_match.groups()
            content_type = content_type.replace(vendor, '')

        try:
            lexer = get_lexer_for_mimetype(content_type)
        except ClassNotFound:
            return content

        if content_type == 'application/json':
            try:
                # Indent and sort the JSON data.
                content = json.dumps(json.loads(content),
                                     sort_keys=True, indent=4,
                                     ensure_ascii=False)
            except ValueError:
                # Invalid JSON - we don't care.
                pass

        return pygments.highlight(content, lexer, self.formatter)
