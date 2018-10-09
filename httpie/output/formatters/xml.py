from __future__ import absolute_import

import xml.dom.minidom

from httpie.plugins import FormatterPlugin

DEFAULT_INDENT = 4


class XMLFormatter(FormatterPlugin):

    def format_body(self, body, mime):
        if 'xml' in mime:
            try:
                parsed_body = xml.dom.minidom.parseString(body)
            except ExpatError:
                pass  # Invalid XML, ignore
            else:
                return parsed_body.toprettyxml(indent=' ' * DEFAULT_INDENT,
                                               encoding='UTF-8')
