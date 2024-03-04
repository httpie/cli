import json
import tempfile
import time
from contextlib import suppress
from datetime import datetime
from pathlib import Path

import pytest

from httpie.internal.daemon_runner import STATUS_FILE
from httpie.internal.daemons import spawn_daemon
from httpie.status import ExitStatus

from .utils import PersistentMockEnvironment, http, httpie

BUILD_CHANNEL = 'test'
BUILD_CHANNEL_2 = 'test2'
UNKNOWN_BUILD_CHANNEL = 'test3'

HIGHEST_VERSION = '999.999.999'
LOWEST_VERSION = '1.1.1'

FIXED_DATE = datetime(1970, 1, 1).isoformat()

MAX_ATTEMPT = 40
MAX_TIMEOUT = 2.0


def check_update_warnings(text):
    return 'A new HTTPie release' in text


@pytest.mark.requires_external_processes
def test_daemon_runner():
    # We have a pseudo daemon task called 'check_status'
    # which creates a temp file called STATUS_FILE under
    # user's temp directory. This test simply ensures that
    # we create a daemon that successfully performs the
    # external task.

    status_file = Path(tempfile.gettempdir()) / STATUS_FILE
    with suppress(FileNotFoundError):
        status_file.unlink()

    spawn_daemon('check_status')

    for attempt in range(MAX_ATTEMPT):
        time.sleep(MAX_TIMEOUT / MAX_ATTEMPT)
        if status_file.exists():
            break
    else:
        pytest.fail(
            'Maximum number of attempts failed for daemon status check.'
        )

    assert status_file.exists()


def test_fetch(static_fetch_data, without_warnings):
    http('fetch_updates', '--daemon', env=without_warnings)

    with open(without_warnings.config.version_info_file) as stream:
        version_data = json.load(stream)

    assert version_data['last_warned_date'] is None
    assert version_data['last_fetched_date'] is not None
    assert (
        version_data['last_released_versions'][BUILD_CHANNEL]
        == HIGHEST_VERSION
    )
    assert (
        version_data['last_released_versions'][BUILD_CHANNEL_2]
        == LOWEST_VERSION
    )


def test_fetch_dont_override_existing_layout(
    static_fetch_data, without_warnings
):
    with open(without_warnings.config.version_info_file, 'w') as stream:
        existing_layout = {
            'last_warned_date': FIXED_DATE,
            'last_fetched_date': FIXED_DATE,
            'last_released_versions': {BUILD_CHANNEL: LOWEST_VERSION},
        }
        json.dump(existing_layout, stream)

    http('fetch_updates', '--daemon', env=without_warnings)

    with open(without_warnings.config.version_info_file) as stream:
        version_data = json.load(stream)

    # The "last updated at" field should not be modified, but the
    # rest need to be updated.
    assert version_data['last_warned_date'] == FIXED_DATE
    assert version_data['last_fetched_date'] != FIXED_DATE
    assert (
        version_data['last_released_versions'][BUILD_CHANNEL]
        == HIGHEST_VERSION
    )


def test_fetch_broken_json(static_fetch_data, without_warnings):
    with open(without_warnings.config.version_info_file, 'w') as stream:
        stream.write('$$broken$$')

    http('fetch_updates', '--daemon', env=without_warnings)

    with open(without_warnings.config.version_info_file) as stream:
        version_data = json.load(stream)

    assert (
        version_data['last_released_versions'][BUILD_CHANNEL]
        == HIGHEST_VERSION
    )


def test_check_updates_disable_warnings(
    without_warnings, httpbin, fetch_update_mock
):
    r = http(httpbin + '/get', env=without_warnings)
    assert not fetch_update_mock.called
    assert not check_update_warnings(r.stderr)


def test_check_updates_first_invocation(
    with_warnings, httpbin, fetch_update_mock
):
    r = http(httpbin + '/get', env=with_warnings)
    assert fetch_update_mock.called
    assert not check_update_warnings(r.stderr)


@pytest.mark.parametrize(
    ['should_issue_warning', 'build_channel'],
    [
        (False, 'lower_build_channel'),
        (True, 'higher_build_channel'),
    ],
)
def test_check_updates_first_time_after_data_fetch(
    with_warnings,
    httpbin,
    fetch_update_mock,
    static_fetch_data,
    should_issue_warning,
    build_channel,
    request,
):
    request.getfixturevalue(build_channel)
    http('fetch_updates', '--daemon', env=with_warnings)
    r = http(httpbin + '/get', env=with_warnings)

    assert not fetch_update_mock.called
    assert (not should_issue_warning) or check_update_warnings(r.stderr)


def test_check_updates_first_time_after_data_fetch_unknown_build_channel(
    with_warnings,
    httpbin,
    fetch_update_mock,
    static_fetch_data,
    unknown_build_channel,
):
    http('fetch_updates', '--daemon', env=with_warnings)
    r = http(httpbin + '/get', env=with_warnings)

    assert not fetch_update_mock.called
    assert not check_update_warnings(r.stderr)


def test_cli_check_updates(
    static_fetch_data, higher_build_channel
):
    r = httpie('cli', 'check-updates')
    assert r.exit_status == ExitStatus.SUCCESS
    assert check_update_warnings(r)


@pytest.mark.parametrize(
    'build_channel', [
        'lower_build_channel',
        'unknown_build_channel',
    ]
)
def test_cli_check_updates_not_shown(
    static_fetch_data, build_channel, request
):
    request.getfixturevalue(build_channel)
    r = httpie('cli', 'check-updates')
    assert r.exit_status == ExitStatus.SUCCESS
    assert not check_update_warnings(r)


@pytest.fixture
def with_warnings(tmp_path):
    env = PersistentMockEnvironment()
    env.config['version_info_file'] = tmp_path / 'version.json'
    env.config['disable_update_warnings'] = False
    return env


@pytest.fixture
def without_warnings(tmp_path):
    env = PersistentMockEnvironment()
    env.config['version_info_file'] = tmp_path / 'version.json'
    env.config['disable_update_warnings'] = True
    return env


@pytest.fixture
def fetch_update_mock(mocker):
    mock_fetch = mocker.patch('httpie.internal.update_warnings.fetch_updates')
    return mock_fetch


@pytest.fixture
def static_fetch_data(mocker):
    mock_get = mocker.patch('requests.get')
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {
        BUILD_CHANNEL: HIGHEST_VERSION,
        BUILD_CHANNEL_2: LOWEST_VERSION,
    }
    return mock_get


@pytest.fixture
def unknown_build_channel(mocker):
    mocker.patch('httpie.internal.update_warnings.BUILD_CHANNEL', UNKNOWN_BUILD_CHANNEL)


@pytest.fixture
def higher_build_channel(mocker):
    mocker.patch('httpie.internal.update_warnings.BUILD_CHANNEL', BUILD_CHANNEL)


@pytest.fixture
def lower_build_channel(mocker):
    mocker.patch('httpie.internal.update_warnings.BUILD_CHANNEL', BUILD_CHANNEL_2)
