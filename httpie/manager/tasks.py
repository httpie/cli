import argparse
import json
from typing import TypeVar, Callable

from httpie.status import ExitStatus
from httpie.context import Environment


T = TypeVar("T")

CLI_TASKS = {}


def task(name: str) -> Callable[[T], T]:
    def wrapper(func: T) -> T:
        CLI_TASKS[name] = func
        return func
    return wrapper


@task("export")
def cli_export(env: Environment, args: argparse.Namespace) -> ExitStatus:
    from httpie.cli.definition import options
    from httpie.cli.options import to_json

    if args.format == 'json':
        env.stdout.write(json.dumps(to_json(options), indent=4))
        env.stdout.write("\n")
