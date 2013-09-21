from pkg_resources import iter_entry_points


ENTRY_POINT_NAMES = [
    'httpie.plugins.auth.v1'
]


class PluginManager(object):

    def __init__(self):
        self._plugins = []

    def __iter__(self):
        return iter(self._plugins)

    def register(self, plugin):
        self._plugins.append(plugin)

    def get_auth_plugins(self):
        return list(self._plugins)

    def get_auth_plugin_mapping(self):
        return dict((plugin.auth_type, plugin) for plugin in self)

    def get_auth_plugin(self, auth_type):
        return self.get_auth_plugin_mapping()[auth_type]

    def load_installed_plugins(self):

        for entry_point_name in ENTRY_POINT_NAMES:
            for entry_point in iter_entry_points(entry_point_name):
                plugin = entry_point.load()
                plugin.package_name = entry_point.dist.key
                self.register(entry_point.load())
