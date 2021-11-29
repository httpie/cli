import argparse

from httpie.context import Environment
from httpie.manager.plugins import PluginInstaller
from httpie.status import ExitStatus
from httpie.manager.cli import missing_subcommand, parser

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


def program(args: argparse.Namespace, env: Environment) -> ExitStatus:
    if args.action is None:
        parser.error(MSG_NAKED_INVOCATION)

    if args.action == 'plugins':
        plugins = PluginInstaller(env, debug=args.debug)
        return plugins.run(args.plugins_action, args)

    return ExitStatus.SUCCESS
