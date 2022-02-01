import argparse
from typing import Any, Dict, Type, TypeVar

from httpie.cli.argparser import HTTPieArgumentParser

from httpie.cli.opts import ParserSpec, Qualifiers
from httpie.cli.utils import LazyChoices

ParserType = TypeVar("ParserType", bound=Type[argparse.ArgumentParser])


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
    concrete_parser.register("action", "lazy_choices", LazyChoices)

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
