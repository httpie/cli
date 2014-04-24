import os
import time

from httpie.compat import urlopen
from httpie.downloads import (
    parse_content_range,
    filename_from_content_disposition,
    filename_from_url,
    get_unique_filename,
    ContentRangeError,
    Download,
)
from tests import (
    BaseTestCase, httpbin, http, TestEnvironment, Response
)


class DownloadUtilsTest(BaseTestCase):

    def test_Content_Range_parsing(self):

        parse = parse_content_range

        self.assertEqual(parse('bytes 100-199/200', 100), 200)
        self.assertEqual(parse('bytes 100-199/*', 100), 200)

        # missing
        self.assertRaises(ContentRangeError, parse, None, 100)

        # syntax error
        self.assertRaises(ContentRangeError, parse, 'beers 100-199/*', 100)

        # unexpected range
        self.assertRaises(ContentRangeError, parse, 'bytes 100-199/*', 99)

        # invalid instance-length
        self.assertRaises(ContentRangeError, parse, 'bytes 100-199/199', 100)

        # invalid byte-range-resp-spec
        self.assertRaises(ContentRangeError, parse, 'bytes 100-99/199', 100)

        # invalid byte-range-resp-spec
        self.assertRaises(ContentRangeError, parse, 'bytes 100-100/*', 100)

    def test_Content_Disposition_parsing(self):
        parse = filename_from_content_disposition
        self.assertEqual(
            parse('attachment; filename=hello-WORLD_123.txt'),
            'hello-WORLD_123.txt'
        )
        self.assertEqual(
            parse('attachment; filename=".hello-WORLD_123.txt"'),
            'hello-WORLD_123.txt'
        )
        self.assertEqual(
            parse('attachment; filename="white space.txt"'),
            'white space.txt'
        )
        self.assertEqual(
            parse(r'attachment; filename="\"quotes\".txt"'),
            '"quotes".txt'
        )
        self.assertEqual(parse('attachment; filename=/etc/hosts'), 'hosts')
        self.assertIsNone(parse('attachment; filename='))

    def test_filename_from_url(self):
        self.assertEqual(filename_from_url(
            url='http://example.org/foo',
            content_type='text/plain'
        ), 'foo.txt')
        self.assertEqual(filename_from_url(
            url='http://example.org/foo',
            content_type='text/html; charset=utf8'
        ), 'foo.html')
        self.assertEqual(filename_from_url(
            url='http://example.org/foo',
            content_type=None
        ), 'foo')
        self.assertEqual(filename_from_url(
            url='http://example.org/foo',
            content_type='x-foo/bar'
        ), 'foo')

    def test_unique_filename(self):

        def make_exists(unique_on_attempt=0):
            # noinspection PyUnresolvedReferences,PyUnusedLocal
            def exists(filename):
                if exists.attempt == unique_on_attempt:
                    return False
                exists.attempt += 1
                return True
            exists.attempt = 0
            return exists

        self.assertEqual(
            get_unique_filename('foo.bar', exists=make_exists()),
            'foo.bar'
        )
        self.assertEqual(
            get_unique_filename('foo.bar', exists=make_exists(1)),
            'foo.bar-1'
        )
        self.assertEqual(
            get_unique_filename('foo.bar', exists=make_exists(10)),
            'foo.bar-10'
        )


class DownloadsTest(BaseTestCase):
    # TODO: more tests

    def test_actual_download(self):
        url = httpbin('/robots.txt')
        body = urlopen(url).read().decode()
        r = http(
            '--download',
            url,
            env=TestEnvironment(
                stdin_isatty=True,
                stdout_isatty=False
            )
        )
        self.assertIn('Downloading', r.stderr)
        self.assertIn('[K', r.stderr)
        self.assertIn('Done', r.stderr)
        self.assertEqual(body, r)

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
        self.assertFalse(download.interrupted)

    def test_download_no_Content_Length(self):
        download = Download(output_file=open(os.devnull, 'w'))
        download.start(Response(url=httpbin('/')))
        time.sleep(1.1)
        download.chunk_downloaded(b'12345')
        download.finish()
        self.assertFalse(download.interrupted)

    def test_download_interrupted(self):
        download = Download(output_file=open(os.devnull, 'w'))
        download.start(Response(
            url=httpbin('/'),
            headers={'Content-Length': 5}
        ))
        download.chunk_downloaded(b'1234')
        download.finish()
        self.assertTrue(download.interrupted)
