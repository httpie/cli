import argparse
import json
from typing import TypeVar, Callable

from httpie.status import ExitStatus
from httpie.context import Environment
from httpie.output.writer import write_raw_data

T = TypeVar("T")

CLI_TASKS = {}


def task(name: str) -> Callable[[T], T]:
    def wrapper(func: T) -> T:
        CLI_TASKS[name] = func
        return func
    return wrapper


FORMAT_TO_CONTENT_TYPE = {
    'json': 'application/json'
}


@task("export")
def cli_export(env: Environment, args: argparse.Namespace) -> ExitStatus:
    from httpie.cli.definition import options
    from httpie.cli.options import to_data

    if args.format == 'json':
        data = json.dumps(to_data(options))
    else:
        raise NotImplementedError(f"Unexpected format value: {args.format}")

    write_raw_data(
        env,
        data,
        stream_kwargs={'mime_overwrite': FORMAT_TO_CONTENT_TYPE[args.format]},
    )
    return ExitStatus.SUCCESS
