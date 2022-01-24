import argparse
import sys

from typing import List, Union

from httpie.context import Environment
from httpie.status import ExitStatus
from httpie.manager.cli import parser
from httpie.manager.core import MSG_COMMAND_CONFUSION, program as main_program


def is_http_command(args: List[Union[str, bytes]], env: Environment) -> bool:
    """Check whether http/https parser can parse the arguments."""

    from httpie.cli.definition import parser as http_parser
    from httpie.manager.cli import COMMANDS

    # If the user already selected a top-level sub-command, never
    # show the http/https version. E.g httpie plugins pie.dev/post
    if len(args) >= 1 and args[0] in COMMANDS:
        return False

    with env.as_silent():
        try:
            http_parser.parse_args(env=env, args=args)
        except (Exception, SystemExit):
            return False
        else:
            return True


def main(args: List[Union[str, bytes]] = sys.argv, env: Environment = Environment()) -> ExitStatus:
    from httpie.core import raw_main

    try:
        return raw_main(
            parser=parser,
            main_program=main_program,
            args=args,
            env=env,
            use_default_options=False,
        )
    except argparse.ArgumentError:
        program_args = args[1:]
        if is_http_command(program_args, env):
            env.stderr.write(MSG_COMMAND_CONFUSION.format(args=' '.join(program_args)) + "\n")

        return ExitStatus.ERROR


def program():
    try:
        exit_status = main()
    except KeyboardInterrupt:
        from httpie.status import ExitStatus
        exit_status = ExitStatus.ERROR_CTRL_C

    return exit_status


if __name__ == '__main__':  # pragma: nocover
    sys.exit(program())
