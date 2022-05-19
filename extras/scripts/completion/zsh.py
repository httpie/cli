from functools import singledispatch
from enum import Enum
from lib2to3.pgen2.pgen import generate_grammar
from completion_flow import (
    Node,
    Check,
    Suggest,
    Variable,
    Condition,
    Suggestion,
    If,
    And,
    Not,
    generate_flow,
)


class ZSHVariable(str, Enum):
    CURRENT = 'CURRENT'
    NORMARG = 'NORMARG'
    PREDECESSOR = 'predecessor'
    METHODS = 'METHODS'


SUGGESTION_TO_FUNCTION = {
    Suggestion.METHOD: '_httpie_method',
    Suggestion.URL: '_httpie_url',
    Suggestion.REQUEST_ITEM: '_httpie_request_item',
}


@singledispatch
def compile_zsh(node: Node) -> ...:
    raise NotImplementedError(f'{type(node)} is not supported')


@compile_zsh.register(If)
def compile_if(node: If) -> str:
    check = compile_zsh(node.check)
    action = compile_zsh(node.action)
    return f'if {check}; then\n    {action} && ret=0\nfi'


@compile_zsh.register(Check)
def compile_check(node: Check) -> str:
    args = [
        ZSHVariable(arg.name) if isinstance(arg, Variable) else arg
        for arg in node.args
    ]

    if node.condition is Condition.POSITION_EQ:
        return (
            f'(( {ZSHVariable.CURRENT} == {ZSHVariable.NORMARG} + {args[0]} ))'
        )
    elif node.condition is Condition.POSITION_GE:
        return (
            f'(( {ZSHVariable.CURRENT} >= {ZSHVariable.NORMARG} + {args[0]} ))'
        )
    elif node.condition is Condition.CONTAINS_PREDECESSOR:
        parts = [
            '[[ ${',
            args[0],
            '[(ie)$',
            ZSHVariable.PREDECESSOR,
            ']}',
            ' -le ${#',
            args[0],
            '} ]]',
        ]
        return ''.join(parts)


@compile_zsh.register(And)
def compile_and(node: And) -> str:
    return ' && '.join(compile_zsh(check) for check in node.checks)


@compile_zsh.register(Not)
def compile_not(node: Not) -> str:
    return f'! {compile_zsh(node.check)}'


@compile_zsh.register(Suggest)
def compile_suggest(node: Suggest) -> str:
    return SUGGESTION_TO_FUNCTION[node.suggestion]
