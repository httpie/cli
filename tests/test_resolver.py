import pytest

from .utils import http

try:
    import qh3
except ImportError:
    qh3 = None


@pytest.mark.skipif(qh3 is None, reason="test require HTTP/3 support")
def test_ensure_resolver_used(remote_httpbin_secure):
    """This test ensure we're using specified resolver to get into pie.dev.
    Using a custom resolver with Niquests enable direct HTTP/3 negotiation and pie.dev
    (DNS) is handled by Cloudflare (NS) services."""
    r = http(
        "--verify=no",
        "--resolver=doh+cloudflare://",
        remote_httpbin_secure + "/get"
    )

    assert "HTTP/3" in r


def test_ensure_override_resolver_used(remote_httpbin):
    """Just an additional check to ensure we are wired properly to Niquests resolver parameter."""
    r = http(
        "--resolver=pie.dev:240.0.0.0",  # override DNS response to TARPIT net addr.
        "--disable-http3",
        remote_httpbin + "/get",
        tolerate_error_exit_status=True
    )

    assert "Request timed out" in r.stderr or "A socket operation was attempted to an unreachable network" in r.stderr
