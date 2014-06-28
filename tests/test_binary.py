"""Tests for dealing with binary request and response data."""
from httpie.compat import urlopen
from httpie.output.streams import BINARY_SUPPRESSED_NOTICE
from utils import TestEnvironment, http
from fixtures import BIN_FILE_PATH, BIN_FILE_CONTENT, BIN_FILE_PATH_ARG


class TestBinaryRequestData:
    def test_binary_stdin(self, httpbin):
        with open(BIN_FILE_PATH, 'rb') as stdin:
            env = TestEnvironment(
                stdin=stdin,
                stdin_isatty=False,
                stdout_isatty=False
            )
            r = http('--print=B', 'POST', httpbin.url + '/post', env=env)
            assert r == BIN_FILE_CONTENT

    def test_binary_file_path(self, httpbin):
        env = TestEnvironment(stdin_isatty=True, stdout_isatty=False)
        r = http('--print=B', 'POST', httpbin.url + '/post',
                 '@' + BIN_FILE_PATH_ARG, env=env, )
        assert r == BIN_FILE_CONTENT

    def test_binary_file_form(self, httpbin):
        env = TestEnvironment(stdin_isatty=True, stdout_isatty=False)
        r = http('--print=B', '--form', 'POST', httpbin.url + '/post',
                 'test@' + BIN_FILE_PATH_ARG, env=env)
        assert bytes(BIN_FILE_CONTENT) in bytes(r)


class TestBinaryResponseData:
    url = 'http://www.google.com/favicon.ico'

    @property
    def bindata(self):
        if not hasattr(self, '_bindata'):
            self._bindata = urlopen(self.url).read()
        return self._bindata

    def test_binary_suppresses_when_terminal(self):
        r = http('GET', self.url)
        assert BINARY_SUPPRESSED_NOTICE.decode() in r

    def test_binary_suppresses_when_not_terminal_but_pretty(self):
        env = TestEnvironment(stdin_isatty=True, stdout_isatty=False)
        r = http('--pretty=all', 'GET', self.url,
                 env=env)
        assert BINARY_SUPPRESSED_NOTICE.decode() in r

    def test_binary_included_and_correct_when_suitable(self):
        env = TestEnvironment(stdin_isatty=True, stdout_isatty=False)
        r = http('GET', self.url, env=env)
        assert r == self.bindata
