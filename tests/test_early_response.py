from .utils import http


def test_early_response_show(remote_httpbin_secure):
    r = http(
        "--verify=no",
        'https://early-hints.fastlylabs.com/'
    )

    assert "103 Early Hints" in r
    assert "200 OK" in r
