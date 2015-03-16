import os

import pytest
import pytest_httpbin.certs
from requests.exceptions import SSLError

from httpie import ExitStatus
from utils import http, HTTP_OK, TESTS_ROOT


CLIENT_CERT = os.path.join(TESTS_ROOT, 'client_certs', 'client.crt')
CLIENT_KEY = os.path.join(TESTS_ROOT, 'client_certs', 'client.key')
CLIENT_PEM = os.path.join(TESTS_ROOT, 'client_certs', 'client.pem')

# We test against a local httpbin instance which uses a self-signed cert.
# Requests without --verify=<CA_BUNDLE> will fail with a verification error.
# See: https://github.com/kevin1024/pytest-httpbin#https-support
CA_BUNDLE = pytest_httpbin.certs.where()


class TestClientSSLCertHandling(object):

    def test_cert_file_not_found(self, httpbin_secure):
        r = http(httpbin_secure + '/get',
                 '--verify', CA_BUNDLE,
                 '--cert', '/__not_found__',
                 error_exit_ok=True)
        assert r.exit_status == ExitStatus.ERROR
        assert 'No such file or directory' in r.stderr

    def test_cert_file_invalid(self, httpbin_secure):
        with pytest.raises(SSLError):
            http(httpbin_secure + '/get',
                 '--verify', CA_BUNDLE,
                 '--cert', __file__)

    def test_cert_ok_but_missing_key(self, httpbin_secure):
        with pytest.raises(SSLError):
            http(httpbin_secure + '/get',
                 '--verify', CA_BUNDLE,
                 '--cert', CLIENT_CERT)

    def test_cert_and_key(self, httpbin_secure):
        r = http(httpbin_secure + '/get',
                 '--verify', CA_BUNDLE,
                 '--cert', CLIENT_CERT,
                 '--cert-key', CLIENT_KEY)
        assert HTTP_OK in r

    def test_cert_pem(self, httpbin_secure):
        r = http(httpbin_secure + '/get',
                 '--verify', CA_BUNDLE,
                 '--cert', CLIENT_PEM)
        assert HTTP_OK in r


class TestServerSSLCertHandling(object):

    def test_self_signed_server_cert_by_default_raises_ssl_error(
            self, httpbin_secure):
        with pytest.raises(SSLError):
            http(httpbin_secure.url + '/get')

    def test_verify_no_OK(self, httpbin_secure):
        r = http(httpbin_secure.url + '/get', '--verify=no')
        assert HTTP_OK in r

    def test_verify_custom_ca_bundle_path(
            self, httpbin_secure):
        r = http(httpbin_secure.url + '/get', '--verify', CA_BUNDLE)
        assert HTTP_OK in r

    def test_verify_custom_ca_bundle_invalid_path(self, httpbin_secure):
        with pytest.raises(SSLError):
            http(httpbin_secure.url + '/get', '--verify', '/__not_found__')

    def test_verify_custom_ca_bundle_invalid_bundle(self, httpbin_secure):
        with pytest.raises(SSLError):
            http(httpbin_secure.url + '/get', '--verify', __file__)
