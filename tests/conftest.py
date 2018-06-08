import pytest
from pytest_httpbin import certs


@pytest.fixture(scope='function', autouse=True)
def httpbin_secure_untrusted(monkeypatch, httpbin_secure):
    """Like the `httpbin_secure` fixture, but without the
    make-CA-trusted-by-default"""
    monkeypatch.setenv('REQUESTS_CA_BUNDLE', certs.where())
    return httpbin_secure
