import pytest
import shutil
import json
from httpie.sessions import SESSIONS_DIR_NAME
from httpie.status import ExitStatus
from httpie.cli.options import PARSER_SPEC_VERSION
from tests.utils import DUMMY_HOST, httpie
from tests.fixtures import SESSION_FILES_PATH, SESSION_FILES_NEW, SESSION_FILES_OLD, read_session_file


OLD_SESSION_FILES_PATH = SESSION_FILES_PATH / 'old'


@pytest.mark.requires_installation
def test_plugins_cli_error_message_without_args():
    # No arguments
    result = httpie(no_debug=True)
    assert result.exit_status == ExitStatus.ERROR
    assert 'usage: ' in result.stderr
    assert 'specify one of these' in result.stderr
    assert 'please use the http/https commands:' in result.stderr


@pytest.mark.parametrize(
    'example',
    [
        'pie.dev/get',
        'DELETE localhost:8000/delete',
        'POST pie.dev/post header:value a=b header_2:value x:=1',
    ],
)
@pytest.mark.requires_installation
def test_plugins_cli_error_messages_with_example(example):
    result = httpie(*example.split(), no_debug=True)
    assert result.exit_status == ExitStatus.ERROR
    assert 'usage: ' in result.stderr
    assert f'http {example}' in result.stderr
    assert f'https {example}' in result.stderr


@pytest.mark.parametrize(
    'example',
    [
        'cli',
        'plugins',
        'cli foo',
        'plugins unknown',
        'plugins unknown.com A:B c=d',
        'unknown.com UNPARSABLE????SYNTAX',
    ],
)
@pytest.mark.requires_installation
def test_plugins_cli_error_messages_invalid_example(example):
    result = httpie(*example.split(), no_debug=True)
    assert result.exit_status == ExitStatus.ERROR
    assert 'usage: ' in result.stderr
    assert f'http {example}' not in result.stderr
    assert f'https {example}' not in result.stderr


HTTPIE_CLI_SESSIONS_UPGRADE_OPTIONS = [
    (
        # Default settings
        [],
        {'__host__': json.dumps(None)},
    ),
    (
        # When --bind-cookies is applied, the __host__ becomes DUMMY_URL.
        ['--bind-cookies'],
        {'__host__': json.dumps(DUMMY_HOST)},
    ),
]


@pytest.mark.parametrize(
    'old_session_file, new_session_file', zip(SESSION_FILES_OLD, SESSION_FILES_NEW)
)
@pytest.mark.parametrize(
    'extra_args, extra_variables',
    HTTPIE_CLI_SESSIONS_UPGRADE_OPTIONS,
)
def test_httpie_sessions_upgrade(tmp_path, old_session_file, new_session_file, extra_args, extra_variables):
    session_path = tmp_path / 'session.json'
    shutil.copyfile(old_session_file, session_path)

    result = httpie(
        'cli', 'sessions', 'upgrade', *extra_args, DUMMY_HOST, str(session_path)
    )
    assert result.exit_status == ExitStatus.SUCCESS
    assert read_session_file(session_path) == read_session_file(
        new_session_file, extra_variables=extra_variables
    )


def test_httpie_sessions_upgrade_on_non_existent_file(tmp_path):
    session_path = tmp_path / 'session.json'
    result = httpie('cli', 'sessions', 'upgrade', DUMMY_HOST, str(session_path))
    assert result.exit_status == ExitStatus.ERROR
    assert 'does not exist' in result.stderr


@pytest.mark.parametrize(
    'extra_args, extra_variables',
    HTTPIE_CLI_SESSIONS_UPGRADE_OPTIONS,
)
def test_httpie_sessions_upgrade_all(tmp_path, mock_env, extra_args, extra_variables):
    mock_env._create_temp_config_dir = False
    mock_env.config_dir = tmp_path / "config"

    session_dir = mock_env.config_dir / SESSIONS_DIR_NAME / DUMMY_HOST
    session_dir.mkdir(parents=True)
    for original_session_file in SESSION_FILES_OLD:
        shutil.copy(original_session_file, session_dir)

    result = httpie(
        'cli', 'sessions', 'upgrade-all', *extra_args, env=mock_env
    )
    assert result.exit_status == ExitStatus.SUCCESS

    for refactored_session_file, expected_session_file in zip(
        sorted(session_dir.glob("*.json")),
        SESSION_FILES_NEW
    ):
        assert read_session_file(refactored_session_file) == read_session_file(
            expected_session_file, extra_variables=extra_variables
        )


@pytest.mark.parametrize(
    'load_func, extra_options', [
        (json.loads, []),
        (json.loads, ['--format=json'])
    ]
)
def test_cli_export(load_func, extra_options):
    response = httpie('cli', 'export-args', *extra_options)
    assert response.exit_status == ExitStatus.SUCCESS
    assert load_func(response)['version'] == PARSER_SPEC_VERSION
