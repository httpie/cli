import pygments
from httpie.output.lexers.common import precise

SPEED_TOKENS = {
    0.45: pygments.token.Number.SPEED.FAST,
    1.00: pygments.token.Number.SPEED.AVG,
    2.50: pygments.token.Number.SPEED.SLOW,
}


def speed_based_token(lexer, match, ctx):
    try:
        value = float(match.group())
    except ValueError:
        return pygments.token.Number

    for limit, token in SPEED_TOKENS.items():
        if value <= limit:
            break
    else:
        token = pygments.token.Number.SPEED.VERY_SLOW

    response_type = precise(
        lexer,
        token,
        pygments.token.Number
    )
    yield match.start(), response_type, match.group()


class MetadataLexer(pygments.lexer.RegexLexer):
    """Simple HTTPie metadata lexer."""

    tokens = {
        'root': [
            (
                r'(Elapsed time)( *)(:)( *)(\d+\.\d+)(s)', pygments.lexer.bygroups(
                    pygments.token.Name.Decorator,  # Name
                    pygments.token.Text,
                    pygments.token.Operator,  # Colon
                    pygments.token.Text,
                    speed_based_token,
                    pygments.token.Name.Builtin  # Value
                )
            ),
            # Generic item
            (
                r'(.*?)( *)(:)( *)(.+)', pygments.lexer.bygroups(
                    pygments.token.Name.Decorator,  # Name
                    pygments.token.Text,
                    pygments.token.Operator,  # Colon
                    pygments.token.Text,
                    pygments.token.Text  # Value
                )
            ),
        ]
    }
