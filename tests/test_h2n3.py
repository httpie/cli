import pytest
import json

from httpie.ssl_ import QuicCapabilityCache

from .utils import HTTP_OK, http, PersistentMockEnvironment


def test_should_not_do_http1_by_default(remote_httpbin_secure):
    r = http(
        "--verify=no",
        remote_httpbin_secure + '/get'
    )

    assert "HTTP/1" not in r
    assert HTTP_OK in r


def test_disable_http2n3(remote_httpbin_secure):
    r = http(
        # Only for DEV environment!
        "--verify=no",  # we have REQUESTS_CA_BUNDLE environment set, so we must disable ext verify.
        '--disable-http2',
        '--disable-http3',
        remote_httpbin_secure + '/get'
    )

    assert "HTTP/1.1" in r
    assert HTTP_OK in r


def test_force_http3(remote_httpbin_secure):
    r = http(
        "--verify=no",
        '--http3',
        remote_httpbin_secure + '/get'
    )

    assert "HTTP/3" in r
    assert HTTP_OK in r


@pytest.fixture
def with_quic_cache_persistent(tmp_path):
    env = PersistentMockEnvironment()
    env.config['quic_file'] = tmp_path / 'quic.json'
    yield env
    env.cleanup(force=True)


def test_ensure_quic_cache(remote_httpbin_secure, with_quic_cache_persistent):
    """
    This test aim to verify that the QuicCapabilityCache work as intended.
    """
    r = http(
        "--verify=no",
        remote_httpbin_secure + '/get',
        env=with_quic_cache_persistent
    )

    assert "HTTP/2" in r
    assert HTTP_OK in r

    r = http(
        "--verify=no",
        remote_httpbin_secure + '/get',
        env=with_quic_cache_persistent
    )

    assert "HTTP/3" in r
    assert HTTP_OK in r

    tmp_path = with_quic_cache_persistent.config['quic_file']

    with open(tmp_path, "r") as fp:
        cache = json.load(fp)

    assert len(cache) == 1
    assert "pie.dev" in list(cache.keys())[0]


def test_h3_not_compatible_anymore(remote_httpbin_secure, with_quic_cache_persistent):
    tmp_path = with_quic_cache_persistent.config['quic_file']

    cache = QuicCapabilityCache(tmp_path)

    # doing a __setitem__ should trigger save automatically!
    cache[("pie.dev", 443)] = ("pie.dev", 61443)  # nothing listen on 61443!

    # without timeout
    r = http(
        "--verify=no",
        remote_httpbin_secure + '/get',
        env=with_quic_cache_persistent,
        tolerate_error_exit_status=True
    )

    assert "HTTP/2 200 OK" in r

    # with timeout
    r = http(
        "--verify=no",
        "--timeout=1",
        remote_httpbin_secure + '/get',
        env=with_quic_cache_persistent,
        tolerate_error_exit_status=True
    )

    assert "HTTP/2 200 OK" in r
