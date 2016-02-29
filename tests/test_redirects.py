"""High-level tests."""
from httpie import ExitStatus
from utils import http, HTTP_OK


class TestRedirects:

    def test_follow_no_show_redirects(self, httpbin):
        r = http('--follow', httpbin.url + '/redirect/2')
        assert r.count('HTTP/1.1') == 1
        assert HTTP_OK in r

    def test_follow_show_redirects(self, httpbin):
        r = http('--follow', '--show-redirects', httpbin.url + '/redirect/2')
        assert r.count('HTTP/1.1') == 3
        assert r.count('HTTP/1.1 302 FOUND', 2)
        assert HTTP_OK in r

    def test_max_redirects(self, httpbin):
        r = http('--max-redirects=1', '--follow', httpbin.url + '/redirect/3',
                 error_exit_ok=True)
        assert r.exit_status == ExitStatus.ERROR_TOO_MANY_REDIRECTS
