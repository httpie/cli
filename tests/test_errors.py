import pytest
import socket
from unittest import mock
from pytest import raises
from requests import Request
from requests.exceptions import ConnectionError

from httpie.status import ExitStatus
from .utils import HTTP_OK, http


@mock.patch('httpie.core.program')
def test_error(program):
    exc = ConnectionError('Connection aborted')
    exc.request = Request(method='GET', url='http://www.google.com')
    program.side_effect = exc
    r = http('www.google.com', tolerate_error_exit_status=True)
    assert r.exit_status == ExitStatus.ERROR
    error_msg = (
        'ConnectionError: '
        'Connection aborted while doing a GET request to URL: '
        'http://www.google.com'
    )
    assert error_msg in r.stderr


@mock.patch('httpie.core.program')
def test_error_traceback(program):
    exc = ConnectionError('Connection aborted')
    exc.request = Request(method='GET', url='http://www.google.com')
    program.side_effect = exc
    with raises(ConnectionError):
        http('--traceback', 'www.google.com')


@mock.patch('httpie.core.program')
@pytest.mark.parametrize("error_code, expected_message", [
    (socket.EAI_AGAIN, "check your connection"),
    (socket.EAI_NONAME, "check the URL"),
])
def test_error_custom_dns(program, error_code, expected_message):
    exc = ConnectionError('Connection aborted')
    exc.__context__ = socket.gaierror(error_code, "<test>")
    program.side_effect = exc

    r = http('www.google.com', tolerate_error_exit_status=True)
    assert r.exit_status == ExitStatus.ERROR
    assert expected_message in r.stderr


def test_max_headers_limit(httpbin_both):
    with raises(ConnectionError) as e:
        http('--max-headers=1', httpbin_both + '/get')
    assert 'got more than 1 headers' in str(e.value)


def test_max_headers_no_limit(httpbin_both):
    assert HTTP_OK in http('--max-headers=0', httpbin_both + '/get')


def test_response_charset_option_unknown_encoding(httpbin_both):
    r = http(
        '--response-charset=foobar',
        httpbin_both + '/get',
        tolerate_error_exit_status=True,
    )
    assert "'foobar' is not a supported encoding" in r.stderr


def test_response_mime_option_invalid_mime_type(httpbin_both):
    r = http(
        '--response-mime=foobar',
        httpbin_both + '/get',
        tolerate_error_exit_status=True,
    )
    assert "'foobar' doesn’t look like a mime type" in r.stderr
