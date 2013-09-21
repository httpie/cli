from .base import AuthPlugin
from .manager import PluginManager
from .builtin import BasicAuthPlugin, DigestAuthPlugin


plugin_manager = PluginManager()
plugin_manager.register(BasicAuthPlugin)
plugin_manager.register(DigestAuthPlugin)

