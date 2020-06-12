# coding=utf-8
import os
import shutil
import sys
import json
from datetime import datetime
from tempfile import gettempdir

import pytest

from httpie.sessions import Session
from httpie.plugins.builtin import HTTPBasicAuth
from httpie.utils import get_expired_cookies
from utils import MockEnvironment, mk_config_dir, http, HTTP_OK
from fixtures import UNICODE


class SessionTestBase:

    def start_session(self, httpbin):
        """Create and reuse a unique config dir for each test."""
        self.config_dir = mk_config_dir()

    def teardown_method(self, method):
        shutil.rmtree(self.config_dir)

    def env(self):
        """
        Return an environment.

        Each environment created within a test method
        will share the same config_dir. It is necessary
        for session files being reused.

        """
        return MockEnvironment(config_dir=self.config_dir)


class TestSessionFlow(SessionTestBase):
    """
    These tests start with an existing session created in `setup_method()`.

    """

    def start_session(self, httpbin):
        """
        Start a full-blown session with a custom request header,
        authorization, and response cookies.

        """
        super().start_session(httpbin)
        r1 = http(
            '--follow',
            '--session=test',
            '--auth=username:password',
            'GET',
            httpbin.url + '/cookies/set?hello=world',
            'Hello:World',
            env=self.env()
        )
        assert HTTP_OK in r1

    def test_session_created_and_reused(self, httpbin):
        self.start_session(httpbin)
        # Verify that the session created in setup_method() has been used.
        r2 = http('--session=test',
                  'GET', httpbin.url + '/get', env=self.env())
        assert HTTP_OK in r2
        assert r2.json['headers']['Hello'] == 'World'
        assert r2.json['headers']['Cookie'] == 'hello=world'
        assert 'Basic ' in r2.json['headers']['Authorization']

    def test_session_update(self, httpbin):
        self.start_session(httpbin)
        # Get a response to a request from the original session.
        r2 = http('--session=test', 'GET', httpbin.url + '/get',
                  env=self.env())
        assert HTTP_OK in r2

        # Make a request modifying the session data.
        r3 = http('--follow', '--session=test', '--auth=username:password2',
                  'GET', httpbin.url + '/cookies/set?hello=world2',
                  'Hello:World2',
                  env=self.env())
        assert HTTP_OK in r3

        # Get a response to a request from the updated session.
        r4 = http('--session=test', 'GET', httpbin.url + '/get',
                  env=self.env())
        assert HTTP_OK in r4
        assert r4.json['headers']['Hello'] == 'World2'
        assert r4.json['headers']['Cookie'] == 'hello=world2'
        assert (r2.json['headers']['Authorization']
                != r4.json['headers']['Authorization'])

    def test_session_read_only(self, httpbin):
        self.start_session(httpbin)
        # Get a response from the original session.
        r2 = http('--session=test', 'GET', httpbin.url + '/get',
                  env=self.env())
        assert HTTP_OK in r2

        # Make a request modifying the session data but
        # with --session-read-only.
        r3 = http('--follow', '--session-read-only=test',
                  '--auth=username:password2', 'GET',
                  httpbin.url + '/cookies/set?hello=world2', 'Hello:World2',
                  env=self.env())
        assert HTTP_OK in r3

        # Get a response from the updated session.
        r4 = http('--session=test', 'GET', httpbin.url + '/get',
                  env=self.env())
        assert HTTP_OK in r4

        # Origin can differ on Travis.
        del r2.json['origin'], r4.json['origin']
        # Different for each request.

        # Should be the same as before r3.
        assert r2.json == r4.json


class TestSession(SessionTestBase):
    """Stand-alone session tests."""

    def test_session_ignored_header_prefixes(self, httpbin):
        self.start_session(httpbin)
        r1 = http('--session=test', 'GET', httpbin.url + '/get',
                  'Content-Type: text/plain',
                  'If-Unmodified-Since: Sat, 29 Oct 1994 19:43:31 GMT',
                  env=self.env())
        assert HTTP_OK in r1
        r2 = http('--session=test', 'GET', httpbin.url + '/get',
                  env=self.env())
        assert HTTP_OK in r2
        assert 'Content-Type' not in r2.json['headers']
        assert 'If-Unmodified-Since' not in r2.json['headers']

    def test_session_by_path(self, httpbin):
        self.start_session(httpbin)
        session_path = self.config_dir / 'session-by-path.json'
        r1 = http('--session', str(session_path), 'GET', httpbin.url + '/get',
                  'Foo:Bar', env=self.env())
        assert HTTP_OK in r1

        r2 = http('--session', str(session_path), 'GET', httpbin.url + '/get',
                  env=self.env())
        assert HTTP_OK in r2
        assert r2.json['headers']['Foo'] == 'Bar'

    def test_session_unicode(self, httpbin):
        self.start_session(httpbin)

        r1 = http('--session=test', u'--auth=test:' + UNICODE,
                  'GET', httpbin.url + '/get', u'Test:%s' % UNICODE,
                  env=self.env())
        assert HTTP_OK in r1

        r2 = http('--session=test', '--verbose', 'GET',
                  httpbin.url + '/get', env=self.env())
        assert HTTP_OK in r2

        # FIXME: Authorization *sometimes* is not present on Python3
        assert (r2.json['headers']['Authorization']
                == HTTPBasicAuth.make_header(u'test', UNICODE))
        # httpbin doesn't interpret utf8 headers
        assert UNICODE in r2

    def test_session_default_header_value_overwritten(self, httpbin):
        self.start_session(httpbin)
        # https://github.com/jakubroztocil/httpie/issues/180
        r1 = http('--session=test',
                  httpbin.url + '/headers', 'User-Agent:custom',
                  env=self.env())
        assert HTTP_OK in r1
        assert r1.json['headers']['User-Agent'] == 'custom'

        r2 = http('--session=test', httpbin.url + '/headers', env=self.env())
        assert HTTP_OK in r2
        assert r2.json['headers']['User-Agent'] == 'custom'

    def test_download_in_session(self, httpbin):
        # https://github.com/jakubroztocil/httpie/issues/412
        self.start_session(httpbin)
        cwd = os.getcwd()
        os.chdir(gettempdir())
        try:
            http('--session=test', '--download',
                 httpbin.url + '/get', env=self.env())
        finally:
            os.chdir(cwd)

    @pytest.mark.parametrize(
        argnames=['initial_cookies', 'expired_cookies'],
        argvalues=[
            ({'id': {'value': 123}}, {'name': 'id'}),
            ({'id': {'value': 123}}, {'name': 'token'})
        ]
    )
    def test_removes_expired_cookies_from_session_obj(self, initial_cookies, expired_cookies, httpbin):
        self.start_session(httpbin)
        session = Session(self.config_dir)
        session['cookies'] = initial_cookies
        session.remove_expired_cookies([expired_cookies])
        assert expired_cookies['name'] not in session.cookies

    def test_expired_cookies(self, httpbin):
        self.start_session(httpbin)
        orig_session = {
            'cookies': {
                'to_expire': {
                    'value': 'foo'
                },
                'to_stay': {
                    'value': 'foo'
                },
            }
        }

        session_path = mk_config_dir() / 'test-session.json'
        session_path.write_text(json.dumps(orig_session))

        r = http(
            '--session', str(session_path),
            '--print=H',
            httpbin.url + '/cookies/delete?to_expire',
        )
        assert 'Cookie: to_expire=foo; to_stay=foo' in r

        updated_session = json.loads(session_path.read_text())
        assert 'to_stay' in updated_session['cookies']
        assert 'to_expire' not in updated_session['cookies']


class TestGetExpiredCookiesUtil:

    @pytest.mark.parametrize(
        argnames=['raw_header', 'timestamp', 'expected'],
        argvalues=[
            ([('X-Powered-By', 'Express'),
              ('Set-Cookie', 'hello=world; Path=/; Expires=Thu, 01-Jan-1970 00:00:00 GMT; HttpOnly'),
                ('Content-Type', 'application/json; charset=utf-8'), ('Content-Length', '35'), ('ETag', 'W/"23-VhiALGYCMivVwSJRaovse0pz+QE"'),
              ('Date', 'Thu, 01-Jan-1970 00:00:00 GMT'), ('Connection', 'keep-alive')],
                None,
                [{'name': 'hello', 'path': '/'}]),
            ([('X-Powered-By', 'Express'),
              ('Set-Cookie', 'hello=world; Path=/; Expires=Thu, 01-Jan-1970 00:00:00 GMT; HttpOnly'),
                ('Set-Cookie', 'pea=pod; Path=/ab; Expires=Thu, 01-Jan-1970 00:00:00 GMT; HttpOnly'),
                ('Content-Type', 'application/json; charset=utf-8'), ('Content-Length', '35'), ('ETag', 'W/"23-VhiALGYCMivVwSJRaovse0pz+QE"'),
              ('Date', 'Thu, 01-Jan-1970 00:00:00 GMT'), ('Connection', 'keep-alive')],
                None,
                [{'name': 'hello', 'path': '/'}, {'name': 'pea', 'path': '/ab'}]),
            ([('X-Powered-By', 'Express'),
              ('Set-Cookie', 'hello=world; Path=/; Expires=Fri, 12 Jun 2020 12:28:55 GMT; HttpOnly'),
                ('Content-Type', 'application/json; charset=utf-8'), ('Content-Length', '35'), ('ETag', 'W/"23-VhiALGYCMivVwSJRaovse0pz+QE"'),
                ('Date', 'Fri, 12 Jun 2020 14:42:15 GMT'), ('Connection', 'keep-alive')],
             datetime(2020, 6, 11).timestamp(),
                [])
        ]
    )
    def test_get_expired_cookies_manages_multiple_cookie_headers(self, raw_header, timestamp, expected):
        assert get_expired_cookies(raw_header, curr_timestamp=timestamp) == expected
