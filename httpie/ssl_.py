import ssl
import typing
from pathlib import Path
from typing import NamedTuple, Optional, Tuple, MutableMapping
import json
import os.path

from httpie.adapters import HTTPAdapter
from .compat import create_urllib3_context, resolve_ssl_version

# the minimum one may hope to negotiate with Python 3.7+ is tls1+
# anything else would be unsupported.
SSL_VERSION_ARG_MAPPING = {
    'tls1': 'PROTOCOL_TLSv1',
    'tls1.1': 'PROTOCOL_TLSv1_1',
    'tls1.2': 'PROTOCOL_TLSv1_2',
    'tls1.3': 'PROTOCOL_TLSv1_3',
}
# todo: we'll need to update this in preparation for Python 3.13+
# could be a removal (after a long deprecation about constants
# PROTOCOL_TLSv1, PROTOCOL_TLSv1_1, ...).
AVAILABLE_SSL_VERSION_ARG_MAPPING = {
    arg: getattr(ssl, constant_name)
    for arg, constant_name in SSL_VERSION_ARG_MAPPING.items()
    if hasattr(ssl, constant_name)
}


class QuicCapabilityCache(
    MutableMapping[Tuple[str, int], Optional[Tuple[str, int]]]
):
    """This class will help us keep (persistent across runs) what hosts are QUIC capable.
    See https://urllib3future.readthedocs.io/en/latest/advanced-usage.html#remembering-http-3-over-quic-support for
    the implementation guide."""

    def __init__(self, path: Path):
        self._path = path
        self._cache = {}
        if os.path.exists(path):
            with open(path, "r") as fp:
                try:
                    self._cache = json.load(fp)
                except json.JSONDecodeError:  # if the file is corrupted (invalid json) then, ignore it.
                    pass

    def save(self):
        with open(self._path, "w") as fp:
            json.dump(self._cache, fp)

    def __contains__(self, item: Tuple[str, int]):
        return f"QUIC_{item[0]}_{item[1]}" in self._cache

    def __setitem__(self, key: Tuple[str, int], value: Optional[Tuple[str, int]]):
        self._cache[f"QUIC_{key[0]}_{key[1]}"] = f"{value[0]}:{value[1]}"
        self.save()

    def __getitem__(self, item: Tuple[str, int]):
        key: str = f"QUIC_{item[0]}_{item[1]}"
        if key in self._cache:
            host, port = self._cache[key].split(":")
            return host, int(port)

        return None

    def __delitem__(self, key: Tuple[str, int]):
        key: str = f"QUIC_{key[0]}_{key[1]}"
        if key in self._cache:
            del self._cache[key]
            self.save()

    def __len__(self):
        return len(self._cache)

    def __iter__(self):
        yield from self._cache.items()


class HTTPieCertificate(NamedTuple):
    cert_file: Optional[str] = None
    key_file: Optional[str] = None
    key_password: Optional[str] = None

    def to_raw_cert(self) -> typing.Union[
        typing.Tuple[typing.Optional[str], typing.Optional[str], typing.Optional[str]],  # with password
        typing.Tuple[typing.Optional[str], typing.Optional[str]]  # without password
    ]:
        """Synthesize a niquests-compatible (2(or 3)-item tuple of cert, key file and optionally password)
        object from HTTPie's internal representation of a certificate."""
        if self.key_password:
            # Niquests support 3-tuple repr in addition to the 2-tuple repr
            return self.cert_file, self.key_file, self.key_password
        return self.cert_file, self.key_file


class HTTPieHTTPSAdapter(HTTPAdapter):
    def __init__(
        self,
        verify: bool,
        ssl_version: str = None,
        ciphers: str = None,
        **kwargs
    ):
        self._ssl_context = None
        self._verify = None

        if ssl_version or ciphers:
            # Only set the custom context if user supplied one.
            # Because urllib3-future set his own secure ctx with a set of
            # ciphers (moz recommended list). thus avoiding excluding QUIC
            # in case some ciphers are accidentally excluded.
            self._ssl_context = self._create_ssl_context(
                verify=verify,
                ssl_version=ssl_version,
                ciphers=ciphers,
            )
        else:
            self._verify = verify

        super().__init__(**kwargs)

    def init_poolmanager(self, *args, **kwargs):
        kwargs['ssl_context'] = self._ssl_context
        if self._verify is not None:
            kwargs['cert_reqs'] = ssl.CERT_REQUIRED if self._verify else ssl.CERT_NONE
        return super().init_poolmanager(*args, **kwargs)

    def proxy_manager_for(self, *args, **kwargs):
        kwargs['ssl_context'] = self._ssl_context
        if self._verify is not None:
            kwargs['cert_reqs'] = ssl.CERT_REQUIRED if self._verify else ssl.CERT_NONE
        return super().proxy_manager_for(*args, **kwargs)

    def cert_verify(self, conn, url, verify, cert):
        if isinstance(cert, HTTPieCertificate):
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

    @classmethod
    def get_default_ciphers_names(cls):
        return [cipher['name'] for cipher in cls._create_ssl_context(verify=False).get_ciphers()]


def _is_key_file_encrypted(key_file):
    """Detects if a key file is encrypted or not.

    Copy of the internal urllib function (urllib3.util.ssl_)"""

    with open(key_file, "r") as f:
        for line in f:
            # Look for Proc-Type: 4,ENCRYPTED
            if "ENCRYPTED" in line:
                return True

    return False


# We used to import the default set of TLS ciphers from urllib3, but they removed it.
# Instead, now urllib3 uses the list of ciphers configured by the system.
# <https://github.com/httpie/cli/pull/1501>
DEFAULT_SSL_CIPHERS_STRING = ':'.join(HTTPieHTTPSAdapter.get_default_ciphers_names())
