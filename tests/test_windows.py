import os
import tempfile
from unittest import TestCase

import pytest

from tests import TestEnvironment, http, httpbin, Environment
from httpie.compat import is_windows


class WindowsOnlyTests(TestCase):

    @pytest.mark.skipif(not is_windows, reason='windows-only')
    def test_windows_colorized_output(self):
        # Spits out the colorized output.
        http(httpbin('/get'), env=Environment())


class FakeWindowsTest(TestCase):

    def test_output_file_pretty_not_allowed_on_windows(self):

        r = http(
            '--output',
            os.path.join(tempfile.gettempdir(), '__httpie_test_output__'),
            '--pretty=all',
            'GET',
            httpbin('/get'),
            env=TestEnvironment(is_windows=True)
        )
        assert 'Only terminal output can be colorized on Windows' in r.stderr
