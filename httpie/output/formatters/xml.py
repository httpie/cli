from typing import TYPE_CHECKING, Optional

from ...encoding import UTF8
from ...plugins import FormatterPlugin

if TYPE_CHECKING:
    from xml.dom.minidom import Document


XML_DECLARATION_OPEN = '<?xml'
XML_DECLARATION_CLOSE = '?>'


def parse_xml(data: str) -> 'Document':
    """Parse given XML `data` string into an appropriate :class:`~xml.dom.minidom.Document` object."""
    from defusedxml.minidom import parseString
    return parseString(data)


def parse_declaration(raw_body: str) -> Optional[str]:
    body = raw_body.strip()
    # XMLDecl ::= '<?xml' DECL_CONTENT '?>'
    if body.startswith(XML_DECLARATION_OPEN):
        end = body.find(XML_DECLARATION_CLOSE)
        if end != -1:
            return body[:end + len(XML_DECLARATION_CLOSE)]


def pretty_xml(document: 'Document',
               declaration: Optional[str] = None,
               encoding: Optional[str] = UTF8,
               indent: int = 2) -> str:
    """Render the given :class:`~xml.dom.minidom.Document` `document` into a prettified string."""
    kwargs = {
        'encoding': encoding or UTF8,
        'indent': ' ' * indent,
    }
    body = document.toprettyxml(**kwargs).decode(kwargs['encoding'])

    # Remove blank lines automatically added by `toprettyxml()`.
    lines = [line for line in body.splitlines() if line.strip()]

    # xml.dom automatically adds the declaration, even if
    # it is not present in the actual body. Remove it.
    if len(lines) >= 1 and parse_declaration(lines[0]):
        lines.pop(0)
        if declaration:
            lines.insert(0, declaration)

    return '\n'.join(lines)


class XMLFormatter(FormatterPlugin):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.enabled = self.format_options['xml']['format']

    def format_body(self, body: str, mime: str):
        if 'xml' not in mime:
            return body

        from xml.parsers.expat import ExpatError
        from defusedxml.common import DefusedXmlException

        declaration = parse_declaration(body)
        try:
            parsed_body = parse_xml(body)
        except ExpatError:
            pass  # Invalid XML, ignore.
        except DefusedXmlException:
            pass  # Unsafe XML, ignore.
        else:
            body = pretty_xml(parsed_body,
                              encoding=parsed_body.encoding,
                              indent=self.format_options['xml']['indent'],
                              declaration=declaration)

        return body
