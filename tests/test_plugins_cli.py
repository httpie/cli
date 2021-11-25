import pytest

from httpie.status import ExitStatus
from tests.utils import httpie
from tests.utils.plugins_cli import parse_listing


def test_plugins_installation(httpie_plugins_success, interface, dummy_plugin):
    lines = httpie_plugins_success('install', dummy_plugin.path)
    assert lines[0].startswith(
        f'Installing {dummy_plugin.path}'
    )
    assert f'Successfully installed {dummy_plugin.name}-{dummy_plugin.version}' in lines
    assert interface.is_installed(dummy_plugin.name)


def test_plugins_listing(httpie_plugins_success, interface, dummy_plugin):
    httpie_plugins_success('install', dummy_plugin.path)
    data = parse_listing(httpie_plugins_success('list'))

    assert data == {
        dummy_plugin.name: dummy_plugin.dump()
    }


def test_plugins_listing_multiple(interface, httpie_plugins_success, dummy_plugins):
    paths = [plugin.path for plugin in dummy_plugins]
    httpie_plugins_success('install', *paths)
    data = parse_listing(httpie_plugins_success('list'))

    assert data == {
        plugin.name: plugin.dump()
        for plugin in dummy_plugins
    }


def test_plugins_uninstall(interface, httpie_plugins_success, dummy_plugin):
    httpie_plugins_success('install', dummy_plugin.path)
    httpie_plugins_success('uninstall', dummy_plugin.name)
    assert not interface.is_installed(dummy_plugin.name)


def test_plugins_listing_after_uninstall(interface, httpie_plugins_success, dummy_plugin):
    httpie_plugins_success('install', dummy_plugin.path)
    httpie_plugins_success('uninstall', dummy_plugin.name)

    data = parse_listing(httpie_plugins_success('list'))
    assert len(data) == 0


def test_plugins_uninstall_specific(interface, httpie_plugins_success):
    new_plugin_1 = interface.make_dummy_plugin()
    new_plugin_2 = interface.make_dummy_plugin()
    target_plugin = interface.make_dummy_plugin()

    httpie_plugins_success('install', new_plugin_1.path, new_plugin_2.path, target_plugin.path)
    httpie_plugins_success('uninstall', target_plugin.name)

    assert interface.is_installed(new_plugin_1.name)
    assert interface.is_installed(new_plugin_2.name)
    assert not interface.is_installed(target_plugin.name)


def test_plugins_installation_failed(httpie_plugins, interface):
    plugin = interface.make_dummy_plugin(build=False)
    result = httpie_plugins('install', plugin.path)

    assert result.exit_status == ExitStatus.ERROR
    assert result.stderr.splitlines()[-1].strip().startswith("Can't install")


def test_plugins_uninstall_non_existent(httpie_plugins, interface):
    plugin = interface.make_dummy_plugin(build=False)
    result = httpie_plugins('uninstall', plugin.name)

    assert result.exit_status == ExitStatus.ERROR
    assert (
        result.stderr.splitlines()[-1].strip()
        == f"Can't uninstall '{plugin.name}': package is not installed"
    )


def test_plugins_double_uninstall(httpie_plugins, httpie_plugins_success, dummy_plugin):
    httpie_plugins_success("install", dummy_plugin.path)
    httpie_plugins_success("uninstall", dummy_plugin.name)

    result = httpie_plugins("uninstall", dummy_plugin.name)

    assert result.exit_status == ExitStatus.ERROR
    assert (
        result.stderr.splitlines()[-1].strip()
        == f"Can't uninstall '{dummy_plugin.name}': package is not installed"
    )


def test_plugins_cli_error_message_without_args():
    # No arguments
    result = httpie(no_debug=True)
    assert result.exit_status == ExitStatus.ERROR
    assert 'Perhaps you are looking for http/https commands' in result.stderr


@pytest.mark.parametrize(
    'example', [
        'pie.dev/get',
        'DELETE localhost:8000/delete',
        'POST pie.dev/post header:value a=b header_2:value x:=1'
    ]
)
def test_plugins_cli_error_messages_with_example(example):
    result = httpie(*example.split(), no_debug=True)
    assert result.exit_status == ExitStatus.ERROR
    assert 'You probably meant one of the following' in result.stderr
    assert f'http {example}' in result.stderr
    assert f'https {example}' in result.stderr


@pytest.mark.parametrize(
    'example', [
        'plugins unknown',
        'plugins unknown.com A:B c=d',
        'unknown.com UNPARSABLE????SYNTAX',
    ]
)
def test_plugins_cli_error_messages_invalid_example(example):
    result = httpie(*example.split(), no_debug=True)
    assert result.exit_status == ExitStatus.ERROR
    assert 'You probably meant one of the following' not in result.stderr
    assert example not in result.stderr
