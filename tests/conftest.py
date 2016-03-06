import pytest
from pytest_httpbin.plugin import httpbin_ca_bundle


# Make httpbin's CA trusted by default
pytest.fixture(autouse=True)(httpbin_ca_bundle)


@pytest.fixture(scope='function')
def httpbin_secure_untrusted(monkeypatch, httpbin_secure):
    """Like the `httpbin_secure` fixture, but without the
    make-CA-trusted-by-default"""
    monkeypatch.delenv('REQUESTS_CA_BUNDLE')
    return httpbin_secure
