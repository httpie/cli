import socket

import pytest
from pytest_httpbin import certs
from pytest_httpbin.serve import Server as PyTestHttpBinServer

from .utils import (  # noqa
    HTTPBIN_WITH_CHUNKED_SUPPORT_DOMAIN,
    HTTPBIN_WITH_CHUNKED_SUPPORT,
    REMOTE_HTTPBIN_DOMAIN,
    IS_PYOPENSSL,
    mock_env
)
from .utils.plugins_cli import (  # noqa
    broken_plugin,
    dummy_plugin,
    dummy_plugins,
    httpie_plugins,
    httpie_plugins_success,
    interface,
)
from .utils.http_server import http_server, localhost_http_server  # noqa


# Patch to support `url = str(server)` in addition to `url = server + '/foo'`.
PyTestHttpBinServer.__str__ = lambda self: self.url


@pytest.fixture(scope='function', autouse=True)
def httpbin_add_ca_bundle(monkeypatch):
    """
    Make pytest-httpbin's CA trusted by default.

    (Same as `httpbin_ca_bundle`, just auto-used.).

    """
    monkeypatch.setenv('REQUESTS_CA_BUNDLE', certs.where())


@pytest.fixture(scope='function')
def httpbin_secure_untrusted(monkeypatch, httpbin_secure):
    """
    Like the `httpbin_secure` fixture, but without the
    make-CA-trusted-by-default.

    """
    monkeypatch.delenv('REQUESTS_CA_BUNDLE')
    return httpbin_secure


@pytest.fixture(scope='session')
def _httpbin_with_chunked_support_available():
    try:
        socket.gethostbyname(HTTPBIN_WITH_CHUNKED_SUPPORT_DOMAIN)
        return True
    except OSError:
        return False


@pytest.fixture(scope='function')
def httpbin_with_chunked_support(_httpbin_with_chunked_support_available):
    if _httpbin_with_chunked_support_available:
        return HTTPBIN_WITH_CHUNKED_SUPPORT
    pytest.skip(f'{HTTPBIN_WITH_CHUNKED_SUPPORT_DOMAIN} not resolvable')


@pytest.fixture(scope='session')
def _remote_httpbin_available():
    try:
        socket.gethostbyname(REMOTE_HTTPBIN_DOMAIN)
        return True
    except OSError:
        return False


@pytest.fixture
def remote_httpbin(_remote_httpbin_available):
    if _remote_httpbin_available:
        return 'http://' + REMOTE_HTTPBIN_DOMAIN
    pytest.skip(f'{REMOTE_HTTPBIN_DOMAIN} not resolvable')


@pytest.fixture(autouse=True, scope='session')
def pyopenssl_inject():
    """
    Injects `pyOpenSSL` module to make sure `requests` will use it.
    <https://github.com/psf/requests/pull/5443#issuecomment-645740394>
    """
    if IS_PYOPENSSL:
        try:
            import urllib3.contrib.pyopenssl
            urllib3.contrib.pyopenssl.inject_into_urllib3()
        except ModuleNotFoundError:
            pytest.fail('Missing "pyopenssl" module.')

    yield
