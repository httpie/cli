from __future__ import absolute_import
import json

import pygments.lexer
import pygments.token
import pygments.styles
import pygments.lexers
import pygments.style
from pygments.formatters.terminal import TerminalFormatter
from pygments.formatters.terminal256 import Terminal256Formatter
from pygments.lexers.special import TextLexer
from pygments.util import ClassNotFound
from pygments.lexers.text import HttpLexer

from httpie.plugins import FormatterPlugin


AVAILABLE_STYLES = set(pygments.styles.STYLE_MAP.keys())


class ColorFormatter(FormatterPlugin):
    """
    Colorize using Pygments

    This processor that applies syntax highlighting to the headers,
    and also to the body if its content type is recognized.

    """
    group_name = 'colors'

    def __init__(self, env, explicit_json=False,
                 color_scheme=None, **kwargs):
        super(ColorFormatter, self).__init__(**kwargs)
        if not env.colors:
            self.enabled = False
            return

        # --json, -j
        self.explicit_json = explicit_json

        if color_scheme and env.colors == 256:
            self.formatter = Terminal256Formatter(style=color_scheme)
        else:
            self.formatter = TerminalFormatter()

    def format_headers(self, headers):
        return pygments.highlight(headers, HttpLexer(), self.formatter).strip()

    def format_body(self, body, mime):
        lexer = self.get_lexer(mime, body)
        if lexer:
            body = pygments.highlight(body, lexer, self.formatter)
        return body.strip()

    def get_lexer(self, mime, body):
        return get_lexer(
            mime=mime,
            explicit_json=self.explicit_json,
            body=body,
        )


def get_lexer(mime, explicit_json=False, body=''):

    # Build candidate mime type and lexer names.
    mime_types, lexer_names = [mime], []
    type_, subtype = mime.split('/', 1)
    if '+' not in subtype:
        lexer_names.append(subtype)
    else:
        subtype_name, subtype_suffix = subtype.split('+', 1)
        lexer_names.extend([subtype_name, subtype_suffix])
        mime_types.extend([
            '%s/%s' % (type_, subtype_name),
            '%s/%s' % (type_, subtype_suffix)
        ])

    # As a last resort, if no lexer feels responsible, and
    # the subtype contains 'json', take the JSON lexer
    if 'json' in subtype:
        lexer_names.append('json')

    # Try to resolve the right lexer.
    lexer = None
    for mime_type in mime_types:
        try:
            lexer = pygments.lexers.get_lexer_for_mimetype(mime_type)
            break
        except ClassNotFound:
            pass
    else:
        for name in lexer_names:
            try:
                lexer = pygments.lexers.get_lexer_by_name(name)
            except ClassNotFound:
                pass

    if explicit_json and body and (not lexer or isinstance(lexer, TextLexer)):
        # JSON response with an incorrect Content-Type?
        try:
            json.loads(body)  # FIXME: the body also gets parsed in json.py
        except ValueError:
            pass  # Nope
        else:
            lexer = pygments.lexers.get_lexer_by_name('json')

    return lexer
