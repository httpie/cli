from .utils import http


def test_meta_elapsed_time(httpbin, monkeypatch):
    r = http('--meta', httpbin + '/delay/1')
    assert 'Elapsed time: 1.' in r
