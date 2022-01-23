from httpie.models import ELAPSED_TIME_LABEL
from .utils import http


def test_meta_elapsed_time(httpbin, monkeypatch):
    r = http('--meta', httpbin + '/delay/1')
    assert f'{ELAPSED_TIME_LABEL}: 1.' in r
