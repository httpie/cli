from httpie.plugins.base import AuthPlugin, FormatterPlugin, ConverterPlugin
from httpie.plugins.manager import PluginManager
from httpie.plugins.builtin import BasicAuthPlugin, DigestAuthPlugin
from httpie.output.formatters.headers import HeadersFormatter
from httpie.output.formatters.json import JSONFormatter
from httpie.output.formatters.xml import XMLFormatter
from httpie.output.formatters.colors import ColorFormatter


plugin_manager = PluginManager()
plugin_manager.register(BasicAuthPlugin,
                        DigestAuthPlugin)
plugin_manager.register(HeadersFormatter,
                        JSONFormatter,
                        XMLFormatter,
                        ColorFormatter)
