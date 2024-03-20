from .utils import HTTP_OK, http


def test_should_not_do_http1_by_default(remote_httpbin_secure):
    r = http(
        "--verify=no",
        remote_httpbin_secure + '/get'
    )

    assert "HTTP/1" not in r
    assert HTTP_OK in r


def test_disable_http2n3(remote_httpbin_secure):
    r = http(
        "--verify=no",
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
