from httpie.plugins.manager import PluginManager
from httpie.plugins.builtin import BasicAuthPlugin, DigestAuthPlugin
from httpie.output.formatters.headers import HeadersFormatter
from httpie.output.formatters.json import JSONFormatter
from httpie.output.formatters.colors import ColorFormatter


plugin_manager = PluginManager()


# Register all built-in plugins.
plugin_manager.register(
    BasicAuthPlugin,
    DigestAuthPlugin,
    HeadersFormatter,
    JSONFormatter,
    ColorFormatter,
)
