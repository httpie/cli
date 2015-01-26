from __future__ import absolute_import
import json
import sys
if sys.version_info >= (2, 7):
    from collections import OrderedDict

from httpie.plugins import FormatterPlugin


DEFAULT_INDENT = 4


class JSONFormatter(FormatterPlugin):

    def format_body(self, body, mime):
        if 'json' in mime:
            try:
                if sys.version_info >= (2, 7):
                    obj = json.loads(body, object_pairs_hook=OrderedDict)
                else:
                    obj = json.loads(body)
            except ValueError:
                # Invalid JSON, ignore.
                pass
            else:
                # Indent, sort keys by name  depending on version
                # and avoid unicode escapes to improve readability.
                if sys.version_info >= (2, 7):
                    sort_keys=False
                else:
                    sort_keys=True
                body = json.dumps(obj,
                                  sort_keys=sort_keys,
                                  ensure_ascii=False,
                                  indent=DEFAULT_INDENT)
        return body
