import textwrap
import datetime
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Iterable

import httpie
from httpie.cli.definition import options
from httpie.cli.options import Argument, ParserSpec, Qualifiers
from httpie.output.ui.rich_help import to_usage
from httpie.output.ui.rich_utils import render_as_string
from httpie.utils import split

LAST_EDIT_DATE = str(datetime.date.today())

ESCAPE_MAP = {
    "'": "\\'",
    '~': '\\~',
    '’': "\\'",
    '\\': '\\\\',
}

ESCAPE_MAP = {ord(key): value for key, value in ESCAPE_MAP.items()}

EXTRAS_DIR = Path(__file__).parent
MAN_PAGE_PATH = EXTRAS_DIR / 'man'

class ManPageBuilder:
    def __init__(self):
        self.source = []

    def title_line(
        self,
        full_name: str,
        program_name: str,
        program_version: str,
        last_edit_date: str,
    ) -> None:
        self.source.append(
            f'.TH {program_name} 1 "{last_edit_date}" '
            f'"{full_name} {program_version}" "{full_name} Manual"'
        )

    def set_name(self, program_name: str) -> None:
        with self.section('NAME'):
            self.write(program_name)

    def write(self, text: str, *, bold: bool = False) -> None:
        if bold:
            text = '.B ' + text
        self.source.append(text)

    def separate(self) -> None:
        self.source.append('.PP')

    def add_options(self, options: Iterable[str]) -> None:
        self.write(f'.IP "{", ".join(options)}"')

    def build(self) -> str:
        return '\n'.join(self.source)

    @contextmanager
    def section(self, section_name: str) -> Iterator[None]:
        self.write(f'.SH {section_name}')
        self.in_section = True
        yield
        self.in_section = False


def _escape_and_dedent(text: str) -> str:
    lines = []
    for should_act, line in enumerate(text.splitlines()):
        # Only dedent after the first line.
        if should_act:
            if line.startswith('    '):
                line = line[4:]

        lines.append(line)
    return '\n'.join(lines).translate(ESCAPE_MAP)


def to_man_page(program_name: str, spec: ParserSpec) -> str:
    builder = ManPageBuilder()

    builder.title_line(
        full_name='HTTPie',
        program_name=program_name,
        program_version=httpie.__version__,
        last_edit_date=LAST_EDIT_DATE,
    )
    builder.set_name(program_name)

    with builder.section('SYNOPSIS'):
        builder.write(render_as_string(to_usage(spec, program_name=program_name)))

    with builder.section('DESCRIPTION'):
        builder.write(spec.description)

    with builder.section('OPTIONS'):
        builder.separate()
        builder.separate()

        for index, group in enumerate(spec.groups, 1):
            builder.write(f'({index}) {group.name}', bold=True)

            if group.description:
                builder.write(group.description)

            for argument in group.arguments:
                raw_arg = argument.serialize()
                builder.add_options(raw_arg['options'])
                builder.write('\n' + _escape_and_dedent(raw_arg.get('description', '')) + '\n')

            builder.separate()

    return builder.build()


def main() -> None:
    for program_name in ['http', 'https']:
        with open((MAN_PAGE_PATH / program_name).with_suffix('.1'), 'w') as stream:
            stream.write(to_man_page(program_name, options))


if __name__ == '__main__':
    main()
