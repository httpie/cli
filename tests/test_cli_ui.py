import pytest
import shutil
import os
import sys
from tests.utils import http


if sys.version_info >= (3, 9):
    REQUEST_ITEM_MSG = "[REQUEST_ITEM ...]"
else:
    REQUEST_ITEM_MSG = "[REQUEST_ITEM [REQUEST_ITEM ...]]"


NAKED_HELP_MESSAGE = f"""\
usage:
    http [METHOD] URL {REQUEST_ITEM_MSG}

error:
    the following arguments are required: URL

for more information:
    run 'http --help' or visit https://httpie.io/docs/cli

"""

NAKED_HELP_MESSAGE_PRETTY_WITH_NO_ARG = f"""\
usage:
    http [--pretty {{all,colors,format,none}}] [METHOD] URL {REQUEST_ITEM_MSG}

error:
    argument --pretty: expected one argument

for more information:
    run 'http --help' or visit https://httpie.io/docs/cli

"""

NAKED_HELP_MESSAGE_PRETTY_WITH_INVALID_ARG = f"""\
usage:
    http [--pretty {{all,colors,format,none}}] [METHOD] URL {REQUEST_ITEM_MSG}

error:
    argument --pretty: invalid choice: '$invalid' (choose from 'all', 'colors', 'format', 'none')

for more information:
    run 'http --help' or visit https://httpie.io/docs/cli

"""


PREDEFINED_TERMINAL_SIZE = (160, 80)


@pytest.fixture(scope="function")
def ignore_terminal_size(monkeypatch):
    """Some tests wrap/crop the output depending on the
    size of the executed terminal, which might not be consistent
    through all runs.

    This fixture ensures every run uses the same exact configuration.
    """

    def fake_terminal_size(*args, **kwargs):
        return os.terminal_size(PREDEFINED_TERMINAL_SIZE)

    # Setting COLUMNS as an env var is required for 3.8<
    monkeypatch.setitem(os.environ, 'COLUMNS', str(PREDEFINED_TERMINAL_SIZE[0]))
    monkeypatch.setattr(shutil, 'get_terminal_size', fake_terminal_size)


@pytest.mark.parametrize(
    'args, expected_msg', [
        ([], NAKED_HELP_MESSAGE),
        (['--pretty'], NAKED_HELP_MESSAGE_PRETTY_WITH_NO_ARG),
        (['pie.dev', '--pretty'], NAKED_HELP_MESSAGE_PRETTY_WITH_NO_ARG),
        (['--pretty', '$invalid'], NAKED_HELP_MESSAGE_PRETTY_WITH_INVALID_ARG),
    ]
)
def test_naked_invocation(ignore_terminal_size, args, expected_msg):
    result = http(*args, tolerate_error_exit_status=True)
    assert result.stderr == expected_msg
