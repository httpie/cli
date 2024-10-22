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


def test_invalid_interface_given(httpbin):
    r = http(
        "--interface=10.25.a.u",  # invalid IP
        httpbin + "/get",
        tolerate_error_exit_status=True,
    )

    assert "'10.25.a.u' does not appear to be an IPv4 or IPv6 address" in r.stderr

    r = http(
        "--interface=abc",  # invalid IP
        httpbin + "/get",
        tolerate_error_exit_status=True,
    )

    assert "'abc' does not appear to be an IPv4 or IPv6 address" in r.stderr


def test_invalid_local_port_given(httpbin):
    r = http(
        "--local-port=127.0.0.1",  # invalid port
        httpbin + "/get",
        tolerate_error_exit_status=True,
    )

    assert '"127.0.0.1" is not a valid port number.' in r.stderr

    r = http(
        "--local-port=a8",  # invalid port
        httpbin + "/get",
        tolerate_error_exit_status=True,
    )

    assert '"a8" is not a valid port number.' in r.stderr

    r = http(
        "--local-port=-8",  # invalid port
        httpbin + "/get",
        tolerate_error_exit_status=True,
    )

    assert 'Negative port number are all invalid values.' in r.stderr

    r = http(
        "--local-port=a-8",  # invalid port range
        httpbin + "/get",
        tolerate_error_exit_status=True,
    )

    assert 'Either "a" or/and "8" is an invalid port number.' in r.stderr

    r = http(
        "--local-port=5555-",  # invalid port range
        httpbin + "/get",
        tolerate_error_exit_status=True,
    )

    assert 'Port range requires both start and end ports to be specified.' in r.stderr


def test_force_ipv6_on_unsupported_system(remote_httpbin):
    from httpie.compat import urllib3
    urllib3.util.connection.HAS_IPV6 = False
    r = http(
        "-6",  # invalid port
        remote_httpbin + "/get",
        tolerate_error_exit_status=True,
    )
    urllib3.util.connection.HAS_IPV6 = True

    assert 'Unable to force IPv6 because your system lack IPv6 support.' in r.stderr


def test_force_both_ipv6_and_ipv4(remote_httpbin):
    r = http(
        "-6",  # force IPv6
        "-4",  # force IPv4
        remote_httpbin + "/get",
        tolerate_error_exit_status=True,
    )

    assert 'Unable to force both IPv4 and IPv6, omit the flags to allow both.' in r.stderr


def test_happy_eyeballs(remote_httpbin_secure):
    r = http(
        "--heb",  # this will automatically and concurrently try IPv6 and IPv4 endpoints
        "--verify=no",
        remote_httpbin_secure + "/get",
    )

    assert r.exit_status == 0
    assert HTTP_OK in r
