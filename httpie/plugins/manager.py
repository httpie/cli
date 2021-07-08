import os.path
import site
import sys
from itertools import groupby
from operator import attrgetter
from typing import Dict, List, Type

from pkg_resources import iter_entry_points, working_set

from . import AuthPlugin, ConverterPlugin, FormatterPlugin
from .base import BasePlugin, TransportPlugin


ENTRY_POINT_NAMES = [
    'httpie.plugins.auth.v1',
    'httpie.plugins.formatter.v1',
    'httpie.plugins.converter.v1',
    'httpie.plugins.transport.v1',
]

# TODO: Should be moved to a specific file when needed elsewhere.
PY_VER = f'{sys.version_info.major}.{sys.version_info.minor}'

EXTENDED_PLUGINS_SEARCH_AREA = [
    site.getuserbase(),
    site.getusersitepackages(),
    # macOS specific
    f'~/Library/Python/{PY_VER}/lib/python/site-packages',
    f'/usr/local/lib/python{PY_VER}/site-packages',
]


class PluginManager(list):

    def register(self, *plugins: Type[BasePlugin]):
        for plugin in plugins:
            self.append(plugin)

    def unregister(self, plugin: Type[BasePlugin]):
        self.remove(plugin)

    def filter(self, by_type=Type[BasePlugin]):
        return [plugin for plugin in self if issubclass(plugin, by_type)]

    def extend_plugins_search_area(self):
        """Extend locations where plugins will be looked for."""
        for path in EXTENDED_PLUGINS_SEARCH_AREA:
            path = os.path.expanduser(path)
            if not os.path.isdir(path):
                continue
            site.addsitedir(path)
            working_set.add_entry(path)

    def load_installed_plugins(self):
        self.extend_plugins_search_area()
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
