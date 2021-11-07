from tests.utils.plugins_cli import parse_listing


def test_plugins_installation(cli, interface, dummy_plugin):
    lines = cli("plugins", "install", dummy_plugin.path)
    assert lines[0].startswith(
        f"Installing {dummy_plugin.path}"
    )
    assert lines[-1].startswith(
        f"Successfully installed {dummy_plugin.name}-{dummy_plugin.version}"
    )
    assert interface.is_installed(dummy_plugin.name)


def test_plugins_listing(cli, interface, dummy_plugin):
    cli("plugins", "install", dummy_plugin.path)
    data = parse_listing(cli("plugins", "list"))

    assert data == {
        dummy_plugin.import_name: dummy_plugin.dump()
    }


def test_plugins_listing_multiple(interface, cli, dummy_plugins):
    paths = [plugin.path for plugin in dummy_plugins]
    cli("plugins", "install", *paths)
    data = parse_listing(cli("plugins", "list"))

    assert data == {
        plugin.import_name: plugin.dump()
        for plugin in dummy_plugins
    }


def test_plugins_uninstall(interface, cli, dummy_plugin):
    cli("plugins", "install", dummy_plugin.path)
    cli("plugins", "uninstall", dummy_plugin.name)
    assert not interface.is_installed(dummy_plugin.name)


def test_plugins_listing_after_uninstall(interface, cli, dummy_plugin):
    cli("plugins", "install", dummy_plugin.path)
    cli("plugins", "uninstall", dummy_plugin.name)

    data = parse_listing(cli("plugins", "list"))
    assert len(data) == 0


def test_plugins_uninstall_specific(interface, cli):
    new_plugin_1 = interface.make_dummy_plugin()
    new_plugin_2 = interface.make_dummy_plugin()
    target_plugin = interface.make_dummy_plugin()

    cli("plugins", "install", new_plugin_1.path, new_plugin_2.path, target_plugin.path)
    cli("plugins", "uninstall", target_plugin.name)

    assert interface.is_installed(new_plugin_1.name)
    assert interface.is_installed(new_plugin_2.name)
    assert not interface.is_installed(target_plugin.name)
