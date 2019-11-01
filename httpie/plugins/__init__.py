"""
WARNING: The plugin API is still work in progress and will
         probably be completely reworked in the future.

"""
from httpie.plugins.base import (
    AuthPlugin, FormatterPlugin,
    ConverterPlugin, TransportPlugin
)
from httpie.plugins.manager import PluginManager
from httpie.plugins.builtin import BasicAuthPlugin, DigestAuthPlugin
from httpie.output.formatters.headers import HeadersFormatter
from httpie.output.formatters.json import JSONFormatter
from httpie.output.formatters.colors import ColorFormatter


plugin_manager = PluginManager()
plugin_manager.register(
    BasicAuthPlugin,
    DigestAuthPlugin,
    HeadersFormatter,
    JSONFormatter,
    ColorFormatter,
)
