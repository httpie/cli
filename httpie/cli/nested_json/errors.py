from typing import Optional

from .tokens import Token, HIGHLIGHTER


class NestedJSONSyntaxError(ValueError):
    def __init__(
        self,
        source: str,
        token: Optional[Token],
        message: str,
        message_kind: str = 'Syntax',
    ) -> None:
        self.source = source
        self.token = token
        self.message = message
        self.message_kind = message_kind

    def __str__(self):
        lines = [f'HTTPie {self.message_kind} Error: {self.message}']
        if self.token is not None:
            lines.append(self.source)
            lines.append(
                ' ' * self.token.start
                + HIGHLIGHTER * (self.token.end - self.token.start)
            )
        return '\n'.join(lines)
