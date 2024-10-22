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


def test_invalid_override_resolver():
    r = http(
        "--resolver=pie.dev:abc",  # we do this nonsense on purpose
        "pie.dev/get",
        tolerate_error_exit_status=True
    )

    assert "'abc' does not appear to be an IPv4 or IPv6 address" in r.stderr

    r = http(
        "--resolver=abc",  # we do this nonsense on purpose
        "pie.dev/get",
        tolerate_error_exit_status=True
    )

    assert "The manual resolver for a specific host requires to be formatted like" in r.stderr

    r = http(
        "--resolver=pie.dev:127.0.0",  # we do this nonsense on purpose
        "pie.dev/get",
        tolerate_error_exit_status=True
    )

    assert "'127.0.0' does not appear to be an IPv4 or IPv6 address" in r.stderr

    r = http(
        "--resolver=doz://example.com",  # we do this nonsense on purpose
        "pie.dev/get",
        tolerate_error_exit_status=True
    )

    assert "'doz' is not a valid ProtocolResolver" in r.stderr
