import os
import json

import pygments

from pygments import token
from pygments.util import ClassNotFound
from pygments.styles import get_style_by_name, STYLE_MAP
from pygments.lexers import get_lexer_for_mimetype, HttpLexer
from pygments.formatters.terminal import TerminalFormatter
from pygments.formatters.terminal256 import Terminal256Formatter

from . import solarized


DEFAULT_STYLE = 'solarized'
AVAILABLE_STYLES = [DEFAULT_STYLE] + list(STYLE_MAP.keys())
FORMATTER = (Terminal256Formatter
             if '256color' in os.environ.get('TERM', '')
             else TerminalFormatter)


def formatter(style_name):
    if style_name == 'solarized':
        style = solarized.SolarizedStyle

    else:
        style = get_style_by_name(style_name)

    return FORMATTER(style=style)
