import json
from typing import Optional, Type, Tuple

import pygments.formatters
import pygments.lexer
import pygments.lexers
import pygments.style
import pygments.styles
import pygments.token
from pygments.formatters.terminal import TerminalFormatter
from pygments.formatters.terminal256 import Terminal256Formatter
from pygments.lexer import Lexer
from pygments.lexers.data import JsonLexer
from pygments.lexers.special import TextLexer
from pygments.lexers.text import HttpLexer as PygmentsHttpLexer
from pygments.util import ClassNotFound

from ..lexers.json import EnhancedJsonLexer
from ..lexers.metadata import MetadataLexer
from ..ui.palette import SHADE_NAMES, get_color
from ...context import Environment
from ...plugins import FormatterPlugin


AUTO_STYLE = 'auto'  # Follows terminal ANSI color styles
DEFAULT_STYLE = AUTO_STYLE
SOLARIZED_STYLE = 'solarized'  # Bundled here

BUNDLED_STYLES = {
    SOLARIZED_STYLE,
    AUTO_STYLE
}


def get_available_styles():
    return BUNDLED_STYLES | set(pygments.styles.get_all_styles())


class ColorFormatter(FormatterPlugin):
    """
    Colorize using Pygments

    This processor that applies syntax highlighting to the headers,
    and also to the body if its content type is recognized.

    """
    group_name = 'colors'
    metadata_lexer = MetadataLexer()

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
            body_formatter = header_formatter = TerminalFormatter()
            precise = False
        else:
            from ..lexers.http import SimplifiedHTTPLexer
            header_formatter, body_formatter, precise = self.get_formatters(color_scheme)
            http_lexer = SimplifiedHTTPLexer(precise=precise)

        self.explicit_json = explicit_json  # --json
        self.header_formatter = header_formatter
        self.body_formatter = body_formatter
        self.http_lexer = http_lexer
        self.metadata_lexer = MetadataLexer(precise=precise)

    def format_headers(self, headers: str) -> str:
        return pygments.highlight(
            code=headers,
            lexer=self.http_lexer,
            formatter=self.header_formatter,
        ).strip()

    def format_body(self, body: str, mime: str) -> str:
        lexer = self.get_lexer_for_body(mime, body)
        if lexer:
            body = pygments.highlight(
                code=body,
                lexer=lexer,
                formatter=self.body_formatter,
            )
        return body

    def format_metadata(self, metadata: str) -> str:
        return pygments.highlight(
            code=metadata,
            lexer=self.metadata_lexer,
            formatter=self.header_formatter,
        ).strip()

    def get_lexer_for_body(
        self, mime: str,
        body: str
    ) -> Optional[Type[Lexer]]:
        return get_lexer(
            mime=mime,
            explicit_json=self.explicit_json,
            body=body,
        )

    def get_formatters(self, color_scheme: str) -> Tuple[
        pygments.formatter.Formatter,
        pygments.formatter.Formatter,
        bool
    ]:
        if color_scheme in PIE_STYLES:
            header_style, body_style = PIE_STYLES[color_scheme]
            precise = True
        else:
            header_style = self.get_style_class(color_scheme)
            body_style = header_style
            precise = False

        return (
            Terminal256Formatter(style=header_style),
            Terminal256Formatter(style=body_style),
            precise
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
            f'{type_}/{subtype_name}',
            f'{type_}/{subtype_suffix}',
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

    # Use our own JSON lexer: it supports JSON bodies preceded by non-JSON data
    # as well as legit JSON bodies.
    if isinstance(lexer, JsonLexer):
        lexer = EnhancedJsonLexer()

    return lexer


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


PIE_HEADER_STYLE = {
    # HTTP line / Headers / Etc.
    pygments.token.Name.Namespace: 'bold primary',
    pygments.token.Keyword.Reserved: 'bold grey',
    pygments.token.Operator: 'bold grey',
    pygments.token.Number: 'bold grey',
    pygments.token.Name.Function.Magic: 'bold green',
    pygments.token.Name.Exception: 'bold green',
    pygments.token.Name.Attribute: 'blue',
    pygments.token.String: 'primary',

    # HTTP Methods
    pygments.token.Name.Function: 'bold grey',
    pygments.token.Name.Function.HTTP.GET: 'bold green',
    pygments.token.Name.Function.HTTP.HEAD: 'bold green',
    pygments.token.Name.Function.HTTP.POST: 'bold yellow',
    pygments.token.Name.Function.HTTP.PUT: 'bold orange',
    pygments.token.Name.Function.HTTP.PATCH: 'bold orange',
    pygments.token.Name.Function.HTTP.DELETE: 'bold red',

    # HTTP status codes
    pygments.token.Number.HTTP.INFO: 'bold aqua',
    pygments.token.Number.HTTP.OK: 'bold green',
    pygments.token.Number.HTTP.REDIRECT: 'bold yellow',
    pygments.token.Number.HTTP.CLIENT_ERR: 'bold orange',
    pygments.token.Number.HTTP.SERVER_ERR: 'bold red',

    # Metadata
    pygments.token.Name.Decorator: 'grey',
    pygments.token.Number.SPEED.FAST: 'bold green',
    pygments.token.Number.SPEED.AVG: 'bold yellow',
    pygments.token.Number.SPEED.SLOW: 'bold orange',
    pygments.token.Number.SPEED.VERY_SLOW: 'bold red',
}

PIE_BODY_STYLE = {
    # {}[]:
    pygments.token.Punctuation: 'grey',

    # Keys
    pygments.token.Name.Tag: 'pink',

    # Values
    pygments.token.Literal.String: 'green',
    pygments.token.Literal.String.Double: 'green',
    pygments.token.Literal.Number: 'aqua',
    pygments.token.Keyword: 'orange',

    # Other stuff
    pygments.token.Text: 'primary',
    pygments.token.Name.Attribute: 'primary',
    pygments.token.Name.Builtin: 'blue',
    pygments.token.Name.Builtin.Pseudo: 'blue',
    pygments.token.Name.Class: 'blue',
    pygments.token.Name.Constant: 'orange',
    pygments.token.Name.Decorator: 'blue',
    pygments.token.Name.Entity: 'orange',
    pygments.token.Name.Exception: 'yellow',
    pygments.token.Name.Function: 'blue',
    pygments.token.Name.Variable: 'blue',
    pygments.token.String: 'aqua',
    pygments.token.String.Backtick: 'secondary',
    pygments.token.String.Char: 'aqua',
    pygments.token.String.Doc: 'aqua',
    pygments.token.String.Escape: 'red',
    pygments.token.String.Heredoc: 'aqua',
    pygments.token.String.Regex: 'red',
    pygments.token.Number: 'aqua',
    pygments.token.Operator: 'primary',
    pygments.token.Operator.Word: 'green',
    pygments.token.Comment: 'secondary',
    pygments.token.Comment.Preproc: 'green',
    pygments.token.Comment.Special: 'green',
    pygments.token.Generic.Deleted: 'aqua',
    pygments.token.Generic.Emph: 'italic',
    pygments.token.Generic.Error: 'red',
    pygments.token.Generic.Heading: 'orange',
    pygments.token.Generic.Inserted: 'green',
    pygments.token.Generic.Strong: 'bold',
    pygments.token.Generic.Subheading: 'orange',
    pygments.token.Token: 'primary',
    pygments.token.Token.Other: 'orange',
}


def make_style(name, raw_styles, shade):
    def format_value(value):
        return ' '.join(
            get_color(part, shade) or part
            for part in value.split()
        )

    bases = (pygments.style.Style,)
    data = {
        'styles': {
            key: format_value(value)
            for key, value in raw_styles.items()
        }
    }
    return type(name, bases, data)


def make_styles():
    styles = {}

    for shade, name in SHADE_NAMES.items():
        styles[name] = [
            make_style(name, style_map, shade)
            for style_name, style_map in [
                (f'Pie{name}HeaderStyle', PIE_HEADER_STYLE),
                (f'Pie{name}BodyStyle', PIE_BODY_STYLE),
            ]
        ]

    return styles


PIE_STYLES = make_styles()
BUNDLED_STYLES |= PIE_STYLES.keys()
