import json
import os
import shutil
from datetime import datetime
from unittest import mock

import pytest

from .fixtures import FILE_PATH_ARG, UNICODE
from httpie.encoding import UTF8
from httpie.plugins import AuthPlugin
from httpie.plugins.builtin import HTTPBasicAuth
from httpie.plugins.registry import plugin_manager
from httpie.sessions import Session
from httpie.utils import get_expired_cookies
from .test_auth_plugins import basic_auth
from .utils import HTTP_OK, MockEnvironment, http, mk_config_dir
from base64 import b64encode


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


class CookieTestBase:
    def setup_method(self, method):
        self.config_dir = mk_config_dir()

        orig_session = {
            'cookies': {
                'cookie1': {
                    'value': 'foo',
                },
                'cookie2': {
                    'value': 'foo',
                }
            }
        }
        self.session_path = self.config_dir / 'test-session.json'
        self.session_path.write_text(json.dumps(orig_session), encoding=UTF8)

    def teardown_method(self, method):
        shutil.rmtree(self.config_dir)


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

    def test_session_overwrite_header(self, httpbin):
        self.start_session(httpbin)

        r2 = http('--session=test', 'GET', httpbin.url + '/get',
                  'Hello:World2', env=self.env())
        assert HTTP_OK in r2
        assert r2.json['headers']['Hello'] == 'World2'

        r3 = http('--session=test', 'GET', httpbin.url + '/get',
                  'Hello:World2', 'Hello:World3', env=self.env())
        assert HTTP_OK in r3
        assert r3.json['headers']['Hello'] == 'World2,World3'

        r3 = http('--session=test', 'GET', httpbin.url + '/get',
                  'Hello:', 'Hello:World3', env=self.env())
        assert HTTP_OK in r3
        assert 'Hello' not in r3.json['headers']['Hello']


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

    def test_session_with_upload(self, httpbin):
        self.start_session(httpbin)
        r = http('--session=test', '--form', '--verbose', 'POST', httpbin.url + '/post',
                 f'test-file@{FILE_PATH_ARG}', 'foo=bar', env=self.env())
        assert HTTP_OK in r

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

    def test_session_with_cookie_followed_by_another_header(self, httpbin):
        """
        Make sure headers don’t get mutated — <https://github.com/httpie/httpie/issues/1126>
        """
        self.start_session(httpbin)
        session_data = {
            "headers": {
                "cookie": "...",
                "zzz": "..."
            }
        }
        session_path = self.config_dir / 'session-data.json'
        session_path.write_text(json.dumps(session_data))
        r = http('--session', str(session_path), 'GET', httpbin.url + '/get',
                 env=self.env())
        assert HTTP_OK in r
        assert 'Zzz' in r

    def test_session_unicode(self, httpbin):
        self.start_session(httpbin)

        r1 = http('--session=test', f'--auth=test:{UNICODE}',
                  'GET', httpbin.url + '/get', f'Test:{UNICODE}',
                  env=self.env())
        assert HTTP_OK in r1

        r2 = http('--session=test', '--verbose', 'GET',
                  httpbin.url + '/get', env=self.env())
        assert HTTP_OK in r2

        # FIXME: Authorization *sometimes* is not present
        assert (r2.json['headers']['Authorization']
                == HTTPBasicAuth.make_header('test', UNICODE))
        # httpbin doesn't interpret UTF-8 headers
        assert UNICODE in r2

    def test_session_default_header_value_overwritten(self, httpbin):
        self.start_session(httpbin)
        # https://github.com/httpie/httpie/issues/180
        r1 = http('--session=test',
                  httpbin.url + '/headers', 'User-Agent:custom',
                  env=self.env())
        assert HTTP_OK in r1
        assert r1.json['headers']['User-Agent'] == 'custom'

        r2 = http('--session=test', httpbin.url + '/headers', env=self.env())
        assert HTTP_OK in r2
        assert r2.json['headers']['User-Agent'] == 'custom'

    def test_download_in_session(self, tmp_path, httpbin):
        # https://github.com/httpie/httpie/issues/412
        self.start_session(httpbin)
        cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            http('--session=test', '--download',
                 httpbin.url + '/get', env=self.env())
        finally:
            os.chdir(cwd)

    @pytest.mark.parametrize(
        'auth_require_param, auth_parse_param',
        [
            (False, False),
            (False, True),
            (True, False)
        ]
    )
    def test_auth_type_reused_in_session(self, auth_require_param, auth_parse_param, httpbin):
        self.start_session(httpbin)
        session_path = self.config_dir / 'test-session.json'

        header = 'Custom dXNlcjpwYXNzd29yZA'

        class Plugin(AuthPlugin):
            auth_type = 'test-reused'
            auth_require = auth_require_param
            auth_parse = auth_parse_param

            def get_auth(self, username=None, password=None):
                return basic_auth(header=f'{header}==')

        plugin_manager.register(Plugin)

        r1 = http(
            '--session', str(session_path),
            httpbin + '/basic-auth/user/password',
            '--auth-type',
            Plugin.auth_type,
            '--auth', 'user:password',
            '--print=H',
        )

        r2 = http(
            '--session', str(session_path),
            httpbin + '/basic-auth/user/password',
            '--print=H',
        )
        assert f'Authorization: {header}' in r1
        assert f'Authorization: {header}' in r2
        plugin_manager.unregister(Plugin)

    def test_auth_plugin_prompt_password_in_session(self, httpbin):
        self.start_session(httpbin)
        session_path = self.config_dir / 'test-session.json'

        class Plugin(AuthPlugin):
            auth_type = 'test-prompted'

            def get_auth(self, username=None, password=None):
                basic_auth_header = "Basic " + b64encode(self.raw_auth.encode()).strip().decode('latin1')
                return basic_auth(basic_auth_header)

        plugin_manager.register(Plugin)

        with mock.patch(
            'httpie.cli.argtypes.AuthCredentials._getpass',
            new=lambda self, prompt: 'password'
        ):
            r1 = http(
                '--session', str(session_path),
                httpbin + '/basic-auth/user/password',
                '--auth-type',
                Plugin.auth_type,
                '--auth', 'user',
            )

        r2 = http(
            '--session', str(session_path),
            httpbin + '/basic-auth/user/password',
        )
        assert HTTP_OK in r1
        assert HTTP_OK in r2

        # additional test for issue: https://github.com/httpie/httpie/issues/1098
        with open(session_path) as session_file:
            session_file_lines = ''.join(session_file.readlines())
            assert "\"type\": \"test-prompted\"" in session_file_lines
            assert "\"raw_auth\": \"user:password\"" in session_file_lines

        plugin_manager.unregister(Plugin)

    def test_auth_type_stored_in_session_file(self, httpbin):
        self.config_dir = mk_config_dir()
        self.session_path = self.config_dir / 'test-session.json'

        class Plugin(AuthPlugin):
            auth_type = 'test-saved'
            auth_require = True

            def get_auth(self, username=None, password=None):
                return basic_auth()

        plugin_manager.register(Plugin)
        http('--session', str(self.session_path),
             httpbin + '/basic-auth/user/password',
             '--auth-type',
             Plugin.auth_type,
             '--auth', 'user:password',
             )
        updated_session = json.loads(self.session_path.read_text(encoding=UTF8))
        assert updated_session['auth']['type'] == 'test-saved'
        assert updated_session['auth']['raw_auth'] == "user:password"
        plugin_manager.unregister(Plugin)


class TestExpiredCookies(CookieTestBase):

    @pytest.mark.parametrize(
        'initial_cookie, expired_cookie',
        [
            ({'id': {'value': 123}}, 'id'),
            ({'id': {'value': 123}}, 'token')
        ]
    )
    def test_removes_expired_cookies_from_session_obj(self, initial_cookie, expired_cookie, httpbin):
        session = Session(self.config_dir)
        session['cookies'] = initial_cookie
        session.remove_cookies([expired_cookie])
        assert expired_cookie not in session.cookies

    def test_expired_cookies(self, httpbin):
        r = http(
            '--session', str(self.session_path),
            '--print=H',
            httpbin.url + '/cookies/delete?cookie2',
        )
        assert 'Cookie: cookie1=foo; cookie2=foo' in r

        updated_session = json.loads(self.session_path.read_text(encoding=UTF8))
        assert 'cookie1' in updated_session['cookies']
        assert 'cookie2' not in updated_session['cookies']

    def test_get_expired_cookies_using_max_age(self):
        cookies = 'one=two; Max-Age=0; path=/; domain=.tumblr.com; HttpOnly'
        expected_expired = [
            {'name': 'one', 'path': '/'}
        ]
        assert get_expired_cookies(cookies, now=None) == expected_expired

    @pytest.mark.parametrize(
        'cookies, now, expected_expired',
        [
            (
                'hello=world; Path=/; Expires=Thu, 01-Jan-1970 00:00:00 GMT; HttpOnly',
                None,
                [
                    {
                        'name': 'hello',
                        'path': '/'
                    }
                ]
            ),
            (
                (
                    'hello=world; Path=/; Expires=Thu, 01-Jan-1970 00:00:00 GMT; HttpOnly, '
                    'pea=pod; Path=/ab; Expires=Thu, 01-Jan-1970 00:00:00 GMT; HttpOnly'
                ),
                None,
                [
                    {'name': 'hello', 'path': '/'},
                    {'name': 'pea', 'path': '/ab'}
                ]
            ),
            (
                # Checks we gracefully ignore expires date in invalid format.
                # <https://github.com/httpie/httpie/issues/963>
                'pfg=; Expires=Sat, 19-Sep-2020 06:58:14 GMT+0000; Max-Age=0; path=/; domain=.tumblr.com; secure; HttpOnly',
                None,
                []
            ),
            (
                'hello=world; Path=/; Expires=Fri, 12 Jun 2020 12:28:55 GMT; HttpOnly',
                datetime(2020, 6, 11).timestamp(),
                []
            ),
        ]
    )
    def test_get_expired_cookies_manages_multiple_cookie_headers(self, cookies, now, expected_expired):
        assert get_expired_cookies(cookies, now=now) == expected_expired


class TestCookieStorage(CookieTestBase):

    @pytest.mark.parametrize(
        'new_cookies, new_cookies_dict, expected',
        [(
            'new=bar',
            {'new': 'bar'},
            'cookie1=foo; cookie2=foo; new=bar'
        ),
            (
            'new=bar;chocolate=milk',
            {'new': 'bar', 'chocolate': 'milk'},
            'chocolate=milk; cookie1=foo; cookie2=foo; new=bar'
        ),
            (
            'new=bar; chocolate=milk',
            {'new': 'bar', 'chocolate': 'milk'},
            'chocolate=milk; cookie1=foo; cookie2=foo; new=bar'
        ),
            (
            'new=bar;; chocolate=milk;;;',
            {'new': 'bar', 'chocolate': 'milk'},
            'cookie1=foo; cookie2=foo; new=bar'
        ),
            (
            'new=bar; chocolate=milk;;;',
            {'new': 'bar', 'chocolate': 'milk'},
            'chocolate=milk; cookie1=foo; cookie2=foo; new=bar'
        )
        ]
    )
    def test_existing_and_new_cookies_sent_in_request(self, new_cookies, new_cookies_dict, expected, httpbin):
        r = http(
            '--session', str(self.session_path),
            '--print=H',
            httpbin.url,
            'Cookie:' + new_cookies,
        )
        # Note: cookies in response are in alphabetical order
        assert f'Cookie: {expected}' in r

        updated_session = json.loads(self.session_path.read_text(encoding=UTF8))
        for name, value in new_cookies_dict.items():
            assert name, value in updated_session['cookies']
            assert 'Cookie' not in updated_session['headers']

    @pytest.mark.parametrize(
        'cli_cookie, set_cookie, expected',
        [(
            '',
            '/cookies/set/cookie1/bar',
            'bar'
        ),
            (
            'cookie1=not_foo',
            '/cookies/set/cookie1/bar',
            'bar'
        ),
            (
            'cookie1=not_foo',
            '',
            'not_foo'
        ),
            (
            '',
            '',
            'foo'
        )
        ]
    )
    def test_cookie_storage_priority(self, cli_cookie, set_cookie, expected, httpbin):
        """
        Expected order of priority for cookie storage in session file:
        1. set-cookie (from server)
        2. command line arg
        3. cookie already stored in session file
        """
        http(
            '--session', str(self.session_path),
            httpbin.url + set_cookie,
            'Cookie:' + cli_cookie,
        )
        updated_session = json.loads(self.session_path.read_text(encoding=UTF8))

        assert updated_session['cookies']['cookie1']['value'] == expected
