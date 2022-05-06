import argparse
from contextlib import redirect_stderr, redirect_stdout
from typing import List

from httpie.context import Environment
from httpie.internal.update_warnings import _fetch_updates, _get_suppress_context
from httpie.status import ExitStatus

STATUS_FILE = '.httpie-test-daemon-status'


def _check_status(env):
    # This function is used only for the testing (test_update_warnings).
    # Since we don't want to trigger the fetch_updates (which would interact
    # with real world resources), we'll only trigger this pseudo task
    # and check whether the STATUS_FILE is created or not.
    import tempfile
    from pathlib import Path

    status_file = Path(tempfile.gettempdir()) / STATUS_FILE
    status_file.touch()


DAEMONIZED_TASKS = {
    'check_status': _check_status,
    'fetch_updates': _fetch_updates,
}


def _parse_options(args: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('task_id')
    parser.add_argument('--daemon', action='store_true')
    return parser.parse_known_args(args)[0]


def is_daemon_mode(args: List[str]) -> bool:
    return '--daemon' in args


def run_daemon_task(env: Environment, args: List[str]) -> ExitStatus:
    options = _parse_options(args)

    assert options.daemon
    assert options.task_id in DAEMONIZED_TASKS
    with redirect_stdout(env.devnull), redirect_stderr(env.devnull):
        with _get_suppress_context(env):
            DAEMONIZED_TASKS[options.task_id](env)

    return ExitStatus.SUCCESS
