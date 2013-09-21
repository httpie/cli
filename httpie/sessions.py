"""Persistent, JSON-serialized sessions.

"""
import re
import os

import requests
from requests.cookies import RequestsCookieJar, create_cookie

from .compat import urlsplit
from .config import BaseConfigDict, DEFAULT_CONFIG_DIR
from httpie.plugins import plugin_manager


SESSIONS_DIR_NAME = 'sessions'
DEFAULT_SESSIONS_DIR = os.path.join(DEFAULT_CONFIG_DIR, SESSIONS_DIR_NAME)
VALID_SESSION_NAME_PATTERN = re.compile('^[a-zA-Z0-9_.-]+$')
# Request headers starting with these prefixes won't be stored in sessions.
# They are specific to each request.
# http://en.wikipedia.org/wiki/List_of_HTTP_header_fields#Requests
SESSION_IGNORED_HEADER_PREFIXES = ['Content-', 'If-']


def get_response(session_name, requests_kwargs, config_dir, args,
                 read_only=False):
    """Like `client.get_response`, but applies permanent
    aspects of the session to the request.

    """
    if os.path.sep in session_name:
        path = os.path.expanduser(session_name)
    else:
        hostname = (
            requests_kwargs['headers'].get('Host', None)
            or urlsplit(requests_kwargs['url']).netloc.split('@')[-1]
        )

        assert re.match('^[a-zA-Z0-9_.:-]+$', hostname)

        # host:port => host_port
        hostname = hostname.replace(':', '_')
        path = os.path.join(config_dir,
                            SESSIONS_DIR_NAME,
                            hostname,
                            session_name + '.json')

    session = Session(path)
    session.load()

    request_headers = requests_kwargs.get('headers', {})
    requests_kwargs['headers'] = dict(session.headers, **request_headers)
    session.update_headers(request_headers)

    if args.auth:
        session.auth = {
            'type': args.auth_type,
            'username': args.auth.key,
            'password': args.auth.value,
        }
    elif session.auth:
        requests_kwargs['auth'] = session.auth

    requests_session = requests.Session()
    requests_session.cookies = session.cookies

    try:
        response = requests_session.request(**requests_kwargs)
    except Exception:
        raise
    else:
        # Existing sessions with `read_only=True` don't get updated.
        if session.is_new or not read_only:
            session.cookies = requests_session.cookies
            session.save()
        return response


class Session(BaseConfigDict):
    helpurl = 'https://github.com/jkbr/httpie#sessions'
    about = 'HTTPie session file'

    def __init__(self, path, *args, **kwargs):
        super(Session, self).__init__(*args, **kwargs)
        self._path = path
        self['headers'] = {}
        self['cookies'] = {}
        self['auth'] = {
            'type': None,
            'username': None,
            'password': None
        }

    def _get_path(self):
        return self._path

    def update_headers(self, request_headers):
        """
        Update the session headers with the request ones while ignoring
        certain name prefixes.

        :type request_headers: dict

        """
        for name, value in request_headers.items():

            if name == 'User-Agent' and value.startswith('HTTPie/'):
                continue

            for prefix in SESSION_IGNORED_HEADER_PREFIXES:
                if name.lower().startswith(prefix.lower()):
                    break
            else:
                self['headers'][name] = value

    @property
    def headers(self):
        return self['headers']

    @property
    def cookies(self):
        jar = RequestsCookieJar()
        for name, cookie_dict in self['cookies'].items():
            jar.set_cookie(create_cookie(
                name, cookie_dict.pop('value'), **cookie_dict))
        jar.clear_expired_cookies()
        return jar

    @cookies.setter
    def cookies(self, jar):
        """
        :type jar: CookieJar
        """
        # http://docs.python.org/2/library/cookielib.html#cookie-objects
        stored_attrs = ['value', 'path', 'secure', 'expires']
        self['cookies'] = {}
        for cookie in jar:
            self['cookies'][cookie.name] = dict(
                (attname, getattr(cookie, attname))
                for attname in stored_attrs
            )

    @property
    def auth(self):
        auth = self.get('auth', None)
        if not auth or not auth['type']:
            return
        auth_plugin = plugin_manager.get_auth_plugin(auth['type'])()
        return auth_plugin.get_auth(auth['username'], auth['password'])

    @auth.setter
    def auth(self, auth):
        assert set(['type', 'username', 'password']) == set(auth.keys())
        self['auth'] = auth
