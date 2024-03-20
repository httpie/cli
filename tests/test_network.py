from .utils import HTTP_OK, http


def test_ensure_interface_parameter(httpbin):
    """We ensure that HTTPie properly wire interface by passing an interface that
        does not exist. thus, we expect an error."""
    r = http(
        "--interface=1.1.1.1",
        httpbin + "/get",
        tolerate_error_exit_status=True
    )

    assert "Cannot assign requested address" in r.stderr


def test_ensure_local_port_parameter(httpbin):
    """We ensure that HTTPie properly wire local-port by passing a port that
    require elevated privilege. thus, we expect an error."""
    r = http(
        "--local-port=89",
        httpbin + "/get",
        tolerate_error_exit_status=True
    )

    assert "Permission denied" in r.stderr


def test_ensure_interface_and_port_parameters(httpbin):
    r = http(
        "--interface=0.0.0.0",  # it's valid, setting 0.0.0.0 means "take the default" here.
        "--local-port=0",  # this will automatically pick a free port in range 1024-65535
        httpbin + "/get",
    )

    assert HTTP_OK in r


def test_ensure_ipv6_toggle_parameter(httpbin):
    """This test is made to ensure we are effectively passing the IPv6-only flag to
    Niquests. Our test server listen exclusively on IPv4."""
    r = http(
        "-6",
        httpbin + "/get",
        tolerate_error_exit_status=True,
    )

    assert r.exit_status != 0
    assert "Name or service not known" in r.stderr
