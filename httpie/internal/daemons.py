"""
This module provides an interface to spawn a detached task to be
run with httpie.internal.daemon_runner on a separate process. It is
based on DVC's daemon system.
https://github.com/iterative/dvc/blob/main/dvc/daemon.py
"""

import inspect
import os
import platform
import sys
import httpie.__main__
from contextlib import suppress
from subprocess import Popen, DEVNULL
from typing import Dict, List
from httpie.compat import is_frozen, is_windows


ProcessContext = Dict[str, str]


def _start_process(cmd: List[str], **kwargs) -> Popen:
    prefix = [sys.executable]
    # If it is frozen, sys.executable points to the binary (http).
    # Otherwise it points to the python interpreter.
    if not is_frozen:
        main_entrypoint = httpie.__main__.__file__
        prefix += [main_entrypoint]
    return Popen(prefix + cmd, close_fds=True, shell=False, stdout=DEVNULL, stderr=DEVNULL, **kwargs)


def _spawn_windows(cmd: List[str], process_context: ProcessContext) -> None:
    from subprocess import (
        CREATE_NEW_PROCESS_GROUP,
        CREATE_NO_WINDOW,
        STARTF_USESHOWWINDOW,
        STARTUPINFO,
    )

    # https://stackoverflow.com/a/7006424
    # https://bugs.python.org/issue41619
    creationflags = CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW

    startupinfo = STARTUPINFO()
    startupinfo.dwFlags |= STARTF_USESHOWWINDOW

    _start_process(
        cmd,
        env=process_context,
        creationflags=creationflags,
        startupinfo=startupinfo,
    )


def _spawn_posix(args: List[str], process_context: ProcessContext) -> None:
    """
    Perform a double fork procedure* to detach from the parent
    process so that we don't block the user even if their original
    command's execution is done but the release fetcher is not.

    [1]: https://pubs.opengroup.org/onlinepubs/9699919799/basedefs/V1_chap11.html#tag_11_01_03
    """

    from httpie.core import main

    try:
        pid = os.fork()
        if pid > 0:
            return
    except OSError:
        os._exit(1)

    os.setsid()

    try:
        pid = os.fork()
        if pid > 0:
            os._exit(0)
    except OSError:
        os._exit(1)

    # Close all standard inputs/outputs
    sys.stdin.close()
    sys.stdout.close()
    sys.stderr.close()

    if platform.system() == 'Darwin':
        # Double-fork is not reliable on MacOS, so we'll use a subprocess
        # to ensure the task is isolated properly.
        process = _start_process(args, env=process_context)
        # Unlike windows, since we already completed the fork procedure
        # we can simply join the process and wait for it.
        process.communicate()
    else:
        os.environ.update(process_context)
        with suppress(BaseException):
            main(['http'] + args)

    os._exit(0)


def _spawn(args: List[str], process_context: ProcessContext) -> None:
    """
    Spawn a new process to run the given command.
    """
    if is_windows:
        _spawn_windows(args, process_context)
    else:
        _spawn_posix(args, process_context)


def spawn_daemon(task: str) -> None:
    args = [task, '--daemon']
    process_context = os.environ.copy()
    if not is_frozen:
        file_path = os.path.abspath(inspect.stack()[0][1])
        process_context['PYTHONPATH'] = os.path.dirname(
            os.path.dirname(os.path.dirname(file_path))
        )

    _spawn(args, process_context)
