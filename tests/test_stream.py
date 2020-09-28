import pytest

from httpie.compat import is_windows
from httpie.output.streams import BINARY_SUPPRESSED_NOTICE
from utils import StdinBytesIO, http, MockEnvironment
from fixtures import BIN_FILE_CONTENT, BIN_FILE_PATH


# GET because httpbin 500s with binary POST body.


@pytest.mark.skipif(is_windows,
                    reason='Pretty redirect not supported under Windows')
def test_pretty_redirected_stream(httpbin):
    """Test that --stream works with prettified redirected output."""
    env = MockEnvironment(
        colors=256,
        stdin=StdinBytesIO(BIN_FILE_PATH.read_bytes()),
        stdin_isatty=False,
        stdout_isatty=False,
    )
    r = http('--verbose', '--pretty=all', '--stream', 'GET',
             httpbin.url + '/get', env=env)
    assert BINARY_SUPPRESSED_NOTICE.decode() in r


def test_encoded_stream(httpbin):
    """Test that --stream works with non-prettified
    redirected terminal output."""
    env = MockEnvironment(
        stdin=StdinBytesIO(BIN_FILE_PATH.read_bytes()),
        stdin_isatty=False,
    )
    r = http('--pretty=none', '--stream', '--verbose', 'GET',
             httpbin.url + '/get', env=env)
    assert BINARY_SUPPRESSED_NOTICE.decode() in r


def test_redirected_stream(httpbin):
    """Test that --stream works with non-prettified
    redirected terminal output."""
    env = MockEnvironment(
        stdout_isatty=False,
        stdin_isatty=False,
        stdin=StdinBytesIO(BIN_FILE_PATH.read_bytes()),
    )
    r = http('--pretty=none', '--stream', '--verbose', 'GET',
             httpbin.url + '/get', env=env)
    assert BIN_FILE_CONTENT in r
