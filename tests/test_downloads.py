import os
import time
from unittest import TestCase

import pytest
from requests.structures import CaseInsensitiveDict

from httpie.compat import urlopen
from httpie.downloads import (
    parse_content_range,
    filename_from_content_disposition,
    filename_from_url,
    get_unique_filename,
    ContentRangeError,
    Download,
)
from tests import httpbin, http, TestEnvironment


class Response(object):
    # noinspection PyDefaultArgument
    def __init__(self, url, headers={}, status_code=200):
        self.url = url
        self.headers = CaseInsensitiveDict(headers)
        self.status_code = status_code


class DownloadUtilsTest(TestCase):
    def test_Content_Range_parsing(self):
        parse = parse_content_range

        assert parse('bytes 100-199/200', 100) == 200
        assert parse('bytes 100-199/*', 100) == 200

        # missing
        pytest.raises(ContentRangeError, parse, None, 100)

        # syntax error
        pytest.raises(ContentRangeError, parse, 'beers 100-199/*', 100)

        # unexpected range
        pytest.raises(ContentRangeError, parse, 'bytes 100-199/*', 99)

        # invalid instance-length
        pytest.raises(ContentRangeError, parse, 'bytes 100-199/199', 100)

        # invalid byte-range-resp-spec
        pytest.raises(ContentRangeError, parse, 'bytes 100-99/199', 100)

        # invalid byte-range-resp-spec
        pytest.raises(ContentRangeError, parse, 'bytes 100-100/*', 100)

    def test_Content_Disposition_parsing(self):
        parse = filename_from_content_disposition
        assert 'hello-WORLD_123.txt' == parse(
            'attachment; filename=hello-WORLD_123.txt')
        assert 'hello-WORLD_123.txt' == parse(
            'attachment; filename=".hello-WORLD_123.txt"')
        assert 'white space.txt' == parse(
            'attachment; filename="white space.txt"')
        assert '"quotes".txt' == parse(
            r'attachment; filename="\"quotes\".txt"')
        assert parse('attachment; filename=/etc/hosts') == 'hosts'
        assert parse('attachment; filename=') is None

    def test_filename_from_url(self):
        assert 'foo.txt' == filename_from_url(
            url='http://example.org/foo',
            content_type='text/plain'
        )
        assert 'foo.html' == filename_from_url(
            url='http://example.org/foo',
            content_type='text/html; charset=utf8'
        )
        assert 'foo' == filename_from_url(
            url='http://example.org/foo',
            content_type=None
        )
        assert 'foo' == filename_from_url(
            url='http://example.org/foo',
            content_type='x-foo/bar'
        )

    def test_unique_filename(self):
        def attempts(unique_on_attempt=0):
            # noinspection PyUnresolvedReferences,PyUnusedLocal
            def exists(filename):
                if exists.attempt == unique_on_attempt:
                    return False
                exists.attempt += 1
                return True

            exists.attempt = 0
            return exists

        assert 'foo.bar' == get_unique_filename('foo.bar', attempts(0))
        assert 'foo.bar-1' == get_unique_filename('foo.bar', attempts(1))
        assert 'foo.bar-10' == get_unique_filename('foo.bar', attempts(10))


class DownloadsTest(TestCase):
    # TODO: more tests

    def test_actual_download(self):
        url = httpbin('/robots.txt')
        body = urlopen(url).read().decode()
        env = TestEnvironment(stdin_isatty=True, stdout_isatty=False)
        r = http('--download', url, env=env)
        assert 'Downloading' in r.stderr
        assert '[K' in r.stderr
        assert 'Done' in r.stderr
        assert body == r

    def test_download_with_Content_Length(self):
        download = Download(output_file=open(os.devnull, 'w'))
        download.start(Response(
            url=httpbin('/'),
            headers={'Content-Length': 10}
        ))
        time.sleep(1.1)
        download.chunk_downloaded(b'12345')
        time.sleep(1.1)
        download.chunk_downloaded(b'12345')
        download.finish()
        assert not download.interrupted

    def test_download_no_Content_Length(self):
        download = Download(output_file=open(os.devnull, 'w'))
        download.start(Response(url=httpbin('/')))
        time.sleep(1.1)
        download.chunk_downloaded(b'12345')
        download.finish()
        assert not download.interrupted

    def test_download_interrupted(self):
        download = Download(output_file=open(os.devnull, 'w'))
        download.start(Response(
            url=httpbin('/'),
            headers={'Content-Length': 5}
        ))
        download.chunk_downloaded(b'1234')
        download.finish()
        assert download.interrupted
