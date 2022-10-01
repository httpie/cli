from typing import Iterator

from .errors import NestedJSONSyntaxError
from .tokens import (
    EMPTY_STRING,
    BACKSLASH,
    TokenKind,
    OPERATORS,
    SPECIAL_CHARS,
    LITERAL_TOKENS,
    Token,
    PathAction,
    Path,
)


__all__ = [
    'parse',
    'assert_cant_happen',
]


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

    # noinspection PyShadowingNames
    def expect(*kinds):
        nonlocal cursor
        assert kinds
        if can_advance():
            token = tokens[cursor]
            cursor += 1
            if token.kind in kinds:
                return token
        elif tokens:
            token = tokens[-1]._replace(
                start=tokens[-1].end + 0,
                end=tokens[-1].end + 1,
            )
        else:
            token = None
        if len(kinds) == 1:
            suffix = kinds[0].to_name()
        else:
            suffix = ', '.join(kind.to_name() for kind in kinds[:-1])
            suffix += ' or ' + kinds[-1].to_name()
        message = f'Expecting {suffix}'
        raise NestedJSONSyntaxError(source, token, message)

    # noinspection PyShadowingNames
    def parse_root():
        tokens = []
        if not can_advance():
            return Path(
                kind=PathAction.KEY,
                accessor=EMPTY_STRING,
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
        # noinspection PyUnboundLocalVariable
        return Path(
            kind=action,
            accessor=value,
            tokens=tokens,
            is_root=True
        )

    yield parse_root()

    # path*
    while can_advance():
        path_tokens = [expect(TokenKind.LEFT_BRACKET)]
        token = expect(TokenKind.TEXT, TokenKind.NUMBER, TokenKind.RIGHT_BRACKET)
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
        # noinspection PyUnboundLocalVariable
        yield path


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
            kind=kind,
            value=value,
            start=cursor - (len(buffer) + backslashes),
            end=cursor,
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


def check_escaped_int(value: str) -> str:
    if not value.startswith(BACKSLASH):
        raise ValueError('Not an escaped int')
    try:
        int(value[1:])
    except ValueError as exc:
        raise ValueError('Not an escaped int') from exc
    else:
        return value[1:]


def assert_cant_happen():
    raise ValueError('Unexpected value')
