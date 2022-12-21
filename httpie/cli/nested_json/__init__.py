"""
A library for parsing the HTTPie nested JSON key syntax and constructing the resulting objects.

<https://httpie.io/docs/cli/nested-json>

It has no dependencies.

"""
from .errors import NestedJSONSyntaxError
from .interpret import interpret_nested_json, unwrap_top_level_list_if_needed
from .tokens import EMPTY_STRING, NestedJSONArray

__all__ = [
    'interpret_nested_json',
    'unwrap_top_level_list_if_needed',
    'EMPTY_STRING',
    'NestedJSONArray',
    'NestedJSONSyntaxError',
]
