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
from ...compat import is_windows
from ...context import Environment
from ...plugins import FormatterPlugin


AUTO_STYLE = 'auto'  # Follows terminal ANSI color styles
DEFAULT_STYLE = AUTO_STYLE

# Bundled here
SOLARIZED_STYLE = 'solarized'
PIE_STYLES = {
    'pie',
    'pie-light',
    'pie-dark'
}

if is_windows:
    # Colors on Windows via colorama don't look that
    # great and fruity seems to give the best result there.
    DEFAULT_STYLE = 'fruity'

BUNDLED_STYLES = {
    SOLARIZED_STYLE,
    AUTO_STYLE,
    *PIE_STYLES,
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
            body_formatter = formatter
            header_formatter = formatter
        else:
            from ..lexers.http import SimplifiedHTTPLexer
            header_formatter, body_formatter, precise = self.get_formatters(color_scheme)
            http_lexer = SimplifiedHTTPLexer(precise=precise)

        self.explicit_json = explicit_json  # --json
        self.header_formatter = header_formatter
        self.body_formatter = body_formatter
        self.http_lexer = http_lexer

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


LIGHT_COLORS = {
    'accent': '#52AB66',
    'backdrop': '#000000',
    'borders': '#D3D3D3',
    'canvas': '#E3E3E3',
    'code-aqua': '#698799',
    'code-blue': '#3B5EBA',
    'code-gray': '#7D7D7D',
    'code-green': '#52AB66',
    'code-orange': '#E3822B',
    'code-pink': '#8745BA',
    'code-primary': '#8745BA',
    'code-purple': '#8745BA',
    'code-red': '#C7382E',
    'code-yellow': '#BABA29',
    'focus': '#698FEB',
    'form-bg': '#EDEDEB',
    'hover': '#307842',
    'secondary': '#6C6969',
    'selection': '#C3E1CA',
    'tertiary': '#BBBABA',
}


DARK_COLORS = {
    'accent': '#73DC8C',
    'backdrop': '#7F7F7F',
    'borders': '#2D2A29',
    'canvas': '#1C1818',
    'code-aqua': '#8CB4CD',
    'code-blue': '#4B78E6',
    'code-gray': '#7D7D7D',
    'code-green': '#73DC8C',
    'code-orange': '#FFA24E',
    'code-pink': '#FA9BFA',
    'code-primary': '#D1D1CF',
    'code-purple': '#B464F0',
    'code-red': '#FF665B',
    'code-yellow': '#DBDE52',
    'focus': '#3B5EBA',
    'form-bg': '#231F1F',
    'hover': '#A1E8B0',
    'secondary': '#9E9D9A',
    'selection': '#37523C',
    'tertiary': '#474344',
}


def format_style(raw_styles, color_mapping):
    def format_value(value):
        return " ".join(
            color_mapping[part]
            if part in color_mapping else part
            for part in value.split()
        )

    return {
        key: format_value(value)
        for key, value in raw_styles.items()
    }


def make_styles(name, raw_styles):
    for mode, color_mapping in [
        ('light', LIGHT_COLORS),
        ('dark', DARK_COLORS)
    ]:
        yield type(
            name.format(mode=mode.title()),
            (pygments.style.Style,),
            {
                "styles": format_style(raw_styles, color_mapping)
            }
        )


PieLightHeaderStyle, PieDarkHeaderStyle = make_styles(
    'Pie{mode}HeaderStyle',
    {
        # HTTP line / Headers / Etc.
        pygments.token.Name.Namespace: 'bold code-primary',
        pygments.token.Keyword.Reserved: 'bold code-gray',
        pygments.token.Operator: 'bold code-gray',
        pygments.token.Number: 'bold code-gray',
        pygments.token.Name.Function.Magic: 'bold code-green',
        pygments.token.Name.Exception: 'bold code-green',
        pygments.token.Name.Attribute: 'code-blue',
        pygments.token.String: 'code-primary',

        # HTTP Methods
        pygments.token.Name.Function: 'bold code-gray',
        pygments.token.Name.Function.HTTP.GET: 'bold code-green',
        pygments.token.Name.Function.HTTP.HEAD: 'bold code-green',
        pygments.token.Name.Function.HTTP.POST: 'bold code-yellow',
        pygments.token.Name.Function.HTTP.PUT: 'bold code-orange',
        pygments.token.Name.Function.HTTP.PATCH: 'bold code-orange',
        pygments.token.Name.Function.HTTP.DELETE: 'bold code-red',

        # HTTP status codes
        pygments.token.Number.HTTP.INFO: 'bold code-aqua',
        pygments.token.Number.HTTP.OK: 'bold code-green',
        pygments.token.Number.HTTP.REDIRECT: 'bold code-yellow',
        pygments.token.Number.HTTP.CLIENT_ERR: 'bold code-orange',
        pygments.token.Number.HTTP.SERVER_ERR: 'bold code-red',
    }
)


PieLightBodyStyle, PieDarkBodyStyle = make_styles(
    'Pie{mode}BodyStyle',
    {
        # {}[]:
        pygments.token.Punctuation: 'code-gray',

        # Keys
        pygments.token.Name.Tag: 'code-pink',

        # Values
        pygments.token.Literal.String: 'code-green',
        pygments.token.Literal.String.Double: 'code-green',
        pygments.token.Literal.Number: 'code-aqua',
        pygments.token.Keyword: 'code-orange',

        # Other stuff
        pygments.token.Text: 'code-primary',
        pygments.token.Name.Attribute: 'code-primary',
        pygments.token.Name.Builtin: 'code-blue',
        pygments.token.Name.Builtin.Pseudo: 'code-blue',
        pygments.token.Name.Class: 'code-blue',
        pygments.token.Name.Constant: 'code-orange',
        pygments.token.Name.Decorator: 'code-blue',
        pygments.token.Name.Entity: 'code-orange',
        pygments.token.Name.Exception: 'code-yellow',
        pygments.token.Name.Function: 'code-blue',
        pygments.token.Name.Variable: 'code-blue',
        pygments.token.String: 'code-aqua',
        pygments.token.String.Backtick: 'secondary',
        pygments.token.String.Char: 'code-aqua',
        pygments.token.String.Doc: 'code-aqua',
        pygments.token.String.Escape: 'code-red',
        pygments.token.String.Heredoc: 'code-aqua',
        pygments.token.String.Regex: 'code-red',
        pygments.token.Number: 'code-aqua',
        pygments.token.Operator: 'code-primary',
        pygments.token.Operator.Word: 'code-green',
        pygments.token.Comment: 'secondary',
        pygments.token.Comment.Preproc: 'code-green',
        pygments.token.Comment.Special: 'code-green',
        pygments.token.Generic.Deleted: 'code-aqua',
        pygments.token.Generic.Emph: 'italic',
        pygments.token.Generic.Error: 'code-red',
        pygments.token.Generic.Heading: 'code-orange',
        pygments.token.Generic.Inserted: 'code-green',
        pygments.token.Generic.Strong: 'bold',
        pygments.token.Generic.Subheading: 'code-orange',
        pygments.token.Token: 'code-primary',
        pygments.token.Token.Other: 'code-orange',
    }
)


PIE_STYLES = {
    'pie': (
        PieDarkHeaderStyle,
        PieDarkBodyStyle,
    ),
    'pie-light': (
        PieLightHeaderStyle,
        PieLightBodyStyle,
    ),
    'pie-dark': (
        PieDarkHeaderStyle,
        PieDarkBodyStyle,
    )
}
