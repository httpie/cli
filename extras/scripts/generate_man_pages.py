import re
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, Iterator, Iterable

import httpie
from httpie.cli.definition import options as core_options
from httpie.cli.options import ParserSpec
from httpie.manager.cli import options as manager_options
from httpie.output.ui.rich_help import OptionsHighlighter, to_usage
from httpie.output.ui.rich_utils import render_as_string
from httpie.utils import split


# Escape certain characters so they are rendered properly on
# all terminals.
ESCAPE_MAP = {
    "'": "\\'",
    '~': '\\~',
    '’': "\\'",
    '\\': '\\\\',
}
ESCAPE_MAP = {ord(key): value for key, value in ESCAPE_MAP.items()}

EXTRAS_DIR = Path(__file__).parent.parent
MAN_PAGE_PATH = EXTRAS_DIR / 'man'

OPTION_HIGHLIGHT_RE = re.compile(
    OptionsHighlighter.highlights[0]
)

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

    def add_options(self, options: Iterable[str], *, metavar: Optional[str] = None) -> None:
        text = ", ".join(map(self.boldify, options))
        if metavar:
            text += f' {self.underline(metavar)}'
        self.write(f'.IP "{text}"')

    def build(self) -> str:
        return '\n'.join(self.source)

    @contextmanager
    def section(self, section_name: str) -> Iterator[None]:
        self.write(f'.SH {section_name}')
        self.in_section = True
        yield
        self.in_section = False

    def underline(self, text: str) -> str:
        return r'\fI\,{}\/\fR'.format(text)

    def boldify(self, text: str) -> str:
        return r'\fB\,{}\/\fR'.format(text)


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
        last_edit_date=httpie.__date__,
    )
    builder.set_name(program_name)

    with builder.section('SYNOPSIS'):
        builder.write(render_as_string(to_usage(spec, program_name=program_name)))

    with builder.section('DESCRIPTION'):
        builder.write(spec.description)

    for index, group in enumerate(spec.groups, 1):
        with builder.section(group.name):
            if group.description:
                builder.write(group.description)

            for argument in group.arguments:
                if argument.is_hidden:
                    continue

                raw_arg = argument.serialize(isolation_mode=True)

                metavar = raw_arg.get('metavar')
                if raw_arg.get('is_positional'):
                    # In case of positional arguments, metavar is always equal
                    # to the list of options (e.g `METHOD`).
                   metavar = None
                builder.add_options(raw_arg['options'], metavar=metavar)

                description = _escape_and_dedent(raw_arg.get('description', ''))
                description = OPTION_HIGHLIGHT_RE.sub(
                    lambda match: builder.boldify(match['option']),
                    description
                )
                builder.write('\n' + description + '\n')

            builder.separate()


        
    return builder.build()


def main() -> None:
    for program_name, spec in [
        ('http', core_options),
        ('https', core_options),
        ('httpie', manager_options),
    ]:
        with open((MAN_PAGE_PATH / program_name).with_suffix('.1'), 'w') as stream:
            stream.write(to_man_page(program_name, spec))



if __name__ == '__main__':
    main()
