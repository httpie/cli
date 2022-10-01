from enum import Enum, auto
from typing import NamedTuple, Union, Optional, List

EMPTY_STRING = ''
HIGHLIGHTER = '^'
OPEN_BRACKET = '['
CLOSE_BRACKET = ']'
BACKSLASH = '\\'


class TokenKind(Enum):
    TEXT = auto()
    NUMBER = auto()
    LEFT_BRACKET = auto()
    RIGHT_BRACKET = auto()
    PSEUDO = auto()  # Not a real token, use when representing location only.

    def to_name(self) -> str:
        for key, value in OPERATORS.items():
            if value is self:
                return repr(key)
        else:
            return 'a ' + self.name.lower()


OPERATORS = {
    OPEN_BRACKET: TokenKind.LEFT_BRACKET,
    CLOSE_BRACKET: TokenKind.RIGHT_BRACKET,
}
SPECIAL_CHARS = OPERATORS.keys() | {BACKSLASH}
LITERAL_TOKENS = [
    TokenKind.TEXT,
    TokenKind.NUMBER,
]


class Token(NamedTuple):
    kind: TokenKind
    value: Union[str, int]
    start: int
    end: int


class PathAction(Enum):
    KEY = auto()
    INDEX = auto()
    APPEND = auto()
    # Pseudo action, used by the interpreter
    SET = auto()

    def to_string(self) -> str:
        return self.name.lower()


class Path:
    def __init__(
        self,
        kind: PathAction,
        accessor: Optional[Union[str, int]] = None,
        tokens: Optional[List[Token]] = None,
        is_root: bool = False,
    ):
        self.kind = kind
        self.accessor = accessor
        self.tokens = tokens or []
        self.is_root = is_root

    def reconstruct(self) -> str:
        if self.kind is PathAction.KEY:
            if self.is_root:
                return str(self.accessor)
            return OPEN_BRACKET + self.accessor + CLOSE_BRACKET
        elif self.kind is PathAction.INDEX:
            return OPEN_BRACKET + str(self.accessor) + CLOSE_BRACKET
        elif self.kind is PathAction.APPEND:
            return OPEN_BRACKET + CLOSE_BRACKET


class NestedJSONArray(list):
    """Denotes a top-level JSON array."""
