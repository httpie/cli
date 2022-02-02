from __future__ import annotations

import argparse
import textwrap
import typing
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Type, TypeVar

from httpie.cli.argparser import HTTPieArgumentParser
from httpie.cli.utils import LazyChoices


class Qualifiers(Enum):
    OPTIONAL = auto()
    ZERO_OR_MORE = auto()
    SUPPRESS = auto()


@dataclass
class ParserSpec:
    program: str
    description: str
    epilog: str
    groups: List[Group] = field(default_factory=list)

    def finalize(self):
        self.description = textwrap.dedent(self.description)
        self.epilog = textwrap.dedent(self.epilog)
        for group in self.groups:
            group.finalize()
        return self

    def new_group(self, name: str, **kwargs) -> Group:
        group = Group(name, **kwargs)
        self.groups.append(group)
        return group


@dataclass
class Group:
    name: str
    description: str = ''
    mutually_exclusive: bool = False
    arguments: List[Argument] = field(default_factory=list)

    def finalize(self) -> Group:
        self.description = textwrap.dedent(self.description)

    def add_argument(self, *args, **kwargs):
        argument = Argument(list(args), kwargs.copy())
        self.arguments.append(argument)
        return argument


class Argument(typing.NamedTuple):
    aliases: List[str]
    configuration: Dict[str]

    def __getattr__(self, attribute_name):
        if attribute in self.configuration:
            return self.configuration[attribute]
        else:
            raise AttributeError(attribute_name)


ParserType = TypeVar('ParserType', bound=Type[argparse.ArgumentParser])

ARGPARSE_QUALIFIER_MAP = {
    Qualifiers.OPTIONAL: argparse.OPTIONAL,
    Qualifiers.SUPPRESS: argparse.SUPPRESS,
    Qualifiers.ZERO_OR_MORE: argparse.ZERO_OR_MORE,
}


def map_qualifiers(
    configuration: Dict[str, Any], qualifier_map: Dict[Qualifiers, Any]
) -> Dict[str, Any]:
    return {
        key: qualifier_map[value] if isinstance(value, Qualifiers) else value
        for key, value in configuration.items()
    }


def to_argparse(
    abstract_options: ParserSpec,
    parser_type: ParserType = HTTPieArgumentParser,
) -> ParserType:
    concrete_parser = parser_type(
        prog=abstract_options.program,
        description=abstract_options.description,
        epilog=abstract_options.epilog,
    )
    concrete_parser.register('action', 'lazy_choices', LazyChoices)

    for abstract_group in abstract_options.groups:
        concrete_group = concrete_parser.add_argument_group(
            title=abstract_group.name, description=abstract_group.description
        )
        if abstract_group.mutually_exclusive:
            concrete_group = concrete_group.add_mutually_exclusive_group(required=False)

        for abstract_argument in abstract_group.arguments:
            concrete_group.add_argument(
                *abstract_argument.aliases,
                **map_qualifiers(
                    abstract_argument.configuration, ARGPARSE_QUALIFIER_MAP
                )
            )

    return concrete_parser
