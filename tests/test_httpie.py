"""High-level tests."""
import io
from unittest import mock

import pytest

import httpie.__main__
from httpie.context import Environment
from httpie.status import ExitStatus
from httpie.cli.exceptions import ParseError
from utils import MockEnvironment, http, HTTP_OK
from fixtures import FILE_PATH, FILE_CONTENT

import httpie


def test_main_entry_point():
    # Patch stdin to bypass pytest capture
    with mock.patch.object(Environment, 'stdin', io.StringIO()):
        with pytest.raises(SystemExit) as e:
            httpie.__main__.main()
        assert e.value.code == ExitStatus.ERROR


@mock.patch('httpie.core.main')
def test_main_entry_point_keyboard_interrupt(main):
    main.side_effect = KeyboardInterrupt()
    with mock.patch.object(Environment, 'stdin', io.StringIO()):
        with pytest.raises(SystemExit) as e:
            httpie.__main__.main()
        assert e.value.code == ExitStatus.ERROR_CTRL_C


def test_debug():
    r = http('--debug')
    assert r.exit_status == ExitStatus.SUCCESS
    assert 'HTTPie %s' % httpie.__version__ in r.stderr


def test_help():
    r = http('--help', tolerate_error_exit_status=True)
    assert r.exit_status == ExitStatus.SUCCESS
    assert 'https://github.com/jakubroztocil/httpie/issues' in r


def test_version():
    r = http('--version', tolerate_error_exit_status=True)
    assert r.exit_status == ExitStatus.SUCCESS
    # FIXME: py3 has version in stdout, py2 in stderr
    assert httpie.__version__ == r.strip()


def test_GET(httpbin_both):
    r = http('GET', httpbin_both + '/get')
    assert HTTP_OK in r


def test_DELETE(httpbin_both):
    r = http('DELETE', httpbin_both + '/delete')
    assert HTTP_OK in r


def test_PUT(httpbin_both):
    r = http('PUT', httpbin_both + '/put', 'foo=bar')
    assert HTTP_OK in r
    assert r.json['json']['foo'] == 'bar'


def test_POST_JSON_data(httpbin_both):
    r = http('POST', httpbin_both + '/post', 'foo=bar')
    assert HTTP_OK in r
    assert r.json['json']['foo'] == 'bar'


def test_POST_form(httpbin_both):
    r = http('--form', 'POST', httpbin_both + '/post', 'foo=bar')
    assert HTTP_OK in r
    assert '"foo": "bar"' in r


def test_POST_form_multiple_values(httpbin_both):
    r = http('--form', 'POST', httpbin_both + '/post', 'foo=bar', 'foo=baz')
    assert HTTP_OK in r
    assert r.json['form'] == {'foo': ['bar', 'baz']}


def test_POST_stdin(httpbin_both):
    with open(FILE_PATH) as f:
        env = MockEnvironment(stdin=f, stdin_isatty=False)
        r = http('--form', 'POST', httpbin_both + '/post', env=env)
    assert HTTP_OK in r
    assert FILE_CONTENT in r


def test_POST_file(httpbin_both):
    r = http('--form', 'POST', httpbin_both + '/post', 'file@' + FILE_PATH)
    assert HTTP_OK in r
    assert FILE_CONTENT in r


def test_headers(httpbin_both):
    r = http('GET', httpbin_both + '/headers', 'Foo:bar')
    assert HTTP_OK in r
    assert '"User-Agent": "HTTPie' in r, r
    assert '"Foo": "bar"' in r


def test_headers_unset(httpbin_both):
    r = http('GET', httpbin_both + '/headers')
    assert 'Accept' in r.json['headers']  # default Accept present

    r = http('GET', httpbin_both + '/headers', 'Accept:')
    assert 'Accept' not in r.json['headers']   # default Accept unset


@pytest.mark.skip('unimplemented')
def test_unset_host_header(httpbin_both):
    r = http('GET', httpbin_both + '/headers')
    assert 'Host' in r.json['headers']  # default Host present

    r = http('GET', httpbin_both + '/headers', 'Host:')
    assert 'Host' not in r.json['headers']   # default Host unset


def test_headers_empty_value(httpbin_both):
    r = http('GET', httpbin_both + '/headers')
    assert r.json['headers']['Accept']  # default Accept has value

    r = http('GET', httpbin_both + '/headers', 'Accept;')
    assert r.json['headers']['Accept'] == ''   # Accept has no value


def test_headers_empty_value_with_value_gives_error(httpbin):
    with pytest.raises(ParseError):
        http('GET', httpbin + '/headers', 'Accept;SYNTAX_ERROR')


def test_json_input_preserve_order(httpbin_both):
    r = http('PATCH', httpbin_both + '/patch',
             'order:={"map":{"1":"first","2":"second"}}')
    assert HTTP_OK in r
    assert r.json['data'] == \
        '{"order": {"map": {"1": "first", "2": "second"}}}'
