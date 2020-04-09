import os

import pytest

from httpie.cli.exceptions import ParseError
from httpie.status import ExitStatus
from utils import MockEnvironment, http, HTTP_OK
from fixtures import FILE_PATH_ARG, FILE_PATH, FILE_CONTENT


class TestMultipartFormDataFileUpload:

    @staticmethod
    def test_non_existent_file_raises_parse_error(httpbin):
        with pytest.raises(ParseError):
            http('--form',
                 'POST', httpbin.url + '/post', 'foo@/__does_not_exist__')

    @staticmethod
    def test_upload_ok(httpbin):
        r = http('--form', '--verbose', 'POST', httpbin.url + '/post',
                 'test-file@%s' % FILE_PATH_ARG, 'foo=bar')
        assert HTTP_OK in r
        assert 'Content-Disposition: form-data; name="foo"' in r
        assert 'Content-Disposition: form-data; name="test-file";' \
               ' filename="%s"' % os.path.basename(FILE_PATH) in r
        assert FILE_CONTENT in r
        assert '"foo": "bar"' in r
        assert 'Content-Type: text/plain' in r

    @staticmethod
    def test_upload_multiple_fields_with_the_same_name(httpbin):
        r = http('--form', '--verbose', 'POST', httpbin.url + '/post',
                 'test-file@%s' % FILE_PATH_ARG,
                 'test-file@%s' % FILE_PATH_ARG)
        assert HTTP_OK in r
        assert r.count('Content-Disposition: form-data; name="test-file";'
                       ' filename="%s"' % os.path.basename(FILE_PATH)) == 2
        # Should be 4, but is 3 because httpbin
        # doesn't seem to support filed field lists
        assert r.count(FILE_CONTENT) in [3, 4]
        assert r.count('Content-Type: text/plain') == 2


class TestRequestBodyFromFilePath:
    """
    `http URL @file'

    """

    @staticmethod
    def test_request_body_from_file_by_path(httpbin):
        r = http('--verbose',
                 'POST', httpbin.url + '/post', '@' + FILE_PATH_ARG)
        assert HTTP_OK in r
        assert FILE_CONTENT in r, r
        assert '"Content-Type": "text/plain"' in r

    @staticmethod
    def test_request_body_from_file_by_path_with_explicit_content_type(
            httpbin):
        r = http('--verbose',
                 'POST', httpbin.url + '/post', '@' + FILE_PATH_ARG,
                 'Content-Type:text/plain; charset=utf8')
        assert HTTP_OK in r
        assert FILE_CONTENT in r
        assert 'Content-Type: text/plain; charset=utf8' in r

    @staticmethod
    def test_request_body_from_file_by_path_no_field_name_allowed(
            httpbin):
        env = MockEnvironment(stdin_isatty=True)
        r = http('POST', httpbin.url + '/post', 'field-name@' + FILE_PATH_ARG,
                 env=env, tolerate_error_exit_status=True)
        assert 'perhaps you meant --form?' in r.stderr

    @staticmethod
    def test_request_body_from_file_by_path_no_data_items_allowed(
            httpbin):
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
