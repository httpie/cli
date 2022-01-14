import sys
import os
import warnings

from itertools import groupby
from operator import attrgetter
from typing import Dict, List, Type, Iterator, Optional, ContextManager
from pathlib import Path
from contextlib import contextmanager, nullcontext

from ..compat import importlib_metadata, find_entry_points, get_dist_name

from ..utils import repr_dict, as_site
from . import AuthPlugin, ConverterPlugin, FormatterPlugin, TransportPlugin
from .base import BasePlugin


ENTRY_POINT_CLASSES = {
    'httpie.plugins.auth.v1': AuthPlugin,
    'httpie.plugins.converter.v1': ConverterPlugin,
    'httpie.plugins.formatter.v1': FormatterPlugin,
    'httpie.plugins.transport.v1': TransportPlugin
}
ENTRY_POINT_NAMES = list(ENTRY_POINT_CLASSES.keys())


@contextmanager
def _load_directory(plugins_dir: Path) -> Iterator[None]:
    plugins_path = os.fspath(plugins_dir)
    sys.path.insert(0, plugins_path)
    try:
        yield
    finally:
        sys.path.remove(plugins_path)


def enable_plugins(plugins_dir: Optional[Path]) -> ContextManager[None]:
    if plugins_dir is None:
        return nullcontext()
    else:
        return _load_directory(as_site(plugins_dir))


class PluginManager(list):
    def register(self, *plugins: Type[BasePlugin]):
        for plugin in plugins:
            self.append(plugin)

    def unregister(self, plugin: Type[BasePlugin]):
        self.remove(plugin)

    def filter(self, by_type=Type[BasePlugin]):
        return [plugin for plugin in self if issubclass(plugin, by_type)]

    def iter_entry_points(self, directory: Optional[Path] = None):
        with enable_plugins(directory):
            eps = importlib_metadata.entry_points()

            for entry_point_name in ENTRY_POINT_NAMES:
                yield from find_entry_points(eps, group=entry_point_name)

    def load_installed_plugins(self, directory: Optional[Path] = None):
        for entry_point in self.iter_entry_points(directory):
            plugin_name = get_dist_name(entry_point)
            try:
                plugin = entry_point.load()
            except BaseException as exc:
                warnings.warn(
                    f'While loading "{plugin_name}", an error ocurred: {exc}\n'
                    f'For uninstallations, please use either "httpie plugins uninstall {plugin_name}" '
                    f'or "pip uninstall {plugin_name}" (depending on how you installed it in the first '
                    'place).'
                )
                continue
            plugin.package_name = plugin_name
            self.register(plugin)

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

    def __str__(self):
        return repr_dict({
            'adapters': self.get_transport_plugins(),
            'auth': self.get_auth_plugins(),
            'converters': self.get_converters(),
            'formatters': self.get_formatters(),
        })

    def __repr__(self):
        return f'<{type(self).__name__} {self}>'
