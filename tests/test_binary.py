"""Tests for dealing with binary request and response data."""
import requests

from fixtures import BIN_FILE_PATH, BIN_FILE_CONTENT, BIN_FILE_PATH_ARG
from httpie.output.streams import BINARY_SUPPRESSED_NOTICE
from utils import MockEnvironment, http


class TestBinaryRequestData:

    def test_binary_stdin(self, httpbin):
        with open(BIN_FILE_PATH, 'rb') as stdin:
            env = MockEnvironment(
                stdin=stdin,
                stdin_isatty=False,
                stdout_isatty=False
            )
            r = http('--print=B', 'POST', httpbin.url + '/post', env=env)
            assert r == BIN_FILE_CONTENT

    def test_binary_file_path(self, httpbin):
        env = MockEnvironment(stdin_isatty=True, stdout_isatty=False)
        r = http('--print=B', 'POST', httpbin.url + '/post',
                 '@' + BIN_FILE_PATH_ARG, env=env, )
        assert r == BIN_FILE_CONTENT

    def test_binary_file_form(self, httpbin):
        env = MockEnvironment(stdin_isatty=True, stdout_isatty=False)
        r = http('--print=B', '--form', 'POST', httpbin.url + '/post',
                 'test@' + BIN_FILE_PATH_ARG, env=env)
        assert bytes(BIN_FILE_CONTENT) in bytes(r)


class TestBinaryResponseData:

    def test_binary_suppresses_when_terminal(self, httpbin):
        r = http('GET', httpbin + '/bytes/1024?seed=1')
        assert BINARY_SUPPRESSED_NOTICE.decode() in r

    def test_binary_suppresses_when_not_terminal_but_pretty(self, httpbin):
        env = MockEnvironment(stdin_isatty=True, stdout_isatty=False)
        r = http('--pretty=all', 'GET', httpbin + '/bytes/1024?seed=1', env=env)
        assert BINARY_SUPPRESSED_NOTICE.decode() in r

    def test_binary_included_and_correct_when_suitable(self, httpbin):
        env = MockEnvironment(stdin_isatty=True, stdout_isatty=False)
        url = httpbin + '/bytes/1024?seed=1'
        r = http('GET', url, env=env)
        expected = requests.get(url).content
        assert r == expected
