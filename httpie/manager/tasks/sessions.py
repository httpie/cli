import argparse

from httpie.sessions import SESSIONS_DIR_NAME, get_httpie_session
from httpie.status import ExitStatus
from httpie.context import Environment
from httpie.legacy import v3_1_0_session_cookie_format, v3_2_0_session_header_format
from httpie.manager.cli import missing_subcommand, parser
from httpie.utils import is_version_greater


FIXERS_TO_VERSIONS = {
    '3.1.0': v3_1_0_session_cookie_format.fix_layout,
    '3.2.0': v3_2_0_session_header_format.fix_layout,
}


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


def upgrade_session(env: Environment, args: argparse.Namespace, hostname: str, session_name: str):
    session = get_httpie_session(
        env=env,
        config_dir=env.config.directory,
        session_name=session_name,
        host=hostname,
        url=hostname,
        suppress_legacy_warnings=True
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
