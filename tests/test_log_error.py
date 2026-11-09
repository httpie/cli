import io
import pytest
from httpie.context import LogLevel
from tests.utils import MockEnvironment


@pytest.mark.parametrize('stdout_isatty', [True, False])
def test_log_error_warning_suppression_with_quiet(stdout_isatty):
    orig_stderr = io.StringIO()
    quiet_stderr = io.StringIO()
    env = MockEnvironment(
        stdout_isatty=stdout_isatty,
        stderr=quiet_stderr,
    )
    env._orig_stderr = orig_stderr
    env.quiet = 2

    env.log_error('test warning message', level=LogLevel.WARNING)

    # When quiet >= threshold (2 for WARNING), warning should go to env.stderr (devnull in real run),
    # not _orig_stderr, regardless of whether stdout is a tty or redirected (#1978).
    assert 'test warning message' not in orig_stderr.getvalue()
    assert 'test warning message' in quiet_stderr.getvalue()


@pytest.mark.parametrize('stdout_isatty', [True, False])
def test_log_error_warning_printed_without_quiet(stdout_isatty):
    orig_stderr = io.StringIO()
    quiet_stderr = io.StringIO()
    env = MockEnvironment(
        stdout_isatty=stdout_isatty,
        stderr=quiet_stderr,
    )
    env._orig_stderr = orig_stderr
    env.quiet = 0

    env.log_error('test warning message', level=LogLevel.WARNING)

    assert 'test warning message' in orig_stderr.getvalue()
    assert 'test warning message' not in quiet_stderr.getvalue()


@pytest.mark.parametrize('stdout_isatty', [True, False])
def test_log_error_error_never_suppressed(stdout_isatty):
    orig_stderr = io.StringIO()
    quiet_stderr = io.StringIO()
    env = MockEnvironment(
        stdout_isatty=stdout_isatty,
        stderr=quiet_stderr,
    )
    env._orig_stderr = orig_stderr
    env.quiet = 2

    env.log_error('critical failure', level=LogLevel.ERROR)

    # Errors should never be hidden regardless of quiet setting or redirection
    assert 'critical failure' in orig_stderr.getvalue()
    assert 'critical failure' not in quiet_stderr.getvalue()
