from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Iterator


class Condition(Enum):
    # $N = check.arguments[N]
    # $words = a list of splitted arguments on the completion
    # current = index in the $words

    # Check whether the $words[current][0] matches the $1
    STARTSWITH = auto()

    # Check whether the $1 contains the $words[current-1]
    CONTAINS_PREDECESSOR = auto()

    # Check whether current == $1
    POSITION_EQ = auto()

    # Check whether current >= $1
    POSITION_GE = auto()


class Suggestion(Enum):
    OPTION = auto()
    METHOD = auto()
    URL = auto()
    REQUEST_ITEM = auto()


class Variable(Enum):
    METHODS = auto()


class Node:
    ...


@dataclass
class Check(Node):
    condition: Condition
    args: List[str] = field(default_factory=list)


@dataclass
class Suggest(Node):
    suggestion: Suggestion


@dataclass
class If(Node):
    check: Node
    action: Node


@dataclass
class And(Node):
    checks: List[Node]

    def __init__(self, *checks) -> None:
        self.checks = checks


@dataclass
class Not(Node):
    check: Node


def main_flow() -> Iterator[Node]:
    # yield from suggest_option()
    yield from suggest_method()
    yield from suggest_url()
    yield from suggest_request_items()


def suggest_option():
    yield If(
        Check(Condition.STARTSWITH, args=['-']),
        action=Suggest(Suggestion.OPTION),
    )


def suggest_method():
    yield If(
        Check(Condition.POSITION_EQ, args=[0]),
        action=Suggest(Suggestion.METHOD),
    )


def suggest_url():
    yield If(
        Check(Condition.POSITION_EQ, args=[0]), action=Suggest(Suggestion.URL)
    )
    yield If(
        And(
            Check(Condition.POSITION_EQ, args=[1]),
            Check(Condition.CONTAINS_PREDECESSOR, args=[Variable.METHODS]),
        ),
        action=Suggest(Suggestion.URL),
    )


def suggest_request_items():
    yield If(
        Check(Condition.POSITION_GE, args=[2]),
        action=Suggest(Suggestion.REQUEST_ITEM),
    )
    yield If(
        And(
            Check(Condition.POSITION_GE, args=[1]),
            Not(
                Check(Condition.CONTAINS_PREDECESSOR, args=[Variable.METHODS])
            ),
        ),
        action=Suggest(Suggestion.REQUEST_ITEM),
    )
