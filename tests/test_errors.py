import pytest
import socket
import sys
from unittest import mock
from pytest import raises
from requests import Request
from requests.exceptions import ConnectionError

from httpie.status import ExitStatus
from httpie.utils import unwrap_context
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


@pytest.mark.parametrize('depth', [0, 1, sys.getrecursionlimit() + 1])
def test_unwrap_context(depth):
    original = ValueError('Original error')
    exc = original
    for _ in range(depth):
        wrapper = RuntimeError('Wrapper')
        wrapper.__context__ = exc
        exc = wrapper

    assert unwrap_context(exc) is original


def test_unwrap_context_stops_at_base_exception():
    exc = ValueError('Original error')
    exc.__context__ = KeyboardInterrupt()

    assert unwrap_context(exc) is exc


@pytest.mark.parametrize('length', [1, 2, 3])
def test_unwrap_context_cycle(length):
    errors = [ValueError('Error') for _ in range(length)]
    for index, error in enumerate(errors):
        error.__context__ = errors[(index + 1) % length]

    assert unwrap_context(errors[0]) is errors[-1]


@mock.patch('httpie.core.program')
def test_error_custom_dns_deep_context(program):
    exc = socket.gaierror(socket.EAI_NONAME, '<test>')
    for _ in range(sys.getrecursionlimit() + 1):
        wrapper = ConnectionError('Connection aborted')
        wrapper.__context__ = exc
        exc = wrapper
    program.side_effect = exc

    r = http('example.org', tolerate_error_exit_status=True)
    assert r.exit_status == ExitStatus.ERROR
    assert 'check the URL' in r.stderr


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
