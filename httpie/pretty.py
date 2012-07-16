import os
import re
import json

import pygments

from pygments.util import ClassNotFound
from pygments.styles import get_style_by_name, STYLE_MAP
from pygments.lexers import get_lexer_for_mimetype, HttpLexer
from pygments.formatters.terminal256 import Terminal256Formatter
from pygments.formatters.terminal import TerminalFormatter

from . import solarized


DEFAULT_STYLE = 'solarized'
AVAILABLE_STYLES = [DEFAULT_STYLE] + list(STYLE_MAP.keys())
FORMATTER = (Terminal256Formatter
             if '256color' in os.environ.get('TERM', '')
             else TerminalFormatter)

application_content_type_re = re.compile(r'application/(.+\+)?(json|xml)$')


class PrettyHttp(object):

    def __init__(self, style_name):
        if style_name == 'solarized':
            style = solarized.SolarizedStyle
        else:
            style = get_style_by_name(style_name)
        self.formatter = FORMATTER(style=style)

    def headers(self, content):
        return pygments.highlight(content, HttpLexer(), self.formatter)

    def body(self, content, content_type):
        content_type = content_type.split(';')[0]
        application_match = re.match(application_content_type_re, content_type)
        if application_match:
            # Strip vendor and extensions from Content-Type
            vendor, extension = application_match.groups()
            content_type = content_type.replace(vendor, u"")

        try:
            lexer = get_lexer_for_mimetype(content_type)
        except ClassNotFound:
            return content

        if content_type == "application/json":
            try:
                # Indent and sort the JSON data.
                content = json.dumps(json.loads(content),
                                     sort_keys=True, indent=4,
                                     ensure_ascii=False)
            except:
                pass

        return pygments.highlight(content, lexer, self.formatter)
