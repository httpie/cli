import os

import pytest

from httpie.input import ParseError
from tests import TestEnvironment, http, httpbin, HTTP_OK
from tests.fixtures import FILE_PATH_ARG, FILE_PATH, FILE_CONTENT


class TestMultipartFormDataFileUpload:
    def test_non_existent_file_raises_parse_error(self):
        with pytest.raises(ParseError):
            http('--form', 'POST', httpbin('/post'), 'foo@/__does_not_exist__')

    def test_upload_ok(self):
        r = http('--form', '--verbose', 'POST', httpbin('/post'),
                 'test-file@%s' % FILE_PATH_ARG, 'foo=bar')
        assert HTTP_OK in r
        assert 'Content-Disposition: form-data; name="foo"' in r
        assert 'Content-Disposition: form-data; name="test-file";' \
               ' filename="%s"' % os.path.basename(FILE_PATH) in r
        assert r.count(FILE_CONTENT) == 2
        assert '"foo": "bar"' in r


class TestRequestBodyFromFilePath:
    """
    `http URL @file'

    """

    def test_request_body_from_file_by_path(self):
        r = http('--verbose', 'POST', httpbin('/post'), '@' + FILE_PATH_ARG)
        assert HTTP_OK in r
        assert FILE_CONTENT in r
        assert '"Content-Type": "text/plain"' in r

    def test_request_body_from_file_by_path_with_explicit_content_type(self):
        r = http('POST', httpbin('/post'), '@' + FILE_PATH_ARG,
                 'Content-Type:x-foo/bar')
        assert HTTP_OK in r
        assert FILE_CONTENT in r
        assert '"Content-Type": "x-foo/bar"' in r

    def test_request_body_from_file_by_path_no_field_name_allowed(self):
        env = TestEnvironment(stdin_isatty=True)
        r = http('POST', httpbin('/post'), 'field-name@' + FILE_PATH_ARG,
                 env=env, error_exit_ok=True)
        assert 'perhaps you meant --form?' in r.stderr

    def test_request_body_from_file_by_path_no_data_items_allowed(self):
        env = TestEnvironment(stdin_isatty=False)
        r = http('POST', httpbin('/post'), '@' + FILE_PATH_ARG, 'foo=bar',
                 env=env, error_exit_ok=True)
        assert 'cannot be mixed' in r.stderr
