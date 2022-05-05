"""Logic for checking and displaying man pages."""

import subprocess
import os
from httpie.context import Environment

MAN_COMMAND = 'man'
NO_MAN_PAGES = os.getenv('HTTPIE_NO_MAN_PAGES', False)

# On some systems, HTTP(n) might exist but we are only
# interested in HTTP(1).
#
# For more information on man page sections: https://unix.stackexchange.com/a/138643

MAN_PAGE_SECTION = '1'


def is_available(program: str) -> bool:
    """Check whether HTTPie's man pages are available in this system."""

    if NO_MAN_PAGES or os.system == 'nt':
        return False

    try:
        process = subprocess.run(
            [MAN_COMMAND, MAN_PAGE_SECTION, program],
            shell=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except Exception:
        # There might be some errors outside of the process, e.g
        # a permission error to execute something that is not an
        # executable.
        return False
    else:
        return process.returncode == 0


def display_for(env: Environment, program: str) -> None:
    """Display the man page for the given command (http/https)."""

    subprocess.run(
        [MAN_COMMAND, MAN_PAGE_SECTION, program],
        stdout=env.stdout,
        stderr=env.stderr
    )
