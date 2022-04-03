import argparse
import json

from httpie.cli.definition import options
from httpie.cli.options import to_data
from httpie.output.writer import write_raw_data
from httpie.status import ExitStatus
from httpie.context import Environment


FORMAT_TO_CONTENT_TYPE = {
    'json': 'application/json'
}


def cli_export_args(env: Environment, args: argparse.Namespace) -> ExitStatus:
    if args.format == 'json':
        data = json.dumps(to_data(options))
    else:
        raise NotImplementedError(f'Unexpected format value: {args.format}')

    write_raw_data(
        env,
        data,
        stream_kwargs={'mime_overwrite': FORMAT_TO_CONTENT_TYPE[args.format]},
    )
    return ExitStatus.SUCCESS
