from itertools import groupby
from pkg_resources import iter_entry_points
from httpie.plugins import AuthPlugin, FormatterPlugin, ConverterPlugin
from httpie.plugins.base import TransportPlugin


ENTRY_POINT_NAMES = [
    'httpie.plugins.auth.v1',
    'httpie.plugins.formatter.v1',
    'httpie.plugins.converter.v1',
    'httpie.plugins.transport.v1',
]


class PluginManager(object):

    def __init__(self):
        self._plugins = []

    def __iter__(self):
        return iter(self._plugins)

    def register(self, *plugins):
        for plugin in plugins:
            self._plugins.append(plugin)

    def unregister(self, plugin):
        self._plugins.remove(plugin)

    def load_installed_plugins(self):
        for entry_point_name in ENTRY_POINT_NAMES:
            for entry_point in iter_entry_points(entry_point_name):
                plugin = entry_point.load()
                plugin.package_name = entry_point.dist.key
                self.register(entry_point.load())

    # Auth
    def get_auth_plugins(self):
        return [plugin for plugin in self if issubclass(plugin, AuthPlugin)]

    def get_auth_plugin_mapping(self):
        return dict((plugin.auth_type, plugin)
                    for plugin in self.get_auth_plugins())

    def get_auth_plugin(self, auth_type):
        return self.get_auth_plugin_mapping()[auth_type]

    # Output processing
    def get_formatters(self):
        return [plugin for plugin in self
                if issubclass(plugin, FormatterPlugin)]

    def get_formatters_grouped(self):
        groups = {}
        for group_name, group in groupby(
                self.get_formatters(),
                key=lambda p: getattr(p, 'group_name', 'format')):
            groups[group_name] = list(group)
        return groups

    def get_converters(self):
        return [plugin for plugin in self
                if issubclass(plugin, ConverterPlugin)]

    # Adapters
    def get_transport_plugins(self):
        return [plugin for plugin in self
                if issubclass(plugin, TransportPlugin)]
