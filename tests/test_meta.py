from .utils import http


def test_meta_elapsed_time(httpbin, monkeypatch):
    r = http('--meta', httpbin + '/get')
    for line in r.splitlines():
        assert 'Elapsed time' in r
