"""Output processing and formatting.

"""
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


class HTTPLexer(lexer.RegexLexer):
    """Simplified HTTP lexer for Pygments.

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


class BaseProcessor(object):

    enabled = True

    def __init__(self, env, **kwargs):
        self.env = env
        self.kwargs = kwargs

    def process_headers(self, headers):
        return headers

    def process_body(self, content, content_type):
        return content


class JSONProcessor(BaseProcessor):

    def process_body(self, content, content_type):
        if content_type == 'application/json':
            try:
                # Indent and sort the JSON data.
                content = json.dumps(
                    json.loads(content),
                    sort_keys=True,
                    ensure_ascii=False,
                    indent=4,
                )
            except ValueError:
                # Invalid JSON - we don't care.
                pass
        return content


class PygmentsProcessor(BaseProcessor):

    def __init__(self, *args, **kwargs):
        super(PygmentsProcessor, self).__init__(*args, **kwargs)

        if not self.env.colors:
            self.enabled = False
            return

        try:
            style = get_style_by_name(
                self.kwargs.get('pygments_style', DEFAULT_STYLE))
        except ClassNotFound:
            style = solarized.SolarizedStyle

        if is_windows or self.env.colors == 256:
            fmt_class = Terminal256Formatter
        else:
            fmt_class = TerminalFormatter
        self.formatter = fmt_class(style=style)

    def process_headers(self, headers):
        return pygments.highlight(
            headers, HTTPLexer(), self.formatter)

    def process_body(self, content, content_type):
        try:
            lexer = get_lexer_for_mimetype(content_type)
        except ClassNotFound:
            pass
        else:
            content = pygments.highlight(content, lexer, self.formatter)
        return content


class OutputProcessor(object):

    installed_processors = [
        JSONProcessor,
        PygmentsProcessor
    ]

    def __init__(self, env, **kwargs):
        self.env = env
        processors = [
            cls(env, **kwargs)
            for cls in self.installed_processors
        ]
        self.processors = [p for p in processors if p.enabled]

    def process_headers(self, headers):
        for processor in self.processors:
         headers = processor.process_headers(headers)
        return headers

    def process_body(self, content, content_type):
        content_type = content_type.split(';')[0]

        application_match = re.match(
            r'application/(.+\+)(json|xml)$',
            content_type
        )
        if application_match:
            # Strip vendor and extensions from Content-Type
            vendor, extension = application_match.groups()
            content_type = content_type.replace(vendor, '')

        for processor in self.processors:
            content = processor.process_body(content, content_type)

        return content
