import argparse
import textwrap
import typing
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Optional, Dict, List, Tuple, Type, TypeVar

from httpie.cli.argparser import HTTPieArgumentParser
from httpie.cli.utils import Manual, LazyChoices


class Qualifiers(Enum):
    OPTIONAL = auto()
    ZERO_OR_MORE = auto()
    ONE_OR_MORE = auto()
    SUPPRESS = auto()


def map_qualifiers(
    configuration: Dict[str, Any], qualifier_map: Dict[Qualifiers, Any]
) -> Dict[str, Any]:
    return {
        key: qualifier_map[value] if isinstance(value, Qualifiers) else value
        for key, value in configuration.items()
    }


def drop_keys(
    configuration: Dict[str, Any], key_blacklist: Tuple[str, ...]
):
    return {
        key: value
        for key, value in configuration.items()
        if key not in key_blacklist
    }


PARSER_SPEC_VERSION = '0.0.1a0'


@dataclass
class ParserSpec:
    program: str
    description: Optional[str] = None
    epilog: Optional[str] = None
    groups: List['Group'] = field(default_factory=list)
    man_page_hint: Optional[str] = None
    source_file: Optional[str] = None

    def finalize(self) -> 'ParserSpec':
        if self.description:
            self.description = textwrap.dedent(self.description)
        if self.epilog:
            self.epilog = textwrap.dedent(self.epilog)
        for group in self.groups:
            group.finalize()
        return self

    def add_group(self, name: str, **kwargs) -> 'Group':
        group = Group(name, **kwargs)
        self.groups.append(group)
        return group

    def serialize(self) -> Dict[str, Any]:
        return {
            'name': self.program,
            'description': self.description,
            'groups': [group.serialize() for group in self.groups],
        }


@dataclass
class Group:
    name: str
    description: str = ''
    is_mutually_exclusive: bool = False
    arguments: List['Argument'] = field(default_factory=list)

    def finalize(self) -> None:
        if self.description:
            self.description = textwrap.dedent(self.description)

    def add_argument(self, *args, **kwargs):
        argument = Argument(list(args), kwargs.copy())
        argument.post_init()
        self.arguments.append(argument)
        return argument

    def serialize(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'description': self.description or None,
            'is_mutually_exclusive': self.is_mutually_exclusive,
            'args': [argument.serialize() for argument in self.arguments],
        }


class Argument(typing.NamedTuple):
    aliases: List[str]
    configuration: Dict[str, Any]

    def post_init(self):
        """Run a bunch of post-init hooks."""
        # If there is a short help, then create the longer version from it.
        short_help = self.configuration.get('short_help')
        if (
            short_help
            and 'help' not in self.configuration
            and self.configuration.get('action') != 'lazy_choices'
        ):
            self.configuration['help'] = f'\n{short_help}\n\n'

    def serialize(self, *, isolation_mode: bool = False) -> Dict[str, Any]:
        configuration = self.configuration.copy()

        # Unpack the dynamically computed choices, since we
        # will need to store the actual values somewhere.
        action = configuration.pop('action', None)
        short_help = configuration.pop('short_help', None)
        nested_options = configuration.pop('nested_options', None)

        if action == 'lazy_choices':
            choices = LazyChoices(
                self.aliases,
                **{'dest': None, **configuration},
                isolation_mode=isolation_mode
            )
            configuration['choices'] = list(choices.load())
            configuration['help'] = choices.help

        result = {}
        if self.aliases:
            result['options'] = self.aliases.copy()
        else:
            result['options'] = [configuration['metavar']]
            result['is_positional'] = True

        qualifiers = JSON_QUALIFIER_TO_OPTIONS[configuration.get('nargs', Qualifiers.SUPPRESS)]
        result.update(qualifiers)

        description = configuration.get('help')
        if description and description is not Qualifiers.SUPPRESS:
            result['short_description'] = short_help
            result['description'] = description

        if nested_options:
            result['nested_options'] = nested_options

        python_type = configuration.get('type')
        if python_type is not None:
            if hasattr(python_type, '__name__'):
                type_name = python_type.__name__
            else:
                type_name = type(python_type).__name__

            result['python_type_name'] = type_name

        result.update({
            key: value
            for key, value in configuration.items()
            if key in JSON_DIRECT_MIRROR_OPTIONS
            if value is not Qualifiers.SUPPRESS
        })

        return result

    @property
    def is_positional(self):
        return len(self.aliases) == 0

    @property
    def is_hidden(self):
        return self.configuration.get('help') is Qualifiers.SUPPRESS

    def __getattr__(self, attribute_name):
        if attribute_name in self.configuration:
            return self.configuration[attribute_name]
        else:
            raise AttributeError(attribute_name)


ParserType = TypeVar('ParserType', bound=Type[argparse.ArgumentParser])

ARGPARSE_QUALIFIER_MAP = {
    Qualifiers.OPTIONAL: argparse.OPTIONAL,
    Qualifiers.SUPPRESS: argparse.SUPPRESS,
    Qualifiers.ZERO_OR_MORE: argparse.ZERO_OR_MORE,
    Qualifiers.ONE_OR_MORE: argparse.ONE_OR_MORE
}
ARGPARSE_IGNORE_KEYS = ('short_help', 'nested_options')


def to_argparse(
    abstract_options: ParserSpec,
    parser_type: ParserType = HTTPieArgumentParser,
) -> ParserType:
    concrete_parser = parser_type(
        prog=abstract_options.program,
        description=abstract_options.description,
        epilog=abstract_options.epilog,
    )
    concrete_parser.spec = abstract_options
    concrete_parser.register('action', 'lazy_choices', LazyChoices)
    concrete_parser.register('action', 'manual', Manual)

    for abstract_group in abstract_options.groups:
        concrete_group = concrete_parser.add_argument_group(
            title=abstract_group.name, description=abstract_group.description
        )
        if abstract_group.is_mutually_exclusive:
            concrete_group = concrete_group.add_mutually_exclusive_group(required=False)

        for abstract_argument in abstract_group.arguments:
            concrete_group.add_argument(
                *abstract_argument.aliases,
                **drop_keys(map_qualifiers(
                    abstract_argument.configuration, ARGPARSE_QUALIFIER_MAP
                ), ARGPARSE_IGNORE_KEYS)
            )

    return concrete_parser


JSON_DIRECT_MIRROR_OPTIONS = (
    'choices',
    'metavar'
)


JSON_QUALIFIER_TO_OPTIONS = {
    Qualifiers.OPTIONAL: {'is_optional': True},
    Qualifiers.ZERO_OR_MORE: {'is_optional': True, 'is_variadic': True},
    Qualifiers.ONE_OR_MORE: {'is_optional': False, 'is_variadic': True},
    Qualifiers.SUPPRESS: {}
}


def to_data(abstract_options: ParserSpec) -> Dict[str, Any]:
    return {'version': PARSER_SPEC_VERSION, 'spec': abstract_options.serialize()}


def parser_to_parser_spec(parser: argparse.ArgumentParser, **kwargs) -> ParserSpec:
    """Take an existing argparse parser, and create a spec from it."""
    return ParserSpec(
        program=parser.prog,
        description=parser.description,
        epilog=parser.epilog,
        **kwargs
    )
