import pytest
import json
from httpie.status import ExitStatus
from httpie.cli.options import PARSER_SPEC_VERSION
from tests.utils import httpie


@pytest.mark.requires_installation
def test_plugins_cli_error_message_without_args():
    # No arguments
    result = httpie(no_debug=True)
    assert result.exit_status == ExitStatus.ERROR
    assert 'usage: ' in result.stderr
    assert 'specify one of these' in result.stderr
    assert 'please use the http/https commands:' in result.stderr


@pytest.mark.parametrize(
    'example', [
        'pie.dev/get',
        'DELETE localhost:8000/delete',
        'POST pie.dev/post header:value a=b header_2:value x:=1'
    ]
)
@pytest.mark.requires_installation
def test_plugins_cli_error_messages_with_example(example):
    result = httpie(*example.split(), no_debug=True)
    assert result.exit_status == ExitStatus.ERROR
    assert 'usage: ' in result.stderr
    assert f'http {example}' in result.stderr
    assert f'https {example}' in result.stderr


@pytest.mark.parametrize(
    'example', [
        'cli',
        'plugins',
        'cli foo',
        'cli export --format=foo',
        'plugins unknown',
        'plugins unknown.com A:B c=d',
        'unknown.com UNPARSABLE????SYNTAX',
    ]
)
@pytest.mark.requires_installation
def test_plugins_cli_error_messages_invalid_example(example):
    result = httpie(*example.split(), no_debug=True)
    assert result.exit_status == ExitStatus.ERROR
    assert 'usage: ' in result.stderr
    assert f'http {example}' not in result.stderr
    assert f'https {example}' not in result.stderr


@pytest.mark.parametrize(
    'load_func, extra_options', [
        (json.loads, []),
        (json.loads, ['--format=json'])
    ]
)
def test_cli_export(load_func, extra_options):
    response = httpie('cli', 'export', *extra_options)
    assert response.exit_status == ExitStatus.SUCCESS
    assert load_func(response)['version'] == PARSER_SPEC_VERSION
