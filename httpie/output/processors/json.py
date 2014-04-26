from __future__ import absolute_import
import json

from .base import BaseProcessor, DEFAULT_INDENT


class JSONProcessor(BaseProcessor):

    def process_body(self, body, mime):
        if 'json' in mime:
            try:
                obj = json.loads(body)
            except ValueError:
                # Invalid JSON, ignore.
                pass
            else:
                # Indent, sort keys by name, and avoid
                # unicode escapes to improve readability.
                body = json.dumps(obj,
                                  sort_keys=True,
                                  ensure_ascii=False,
                                  indent=DEFAULT_INDENT)
        return body
