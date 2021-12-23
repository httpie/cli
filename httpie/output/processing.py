import re
from typing import Optional, List

from ..plugins import ConverterPlugin
from ..plugins.registry import plugin_manager
from ..context import Environment


MIME_RE = re.compile(r'^[^/]+/[^/]+$')


def is_valid_mime(mime):
    return mime and MIME_RE.match(mime)


class Conversion:

    @staticmethod
    def get_converter(mime: str) -> Optional[ConverterPlugin]:
        if is_valid_mime(mime):
            for converter_class in plugin_manager.get_converters():
                if converter_class.supports(mime):
                    return converter_class(mime)


class Formatting:
    """A delegate class that invokes the actual processors."""

    def __init__(self, groups: List[str], env=Environment(), **kwargs):
        """
        :param groups: names of processor groups to be applied
        :param env: Environment
        :param kwargs: additional keyword arguments for processors

        """
        available_plugins = plugin_manager.get_formatters_grouped()
        self.enabled_plugins = []
        for group in groups:
            for cls in available_plugins[group]:
                p = cls(env=env, **kwargs)
                if p.enabled:
                    self.enabled_plugins.append(p)

    def format_headers(self, headers: str) -> str:
        for p in self.enabled_plugins:
            headers = p.format_headers(headers)
        return headers

    def format_body(self, content: str, mime: str) -> str:
        if is_valid_mime(mime):
            for p in self.enabled_plugins:
                content = p.format_body(content, mime)
        return content

    def format_metadata(self, metadata: str) -> str:
        for p in self.enabled_plugins:
            metadata = p.format_metadata(metadata)
        return metadata
