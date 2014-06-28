"""Miscellaneous regression tests"""
import socket

from utils import http, HTTP_OK


def test_Host_header_overwrite():
    """
    https://github.com/jakubroztocil/httpie/issues/235

    """
    host = 'httpbin.org'
    url = 'http://{httpbin_ip}/get'.format(
        httpbin_ip=socket.gethostbyname(host))
    r = http('--print=hH', url, 'host:{}'.format(host))
    assert HTTP_OK in r
    assert r.lower().count('host:') == 1
