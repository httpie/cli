import re
from typing import AbstractSet, Iterable, Optional, Tuple

from rich.console import RenderableType
from rich.highlighter import RegexHighlighter
from rich.padding import Padding
from rich.table import Table
from rich.text import Text

from httpie.cli.constants import SEPARATOR_GROUP_ALL_ITEMS
from httpie.cli.options import Argument, ParserSpec, Qualifiers

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
LEFT_PADDING_5 = (0, 0, 0, 4)

LEFT_INDENT_2 = (1, 0, 0, 2)
LEFT_INDENT_3 = (1, 0, 0, 3)
LEFT_INDENT_BOTTOM_3 = (0, 0, 1, 3)

SINGLE_NEWLINE_RE = re.compile(r"(?<!\n)\n(?!\n)")

class OptionsHighlighter(RegexHighlighter):
    highlights = [
        r'(^|\W)(?P<option>\-{1,2}[\w|-]+)(?![a-zA-Z0-9])',
        r'(?P<bold>HTTPie)',
    ]


options_highlighter = OptionsHighlighter()


def render_description(raw: str) -> str:
    final = []
    line_break = '\n'
    space = ' '
    para = line_break + line_break
    empty_line = False
    for line in raw.splitlines():
        if not line:
            empty_line = True
            continue

        is_indented = line.startswith(space)
        is_prev_indented = final and final[-1].startswith(space)

        if not empty_line and not is_indented and final:
            final.append(space)
        elif empty_line:
            final.append(para)
        if is_prev_indented and is_indented:
            final.append(line_break)
        final.append(line)
        empty_line = False

    return ''.join(final)


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

    text = Text(program_name or spec.program, style='bold')
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

            raw_form = argument.serialize()
            opt1, opt2 = unpack_argument(argument)
            if opt2:
                opt1.append('/')
                opt1.append(opt2)

            description = Text('')

            metavar_text = argument.configuration.get('metavar', '')
            if metavar_text and metavar_text != str(opt1):
                description.append(
                    Text(metavar_text, style=STYLE_METAVAR)
                )
                description.append('\n')
            elif raw_form.get('choices'):
                description.append(Text(f'{{{", ".join(raw_form["choices"])}}}', style=STYLE_METAVAR))
                description.append('\n')

            description_text = raw_form.get('description', '').strip()
            description_text = render_description(description_text)
            # description_text = SINGLE_NEWLINE_RE.sub(' ', description_text)
            description.append(description_text)
            description.append('\n')

            rows = [
                Padding(
                    options_highlighter(opt1),
                    LEFT_PADDING_2,
                ),
                options_highlighter(description),
            ]

            options_rows.append(rows)

        group_rows[group.name] = options_rows

    # We use a table of two rows
    # Row 1 is the option name (`-o/--option`)
    # Row 2 is the metavar/ description
    options_table = Table.grid(expand=True)
    for group_name, options_rows in group_rows.items():
        options_table.add_row(Text(), Text())
        options_table.add_row(
            Text(group_name, style=STYLE_SWITCH),
            Text(),
        )
        options_table.add_row(Text(), Text())
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
        spec.epilog.rstrip('\n'),
        LEFT_INDENT_BOTTOM_3,
    )
