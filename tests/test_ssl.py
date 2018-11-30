import os

import pytest
import pytest_httpbin.certs
import requests.exceptions

from httpie import ExitStatus
from httpie.input import SSL_VERSION_ARG_MAPPING
from utils import HTTP_OK, TESTS_ROOT, http


try:
    # Handle OpenSSL errors, if installed.
    # See <https://github.com/jakubroztocil/httpie/issues/729>
    # noinspection PyUnresolvedReferences
    import OpenSSL.SSL
    ssl_errors = (
        requests.exceptions.SSLError,
        OpenSSL.SSL.Error,
    )
except ImportError:
    ssl_errors = (
        requests.exceptions.SSLError,
    )


CLIENT_CERT = os.path.join(TESTS_ROOT, 'client_certs', 'client.crt')
CLIENT_KEY = os.path.join(TESTS_ROOT, 'client_certs', 'client.key')
CLIENT_PEM = os.path.join(TESTS_ROOT, 'client_certs', 'client.pem')
# FIXME:
# We test against a local httpbin instance which uses a self-signed cert.
# Requests without --verify=<CA_BUNDLE> will fail with a verification error.
# See: https://github.com/kevin1024/pytest-httpbin#https-support
CA_BUNDLE = pytest_httpbin.certs.where()


@pytest.mark.parametrize('ssl_version', SSL_VERSION_ARG_MAPPING.keys())
def test_ssl_version(httpbin_secure, ssl_version):
    try:
        r = http(
            '--ssl', ssl_version,
            httpbin_secure + '/get'
        )
        assert HTTP_OK in r
    except ssl_errors as e:
        if ssl_version == 'ssl3':
            # pytest-httpbin doesn't support ssl3
            assert 'SSLV3_ALERT_HANDSHAKE_FAILURE' in str(e)
        else:
            raise


class TestClientCert:

    def test_cert_and_key(self, httpbin_secure):
        r = http(httpbin_secure + '/get',
                 '--cert', CLIENT_CERT,
                 '--cert-key', CLIENT_KEY)
        assert HTTP_OK in r

    def test_cert_pem(self, httpbin_secure):
        r = http(httpbin_secure + '/get',
                 '--cert', CLIENT_PEM)
        assert HTTP_OK in r

    def test_cert_file_not_found(self, httpbin_secure):
        r = http(httpbin_secure + '/get',
                 '--cert', '/__not_found__',
                 error_exit_ok=True)
        assert r.exit_status == ExitStatus.ERROR
        assert 'No such file or directory' in r.stderr

    def test_cert_file_invalid(self, httpbin_secure):
        with pytest.raises(ssl_errors):
            http(httpbin_secure + '/get',
                 '--cert', __file__)

    def test_cert_ok_but_missing_key(self, httpbin_secure):
        with pytest.raises(ssl_errors):
            http(httpbin_secure + '/get',
                 '--cert', CLIENT_CERT)


class TestServerCert:

    def test_verify_no_OK(self, httpbin_secure):
        r = http(httpbin_secure.url + '/get', '--verify=no')
        assert HTTP_OK in r

    @pytest.mark.parametrize('verify_value', ['false', 'fALse'])
    def test_verify_false_OK(self, httpbin_secure, verify_value):
        r = http(httpbin_secure.url + '/get', '--verify', verify_value)
        assert HTTP_OK in r

    def test_verify_custom_ca_bundle_path(
        self, httpbin_secure_untrusted
    ):
        r = http(httpbin_secure_untrusted + '/get', '--verify', CA_BUNDLE)
        assert HTTP_OK in r

    def test_self_signed_server_cert_by_default_raises_ssl_error(
        self,
        httpbin_secure_untrusted
    ):
        with pytest.raises(ssl_errors):
            http(httpbin_secure_untrusted.url + '/get')

    def test_verify_custom_ca_bundle_invalid_path(self, httpbin_secure):
        # since 2.14.0 requests raises IOError
        with pytest.raises(ssl_errors + (IOError,)):
            http(httpbin_secure.url + '/get', '--verify', '/__not_found__')

    def test_verify_custom_ca_bundle_invalid_bundle(self, httpbin_secure):
        with pytest.raises(ssl_errors):
            http(httpbin_secure.url + '/get', '--verify', __file__)
