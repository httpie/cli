import sys
from typing import TYPE_CHECKING, Optional

from ...constants import UTF8
from ...plugins import FormatterPlugin

if TYPE_CHECKING:
    from xml.dom.minidom import Document


def parse_xml(data: str) -> 'Document':
    """Parse given XML `data` string into an appropriate :class:`~xml.dom.minidom.Document` object."""
    from defusedxml.minidom import parseString
    return parseString(data)


def pretty_xml(document: 'Document',
               encoding: Optional[str] = UTF8,
               indent: int = 2,
               standalone: Optional[bool] = None) -> str:
    """Render the given :class:`~xml.dom.minidom.Document` `document` into a prettified string."""
    kwargs = {
        'encoding': encoding or UTF8,
        'indent': ' ' * indent,
    }
    if standalone is not None and sys.version_info >= (3, 9):
        kwargs['standalone'] = standalone
    body = document.toprettyxml(**kwargs).decode()

    # Remove blank lines automatically added by `toprettyxml()`.
    return '\n'.join(line for line in body.splitlines() if line.strip())


class XMLFormatter(FormatterPlugin):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.enabled = self.format_options['xml']['format']

    def format_body(self, body: str, mime: str):
        if 'xml' not in mime:
            return body

        from xml.parsers.expat import ExpatError
        from defusedxml.common import DefusedXmlException

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
                              standalone=parsed_body.standalone)

        return body
