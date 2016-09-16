from __future__ import absolute_import

from httpie.plugins import FormatterPlugin
from httpie.utils import load_json_preserve_order, pretty_print_json


DEFAULT_INDENT = 4


class JSONFormatter(FormatterPlugin):

    def format_body(self, body, mime):
        maybe_json = [
            'json',
            'javascript',
            'text',
        ]
        if (self.kwargs['explicit_json'] or
                any(token in mime for token in maybe_json)):
            try:
                obj = load_json_preserve_order(body)
            except ValueError:
                pass  # Invalid JSON, ignore.
            else:
                body = pretty_print_json(obj, DEFAULT_INDENT)
        return body
