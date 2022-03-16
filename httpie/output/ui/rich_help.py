import re
import textwrap
from typing import Optional, Tuple, Iterable, AbstractSet

from rich.align import Align
from rich.console import RenderableType
from rich.highlighter import RegexHighlighter
from rich.layout import Layout
from rich.padding import Padding
from rich.table import Table
from rich.text import Text

from httpie.cli.options import Argument, ParserSpec, Qualifiers
from httpie.cli.constants import SEPARATOR_GROUP_ALL_ITEMS

SEPARATORS = '|'.join(map(re.escape, SEPARATOR_GROUP_ALL_ITEMS))

STYLE_METAVAR = 'yellow'
STYLE_SWITCH = 'green'
STYLE_PROGRAM_NAME = 'bold green'
STYLE_USAGE_OPTIONAL = 'grey46'
STYLE_USAGE_REGULAR = 'white'
STYLE_USAGE_ERROR = 'red'
STYLE_USAGE_MISSING = 'yellow'

MAX_CHOICE_CHARS = 80

LEFT_PADDING_2 = (0, 0, 0, 2)
LEFT_PADDING_4 = (0, 0, 0, 4)


class RequestItemHighlighter(RegexHighlighter):
    highlights = [
        rf'(?P<key>\w+)(?P<sep>({SEPARATORS}))(?P<value>.+)',
    ]


request_item_highlighter = RequestItemHighlighter()


def unpack_argument(argument: Argument) -> Tuple[Text, Text]:
    opt1 = opt2 = ''
    if argument.aliases:
        if len(argument.aliases) >= 2:
            opt2, opt1 = argument.aliases
        else:
            (opt1,) = argument.aliases
    else:
        opt1 = argument.metavar

    return Text(opt1), Text(opt2)


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
        if (
            not argument.aliases
            or whitelist.intersection(argument.aliases)
        )
    ]

    # Sort the shown_arguments so that --dash options are
    # shown first
    shown_arguments.sort(key=lambda argument: argument.aliases, reverse=True)

    text = Text(program_name or spec.program)
    for argument in shown_arguments:
        text.append(' ')

        is_whitelisted = whitelist.intersection(argument.aliases)
        if argument.aliases:
            name = '/'.join(sorted(argument.aliases, key=len))
        else:
            name = argument.metavar

        nargs = argument.configuration.get('nargs')
        if nargs is Qualifiers.OPTIONAL:
            text.append(
                '[' + name + ']', style=STYLE_USAGE_OPTIONAL
            )
        elif nargs is Qualifiers.ZERO_OR_MORE:
            text.append(
                '[' + name + ' ...]', style=STYLE_USAGE_OPTIONAL
            )
        else:
            text.append(name, style=STYLE_USAGE_ERROR if is_whitelisted else STYLE_USAGE_REGULAR)

        raw_form = argument.serialize()
        if raw_form.get('choices'):
            text.append(' ')
            text.append('{' + ', '.join(raw_form['choices']) + '}', style=STYLE_USAGE_MISSING)

    return text


# This part is loosely based on the rich-click's help message
# generation.
def to_help_message(spec: ParserSpec) -> Iterable[RenderableType]:
    usage_text = Text('usage:\n    ', style='bold')
    usage_text.append(to_usage(spec))
    yield Padding(usage_text, 1)

    yield Padding(
        Align(spec.description, pad=False),
        (0, 1, 1, 1),
    )

    Layout()
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
                desc += textwrap.shorten(', '.join(raw_form.get('choices')), MAX_CHOICE_CHARS)
                desc += ')'

            rows = [
                Padding(opt1, LEFT_PADDING_2),
                metavar,
                desc,
            ]

            options_rows.append(rows)
            if argument.configuration.get('nested_options'):
                options_rows.extend(
                    [
                        (Padding(key, LEFT_PADDING_4), value, dec)
                        for key, value, dec in argument.nested_options
                    ]
                )

        group_rows[group.name] = options_rows

    options_table = Table(highlight=False, box=None, show_header=False)
    for group_name, options_rows in group_rows.items():
        options_table.add_row(Text(), Text(), Text())
        options_table.add_row(
            Text(group_name, style=STYLE_SWITCH), Text(), Text()
        )
        options_table.add_row(Text(), Text(), Text())
        for row in options_rows:
            options_table.add_row(*row)

    yield Padding(options_table, LEFT_PADDING_2)
    yield Padding(Align(spec.epilog.rstrip('\n'), pad=False), 1)
