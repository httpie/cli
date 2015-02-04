# coding=utf-8
"""Tests for unix domain socket support

"""

import multiprocessing
import os
import time
import uuid

import pytest
from requests import ConnectionError
from requests_unixsocket.testutils import UnixSocketServerThread

from utils import http, HTTP_OK


class TestUnixSocket:

    def test_unix_domain_adapter_ok(self):
        from requests.compat import quote_plus

        with UnixSocketServerThread() as usock_thread:
            print('usock_thread.usock = %r' % usock_thread.usock)
            urlencoded_socket_name = quote_plus(usock_thread.usock)
            print('urlencoded_socket_name = %r' % urlencoded_socket_name)
            url = 'http+unix://%s/path/to/page' % urlencoded_socket_name
            print('url = %r' % url)

            for i in range(1, 5):
                try:
                    r = http('GET', url)
                    break
                except ConnectionError:
                    time.sleep(1)
                r = http('GET', url)

            assert HTTP_OK in r
            print('r = %r' % r)
            assert 'Server: waitress' in r
            assert 'X-Transport: unix domain socket' in r
            assert 'X-Requested-Path: /path/to/page' in r
            assert 'X-Socket-Path: %s' % usock_thread.usock in r
            assert 'Hello world' in r

    def test_unix_domain_adapter_connection_error(self):
        with pytest.raises(ConnectionError):
            http('GET', 'http+unix://socket_does_not_exist/path/to/page')
