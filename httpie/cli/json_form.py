"""
Routines for JSON form syntax, used to support nested JSON request items.

Highly inspired from the great jarg project <https://github.com/jdp/jarg/blob/master/jarg/jsonform.py>.
"""
import re
from typing import Optional


def step(value: str, is_escaped: bool) -> str:
    if is_escaped:
        value = value.replace(r'\[', '[').replace(r'\]', ']')
    return value


def find_opening_bracket(
    value: str,
    search=re.compile(r'(?<!\\)\[').search
) -> Optional[int]:
    match = search(value)
    if not match:
        return None
    return match.start()


def find_closing_bracket(
    value: str,
    search=re.compile(r'(?<!\\)\]').search
) -> Optional[int]:
    match = search(value)
    if not match:
        return None
    return match.start()


def parse_path(path):
    """
    Parse a string as a JSON path.

    An implementation of "steps to parse a JSON encoding path".
    <https://www.w3.org/TR/html-json-forms/#dfn-steps-to-parse-a-json-encoding-path>

    """
    original = path
    is_escaped = r'\[' in original

    opening_bracket = find_opening_bracket(original)
    last_step = [(step(path, is_escaped), {'last': True, 'type': 'object'})]
    if opening_bracket is None:
        return last_step

    steps = [(step(original[:opening_bracket], is_escaped), {'type': 'object'})]
    path = original[opening_bracket:]
    while path:
        if path.startswith('[]'):
            steps[-1][1]['append'] = True
            path = path[2:]
            if path:
                return last_step
        elif path[0] == '[':
            path = path[1:]
            closing_bracket = find_closing_bracket(path)
            if closing_bracket is None:
                return last_step
            key = path[:closing_bracket]
            path = path[closing_bracket + 1:]
            try:
                steps.append((int(key), {'type': 'array'}))
            except ValueError:
                steps.append((key, {'type': 'object'}))
        elif path[:2] == r'\[':
            key = step(path[1:path.index(r'\]') + 2], is_escaped)
            path = path[path.index(r'\]') + 2:]
            steps.append((key, {'type': 'object'}))
        else:
            return last_step

    for i in range(len(steps) - 1):
        steps[i][1]['type'] = steps[i + 1][1]['type']
    steps[-1][1]['last'] = True
    return steps


def set_value(context, step, current_value, entry_value):
    """Apply a JSON value to a context object.

    An implementation of "steps to set a JSON encoding value".
    <https://www.w3.org/TR/html-json-forms/#dfn-steps-to-set-a-json-encoding-value>

    """
    key, flags = step
    if flags.get('last', False):
        if current_value is None:
            if flags.get('append', False):
                context[key] = [entry_value]
            else:
                if isinstance(context, list) and len(context) <= key:
                    context.extend([None] * (key - len(context) + 1))
                context[key] = entry_value
        elif isinstance(current_value, list):
            context[key].append(entry_value)
        else:
            context[key] = [current_value, entry_value]
        return context

    if current_value is None:
        if flags.get('type') == 'array':
            context[key] = []
        else:
            if isinstance(context, list) and len(context) <= key:
                context.extend([None] * (key - len(context) + 1))
            context[key] = {}
        return context[key]

    if isinstance(current_value, dict):
        return context[key]

    if isinstance(current_value, list):
        if flags.get('type') == 'array':
            return current_value

        obj = {}
        for i, item in enumerate(current_value):
            if item is not None:
                obj[i] = item
        else:
            context[key] = obj
        return obj

    obj = {'': current_value}
    context[key] = obj
    return obj


def interpret_json_form(pairs):
    """The application/json form encoding algorithm.

    <https://www.w3.org/TR/html-json-forms/#dfn-application-json-encoding-algorithm>

    """
    result = {}
    for key, value in pairs:
        steps = parse_path(key)
        context = result
        for step in steps:
            try:
                current_value = context.get(step[0], None)
            except AttributeError:
                try:
                    current_value = context[step[0]]
                except IndexError:
                    current_value = None
            context = set_value(context, step, current_value, value)
    return result
