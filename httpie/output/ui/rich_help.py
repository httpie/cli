import re
import textwrap
from typing import AbstractSet, Iterable, Optional, Tuple

from rich.console import RenderableType
from rich.highlighter import RegexHighlighter
from rich.padding import Padding
from rich.table import Table
from rich.text import Text

from httpie.cli.constants import SEPARATOR_GROUP_ALL_ITEMS
from httpie.cli.options import Argument, ParserSpec, Qualifiers
from httpie.output.ui.palette import GenericColor

SEPARATORS = '|'.join(map(re.escape, SEPARATOR_GROUP_ALL_ITEMS))

STYLE_METAVAR = GenericColor.YELLOW
STYLE_SWITCH = GenericColor.GREEN
STYLE_PROGRAM_NAME = GenericColor.GREEN  # .boldify()
STYLE_USAGE_OPTIONAL = GenericColor.GREY
STYLE_USAGE_REGULAR = GenericColor.WHITE
STYLE_USAGE_ERROR = GenericColor.RED
STYLE_USAGE_MISSING = GenericColor.YELLOW
STYLE_BOLD = 'bold'

MAX_CHOICE_CHARS = 80

LEFT_PADDING_2 = (0, 0, 0, 2)
LEFT_PADDING_3 = (0, 0, 0, 3)
LEFT_PADDING_4 = (0, 0, 0, 4)
LEFT_PADDING_5 = (0, 0, 0, 4)

LEFT_INDENT_2 = (1, 0, 0, 2)
LEFT_INDENT_3 = (1, 0, 0, 3)
LEFT_INDENT_BOTTOM_3 = (0, 0, 1, 3)

MORE_INFO_COMMANDS = """
To learn more, you can try:
    -> running 'http --manual'
    -> visiting our full documentation at https://httpie.io/docs/cli
"""


class OptionsHighlighter(RegexHighlighter):
    highlights = [
        r'(^|\W)(?P<option>\-{1,2}[\w|-]+)(?![a-zA-Z0-9])',
        r'(?P<bold>HTTPie)',
    ]


options_highlighter = OptionsHighlighter()


def unpack_argument(
    argument: Argument,
) -> Tuple[Text, Text]:
    opt1 = opt2 = ''

    style = None
    if argument.aliases:
        if len(argument.aliases) >= 2:
            opt2, opt1 = argument.aliases
        else:
            (opt1,) = argument.aliases
    else:
        opt1 = argument.metavar
        style = STYLE_USAGE_REGULAR

    return Text(opt1, style=style), Text(opt2)


def to_usage(
    spec: ParserSpec,
    *,
    program_name: Optional[str] = None,
    whitelist: AbstractSet[str] = frozenset()
) -> RenderableType:
    shown_arguments = [
        argument
        for group in spec.groups
        for argument in group.arguments
        if (not argument.aliases or whitelist.intersection(argument.aliases))
    ]

    # Sort the shown_arguments so that --dash options are
    # shown first
    shown_arguments.sort(key=lambda argument: argument.aliases, reverse=True)

    text = Text(program_name or spec.program, style=STYLE_BOLD)
    for argument in shown_arguments:
        text.append(' ')

        is_whitelisted = whitelist.intersection(argument.aliases)
        if argument.aliases:
            name = '/'.join(sorted(argument.aliases, key=len))
        else:
            name = argument.metavar

        nargs = argument.configuration.get('nargs')
        if nargs is Qualifiers.OPTIONAL:
            text.append('[' + name + ']', style=STYLE_USAGE_OPTIONAL)
        elif nargs is Qualifiers.ZERO_OR_MORE:
            text.append(
                '[' + name + ' ...]',
                style=STYLE_USAGE_OPTIONAL,
            )
        else:
            text.append(
                name,
                style=STYLE_USAGE_ERROR
                if is_whitelisted
                else STYLE_USAGE_REGULAR,
            )

        raw_form = argument.serialize()
        if raw_form.get('choices'):
            text.append(' ')
            text.append(
                '{' + ', '.join(raw_form['choices']) + '}',
                style=STYLE_USAGE_MISSING,
            )

    return text


# This part is loosely based on the rich-click's help message
# generation.
def to_help_message(
    spec: ParserSpec,
) -> Iterable[RenderableType]:
    yield Padding(
        options_highlighter(spec.description),
        LEFT_INDENT_2,
    )

    yield Padding(
        Text('Usage', style=STYLE_SWITCH),
        LEFT_INDENT_2,
    )
    yield Padding(to_usage(spec), LEFT_INDENT_3)

    group_rows = {}
    for group in spec.groups:
        options_rows = []

        for argument in group.arguments:
            if argument.is_hidden:
                continue

            opt1, opt2 = unpack_argument(argument)
            if opt2:
                opt1.append('/')
                opt1.append(opt2)

            # Column for a metavar, if we have one
            metavar = Text(style=STYLE_METAVAR)
            metavar.append(argument.configuration.get('metavar', ''))

            if opt1 == metavar:
                metavar = Text('')

            raw_form = argument.serialize()
            desc = raw_form.get('short_description', '')
            if raw_form.get('choices'):
                desc += ' (choices: '
                desc += textwrap.shorten(
                    ', '.join(raw_form.get('choices')),
                    MAX_CHOICE_CHARS,
                )
                desc += ')'

            rows = [
                Padding(
                    options_highlighter(opt1),
                    LEFT_PADDING_2,
                ),
                metavar,
                options_highlighter(desc),
            ]

            options_rows.append(rows)
            if argument.configuration.get('nested_options'):
                options_rows.extend(
                    [
                        (
                            Padding(
                                Text(
                                    key,
                                    style=STYLE_USAGE_OPTIONAL,
                                ),
                                LEFT_PADDING_4,
                            ),
                            value,
                            dec,
                        )
                        for key, value, dec in argument.nested_options
                    ]
                )

        group_rows[group.name] = options_rows

    options_table = Table(highlight=False, box=None, show_header=False)
    for group_name, options_rows in group_rows.items():
        options_table.add_row(Text(), Text(), Text())
        options_table.add_row(
            Text(group_name, style=STYLE_SWITCH),
            Text(),
            Text(),
        )
        options_table.add_row(Text(), Text(), Text())
        for row in options_rows:
            options_table.add_row(*row)

    yield Padding(
        Text('Options', style=STYLE_SWITCH),
        LEFT_INDENT_2,
    )
    yield Padding(options_table, LEFT_PADDING_2)
    yield Padding(
        Text('More Information', style=STYLE_SWITCH),
        LEFT_INDENT_2,
    )
    yield Padding(
        MORE_INFO_COMMANDS.rstrip('\n'),
        LEFT_PADDING_3
    )
    yield Padding(
        spec.epilog.rstrip('\n'),
        LEFT_INDENT_BOTTOM_3,
    )
