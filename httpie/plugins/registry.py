from ..output.formatters.colors import ColorFormatter
from ..output.formatters.headers import HeadersFormatter
from ..output.formatters.json import JSONFormatter
from ..output.formatters.xml import XMLFormatter
from .builtin import BasicAuthPlugin, BearerAuthPlugin, DigestAuthPlugin
from .manager import PluginManager

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
