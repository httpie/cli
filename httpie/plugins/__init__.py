"""
WARNING: The plugin API is still work in progress and will
         probably be completely reworked by v1.0.0.

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
plugin_manager.register(BasicAuthPlugin,
                        DigestAuthPlugin)
plugin_manager.register(HeadersFormatter,
                        JSONFormatter,
                        ColorFormatter)
