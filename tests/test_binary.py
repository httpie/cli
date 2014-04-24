"""Tests for dealing with binary request and response data."""
from unittest import TestCase

from httpie.compat import urlopen
from httpie.output import BINARY_SUPPRESSED_NOTICE
from tests import TestEnvironment, http, httpbin
from tests.fixtures import BIN_FILE_PATH, BIN_FILE_CONTENT, BIN_FILE_PATH_ARG


class BinaryRequestDataTest(TestCase):

    def test_binary_stdin(self):
        with open(BIN_FILE_PATH, 'rb') as stdin:
            env = TestEnvironment(
                stdin=stdin,
                stdin_isatty=False,
                stdout_isatty=False
            )
            r = http(
                '--print=B',
                'POST',
                httpbin('/post'),
                env=env,
            )
            assert r == BIN_FILE_CONTENT

    def test_binary_file_path(self):
        env = TestEnvironment(
            stdin_isatty=True,
            stdout_isatty=False
        )
        r = http(
            '--print=B',
            'POST',
            httpbin('/post'),
            '@' + BIN_FILE_PATH_ARG,
            env=env,
        )

        assert r == BIN_FILE_CONTENT

    def test_binary_file_form(self):
        env = TestEnvironment(
            stdin_isatty=True,
            stdout_isatty=False
        )
        r = http(
            '--print=B',
            '--form',
            'POST',
            httpbin('/post'),
            'test@' + BIN_FILE_PATH_ARG,
            env=env,
        )
        assert bytes(BIN_FILE_CONTENT) in bytes(r)


class BinaryResponseDataTest(TestCase):

    url = 'http://www.google.com/favicon.ico'

    @property
    def bindata(self):
        if not hasattr(self, '_bindata'):
            self._bindata = urlopen(self.url).read()
        return self._bindata

    def test_binary_suppresses_when_terminal(self):
        r = http(
            'GET',
            self.url
        )
        assert BINARY_SUPPRESSED_NOTICE.decode() in r

    def test_binary_suppresses_when_not_terminal_but_pretty(self):
        r = http(
            '--pretty=all',
            'GET',
            self.url,
            env=TestEnvironment(stdin_isatty=True,
                            stdout_isatty=False)
        )
        assert BINARY_SUPPRESSED_NOTICE.decode() in r

    def test_binary_included_and_correct_when_suitable(self):
        r = http(
            'GET',
            self.url,
            env=TestEnvironment(stdin_isatty=True,
                            stdout_isatty=False)
        )
        assert r == self.bindata
