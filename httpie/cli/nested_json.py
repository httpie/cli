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
                + '^' * (self.token.end - self.token.start)
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


OPERATORS = {'[': TokenKind.LEFT_BRACKET, ']': TokenKind.RIGHT_BRACKET}
SPECIAL_CHARS = OPERATORS.keys() | {'\\'}


class Token(NamedTuple):
    kind: TokenKind
    value: Union[str, int]
    start: int
    end: int


def assert_cant_happen() -> NoReturn:
    raise ValueError('Unexpected value')


def check_escaped_int(value: str) -> str:
    if not value.startswith('\\'):
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
        else:
            kind = TokenKind.TEXT

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
        elif index == '\\' and can_advance():
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


class Path:
    def __init__(
        self,
        kind: str,
        accessor: Optional[Union[str, int]] = None,
        tokens: Optional[List[Token]] = None,
        is_root: bool = False,
    ):
        self.kind = kind
        self.accessor = accessor
        self.tokens = tokens or []
        self.is_root = is_root

    def reconstruct(self) -> str:
        if self.kind == 'key':
            if self.is_root:
                return self.accessor
            return '[' + self.accessor + ']'
        elif self.kind == 'index':
            return '[' + str(self.accessor) + ']'
        elif self.kind == 'append':
            return '[]'
        else:
            assert_cant_happen()


def parse(source: str) -> Iterator[Path]:
    """
    start: literal? path*

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
        else:
            token = tokens[-1]._replace(
                start=tokens[-1].end + 0, end=tokens[-1].end + 1
            )

        if len(kinds) == 1:
            suffix = kinds[0].to_name()
        else:
            suffix = ', '.join(kind.to_name() for kind in kinds[:-1])
            suffix += ' or ' + kinds[-1].to_name()

        message = f'Expecting {suffix}'
        raise HTTPieSyntaxError(source, token, message)

    root = Path('key', '', is_root=True)
    if can_advance():
        token = tokens[cursor]
        if token.kind in {TokenKind.TEXT, TokenKind.NUMBER}:
            token = expect(TokenKind.TEXT, TokenKind.NUMBER)
            root.accessor = str(token.value)
            root.tokens.append(token)

    yield root

    while can_advance():
        path_tokens = []
        path_tokens.append(expect(TokenKind.LEFT_BRACKET))

        token = expect(
            TokenKind.TEXT, TokenKind.NUMBER, TokenKind.RIGHT_BRACKET
        )
        path_tokens.append(token)
        if token.kind is TokenKind.RIGHT_BRACKET:
            path = Path('append', tokens=path_tokens)
        elif token.kind is TokenKind.TEXT:
            path = Path('key', token.value, tokens=path_tokens)
            path_tokens.append(expect(TokenKind.RIGHT_BRACKET))
        elif token.kind is TokenKind.NUMBER:
            path = Path('index', token.value, tokens=path_tokens)
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
    paths.append(Path('set', value))

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

            message = f"Can't perform {path.kind!r} based access on "
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

    def object_for(kind: str) -> str:
        if kind == 'key':
            return {}
        elif kind in {'index', 'append'}:
            return []
        else:
            assert_cant_happen()

    for index, (path, next_path) in enumerate(zip(paths, paths[1:])):
        if path.kind == 'key':
            type_check(index, path, dict)
            if next_path.kind == 'set':
                cursor[path.accessor] = next_path.accessor
                break

            cursor = cursor.setdefault(
                path.accessor, object_for(next_path.kind)
            )
        elif path.kind == 'index':
            type_check(index, path, list)
            if path.accessor < 0:
                raise HTTPieSyntaxError(
                    key,
                    path.tokens[1],
                    'Negative indexes are not supported.',
                    message_kind='Value',
                )
            cursor.extend([None] * (path.accessor - len(cursor) + 1))
            if next_path.kind == 'set':
                cursor[path.accessor] = next_path.accessor
                break

            if cursor[path.accessor] is None:
                cursor[path.accessor] = object_for(next_path.kind)

            cursor = cursor[path.accessor]
        elif path.kind == 'append':
            type_check(index, path, list)
            if next_path.kind == 'set':
                cursor.append(next_path.accessor)
                break

            cursor.append(object_for(next_path.kind))
            cursor = cursor[-1]
        else:
            assert_cant_happen()

    return context


def interpret_nested_json(pairs):
    context = {}
    for key, value in pairs:
        interpret(context, key, value)
    return context
