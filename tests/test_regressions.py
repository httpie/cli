"""Miscellaneous regression tests"""
import pytest

from httpie.compat import is_windows
from tests.utils.matching import assert_output_matches, Expect
from utils import HTTP_OK, MockEnvironment, http


def test_Host_header_overwrite(httpbin):
    """
    https://github.com/httpie/httpie/issues/235

    """
    host = 'pie.dev'
    url = httpbin.url + '/get'
    r = http('--print=hH', url, 'host:{0}'.format(host))
    assert HTTP_OK in r
    assert r.lower().count('host:') == 1
    assert 'host: {0}'.format(host) in r


@pytest.mark.skipif(is_windows, reason='Unix-only')
def test_output_devnull(httpbin):
    """
    https://github.com/httpie/httpie/issues/252

    """
    http('--output=/dev/null', httpbin + '/get')


def test_verbose_redirected_stdout_separator(httpbin):
    """

    <https://github.com/httpie/httpie/issues/1006>
    """
    r = http(
        '-v',
        httpbin.url + '/post',
        'a=b',
        env=MockEnvironment(stdout_isatty=False),
    )
    assert '}HTTP/' not in r
    assert_output_matches(r, [
        Expect.REQUEST_HEADERS,
        Expect.BODY,
        Expect.SEPARATOR,
        Expect.RESPONSE_HEADERS,
        Expect.BODY,
    ])
