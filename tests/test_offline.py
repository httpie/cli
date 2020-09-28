from fixtures import FILE_CONTENT, FILE_PATH_ARG
from utils import http


def test_offline():
    r = http(
        '--offline',
        'https://this-should.never-resolve/foo',
    )
    assert 'GET /foo' in r


def test_offline_form():
    r = http(
        '--offline',
        '--form',
        'https://this-should.never-resolve/foo',
        'foo=bar'
    )
    assert 'POST /foo' in r
    assert 'foo=bar' in r


def test_offline_json():
    r = http(
        '--offline',
        'https://this-should.never-resolve/foo',
        'foo=bar'
    )
    assert 'POST /foo' in r
    assert r.json == {'foo': 'bar'}


def test_offline_multipart():
    r = http(
        '--offline',
        '--multipart',
        'https://this-should.never-resolve/foo',
        'foo=bar'
    )
    assert 'POST /foo' in r
    assert 'name="foo"' in r


def test_offline_from_file():
    r = http(
        '--offline',
        'https://this-should.never-resolve/foo',
        f'@{FILE_PATH_ARG}'
    )
    assert 'POST /foo' in r
    assert FILE_CONTENT in r


def test_offline_chunked():
    r = http(
        '--offline',
        '--chunked',
        '--form',
        'https://this-should.never-resolve/foo',
        'hello=world'
    )
    assert 'POST /foo' in r
    assert 'Transfer-Encoding: chunked' in r, r
    assert 'hello=world' in r


def test_offline_download():
    """Absence of response should be handled gracefully with --download"""
    r = http(
        '--offline',
        '--download',
        'https://this-should.never-resolve/foo',
    )
    assert 'GET /foo' in r
