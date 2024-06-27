import os
import tempfile
import time
import zlib
from unittest import mock
from urllib.request import urlopen

import niquests
import pytest
import responses
from httpie.downloads import (
    parse_content_range,
    filename_from_content_disposition,
    filename_from_url,
    get_unique_filename,
    ContentRangeError,
    Downloader,
    PARTIAL_CONTENT,
    DECODED_FROM_SUFFIX,
)
from niquests.structures import CaseInsensitiveDict
from .utils import http, MockEnvironment, cd_clean_tmp_dir, DUMMY_URL


class Response(niquests.Response):
    # noinspection PyDefaultArgument
    def __init__(self, url, headers={}, status_code=200):
        self.url = url
        self.headers = CaseInsensitiveDict(headers)
        self.status_code = status_code


class TestDownloadUtils:

    def test_Content_Range_parsing(self):
        parse = parse_content_range

        assert parse('bytes 100-199/200', 100) == 200
        assert parse('bytes 100-199/*', 100) == 200

        # single byte
        assert parse('bytes 100-100/*', 100) == 101

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

    @pytest.mark.parametrize('header, expected_filename', [
        ('attachment; filename=hello-WORLD_123.txt', 'hello-WORLD_123.txt'),
        ('attachment; filename=".hello-WORLD_123.txt"', 'hello-WORLD_123.txt'),
        ('attachment; filename="white space.txt"', 'white space.txt'),
        (r'attachment; filename="\"quotes\".txt"', '"quotes".txt'),
        ('attachment; filename=/etc/hosts', 'hosts'),
        ('attachment; filename=', None)
    ])
    def test_Content_Disposition_parsing(self, header, expected_filename):
        assert filename_from_content_disposition(header) == expected_filename

    def test_filename_from_url(self):
        assert 'foo.txt' == filename_from_url(
            url='http://example.org/foo',
            content_type='text/plain'
        )
        assert 'foo.html' == filename_from_url(
            url='http://example.org/foo',
            content_type='text/html; charset=UTF-8'
        )
        assert 'foo' == filename_from_url(
            url='http://example.org/foo',
            content_type=None
        )
        assert 'foo' == filename_from_url(
            url='http://example.org/foo',
            content_type='x-foo/bar'
        )

    @pytest.mark.parametrize(
        'orig_name, unique_on_attempt, expected',
        [
            # Simple
            ('foo.bar', 0, 'foo.bar'),
            ('foo.bar', 1, 'foo.bar-1'),
            ('foo.bar', 10, 'foo.bar-10'),
            # Trim
            ('A' * 20, 0, 'A' * 10),
            ('A' * 20, 1, 'A' * 8 + '-1'),
            ('A' * 20, 10, 'A' * 7 + '-10'),
            # Trim before ext
            ('A' * 20 + '.txt', 0, 'A' * 6 + '.txt'),
            ('A' * 20 + '.txt', 1, 'A' * 4 + '.txt-1'),
            # Trim at the end
            ('foo.' + 'A' * 20, 0, 'foo.' + 'A' * 6),
            ('foo.' + 'A' * 20, 1, 'foo.' + 'A' * 4 + '-1'),
            ('foo.' + 'A' * 20, 10, 'foo.' + 'A' * 3 + '-10'),
        ]
    )
    @mock.patch('httpie.downloads.get_filename_max_length')
    def test_unique_filename(self, get_filename_max_length,
                             orig_name, unique_on_attempt,
                             expected):
        def attempts(unique_on_attempt=0):
            # noinspection PyUnresolvedReferences,PyUnusedLocal
            def exists(filename):
                if exists.attempt == unique_on_attempt:
                    return False
                exists.attempt += 1
                return True

            exists.attempt = 0
            return exists

        get_filename_max_length.return_value = 10

        actual = get_unique_filename(orig_name, attempts(unique_on_attempt))
        assert expected == actual


class TestDownloader:

    def test_actual_download(self, httpbin_both, httpbin):
        robots_txt = '/robots.txt'
        body = urlopen(httpbin + robots_txt).read().decode()
        env = MockEnvironment(stdin_isatty=True, stdout_isatty=False, show_displays=True)
        r = http('--download', httpbin_both.url + robots_txt, env=env)
        assert 'Downloading' in r.stderr
        assert body == r

    def test_download_with_Content_Length(self, mock_env, httpbin_both):
        with open(os.devnull, 'w') as devnull:
            downloader = Downloader(mock_env, output_file=devnull)
            downloader.start(
                initial_url='/',
                final_response=Response(
                    url=httpbin_both.url + '/',
                    headers={'Content-Length': 10}
                )
            )
            time.sleep(1.1)
            downloader.chunk_downloaded(b'12345')
            time.sleep(1.1)
            downloader.chunk_downloaded(b'12345')
            downloader.finish()
            assert not downloader.is_interrupted

    def test_download_no_Content_Length(self, mock_env, httpbin_both):
        with open(os.devnull, 'w') as devnull:
            downloader = Downloader(mock_env, output_file=devnull)
            downloader.start(
                final_response=Response(url=httpbin_both.url + '/'),
                initial_url='/'
            )
            time.sleep(1.1)
            downloader.chunk_downloaded(b'12345')
            downloader.finish()
            assert not downloader.is_interrupted

    def test_download_output_from_content_disposition(self, mock_env, httpbin_both):
        output_file_name = 'filename.bin'
        with cd_clean_tmp_dir(assert_filenames_after=[output_file_name]):
            downloader = Downloader(mock_env)
            downloader.start(
                final_response=Response(
                    url=httpbin_both.url + '/',
                    headers={
                        'Content-Length': 5,
                        'Content-Disposition': f'attachment; filename="{output_file_name}"',
                    }
                ),
                initial_url='/'
            )
            downloader.chunk_downloaded(b'12345')
            downloader.finish()
            downloader.failed()  # Stop the reporter
            assert not downloader.is_interrupted

            # TODO: Auto-close the file in that case?
            downloader._output_file.close()

    def test_downloader_is_interrupted(self, mock_env, httpbin_both):
        with open(os.devnull, 'w') as devnull:
            downloader = Downloader(mock_env, output_file=devnull)
            downloader.start(
                final_response=Response(
                    url=httpbin_both.url + '/',
                    headers={'Content-Length': 5}
                ),
                initial_url='/'
            )
            downloader.chunk_downloaded(b'1234')
            downloader.finish()
            assert downloader.is_interrupted

    def test_download_resumed(self, mock_env, httpbin_both):
        with tempfile.TemporaryDirectory() as tmp_dirname:
            file = os.path.join(tmp_dirname, 'file.bin')
            with open(file, 'a'):
                pass

            with open(file, 'a+b') as output_file:
                # Start and interrupt the transfer after 3 bytes written
                downloader = Downloader(mock_env, output_file=output_file)
                downloader.start(
                    final_response=Response(
                        url=httpbin_both.url + '/',
                        headers={'Content-Length': 5}
                    ),
                    initial_url='/'
                )
                downloader.chunk_downloaded(b'123')
                downloader.finish()
                downloader.failed()
                assert downloader.is_interrupted

            # Write bytes
            with open(file, 'wb') as fh:
                fh.write(b'123')

            with open(file, 'a+b') as output_file:
                # Resume the transfer
                downloader = Downloader(mock_env, output_file=output_file, resume=True)

                # Ensure `pre_request()` is working as expected too
                headers = {}
                downloader.pre_request(headers)
                assert headers['Range'] == 'bytes=3-'

                downloader.start(
                    final_response=Response(
                        url=httpbin_both.url + '/',
                        headers={
                            'Content-Length': 5,
                            'Content-Range': 'bytes 3-4/5',
                        },
                        status_code=PARTIAL_CONTENT
                    ),
                    initial_url='/'
                )
                downloader.chunk_downloaded(b'45')
                downloader.finish()

    def test_download_with_redirect_original_url_used_for_filename(self, httpbin):
        # Redirect from `/redirect/1` to `/get`.
        expected_filename = '1.json'
        with cd_clean_tmp_dir(assert_filenames_after=[expected_filename]):
            http('--download', httpbin + '/redirect/1')

    def test_download_gzip_content_encoding(self, httpbin):
        expected_filename = 'gzip.json'
        with cd_clean_tmp_dir(assert_filenames_after=[expected_filename]):
            r = http('--download', httpbin + '/gzip')
        assert r.exit_status == 0

    @responses.activate
    def test_incomplete_response(self):
        # We have incompleteness checks in the downloader, but it might not be needed as it’s built into (ni|req)uests.
        error_msg = 'IncompleteRead(2 bytes read, 1 more expected)'
        responses.add(
            method=responses.GET,
            url=DUMMY_URL,
            headers={
                'Content-Length': '3',
            },
            body='12',
        )
        with cd_clean_tmp_dir(), pytest.raises(Exception) as exc_info:
            http('--download', DUMMY_URL)
        assert error_msg in str(exc_info.value)


class TestDecodedDownloads:
    """Test downloading responses with `Content-Encoding`"""

    @responses.activate
    def test_decoded_response_no_content_length(self):
        responses.add(
            method=responses.GET,
            url=DUMMY_URL,
            headers={
                'Content-Encoding': 'deflate',
            },
            body=zlib.compress(b"foobar"),
        )
        with cd_clean_tmp_dir():
            r = http('--download', '--headers', DUMMY_URL)
        print(r.stderr)
        assert DECODED_FROM_SUFFIX.format(encodings='`deflate`') in r.stderr

    @responses.activate
    def test_decoded_response_with_content_length(self):
        payload = zlib.compress(b"foobar")

        responses.add(
            method=responses.GET,
            url=DUMMY_URL,
            headers={
                'Content-Encoding': 'deflate',
                'Content-Length': str(len(payload)),
            },
            body=payload,
        )
        with cd_clean_tmp_dir():
            r = http('--download', DUMMY_URL)
        print(r.stderr)
        assert DECODED_FROM_SUFFIX.format(encodings='`deflate`') in r.stderr

    @responses.activate
    def test_decoded_response_without_content_length(self):
        responses.add(
            method=responses.GET,
            url=DUMMY_URL,
            headers={
                'Content-Encoding': 'deflate',
            },
            body=zlib.compress(b'foobar'),
        )
        with cd_clean_tmp_dir():
            r = http('--download', DUMMY_URL)
        print(r.stderr)
        assert DECODED_FROM_SUFFIX.format(encodings='`deflate`') in r.stderr

    @responses.activate
    def test_non_decoded_response_without_content_length(self):
        responses.add(
            method=responses.GET,
            url=DUMMY_URL,
            headers={
                'Content-Length': '3',
            },
            body='123',
        )
        with cd_clean_tmp_dir():
            r = http('--download', DUMMY_URL)
        print(r.stderr)

    @responses.activate
    def test_non_decoded_response_with_content_length(self):
        responses.add(
            method=responses.GET,
            url=DUMMY_URL,
            headers={
            },
            body='123',
        )
        with cd_clean_tmp_dir():
            r = http('--download', DUMMY_URL)
        print(r.stderr)
