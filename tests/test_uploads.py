import os

from httpie.input import ParseError
from tests import (
    BaseTestCase, TestEnvironment, http, httpbin,
    FILE_PATH_ARG, FILE_PATH, OK, FILE_CONTENT,
)


class MultipartFormDataFileUploadTest(BaseTestCase):

    def test_non_existent_file_raises_parse_error(self):
        self.assertRaises(ParseError, http,
            '--form',
            'POST',
            httpbin('/post'),
            'foo@/__does_not_exist__',
        )

    def test_upload_ok(self):
        r = http(
            '--form',
            '--verbose',
            'POST',
            httpbin('/post'),
            'test-file@%s' % FILE_PATH_ARG,
            'foo=bar'
        )

        self.assertIn(OK, r)
        self.assertIn('Content-Disposition: form-data; name="foo"', r)
        self.assertIn('Content-Disposition: form-data; name="test-file";'
                      ' filename="%s"' % os.path.basename(FILE_PATH), r)
        #noinspection PyUnresolvedReferences
        self.assertEqual(r.count(FILE_CONTENT), 2)
        self.assertIn('"foo": "bar"', r)


class RequestBodyFromFilePathTest(BaseTestCase):
    """
    `http URL @file'

    """
    def test_request_body_from_file_by_path(self):
        r = http(
            '--verbose',
            'POST',
            httpbin('/post'),
            '@' + FILE_PATH_ARG
        )
        self.assertIn(OK, r)
        self.assertIn(FILE_CONTENT, r)
        self.assertIn('"Content-Type": "text/plain"', r)

    def test_request_body_from_file_by_path_with_explicit_content_type(self):
        r = http(
            'POST',
            httpbin('/post'),
            '@' + FILE_PATH_ARG,
            'Content-Type:x-foo/bar'
        )
        self.assertIn(OK, r)
        self.assertIn(FILE_CONTENT, r)
        self.assertIn('"Content-Type": "x-foo/bar"', r)

    def test_request_body_from_file_by_path_no_field_name_allowed(self):
        env = TestEnvironment(stdin_isatty=True)
        r = http(
            'POST',
            httpbin('/post'),
            'field-name@' + FILE_PATH_ARG,
            env=env
        )
        self.assertIn('perhaps you meant --form?', r.stderr)

    def test_request_body_from_file_by_path_no_data_items_allowed(self):
        r = http(
            'POST',
            httpbin('/post'),
            '@' + FILE_PATH_ARG,
            'foo=bar',
            env=TestEnvironment(stdin_isatty=False)
        )
        self.assertIn('cannot be mixed', r.stderr)
