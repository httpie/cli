from __future__ import absolute_import

import json
from typing import Optional, Type

import pygments.lexer
import pygments.lexers
import pygments.style
import pygments.styles
import pygments.token
from pygments.formatters.terminal import TerminalFormatter
from pygments.formatters.terminal256 import Terminal256Formatter
from pygments.lexer import Lexer
from pygments.lexers.special import TextLexer
from pygments.lexers.text import HttpLexer as PygmentsHttpLexer
from pygments.util import ClassNotFound

from httpie.compat import is_windows
from httpie.context import Environment
from httpie.plugins import FormatterPlugin


AUTO_STYLE = 'auto'  # Follows terminal ANSI color styles
DEFAULT_STYLE = AUTO_STYLE
SOLARIZED_STYLE = 'solarized'  # Bundled here
if is_windows:
    # Colors on Windows via colorama don't look that
    # great and fruity seems to give the best result there.
    DEFAULT_STYLE = 'fruity'

AVAILABLE_STYLES = set(pygments.styles.get_all_styles())
AVAILABLE_STYLES.add(SOLARIZED_STYLE)
AVAILABLE_STYLES.add(AUTO_STYLE)


class ColorFormatter(FormatterPlugin):
    """
    Colorize using Pygments

    This processor that applies syntax highlighting to the headers,
    and also to the body if its content type is recognized.

    """
    group_name = 'colors'

    def __init__(
        self,
        env: Environment,
        explicit_json=False,
        color_scheme=DEFAULT_STYLE,
        **kwargs
    ):
        super().__init__(**kwargs)

        if not env.colors:
            self.enabled = False
            return

        use_auto_style = color_scheme == AUTO_STYLE
        has_256_colors = env.colors == 256
        if use_auto_style or not has_256_colors:
            http_lexer = PygmentsHttpLexer()
            formatter = TerminalFormatter()
        else:
            http_lexer = SimplifiedHTTPLexer()
            formatter = Terminal256Formatter(
                style=self.get_style_class(color_scheme)
            )

        self.explicit_json = explicit_json  # --json
        self.formatter = formatter
        self.http_lexer = http_lexer

    def format_headers(self, headers: str) -> str:
        return pygments.highlight(
            code=headers,
            lexer=self.http_lexer,
            formatter=self.formatter,
        ).strip()

    def format_body(self, body: str, mime: str) -> str:
        lexer = self.get_lexer_for_body(mime, body)
        if lexer:
            body = pygments.highlight(
                code=body,
                lexer=lexer,
                formatter=self.formatter,
            )
        return body.strip()

    def get_lexer_for_body(
        self, mime: str,
        body: str
    ) -> Optional[Type[Lexer]]:
        return get_lexer(
            mime=mime,
            explicit_json=self.explicit_json,
            body=body,
        )

    @staticmethod
    def get_style_class(color_scheme: str) -> Type[pygments.style.Style]:
        try:
            return pygments.styles.get_style_by_name(color_scheme)
        except ClassNotFound:
            return Solarized256Style


def get_lexer(
    mime: str,
    explicit_json=False,
    body=''
) -> Optional[Type[Lexer]]:
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


class SimplifiedHTTPLexer(pygments.lexer.RegexLexer):
    """Simplified HTTP lexer for Pygments.

    It only operates on headers and provides a stronger contrast between
    their names and values than the original one bundled with Pygments
    (:class:`pygments.lexers.text import HttpLexer`), especially when
    Solarized color scheme is used.

    """
    name = 'HTTP'
    aliases = ['http']
    filenames = ['*.http']
    tokens = {
        'root': [
            # Request-Line
            (r'([A-Z]+)( +)([^ ]+)( +)(HTTP)(/)(\d+\.\d+)',
             pygments.lexer.bygroups(
                 pygments.token.Name.Function,
                 pygments.token.Text,
                 pygments.token.Name.Namespace,
                 pygments.token.Text,
                 pygments.token.Keyword.Reserved,
                 pygments.token.Operator,
                 pygments.token.Number
             )),
            # Response Status-Line
            (r'(HTTP)(/)(\d+\.\d+)( +)(\d{3})( +)(.+)',
             pygments.lexer.bygroups(
                 pygments.token.Keyword.Reserved,  # 'HTTP'
                 pygments.token.Operator,  # '/'
                 pygments.token.Number,  # Version
                 pygments.token.Text,
                 pygments.token.Number,  # Status code
                 pygments.token.Text,
                 pygments.token.Name.Exception,  # Reason
             )),
            # Header
            (r'(.*?)( *)(:)( *)(.+)', pygments.lexer.bygroups(
                pygments.token.Name.Attribute,  # Name
                pygments.token.Text,
                pygments.token.Operator,  # Colon
                pygments.token.Text,
                pygments.token.String  # Value
            ))
        ]
    }


class Solarized256Style(pygments.style.Style):
    """
    solarized256
    ------------

    A Pygments style inspired by Solarized's 256 color mode.

    :copyright: (c) 2011 by Hank Gay, (c) 2012 by John Mastro.
    :license: BSD, see LICENSE for more details.

    """
    BASE03 = "#1c1c1c"
    BASE02 = "#262626"
    BASE01 = "#4e4e4e"
    BASE00 = "#585858"
    BASE0 = "#808080"
    BASE1 = "#8a8a8a"
    BASE2 = "#d7d7af"
    BASE3 = "#ffffd7"
    YELLOW = "#af8700"
    ORANGE = "#d75f00"
    RED = "#af0000"
    MAGENTA = "#af005f"
    VIOLET = "#5f5faf"
    BLUE = "#0087ff"
    CYAN = "#00afaf"
    GREEN = "#5f8700"

    background_color = BASE03
    styles = {
        pygments.token.Keyword: GREEN,
        pygments.token.Keyword.Constant: ORANGE,
        pygments.token.Keyword.Declaration: BLUE,
        pygments.token.Keyword.Namespace: ORANGE,
        pygments.token.Keyword.Reserved: BLUE,
        pygments.token.Keyword.Type: RED,
        pygments.token.Name.Attribute: BASE1,
        pygments.token.Name.Builtin: BLUE,
        pygments.token.Name.Builtin.Pseudo: BLUE,
        pygments.token.Name.Class: BLUE,
        pygments.token.Name.Constant: ORANGE,
        pygments.token.Name.Decorator: BLUE,
        pygments.token.Name.Entity: ORANGE,
        pygments.token.Name.Exception: YELLOW,
        pygments.token.Name.Function: BLUE,
        pygments.token.Name.Tag: BLUE,
        pygments.token.Name.Variable: BLUE,
        pygments.token.String: CYAN,
        pygments.token.String.Backtick: BASE01,
        pygments.token.String.Char: CYAN,
        pygments.token.String.Doc: CYAN,
        pygments.token.String.Escape: RED,
        pygments.token.String.Heredoc: CYAN,
        pygments.token.String.Regex: RED,
        pygments.token.Number: CYAN,
        pygments.token.Operator: BASE1,
        pygments.token.Operator.Word: GREEN,
        pygments.token.Comment: BASE01,
        pygments.token.Comment.Preproc: GREEN,
        pygments.token.Comment.Special: GREEN,
        pygments.token.Generic.Deleted: CYAN,
        pygments.token.Generic.Emph: 'italic',
        pygments.token.Generic.Error: RED,
        pygments.token.Generic.Heading: ORANGE,
        pygments.token.Generic.Inserted: GREEN,
        pygments.token.Generic.Strong: 'bold',
        pygments.token.Generic.Subheading: ORANGE,
        pygments.token.Token: BASE1,
        pygments.token.Token.Other: ORANGE,
    }
