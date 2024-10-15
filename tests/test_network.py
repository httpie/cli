from .utils import HTTP_OK, http


def test_ensure_interface_parameter(httpbin):
    """We ensure that HTTPie properly wire interface by passing an interface that
        does not exist. thus, we expect an error."""
    r = http(
        "--interface=1.1.1.1",
        httpbin + "/get",
        tolerate_error_exit_status=True
    )

    assert r.exit_status != 0
    assert "assign requested address" in r.stderr or "The requested address is not valid in its context" in r.stderr


def test_ensure_local_port_parameter(httpbin):
    """We ensure that HTTPie properly wire local-port by passing a port that
    does not exist. thus, we expect an error."""
    r = http(
        "--local-port=70000",
        httpbin + "/get",
        tolerate_error_exit_status=True
    )

    assert r.exit_status != 0
    assert "port must be 0-65535" in r.stderr


def test_ensure_interface_and_port_parameters(httpbin):
    r = http(
        "--interface=0.0.0.0",  # it's valid, setting 0.0.0.0 means "take the default" here.
        "--local-port=0",  # this will automatically pick a free port in range 1024-65535
        httpbin + "/get",
    )

    assert r.exit_status == 0
    assert HTTP_OK in r


def test_happy_eyeballs(remote_httpbin_secure):
    r = http(
        "--heb",  # this will automatically and concurrently try IPv6 and IPv4 endpoints
        remote_httpbin_secure + "/get",
    )

    assert r.exit_status == 0
    assert HTTP_OK in r
