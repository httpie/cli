from httpie.models import ELAPSED_TIME_LABEL
from .utils import http, MockEnvironment


def test_meta_elapsed_time(httpbin, monkeypatch):
    r = http('--meta', httpbin + '/delay/1')
    assert f'{ELAPSED_TIME_LABEL}: 1.' in r


def test_meta_elapsed_time_colors_pie_style(httpbin, monkeypatch):
    r = http('--style=fruity', '--meta', httpbin + '/get', env=MockEnvironment(colors=256))
    assert ELAPSED_TIME_LABEL in r


def test_meta_elapsed_time_colors_non_pie_style(httpbin, monkeypatch):
    r = http('--style=pie-dark', '--meta', httpbin + '/get', env=MockEnvironment(colors=256))
    assert ELAPSED_TIME_LABEL in r
