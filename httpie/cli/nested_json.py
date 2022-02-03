from enum import Enum, auto
from typing import (
    Any,
    Iterator,
    NamedTuple,
    Optional,
    List,
    NoReturn,
    Type,
    Union,
)
from httpie.cli.dicts import NestedJSONArray
from httpie.cli.constants import EMPTY_STRING, OPEN_BRACKET, CLOSE_BRACKET, BACKSLASH, HIGHLIGHTER


class HTTPieSyntaxError(ValueError):
    def __init__(
        self,
        source: str,
        token: Optional['Token'],
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
                ' ' * (self.token.start)
                + HIGHLIGHTER * (self.token.end - self.token.start)
            )
        return '\n'.join(lines)


class TokenKind(Enum):
    TEXT = auto()
    NUMBER = auto()
    LEFT_BRACKET = auto()
    RIGHT_BRACKET = auto()

    def to_name(self) -> str:
        for key, value in OPERATORS.items():
            if value is self:
                return repr(key)
        else:
            return 'a ' + self.name.lower()


OPERATORS = {OPEN_BRACKET: TokenKind.LEFT_BRACKET, CLOSE_BRACKET: TokenKind.RIGHT_BRACKET}
SPECIAL_CHARS = OPERATORS.keys() | {BACKSLASH}
LITERAL_TOKENS = [TokenKind.TEXT, TokenKind.NUMBER]


class Token(NamedTuple):
    kind: TokenKind
    value: Union[str, int]
    start: int
    end: int


def assert_cant_happen() -> NoReturn:
    raise ValueError('Unexpected value')


def check_escaped_int(value: str) -> str:
    if not value.startswith(BACKSLASH):
        raise ValueError('Not an escaped int')

    try:
        int(value[1:])
    except ValueError as exc:
        raise ValueError('Not an escaped int') from exc
    else:
        return value[1:]


def tokenize(source: str) -> Iterator[Token]:
    cursor = 0
    backslashes = 0
    buffer = []

    def send_buffer() -> Iterator[Token]:
        nonlocal backslashes
        if not buffer:
            return None

        value = ''.join(buffer)
        kind = TokenKind.TEXT
        if not backslashes:
            for variation, kind in [
                (int, TokenKind.NUMBER),
                (check_escaped_int, TokenKind.TEXT),
            ]:
                try:
                    value = variation(value)
                except ValueError:
                    continue
                else:
                    break

        yield Token(
            kind, value, start=cursor - (len(buffer) + backslashes), end=cursor
        )
        buffer.clear()
        backslashes = 0

    def can_advance() -> bool:
        return cursor < len(source)

    while can_advance():
        index = source[cursor]
        if index in OPERATORS:
            yield from send_buffer()
            yield Token(OPERATORS[index], index, cursor, cursor + 1)
        elif index == BACKSLASH and can_advance():
            if source[cursor + 1] in SPECIAL_CHARS:
                backslashes += 1
            else:
                buffer.append(index)

            buffer.append(source[cursor + 1])
            cursor += 1
        else:
            buffer.append(index)

        cursor += 1

    yield from send_buffer()


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
        else:
            assert_cant_happen()


def parse(source: str) -> Iterator[Path]:
    """
    start: root_path path*
    root_path: (literal | index_path | append_path)
    literal: TEXT | NUMBER

    path:
        key_path
        | index_path
        | append_path
    key_path: LEFT_BRACKET TEXT RIGHT_BRACKET
    index_path: LEFT_BRACKET NUMBER RIGHT_BRACKET
    append_path: LEFT_BRACKET RIGHT_BRACKET
    """

    tokens = list(tokenize(source))
    cursor = 0

    def can_advance():
        return cursor < len(tokens)

    def expect(*kinds):
        nonlocal cursor

        assert len(kinds) > 0
        if can_advance():
            token = tokens[cursor]
            cursor += 1
            if token.kind in kinds:
                return token
        elif tokens:
            token = tokens[-1]._replace(
                start=tokens[-1].end + 0, end=tokens[-1].end + 1
            )
        else:
            token = None

        if len(kinds) == 1:
            suffix = kinds[0].to_name()
        else:
            suffix = ', '.join(kind.to_name() for kind in kinds[:-1])
            suffix += ' or ' + kinds[-1].to_name()

        message = f'Expecting {suffix}'
        raise HTTPieSyntaxError(source, token, message)

    def parse_root():
        tokens = []
        if not can_advance():
            return Path(
                PathAction.KEY,
                EMPTY_STRING,
                is_root=True
            )

        # (literal | index_path | append_path)?
        token = expect(*LITERAL_TOKENS, TokenKind.LEFT_BRACKET)
        tokens.append(token)

        if token.kind in LITERAL_TOKENS:
            action = PathAction.KEY
            value = str(token.value)
        elif token.kind is TokenKind.LEFT_BRACKET:
            token = expect(TokenKind.NUMBER, TokenKind.RIGHT_BRACKET)
            tokens.append(token)
            if token.kind is TokenKind.NUMBER:
                action = PathAction.INDEX
                value = token.value
                tokens.append(expect(TokenKind.RIGHT_BRACKET))
            elif token.kind is TokenKind.RIGHT_BRACKET:
                action = PathAction.APPEND
                value = None
            else:
                assert_cant_happen()
        else:
            assert_cant_happen()

        return Path(
            action,
            value,
            tokens=tokens,
            is_root=True
        )

    yield parse_root()

    # path*
    while can_advance():
        path_tokens = []
        path_tokens.append(expect(TokenKind.LEFT_BRACKET))

        token = expect(
            TokenKind.TEXT, TokenKind.NUMBER, TokenKind.RIGHT_BRACKET
        )
        path_tokens.append(token)
        if token.kind is TokenKind.RIGHT_BRACKET:
            path = Path(PathAction.APPEND, tokens=path_tokens)
        elif token.kind is TokenKind.TEXT:
            path = Path(PathAction.KEY, token.value, tokens=path_tokens)
            path_tokens.append(expect(TokenKind.RIGHT_BRACKET))
        elif token.kind is TokenKind.NUMBER:
            path = Path(PathAction.INDEX, token.value, tokens=path_tokens)
            path_tokens.append(expect(TokenKind.RIGHT_BRACKET))
        else:
            assert_cant_happen()
        yield path


JSON_TYPE_MAPPING = {
    dict: 'object',
    list: 'array',
    int: 'number',
    float: 'number',
    str: 'string',
}


def interpret(context: Any, key: str, value: Any) -> Any:
    cursor = context

    paths = list(parse(key))
    paths.append(Path(PathAction.SET, value))

    def type_check(index: int, path: Path, expected_type: Type[Any]) -> None:
        if not isinstance(cursor, expected_type):
            if path.tokens:
                pseudo_token = Token(
                    None, None, path.tokens[0].start, path.tokens[-1].end
                )
            else:
                pseudo_token = None

            cursor_type = JSON_TYPE_MAPPING.get(
                type(cursor), type(cursor).__name__
            )
            required_type = JSON_TYPE_MAPPING[expected_type]

            message = f"Can't perform {path.kind.to_string()!r} based access on "
            message += repr(
                ''.join(path.reconstruct() for path in paths[:index])
            )
            message += (
                f' which has a type of {cursor_type!r} but this operation'
            )
            message += f' requires a type of {required_type!r}.'
            raise HTTPieSyntaxError(
                key, pseudo_token, message, message_kind='Type'
            )

    def object_for(kind: str) -> Any:
        if kind is PathAction.KEY:
            return {}
        elif kind in {PathAction.INDEX, PathAction.APPEND}:
            return []
        else:
            assert_cant_happen()

    for index, (path, next_path) in enumerate(zip(paths, paths[1:])):
        # If there is no context yet, set it.
        if cursor is None:
            context = cursor = object_for(path.kind)

        if path.kind is PathAction.KEY:
            type_check(index, path, dict)
            if next_path.kind is PathAction.SET:
                cursor[path.accessor] = next_path.accessor
                break

            cursor = cursor.setdefault(
                path.accessor, object_for(next_path.kind)
            )
        elif path.kind is PathAction.INDEX:
            type_check(index, path, list)
            if path.accessor < 0:
                raise HTTPieSyntaxError(
                    key,
                    path.tokens[1],
                    'Negative indexes are not supported.',
                    message_kind='Value',
                )
            cursor.extend([None] * (path.accessor - len(cursor) + 1))
            if next_path.kind is PathAction.SET:
                cursor[path.accessor] = next_path.accessor
                break

            if cursor[path.accessor] is None:
                cursor[path.accessor] = object_for(next_path.kind)

            cursor = cursor[path.accessor]
        elif path.kind is PathAction.APPEND:
            type_check(index, path, list)
            if next_path.kind is PathAction.SET:
                cursor.append(next_path.accessor)
                break

            cursor.append(object_for(next_path.kind))
            cursor = cursor[-1]
        else:
            assert_cant_happen()

    return context


def wrap_with_dict(context):
    if context is None:
        return {}
    elif isinstance(context, list):
        return {EMPTY_STRING: NestedJSONArray(context)}
    else:
        assert isinstance(context, dict)
        return context


def interpret_nested_json(pairs):
    context = None
    for key, value in pairs:
        context = interpret(context, key, value)

    return wrap_with_dict(context)
