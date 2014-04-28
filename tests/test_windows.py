import os
import tempfile

import pytest
from httpie.context import Environment

from utils import TestEnvironment, http, httpbin
from httpie.compat import is_windows


@pytest.mark.skipif(not is_windows, reason='windows-only')
class TestWindowsOnly:

    @pytest.mark.skipif(True,
                        reason='this test for some reason kills the process')
    def test_windows_colorized_output(self):
        # Spits out the colorized output.
        http(httpbin('/get'), env=Environment())


class TestFakeWindows:
    def test_output_file_pretty_not_allowed_on_windows(self):
        env = TestEnvironment(is_windows=True)
        output_file = os.path.join(
            tempfile.gettempdir(), '__httpie_test_output__')
        r = http('--output', output_file,
                 '--pretty=all', 'GET', httpbin('/get'),
                 env=env, error_exit_ok=True)
        assert 'Only terminal output can be colorized on Windows' in r.stderr
