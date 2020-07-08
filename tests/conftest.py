import os
import pytest
from pytest_httpbin import certs


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


@pytest.fixture(autouse=True, scope='session')
def pyopenssl_inject():
    """
    Injects `pyOpenSSL` module to make sure `requests`
    will use it.

    <https://github.com/psf/requests/pull/5443#issuecomment-645740394>
    """
    import urllib3.contrib.pyopenssl
    urllib3.contrib.pyopenssl.inject_into_urllib3()

    if os.getenv('HTTPIE_TEST_WITH_PYOPENSSL', default='0') == '0':
        urllib3.contrib.pyopenssl.extract_from_urllib3()

    yield
    urllib3.contrib.pyopenssl.extract_from_urllib3()
