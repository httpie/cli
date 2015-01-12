from __future__ import absolute_import
import json
import collections

from httpie.plugins import FormatterPlugin


DEFAULT_INDENT = 4


class JSONFormatter(FormatterPlugin):

    def format_body(self, body, mime):
        if 'json' in mime:
            try:
                obj = json.loads(body, object_pairs_hook=collections.OrderedDict)
            except ValueError:
                # Invalid JSON, ignore.
                pass
            else:
                # Indent, sort keys by name, and avoid
                # unicode escapes to improve readability.
                body = json.dumps(obj,
                                  sort_keys=False,
                                  ensure_ascii=False,
                                  indent=DEFAULT_INDENT)
        return body
