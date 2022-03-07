import argparse
from typing import TypeVar, Callable, Tuple

from httpie.sessions import SESSIONS_DIR_NAME, get_httpie_session
from httpie.status import ExitStatus
from httpie.context import Environment
from httpie.legacy import cookie_format as legacy_cookies
from httpie.manager.cli import missing_subcommand, parser

T = TypeVar('T')

CLI_TASKS = {}


def task(name: str) -> Callable[[T], T]:
    def wrapper(func: T) -> T:
        CLI_TASKS[name] = func
        return func
    return wrapper


@task('sessions')
def cli_sessions(env: Environment, args: argparse.Namespace) -> ExitStatus:
    action = args.cli_sessions_action
    if action is None:
        parser.error(missing_subcommand('cli', 'sessions'))

    if action == 'upgrade':
        return cli_upgrade_session(env, args)
    elif action == 'upgrade-all':
        return cli_upgrade_all_sessions(env, args)
    else:
        raise ValueError(f'Unexpected action: {action}')


def is_version_greater(version_1: str, version_2: str) -> bool:
    # In an ideal scenerio, we would depend on `packaging` in order
    # to offer PEP 440 compatible parsing. But since it might not be
    # commonly available for outside packages, and since we are only
    # going to parse HTTPie's own version it should be fine to compare
    # this in a SemVer subset fashion.

    def split_version(version: str) -> Tuple[int, ...]:
        parts = []
        for part in version.split('.')[:3]:
            try:
                parts.append(int(part))
            except ValueError:
                break
        return tuple(parts)

    return split_version(version_1) > split_version(version_2)


FIXERS_TO_VERSIONS = {
    '3.1.0': legacy_cookies.fix_layout
}


def upgrade_session(env: Environment, args: argparse.Namespace, hostname: str, session_name: str):
    session = get_httpie_session(
        env=env,
        config_dir=env.config.directory,
        session_name=session_name,
        host=hostname,
        url=hostname,
        refactor_mode=True
    )

    session_name = session.path.stem
    if session.is_new():
        env.log_error(f'{session_name!r} @ {hostname!r} does not exist.')
        return ExitStatus.ERROR

    fixers = [
        fixer
        for version, fixer in FIXERS_TO_VERSIONS.items()
        if is_version_greater(version, session.version)
    ]

    if len(fixers) == 0:
        env.stdout.write(f'{session_name!r} @ {hostname!r} is already up to date.\n')
        return ExitStatus.SUCCESS

    for fixer in fixers:
        fixer(session, hostname, args)

    session.save(bump_version=True)
    env.stdout.write(f'Upgraded {session_name!r} @ {hostname!r} to v{session.version}\n')
    return ExitStatus.SUCCESS


def cli_upgrade_session(env: Environment, args: argparse.Namespace) -> ExitStatus:
    return upgrade_session(
        env,
        args=args,
        hostname=args.hostname,
        session_name=args.session
    )


def cli_upgrade_all_sessions(env: Environment, args: argparse.Namespace) -> ExitStatus:
    session_dir_path = env.config_dir / SESSIONS_DIR_NAME

    status = ExitStatus.SUCCESS
    for host_path in session_dir_path.iterdir():
        hostname = host_path.name
        for session_path in host_path.glob("*.json"):
            session_name = session_path.stem
            status |= upgrade_session(
                env,
                args=args,
                hostname=hostname,
                session_name=session_name
            )
    return status


FORMAT_TO_CONTENT_TYPE = {
    'json': 'application/json'
}


@task('export-args')
def cli_export(env: Environment, args: argparse.Namespace) -> ExitStatus:
    import json
    from httpie.cli.definition import options
    from httpie.cli.options import to_data
    from httpie.output.writer import write_raw_data

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
