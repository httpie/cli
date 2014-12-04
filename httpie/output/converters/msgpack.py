from __future__ import absolute_import
from httpie.plugins import ConverterPlugin
import json

# This will fail automatically if msgpack is not enabled
try:
    import msgpack
except ImportError:
    msgpack = None

DEFAULT_INDENT = 4

MSGPACK_NOT_INSTALLED_NOTICE = (
    b'\n'
    b'+-------------------------------------------------------+\n'
    b'| NOTE: install msgpack Python package to show contents |\n'
    b'+-------------------------------------------------------+'
)


class MsgpackConverter(ConverterPlugin):

    @classmethod
    def supports(cls, mime):
      return 'x-msgpack' in mime

    def convert(self, body):
        if msgpack is None:
            return "text/plain", MSGPACK_NOT_INSTALLED_NOTICE
        return "application/json", json.dumps(msgpack.loads(body))
