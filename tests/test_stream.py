from unittest import TestCase

import pytest

from httpie.compat import is_windows
from httpie.output import BINARY_SUPPRESSED_NOTICE
from tests import http, httpbin, TestEnvironment
from tests.fixtures import BIN_FILE_CONTENT, BIN_FILE_PATH


class StreamTest(TestCase):
    # GET because httpbin 500s with binary POST body.

    @pytest.mark.skipif(is_windows,
                        reason='Pretty redirect not supported under Windows')
    def test_pretty_redirected_stream(self):
        """Test that --stream works with prettified redirected output."""
        with open(BIN_FILE_PATH, 'rb') as f:
            r = http(
                '--verbose',
                '--pretty=all',
                '--stream',
                'GET',
                httpbin('/get'),
                env=TestEnvironment(
                    colors=256,
                    stdin=f,
                    stdin_isatty=False,
                    stdout_isatty=False,
                )
            )
        assert BINARY_SUPPRESSED_NOTICE.decode() in r
        # We get 'Bad Request' but it's okay.
        #self.assertIn(OK_COLOR, r)

    def test_encoded_stream(self):
        """Test that --stream works with non-prettified
        redirected terminal output."""
        with open(BIN_FILE_PATH, 'rb') as f:
            r = http(
                '--pretty=none',
                '--stream',
                '--verbose',
                'GET',
                httpbin('/get'),
                env=TestEnvironment(
                    stdin=f,
                    stdin_isatty=False
                ),
            )
        assert BINARY_SUPPRESSED_NOTICE.decode() in r
        # We get 'Bad Request' but it's okay.
        #self.assertIn(OK, r)

    def test_redirected_stream(self):
        """Test that --stream works with non-prettified
        redirected terminal output."""
        with open(BIN_FILE_PATH, 'rb') as f:
            r = http(
                '--pretty=none',
                '--stream',
                '--verbose',
                'GET',
                httpbin('/get'),
                env=TestEnvironment(
                    stdout_isatty=False,
                    stdin=f,
                    stdin_isatty=False
                )
            )
        # We get 'Bad Request' but it's okay.
        #self.assertIn(OK.encode(), r)
        assert BIN_FILE_CONTENT in r
