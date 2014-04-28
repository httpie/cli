from __future__ import absolute_import
import re
from xml.etree import ElementTree

from httpie.plugins import FormatterPlugin


DECLARATION_RE = re.compile('<\?xml[^\n]+?\?>', flags=re.I)
DOCTYPE_RE = re.compile('<!DOCTYPE[^\n]+?>', flags=re.I)


DEFAULT_INDENT = 4


def indent(elem, indent_text=' ' * DEFAULT_INDENT):
    """
    In-place prettyprint formatter
    C.f. http://effbot.org/zone/element-lib.htm#prettyprint

    """
    def _indent(elem, level=0):
        i = "\n" + level * indent_text
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + indent_text
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for elem in elem:
                _indent(elem, level + 1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i

    return _indent(elem)


class XMLFormatter(FormatterPlugin):
    # TODO: tests

    def format_body(self, body, mime):
        if 'xml' in mime:
            # FIXME: orig NS names get forgotten during the conversion, etc.
            try:
                root = ElementTree.fromstring(body.encode('utf8'))
            except ElementTree.ParseError:
                # Ignore invalid XML errors (skips attempting to pretty print)
                pass
            else:
                indent(root)
                # Use the original declaration
                declaration = DECLARATION_RE.match(body)
                doctype = DOCTYPE_RE.match(body)
                body = ElementTree.tostring(root, encoding='utf-8')\
                                  .decode('utf8')
                if doctype:
                    body = '%s\n%s' % (doctype.group(0), body)
                if declaration:
                    body = '%s\n%s' % (declaration.group(0), body)
        return body
