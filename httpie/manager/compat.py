import sys
import shutil
import subprocess

from contextlib import suppress
from typing import List, Optional
from httpie.compat import is_frozen


class PipError(Exception):
    """An exception that occurs when pip exits with an error status code."""

    def __init__(self, stdout, stderr):
        self.stdout = stdout
        self.stderr = stderr


def _discover_system_pip() -> List[str]:
    # When we are running inside of a frozen binary, we need the system
    # pip to install plugins since there is no way for us to execute any
    # code outside of the HTTPie.
    #
    # We explicitly depend on system pip, so the SystemError should not
    # be executed (except for broken installations).
    def _check_pip_version(pip_location: Optional[str]) -> bool:
        if not pip_location:
            return False

        with suppress(subprocess.CalledProcessError):
            stdout = subprocess.check_output([pip_location, "--version"], text=True)
            return "python 3" in stdout

    targets = [
        "pip",
        "pip3"
    ]
    for target in targets:
        pip_location = shutil.which(target)
        if _check_pip_version(pip_location):
            return pip_location

    raise SystemError("Couldn't find 'pip' executable. Please ensure that pip in your system is available.")


def _run_pip_subprocess(pip_executable: List[str], args: List[str]) -> bytes:
    import subprocess

    cmd = [*pip_executable, *args]
    try:
        process = subprocess.run(
            cmd,
            check=True,
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    except subprocess.CalledProcessError as error:
        raise PipError(error.stdout, error.stderr) from error
    else:
        return process.stdout


def run_pip(args: List[str]) -> bytes:
    if is_frozen:
        pip_executable = [_discover_system_pip()]
    else:
        pip_executable = [sys.executable, '-m', 'pip']

    return _run_pip_subprocess(pip_executable, args)
