import pytest
import json

from httpie.ssl_ import QuicCapabilityCache

from .utils import HTTP_OK, http, PersistentMockEnvironment

try:
    import qh3
except ImportError:
    qh3 = None


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


@pytest.mark.skipif(qh3 is None, reason="test require HTTP/3 support")
def test_force_http3(remote_httpbin_secure):
    r = http(
        "--verify=no",
        '--http3',
        remote_httpbin_secure + '/get'
    )

    assert "HTTP/3" in r
    assert HTTP_OK in r


def test_force_multiple_error(remote_httpbin_secure):
    r = http(
        "--verify=no",
        '--http3',
        '--http2',
        remote_httpbin_secure + '/get',
        tolerate_error_exit_status=True,
    )

    assert 'You may only force one of --http1, --http2 or --http3.' in r.stderr


def test_disable_all_error_https(remote_httpbin_secure):
    r = http(
        "--verify=no",
        '--disable-http1',
        '--disable-http2',
        '--disable-http3',
        remote_httpbin_secure + '/get',
        tolerate_error_exit_status=True,
    )

    assert 'At least one HTTP protocol version must be enabled.' in r.stderr


def test_disable_all_error_http(remote_httpbin):
    r = http(
        "--verify=no",
        '--disable-http1',
        '--disable-http2',
        remote_httpbin + '/get',
        tolerate_error_exit_status=True,
    )

    try:
        import qh3  # noqa: F401
    except ImportError:
        # that branch means that the user does not have HTTP/3
        # so, the message says that he disabled everything.
        assert 'You disabled every supported protocols.' in r.stderr
    else:
        assert 'No compatible protocol are enabled to emit request. You currently are connected using TCP Unencrypted and must have HTTP/1.1 or/and HTTP/2 enabled to pursue.' in r.stderr


@pytest.fixture
def with_quic_cache_persistent(tmp_path):
    env = PersistentMockEnvironment()
    env.config['quic_file'] = tmp_path / 'quic.json'
    try:
        yield env
    finally:
        env.cleanup(force=True)


@pytest.mark.skipif(qh3 is None, reason="test require HTTP/3 support")
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


@pytest.mark.skipif(qh3 is None, reason="test require HTTP/3 support")
def test_h3_not_compatible_anymore(remote_httpbin_secure, with_quic_cache_persistent):
    """verify that we can handle failures and fallback appropriately."""
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
