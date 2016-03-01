from __future__ import absolute_import
import json

from httpie.plugins import FormatterPlugin


DEFAULT_INDENT = 4


class JSONFormatter(FormatterPlugin):

    def format_body(self, body, mime):
        if 'json' in mime or self.kwargs['explicit_json']:
            try:
                obj = json.loads(body)
            except ValueError:
                pass  # Invalid JSON, ignore.
            else:
                # Indent, sort keys by name, and avoid
                # unicode escapes to improve readability.
                body = json.dumps(
                    obj=obj,
                    sort_keys=True,
                    ensure_ascii=False,
                    indent=DEFAULT_INDENT
                )
        return body
