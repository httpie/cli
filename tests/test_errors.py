import mock
from pytest import raises
from requests import Request
from requests.exceptions import ConnectionError
from httpie.status import ExitStatus
from utils import HTTP_OK, http


@mock.patch('httpie.core.program')
def test_error(program):
    exc = ConnectionError('Connection aborted')
    exc.request = Request(method='GET', url='http://www.google.com')
    program.side_effect = exc
    r = http('www.google.com', tolerate_error_exit_status=True)
    assert r.exit_status == ExitStatus.ERROR
    error_msg = (
        'Connection from http://www.google.com aborted while doing a GET request'
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
def test_connection_error(program):
    exc = ConnectionError('Connection aborted')
    exc.request = Request(method='GET', url='http://test.invalid')
    program.side_effect = exc
    r = http('http://test.invalid', tolerate_error_exit_status=True)
    assert r.exit_status == ExitStatus.ERROR
    error_msg = (
        'Connection from http://test.invalid aborted while doing a GET request'
    )
    assert error_msg in r.stderr


def test_max_headers_limit(httpbin_both):
    with raises(ConnectionError) as e:
        http('--max-headers=1', httpbin_both + '/get')
    assert 'got more than 1 headers' in str(e.value)


def test_max_headers_no_limit(httpbin_both):
    assert HTTP_OK in http('--max-headers=0', httpbin_both + '/get')
