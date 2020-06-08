import os

import pytest

from httpie.cli.exceptions import ParseError
from httpie.status import ExitStatus
from utils import MockEnvironment, http, HTTP_OK
from fixtures import FILE_PATH_ARG, FILE_PATH, FILE_CONTENT


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
        r = http('--form', '--verbose', 'POST', httpbin.url + '/post',
                 f'test-file@{FILE_PATH_ARG};type=image/vnd.microsoft.icon')
        assert HTTP_OK in r
        # Content type is stripped from the filename
        assert 'Content-Disposition: form-data; name="test-file";' \
               f' filename="{os.path.basename(FILE_PATH)}"' in r
        assert FILE_CONTENT in r
        assert 'Content-Type: image/vnd.microsoft.icon' in r


class TestRequestBodyFromFilePath:
    """
    `http URL @file'

    """

    def test_request_body_from_file_by_path(self, httpbin):
        r = http('--verbose',
                 'POST', httpbin.url + '/post', '@' + FILE_PATH_ARG)
        assert HTTP_OK in r
        assert FILE_CONTENT in r, r
        assert '"Content-Type": "text/plain"' in r

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
