from enum import Enum
from functools import singledispatch

from completion_flow import (
    And,
    Check,
    Condition,
    If,
    Node,
    Not,
    Suggest,
    Suggestion,
    Variable,
    generate_flow,
)


class BashVariable(str, Enum):
    CURRENT = 'COMP_CWORD'
    NORMARG = 'NORMARG'
    CURRENT_WORD = 'cur_word'
    PREDECESSOR = 'prev_word'
    METHODS = 'METHODS'


SUGGESTION_TO_FUNCTION = {
    Suggestion.METHOD: '_http_complete_methods',
    Suggestion.URL: '_http_complete_url',
    Suggestion.REQUEST_ITEM: '_httpie_complete_request_item',
}


@singledispatch
def compile_bash(node: Node) -> ...:
    raise NotImplementedError(f'{type(node)} is not supported')


@compile_bash.register(If)
def compile_if(node: If) -> str:
    check = compile_bash(node.check)
    action = compile_bash(node.action)
    return f'if {check}; then\n    {action}\nfi'


@compile_bash.register(Check)
def compile_check(node: Check) -> str:
    args = [
        BashVariable(arg.name) if isinstance(arg, Variable) else arg
        for arg in node.args
    ]

    if node.condition is Condition.POSITION_EQ:
        return f'(( {BashVariable.CURRENT} == {BashVariable.NORMARG} + {args[0]} ))'
    elif node.condition is Condition.POSITION_GE:
        return f'(( {BashVariable.CURRENT} >= {BashVariable.NORMARG} + {args[0]} ))'
    elif node.condition is Condition.CONTAINS_PREDECESSOR:
        parts = [
            '[[ ',
            '" ${',
            BashVariable.METHODS,
            '[*]} " =~ " ${',
            BashVariable.PREDECESSOR,
            '} " ]]',
        ]
        return ''.join(parts)


@compile_bash.register(And)
def compile_and(node: And) -> str:
    return ' && '.join(compile_bash(check) for check in node.checks)


@compile_bash.register(Not)
def compile_not(node: Not) -> str:
    return f'! {compile_bash(node.check)}'


@compile_bash.register(Suggest)
def compile_suggest(node: Suggest) -> str:
    return (
        SUGGESTION_TO_FUNCTION[node.suggestion]
        + f' "${BashVariable.CURRENT_WORD}"'
    )
