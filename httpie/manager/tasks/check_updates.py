import argparse
from httpie.context import Environment
from httpie.status import ExitStatus
from httpie.internal.update_warnings import fetch_updates, get_update_status


def cli_check_updates(env: Environment, args: argparse.Namespace) -> ExitStatus:
    fetch_updates(env, lazy=False)
    env.stdout.write(get_update_status(env))
    return ExitStatus.SUCCESS
