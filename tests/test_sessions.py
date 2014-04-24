import os
import shutil

from tests import (
    BaseTestCase, TestEnvironment,
    mk_config_dir, http, httpbin,
    OK,
)


class SessionsTest(BaseTestCase):

    @property
    def env(self):
        return TestEnvironment(config_dir=self.config_dir)

    def setUp(self):
        # Start a full-blown session with a custom request header,
        # authorization, and response cookies.
        self.config_dir = mk_config_dir()
        r = http(
            '--follow',
            '--session=test',
            '--auth=username:password',
            'GET',
            httpbin('/cookies/set?hello=world'),
            'Hello:World',
            env=self.env
        )
        self.assertIn(OK, r)

    def tearDown(self):
        shutil.rmtree(self.config_dir)

    def test_session_create(self):
        # Verify that the session has been created.
        r = http(
            '--session=test',
            'GET',
            httpbin('/get'),
            env=self.env
        )
        self.assertIn(OK, r)

        self.assertEqual(r.json['headers']['Hello'], 'World')
        self.assertEqual(r.json['headers']['Cookie'], 'hello=world')
        self.assertIn('Basic ', r.json['headers']['Authorization'])

    def test_session_ignored_header_prefixes(self):
        r = http(
            '--session=test',
            'GET',
            httpbin('/get'),
            'Content-Type: text/plain',
            'If-Unmodified-Since: Sat, 29 Oct 1994 19:43:31 GMT',
            env=self.env
        )
        self.assertIn(OK, r)

        r2 = http(
            '--session=test',
            'GET',
            httpbin('/get')
        )
        self.assertIn(OK, r2)
        self.assertNotIn('Content-Type', r2.json['headers'])
        self.assertNotIn('If-Unmodified-Since', r2.json['headers'])

    def test_session_update(self):
        # Get a response to a request from the original session.
        r1 = http(
            '--session=test',
            'GET',
            httpbin('/get'),
            env=self.env
        )
        self.assertIn(OK, r1)

        # Make a request modifying the session data.
        r2 = http(
            '--follow',
            '--session=test',
            '--auth=username:password2',
            'GET',
            httpbin('/cookies/set?hello=world2'),
            'Hello:World2',
            env=self.env
        )
        self.assertIn(OK, r2)

        # Get a response to a request from the updated session.
        r3 = http(
            '--session=test',
            'GET',
            httpbin('/get'),
            env=self.env
        )
        self.assertIn(OK, r3)

        self.assertEqual(r3.json['headers']['Hello'], 'World2')
        self.assertEqual(r3.json['headers']['Cookie'], 'hello=world2')
        self.assertNotEqual(r1.json['headers']['Authorization'],
                            r3.json['headers']['Authorization'])

    def test_session_read_only(self):
        # Get a response from the original session.
        r1 = http(
            '--session=test',
            'GET',
            httpbin('/get'),
            env=self.env
        )
        self.assertIn(OK, r1)

        # Make a request modifying the session data but
        # with --session-read-only.
        r2 = http(
            '--follow',
            '--session-read-only=test',
            '--auth=username:password2',
            'GET',
            httpbin('/cookies/set?hello=world2'),
            'Hello:World2',
            env=self.env
        )
        self.assertIn(OK, r2)

        # Get a response from the updated session.
        r3 = http(
            '--session=test',
            'GET',
            httpbin('/get'),
            env=self.env
        )
        self.assertIn(OK, r3)

        # Origin can differ on Travis.
        del r1.json['origin'], r3.json['origin']
        # Different for each request.
        del r1.json['headers']['X-Request-Id'], \
            r3.json['headers']['X-Request-Id']
        # Should be the same as before r2.
        self.assertDictEqual(r1.json, r3.json)

    def test_session_by_path(self):
        session_path = os.path.join(self.config_dir, 'session-by-path.json')

        r1 = http(
            '--session=' + session_path,
            'GET',
            httpbin('/get'),
            'Foo:Bar',
            env=self.env
        )
        self.assertIn(OK, r1)

        r2 = http(
            '--session=' + session_path,
            'GET',
            httpbin('/get'),
            env=self.env
        )
        self.assertIn(OK, r2)

        self.assertEqual(r2.json['headers']['Foo'], 'Bar')
