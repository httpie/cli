import pygments


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
