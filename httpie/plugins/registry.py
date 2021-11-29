from .manager import PluginManager
from .builtin import BasicAuthPlugin, DigestAuthPlugin, BearerAuthPlugin
from ..output.formatters.headers import HeadersFormatter
from ..output.formatters.json import JSONFormatter
from ..output.formatters.xml import XMLFormatter
from ..output.formatters.colors import ColorFormatter


plugin_manager = PluginManager()


# Register all built-in plugins.
plugin_manager.register(
    BasicAuthPlugin,
    DigestAuthPlugin,
    BearerAuthPlugin,
    HeadersFormatter,
    JSONFormatter,
    XMLFormatter,
    ColorFormatter,
)
