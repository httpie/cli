import sys

import pytest
import responses

from httpie.encoding import UTF8
from httpie.output.formatters.xml import parse_xml, pretty_xml

from .fixtures import XML_FILES_PATH, XML_FILES_VALID, XML_FILES_INVALID
from .utils import http, URL_EXAMPLE

XML_DATA_RAW = '<?xml version="1.0" encoding="utf-8"?><root><e>text</e></root>'
XML_DATA_FORMATTED = pretty_xml(parse_xml(XML_DATA_RAW))


@pytest.mark.parametrize(
    'options, expected_xml',
    [
        ('xml.format:false', XML_DATA_RAW),
        ('xml.indent:2', XML_DATA_FORMATTED),
        ('xml.indent:4', pretty_xml(parse_xml(XML_DATA_RAW), indent=4)),
    ]
)
@responses.activate
def test_xml_format_options(options, expected_xml):
    responses.add(
        responses.GET,
        URL_EXAMPLE,
        body=XML_DATA_RAW,
        content_type='application/xml',
    )

    r = http('--format-options', options, URL_EXAMPLE)
    assert expected_xml in r


@pytest.mark.parametrize('file', XML_FILES_VALID)
@responses.activate
def test_valid_xml(file):
    """Test XML formatter limits with data containing comments, doctypes
    and other XML-specific subtles.
    """
    if 'standalone' in file.stem and sys.version_info < (3, 9):
        pytest.skip('Standalone XML requires Python 3.9+')

    xml_data = file.read_text(encoding=UTF8)
    expected_xml_file = file.with_name(file.name.replace('_raw', '_formatted'))
    expected_xml_output = expected_xml_file.read_text(encoding=UTF8)
    responses.add(
        responses.GET,
        URL_EXAMPLE,
        body=xml_data,
        content_type='application/xml',
    )

    r = http(URL_EXAMPLE)
    assert expected_xml_output in r


@responses.activate
def test_xml_xhtml():
    """XHTML responses are handled by the XML formatter."""
    file = XML_FILES_PATH / 'xhtml' / 'xhtml_raw.xml'
    xml_data = file.read_text(encoding=UTF8)

    # Python < 3.8 was sorting attributes (https://bugs.python.org/issue34160)
    # so we have 2 different output expected given the Python version.
    expected_file_name = (
        'xhtml_formatted_python_less_than_3.8.xml'
        if sys.version_info < (3, 8)
        else 'xhtml_formatted.xml'
    )
    expected_xml_file = file.with_name(expected_file_name)
    expected_xml_output = expected_xml_file.read_text(encoding=UTF8)
    responses.add(
        responses.GET,
        URL_EXAMPLE,
        body=xml_data,
        content_type='application/xhtml+xml',
    )

    r = http(URL_EXAMPLE)
    assert expected_xml_output in r


@pytest.mark.parametrize('file', XML_FILES_INVALID)
@responses.activate
def test_invalid_xml(file):
    """Testing several problematic XML files, none should be formatted
    and none should make HTTPie to crash.
    """
    xml_data = file.read_text(encoding=UTF8)
    responses.add(
        responses.GET,
        URL_EXAMPLE,
        body=xml_data,
        content_type='application/xml',
    )

    # No formatting done, data is simply printed as-is.
    r = http(URL_EXAMPLE)
    assert xml_data in r


@responses.activate
def test_response_mime_type_from_option():
    """Test XML response with a incorrect Content-Type header.
    Using the appropriate option to force the good one.
    """
    responses.add(
        responses.GET,
        URL_EXAMPLE,
        body=XML_DATA_RAW,
        content_type='text/plain',
    )
    args = ('--response-mime=application/xml', URL_EXAMPLE)

    # Ensure the option is taken into account only for responses.
    # Request
    r = http('--offline', '--raw', XML_DATA_RAW, *args)
    assert XML_DATA_RAW in r

    # Response
    r = http(*args)
    assert XML_DATA_FORMATTED in r


@responses.activate
def test_reponse_mime_type_from_option_incomplete():
    """Test XML response with a incorrect Content-Type header.
    Using the appropriate option to set an incorrect mime type.
    """
    responses.add(
        responses.GET,
        URL_EXAMPLE,
        body=XML_DATA_RAW,
        content_type='text/plain',
    )

    # The provided Content-Type is simply ignored, and so no formatting is done.
    r = http('--response-mime=incorrect/type', URL_EXAMPLE)
    assert XML_DATA_RAW in r
