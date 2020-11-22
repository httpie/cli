import os

import pytest

from httpie.cli.exceptions import ParseError
from httpie.client import FORM_CONTENT_TYPE
from httpie.status import ExitStatus
from utils import (
    HTTPBIN_WITH_CHUNKED_SUPPORT, MockEnvironment, StdinBytesIO, http,
    HTTP_OK,
)
from fixtures import FILE_PATH_ARG, FILE_PATH, FILE_CONTENT


def test_chunked_json():
    r = http(
        '--verbose',
        '--chunked',
        HTTPBIN_WITH_CHUNKED_SUPPORT + '/post',
        'hello=world',
    )
    assert HTTP_OK in r
    assert 'Transfer-Encoding: chunked' in r
    assert r.count('hello') == 3


def test_chunked_form():
    r = http(
        '--verbose',
        '--chunked',
        '--form',
        HTTPBIN_WITH_CHUNKED_SUPPORT + '/post',
        'hello=world',
    )
    assert HTTP_OK in r
    assert 'Transfer-Encoding: chunked' in r
    assert r.count('hello') == 2


def test_chunked_stdin():
    r = http(
        '--verbose',
        '--chunked',
        HTTPBIN_WITH_CHUNKED_SUPPORT + '/post',
        env=MockEnvironment(
            stdin=StdinBytesIO(FILE_PATH.read_bytes()),
            stdin_isatty=False,
        )
    )
    assert HTTP_OK in r
    assert 'Transfer-Encoding: chunked' in r
    assert r.count(FILE_CONTENT) == 2


def test_chunked_stdin_multiple_chunks():
    stdin_bytes = FILE_PATH.read_bytes() + b'\n' + FILE_PATH.read_bytes()
    r = http(
        '--verbose',
        '--chunked',
        HTTPBIN_WITH_CHUNKED_SUPPORT + '/post',
        env=MockEnvironment(
            stdin=StdinBytesIO(stdin_bytes),
            stdin_isatty=False,
            stdout_isatty=True,
        )
    )
    assert HTTP_OK in r
    assert 'Transfer-Encoding: chunked' in r
    assert r.count(FILE_CONTENT) == 4


class TestMultipartFormDataFileUpload:

    def test_non_existent_file_raises_parse_error(self, httpbin):
        with pytest.raises(ParseError):
            http('--form',
                 'POST', httpbin.url + '/post', 'foo@/__does_not_exist__')

    def test_upload_ok(self, httpbin):
        r = http('--form', '--verbose', 'POST', httpbin.url + '/post',
                 f'test-file@{FILE_PATH_ARG}', 'foo=bar')
        assert HTTP_OK in r
        assert 'Content-Disposition: form-data; name="foo"' in r
        assert 'Content-Disposition: form-data; name="test-file";' \
               f' filename="{os.path.basename(FILE_PATH)}"' in r
        assert FILE_CONTENT in r
        assert '"foo": "bar"' in r
        assert 'Content-Type: text/plain' in r

    def test_upload_multiple_fields_with_the_same_name(self, httpbin):
        r = http('--form', '--verbose', 'POST', httpbin.url + '/post',
                 f'test-file@{FILE_PATH_ARG}',
                 f'test-file@{FILE_PATH_ARG}')
        assert HTTP_OK in r
        assert r.count('Content-Disposition: form-data; name="test-file";'
                       f' filename="{os.path.basename(FILE_PATH)}"') == 2
        # Should be 4, but is 3 because httpbin
        # doesn't seem to support filed field lists
        assert r.count(FILE_CONTENT) in [3, 4]
        assert r.count('Content-Type: text/plain') == 2

    def test_upload_custom_content_type(self, httpbin):
        r = http(
            '--form',
            '--verbose',
            httpbin.url + '/post',
            f'test-file@{FILE_PATH_ARG};type=image/vnd.microsoft.icon'
        )
        assert HTTP_OK in r
        # Content type is stripped from the filename
        assert 'Content-Disposition: form-data; name="test-file";' \
               f' filename="{os.path.basename(FILE_PATH)}"' in r
        assert r.count(FILE_CONTENT) == 2
        assert 'Content-Type: image/vnd.microsoft.icon' in r

    def test_form_no_files_urlencoded(self, httpbin):
        r = http(
            '--form',
            '--verbose',
            httpbin.url + '/post',
            'AAAA=AAA',
            'BBB=BBB',
        )
        assert HTTP_OK in r
        assert FORM_CONTENT_TYPE in r

    def test_multipart(self, httpbin):
        r = http(
            '--verbose',
            '--multipart',
            httpbin.url + '/post',
            'AAAA=AAA',
            'BBB=BBB',
        )
        assert HTTP_OK in r
        assert FORM_CONTENT_TYPE not in r
        assert 'multipart/form-data' in r

    def test_form_multipart_custom_boundary(self, httpbin):
        boundary = 'HTTPIE_FTW'
        r = http(
            '--print=HB',
            '--check-status',
            '--multipart',
            f'--boundary={boundary}',
            httpbin.url + '/post',
            'AAAA=AAA',
            'BBB=BBB',
        )
        assert f'multipart/form-data; boundary={boundary}' in r
        assert r.count(boundary) == 4

    def test_multipart_custom_content_type_boundary_added(self, httpbin):
        boundary = 'HTTPIE_FTW'
        r = http(
            '--print=HB',
            '--check-status',
            '--multipart',
            f'--boundary={boundary}',
            httpbin.url + '/post',
            'Content-Type: multipart/magic',
            'AAAA=AAA',
            'BBB=BBB',
        )
        assert f'multipart/magic; boundary={boundary}' in r
        assert r.count(boundary) == 4

    def test_multipart_custom_content_type_boundary_preserved(self, httpbin):
        # Allow explicit nonsense requests.
        boundary_in_header = 'HEADER_BOUNDARY'
        boundary_in_body = 'BODY_BOUNDARY'
        r = http(
            '--print=HB',
            '--check-status',
            '--multipart',
            f'--boundary={boundary_in_body}',
            httpbin.url + '/post',
            f'Content-Type: multipart/magic; boundary={boundary_in_header}',
            'AAAA=AAA',
            'BBB=BBB',
        )
        assert f'multipart/magic; boundary={boundary_in_header}' in r
        assert r.count(boundary_in_body) == 3

    def test_multipart_chunked(self, httpbin):
        r = http(
            '--verbose',
            '--multipart',
            '--chunked',
            HTTPBIN_WITH_CHUNKED_SUPPORT + '/post',
            'AAA=AAA',
        )
        assert 'Transfer-Encoding: chunked' in r
        assert 'multipart/form-data' in r
        assert 'name="AAA"' in r  # in request
        assert '"AAA": "AAA"', r  # in response

    def test_multipart_preserve_order(self, httpbin):
        r = http(
            '--form',
            '--offline',
            httpbin + '/post',
            'text_field=foo',
            f'file_field@{FILE_PATH_ARG}',
        )
        assert r.index('text_field') < r.index('file_field')

        r = http(
            '--form',
            '--offline',
            httpbin + '/post',
            f'file_field@{FILE_PATH_ARG}',
            'text_field=foo',
        )
        assert r.index('text_field') > r.index('file_field')


class TestRequestBodyFromFilePath:
    """
    `http URL @file'

    """

    def test_request_body_from_file_by_path(self, httpbin):
        r = http(
            '--verbose',
            'POST', httpbin.url + '/post',
            '@' + FILE_PATH_ARG,
        )
        assert HTTP_OK in r
        assert r.count(FILE_CONTENT) == 2
        assert '"Content-Type": "text/plain"' in r

    def test_request_body_from_file_by_path_chunked(self, httpbin):
        r = http(
            '--verbose', '--chunked',
            HTTPBIN_WITH_CHUNKED_SUPPORT + '/post',
            '@' + FILE_PATH_ARG,
        )
        assert HTTP_OK in r
        assert 'Transfer-Encoding: chunked' in r
        assert '"Content-Type": "text/plain"' in r
        assert r.count(FILE_CONTENT) == 2

    def test_request_body_from_file_by_path_with_explicit_content_type(
            self, httpbin):
        r = http('--verbose',
                 'POST', httpbin.url + '/post', '@' + FILE_PATH_ARG,
                 'Content-Type:text/plain; charset=utf8')
        assert HTTP_OK in r
        assert FILE_CONTENT in r
        assert 'Content-Type: text/plain; charset=utf8' in r

    def test_request_body_from_file_by_path_no_field_name_allowed(
            self, httpbin):
        env = MockEnvironment(stdin_isatty=True)
        r = http('POST', httpbin.url + '/post', 'field-name@' + FILE_PATH_ARG,
                 env=env, tolerate_error_exit_status=True)
        assert 'perhaps you meant --form?' in r.stderr

    def test_request_body_from_file_by_path_no_data_items_allowed(
            self, httpbin):
        env = MockEnvironment(stdin_isatty=False)
        r = http(
            'POST',
            httpbin.url + '/post',
            '@' + FILE_PATH_ARG, 'foo=bar',
            env=env,
            tolerate_error_exit_status=True,
        )
        assert r.exit_status == ExitStatus.ERROR
        assert 'cannot be mixed' in r.stderr
