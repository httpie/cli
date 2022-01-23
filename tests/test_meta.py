import pytest

from httpie.models import ELAPSED_TIME_LABEL
from httpie.output.formatters.colors import PIE_STYLE_NAMES
from .utils import http, MockEnvironment, COLOR


def test_meta_elapsed_time(httpbin):
    r = http('--meta', httpbin + '/delay/1')
    assert f'{ELAPSED_TIME_LABEL}: 1.' in r


@pytest.mark.parametrize('style', ['auto', 'fruity', *PIE_STYLE_NAMES])
def test_meta_elapsed_time_colors(httpbin, style):
    r = http('--style', style, '--meta', httpbin + '/get', env=MockEnvironment(colors=256))
    assert COLOR in r
    assert ELAPSED_TIME_LABEL in r
