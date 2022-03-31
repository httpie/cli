"""Logic for checking and displaying man pages."""

import subprocess
import os
from httpie.context import Environment

MAN_COMMAND = 'man'


def is_available(program: str) -> bool:
    """Check whether HTTPie's man pages are available in this system."""

    if os.system == 'nt':
        return False

    process = subprocess.run(
        [MAN_COMMAND, program],
        shell=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    return process.returncode == 0


def display_for(env: Environment, program: str) -> None:
    """Display the man page for the given command (http/https)."""

    subprocess.run(
        [MAN_COMMAND, program],
        stdout=env.stdout,
        stderr=env.stderr
    )
