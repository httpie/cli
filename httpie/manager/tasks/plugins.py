import argparse

from httpie.status import ExitStatus
from httpie.context import Environment
from httpie.manager.plugins import PluginInstaller


def cli_plugins(env: Environment, args: argparse.Namespace) -> ExitStatus:
    plugins = PluginInstaller(env, debug=args.debug)

    try:
        action = args.cli_plugins_action
    except AttributeError:
        action = args.plugins_action

    return plugins.run(action, args)
