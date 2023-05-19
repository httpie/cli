import ssl
from typing import NamedTuple, Optional

from httpie.adapters import HTTPAdapter
# noinspection PyPackageRequirements
from urllib3.util.ssl_ import (
    create_urllib3_context,
    resolve_ssl_version,
)

# We used to import default SSL ciphers via `SSL_CIPHERS` from `urllib3` but it’s been removed,
# so we’ve copied the original list here.
# Our issue: <https://github.com/httpie/httpie/issues/1499>
# Removal commit: <https://github.com/urllib3/urllib3/commit/e5eac0c>
DEFAULT_SSL_CIPHERS = ":".join([
    # <urllib3>
    # A secure default.
    # Sources for more information on TLS ciphers:
    #
    # - https://wiki.mozilla.org/Security/Server_Side_TLS
    # - https://www.ssllabs.com/projects/best-practices/index.html
    # - https://hynek.me/articles/hardening-your-web-servers-ssl-ciphers/
    #
    # The general intent is:
    # - prefer cipher suites that offer perfect forward secrecy (DHE/ECDHE),
    # - prefer ECDHE over DHE for better performance,
    # - prefer any AES-GCM and ChaCha20 over any AES-CBC for better performance and
    #   security,
    # - prefer AES-GCM over ChaCha20 because hardware-accelerated AES is common,
    # - disable NULL authentication, MD5 MACs, DSS, and other
    #   insecure ciphers for security reasons.
    # - NOTE: TLS 1.3 cipher suites are managed through a different interface
    #   not exposed by CPython (yet!) and are enabled by default if they're available.
    "ECDHE+AESGCM",
    "ECDHE+CHACHA20",
    "DHE+AESGCM",
    "DHE+CHACHA20",
    "ECDH+AESGCM",
    "DH+AESGCM",
    "ECDH+AES",
    "DH+AES",
    "RSA+AESGCM",
    "RSA+AES",
    "!aNULL",
    "!eNULL",
    "!MD5",
    "!DSS",
    "!AESCCM",
    # </urllib3>
])
SSL_VERSION_ARG_MAPPING = {
    'ssl2.3': 'PROTOCOL_SSLv23',
    'ssl3': 'PROTOCOL_SSLv3',
    'tls1': 'PROTOCOL_TLSv1',
    'tls1.1': 'PROTOCOL_TLSv1_1',
    'tls1.2': 'PROTOCOL_TLSv1_2',
    'tls1.3': 'PROTOCOL_TLSv1_3',
}
AVAILABLE_SSL_VERSION_ARG_MAPPING = {
    arg: getattr(ssl, constant_name)
    for arg, constant_name in SSL_VERSION_ARG_MAPPING.items()
    if hasattr(ssl, constant_name)
}


class HTTPieCertificate(NamedTuple):
    cert_file: Optional[str] = None
    key_file: Optional[str] = None
    key_password: Optional[str] = None

    def to_raw_cert(self):
        """Synthesize a requests-compatible (2-item tuple of cert and key file)
        object from HTTPie's internal representation of a certificate."""
        return (self.cert_file, self.key_file)


class HTTPieHTTPSAdapter(HTTPAdapter):
    def __init__(
        self,
        verify: bool,
        ssl_version: str = None,
        ciphers: str = None,
        **kwargs
    ):
        self._ssl_context = self._create_ssl_context(
            verify=verify,
            ssl_version=ssl_version,
            ciphers=ciphers,
        )
        super().__init__(**kwargs)

    def init_poolmanager(self, *args, **kwargs):
        kwargs['ssl_context'] = self._ssl_context
        return super().init_poolmanager(*args, **kwargs)

    def proxy_manager_for(self, *args, **kwargs):
        kwargs['ssl_context'] = self._ssl_context
        return super().proxy_manager_for(*args, **kwargs)

    def cert_verify(self, conn, url, verify, cert):
        if isinstance(cert, HTTPieCertificate):
            conn.key_password = cert.key_password
            cert = cert.to_raw_cert()

        return super().cert_verify(conn, url, verify, cert)

    @staticmethod
    def _create_ssl_context(
        verify: bool,
        ssl_version: str = None,
        ciphers: str = None,
    ) -> 'ssl.SSLContext':
        return create_urllib3_context(
            ciphers=ciphers,
            ssl_version=resolve_ssl_version(ssl_version),
            # Since we are using a custom SSL context, we need to pass this
            # here manually, even though it’s also passed to the connection
            # in `super().cert_verify()`.
            cert_reqs=ssl.CERT_REQUIRED if verify else ssl.CERT_NONE
        )


def _is_key_file_encrypted(key_file):
    """Detects if a key file is encrypted or not.

    Copy of the internal urllib function (urllib3.util.ssl_)"""

    with open(key_file, "r") as f:
        for line in f:
            # Look for Proc-Type: 4,ENCRYPTED
            if "ENCRYPTED" in line:
                return True

    return False
