import pygments
from pygments import token, lexer
from pygments.styles import get_style_by_name, STYLE_MAP
from pygments.lexers import get_lexer_for_mimetype, get_lexer_by_name
from pygments.formatters.terminal import TerminalFormatter
from pygments.formatters.terminal256 import Terminal256Formatter
from pygments.util import ClassNotFound
from pygments.style import Style

from httpie.compat import is_windows
from .base import BaseProcessor


# Colors on Windows via colorama don't look that
# great and fruity seems to give the best result there.
AVAILABLE_STYLES = set(STYLE_MAP.keys())
AVAILABLE_STYLES.add('solarized')
DEFAULT_STYLE = 'solarized' if not is_windows else 'fruity'


class PygmentsProcessor(BaseProcessor):
    """
    Colorize using Pygments

    This processor that applies syntax highlighting to the headers,
    and also to the body if its content type is recognized.

    """
    def __init__(self, *args, **kwargs):
        super(PygmentsProcessor, self).__init__(*args, **kwargs)

        if not self.env.colors:
            self.enabled = False
            return

        # Cache to speed things up when we process streamed body by line.
        self.lexers_by_type = {}

        try:
            style = get_style_by_name(
                self.kwargs.get('pygments_style', DEFAULT_STYLE))
        except ClassNotFound:
            style = Solarized256Style

        if self.env.is_windows or self.env.colors == 256:
            fmt_class = Terminal256Formatter
        else:
            fmt_class = TerminalFormatter
        self.formatter = fmt_class(style=style)

    def process_headers(self, headers):
        return pygments.highlight(headers, HTTPLexer(), self.formatter).strip()

    def process_body(self, body, mime):
        lexer = self.get_lexer(mime)
        if lexer:
            body = pygments.highlight(body, lexer, self.formatter)
        return body.strip()

    def get_lexer(self, mime):
        lexer = self.lexers_by_type.get(mime)
        if not lexer:
            try:
                lexer = get_lexer_for_mimetype(mime)
            except ClassNotFound:
                if '+' in mime:
                    # 'application/atom+xml' => 'xml'
                    subtype = mime.split('+')[-1]
                    try:
                        lexer = get_lexer_by_name(subtype)
                    except ClassNotFound:
                        pass
        self.lexers_by_type[mime] = lexer
        return lexer


class HTTPLexer(lexer.RegexLexer):
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
                token.Name.Attribute,  # Name
                token.Text,
                token.Operator,  # Colon
                token.Text,
                token.String  # Value
            ))
        ]
    }


class Solarized256Style(Style):
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
        token.Keyword: GREEN,
        token.Keyword.Constant: ORANGE,
        token.Keyword.Declaration: BLUE,
        token.Keyword.Namespace: ORANGE,
        token.Keyword.Reserved: BLUE,
        token.Keyword.Type: RED,
        token.Name.Attribute: BASE1,
        token.Name.Builtin: BLUE,
        token.Name.Builtin.Pseudo: BLUE,
        token.Name.Class: BLUE,
        token.Name.Constant: ORANGE,
        token.Name.Decorator: BLUE,
        token.Name.Entity: ORANGE,
        token.Name.Exception: YELLOW,
        token.Name.Function: BLUE,
        token.Name.Tag: BLUE,
        token.Name.Variable: BLUE,
        token.String: CYAN,
        token.String.Backtick: BASE01,
        token.String.Char: CYAN,
        token.String.Doc: CYAN,
        token.String.Escape: RED,
        token.String.Heredoc: CYAN,
        token.String.Regex: RED,
        token.Number: CYAN,
        token.Operator: BASE1,
        token.Operator.Word: GREEN,
        token.Comment: BASE01,
        token.Comment.Preproc: GREEN,
        token.Comment.Special: GREEN,
        token.Generic.Deleted: CYAN,
        token.Generic.Emph: 'italic',
        token.Generic.Error: RED,
        token.Generic.Heading: ORANGE,
        token.Generic.Inserted: GREEN,
        token.Generic.Strong: 'bold',
        token.Generic.Subheading: ORANGE,
        token.Token: BASE1,
        token.Token.Other: ORANGE,
    }
