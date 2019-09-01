from itertools import groupby
from operator import attrgetter
from typing import Dict, List, Type

from pkg_resources import iter_entry_points

from httpie.plugins import AuthPlugin, ConverterPlugin, FormatterPlugin
from httpie.plugins.base import BasePlugin, TransportPlugin


ENTRY_POINT_NAMES = [
    'httpie.plugins.auth.v1',
    'httpie.plugins.formatter.v1',
    'httpie.plugins.converter.v1',
    'httpie.plugins.transport.v1',
]


class PluginManager(list):

    def register(self, *plugins: Type[BasePlugin]):
        for plugin in plugins:
            self.append(plugin)

    def unregister(self, plugin: Type[BasePlugin]):
        self.remove(plugin)

    def filter(self, by_type=Type[BasePlugin]):
        return [plugin for plugin in self if issubclass(plugin, by_type)]

    def load_installed_plugins(self):
        for entry_point_name in ENTRY_POINT_NAMES:
            for entry_point in iter_entry_points(entry_point_name):
                plugin = entry_point.load()
                plugin.package_name = entry_point.dist.key
                self.register(entry_point.load())

    # Auth
    def get_auth_plugins(self) -> List[Type[AuthPlugin]]:
        return self.filter(AuthPlugin)

    def get_auth_plugin_mapping(self) -> Dict[str, Type[AuthPlugin]]:
        return {
            plugin.auth_type: plugin for plugin in self.get_auth_plugins()
        }

    def get_auth_plugin(self, auth_type: str) -> Type[AuthPlugin]:
        return self.get_auth_plugin_mapping()[auth_type]

    # Output processing
    def get_formatters(self) -> List[Type[FormatterPlugin]]:
        return self.filter(FormatterPlugin)

    def get_formatters_grouped(self) -> Dict[str, List[Type[FormatterPlugin]]]:
        return {
            group_name: list(group)
            for group_name, group
            in groupby(self.get_formatters(), key=attrgetter('group_name'))
        }

    def get_converters(self) -> List[Type[ConverterPlugin]]:
        return self.filter(ConverterPlugin)

    # Adapters
    def get_transport_plugins(self) -> List[Type[TransportPlugin]]:
        return self.filter(TransportPlugin)

    def __repr__(self):
        return f'<PluginManager: {list(self)}>'
