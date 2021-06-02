import pytest
from httpie.context import Environment

from .utils import MockEnvironment, http
from httpie.compat import is_windows


@pytest.mark.skipif(not is_windows, reason='windows-only')
class TestWindowsOnly:

    @pytest.mark.skipif(True,
                        reason='this test for some reason kills the process')
    def test_windows_colorized_output(self, httpbin):
        # Spits out the colorized output.
        http(httpbin.url + '/get', env=Environment())


class TestFakeWindows:
    def test_output_file_pretty_not_allowed_on_windows(self, tmp_path, httpbin):
        env = MockEnvironment(is_windows=True)
        output_file = tmp_path / 'test_output_file_pretty_not_allowed_on_windows'
        r = http('--output', str(output_file),
                 '--pretty=all', 'GET', httpbin.url + '/get',
                 env=env, tolerate_error_exit_status=True)
        assert 'Only terminal output can be colorized on Windows' in r.stderr
