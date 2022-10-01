from typing import Type, Union, Any, Iterable, Tuple

from .parse import parse, assert_cant_happen
from .errors import NestedJSONSyntaxError
from .tokens import EMPTY_STRING, TokenKind, Token, PathAction, Path, NestedJSONArray


__all__ = [
    'interpret_nested_json',
    'unwrap_top_level_list_if_needed',
]

JSONType = Type[Union[dict, list, int, float, str]]
JSON_TYPE_MAPPING = {
    dict: 'object',
    list: 'array',
    int: 'number',
    float: 'number',
    str: 'string',
}


def interpret_nested_json(pairs: Iterable[Tuple[str, str]]) -> dict:
    context = None
    for key, value in pairs:
        context = interpret(context, key, value)
    return wrap_with_dict(context)


def interpret(context: Any, key: str, value: Any) -> Any:
    cursor = context
    paths = list(parse(key))
    paths.append(Path(PathAction.SET, value))

    # noinspection PyShadowingNames
    def type_check(index: int, path: Path, expected_type: JSONType):
        if not isinstance(cursor, expected_type):
            if path.tokens:
                pseudo_token = Token(
                    kind=TokenKind.PSEUDO,
                    value='',
                    start=path.tokens[0].start,
                    end=path.tokens[-1].end,
                )
            else:
                pseudo_token = None
            cursor_type = JSON_TYPE_MAPPING.get(type(cursor), type(cursor).__name__)
            required_type = JSON_TYPE_MAPPING[expected_type]
            message = f'Cannot perform {path.kind.to_string()!r} based access on '
            message += repr(''.join(path.reconstruct() for path in paths[:index]))
            message += f' which has a type of {cursor_type!r} but this operation'
            message += f' requires a type of {required_type!r}.'
            raise NestedJSONSyntaxError(
                source=key,
                token=pseudo_token,
                message=message,
                message_kind='Type',
            )

    def object_for(kind: PathAction) -> Any:
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
            cursor = cursor.setdefault(path.accessor, object_for(next_path.kind))
        elif path.kind is PathAction.INDEX:
            type_check(index, path, list)
            if path.accessor < 0:
                raise NestedJSONSyntaxError(
                    source=key,
                    token=path.tokens[1],
                    message='Negative indexes are not supported.',
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
        return {
            EMPTY_STRING: NestedJSONArray(context),
        }
    else:
        assert isinstance(context, dict)
        return context


def unwrap_top_level_list_if_needed(data: dict):
    """
    Propagate the top-level list, if that’s what we got.

    """
    if len(data) == 1:
        key, value = list(data.items())[0]
        if isinstance(value, NestedJSONArray):
            assert key == EMPTY_STRING
            return value
    return data
