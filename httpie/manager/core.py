import argparse
from typing import Optional

from httpie.context import Environment
from httpie.status import ExitStatus
from httpie.manager.cli import missing_subcommand, parser
from httpie.manager.tasks import CLI_TASKS

MSG_COMMAND_CONFUSION = '''\
This command is only for managing HTTPie plugins.
To send a request, please use the http/https commands:

  $ http {args}

  $ https {args}
'''

# noinspection PyStringFormat
MSG_NAKED_INVOCATION = f'''\
{missing_subcommand()}

{MSG_COMMAND_CONFUSION}
'''.rstrip("\n").format(args='POST pie.dev/post hello=world')


def dispatch_cli_task(env: Environment, action: Optional[str], args: argparse.Namespace) -> ExitStatus:
    if action is None:
        parser.error(missing_subcommand('cli'))

    return CLI_TASKS[action](env, args)


def program(args: argparse.Namespace, env: Environment) -> ExitStatus:
    if args.action is None:
        parser.error(MSG_NAKED_INVOCATION)

    if args.action == 'plugins':
        return dispatch_cli_task(env, args.action, args)
    elif args.action == 'cli':
        return dispatch_cli_task(env, args.cli_action, args)

    return ExitStatus.SUCCESS
