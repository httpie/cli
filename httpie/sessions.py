"""Persistent, JSON-serialized sessions.

"""
import argparse
import re
import os
from pathlib import Path
from typing import Optional, Union
from urllib.parse import urlsplit

from requests.auth import AuthBase
from requests.cookies import RequestsCookieJar, create_cookie
import requests

from httpie.config import BaseConfigDict, DEFAULT_CONFIG_DIR
from httpie.plugins import plugin_manager


SESSIONS_DIR_NAME = 'sessions'
DEFAULT_SESSIONS_DIR = DEFAULT_CONFIG_DIR / SESSIONS_DIR_NAME
VALID_SESSION_NAME_PATTERN = re.compile('^[a-zA-Z0-9_.-]+$')
# Request headers starting with these prefixes won't be stored in sessions.
# They are specific to each request.
# https://en.wikipedia.org/wiki/List_of_HTTP_header_fields#Requests
SESSION_IGNORED_HEADER_PREFIXES = ['Content-', 'If-']


def get_response(
    requests_session: requests.Session,
    session_name: str,
    config_dir: Path,
    args: argparse.Namespace,
    read_only=False,
) -> requests.Response:
    """Like `client.get_responses`, but applies permanent
    aspects of the session to the request.

    """
    from .client import get_requests_kwargs, dump_request
    if os.path.sep in session_name:
        path = os.path.expanduser(session_name)
    else:
        hostname = (args.headers.get('Host', None)
                    or urlsplit(args.url).netloc.split('@')[-1])
        if not hostname:
            # HACK/FIXME: httpie-unixsocket's URLs have no hostname.
            hostname = 'localhost'

        # host:port => host_port
        hostname = hostname.replace(':', '_')
        path = (
            config_dir / SESSIONS_DIR_NAME / hostname
            / (session_name + '.json')
        )

    session = Session(path)
    session.load()

    kwargs = get_requests_kwargs(args, base_headers=session.headers)
    if args.debug:
        dump_request(kwargs)
    session.update_headers(kwargs['headers'])

    if args.auth_plugin:
        session.auth = {
            'type': args.auth_plugin.auth_type,
            'raw_auth': args.auth_plugin.raw_auth,
        }
    elif session.auth:
        kwargs['auth'] = session.auth

    requests_session.cookies = session.cookies

    try:
        response = requests_session.request(**kwargs)
    except Exception:
        raise
    else:
        # Existing sessions with `read_only=True` don't get updated.
        if session.is_new() or not read_only:
            session.cookies = requests_session.cookies
            session.save()
        return response


class Session(BaseConfigDict):
    helpurl = 'https://httpie.org/doc#sessions'
    about = 'HTTPie session file'

    def __init__(self, path: Union[str, Path]):
        super().__init__()
        self._path = Path(path)
        self['headers'] = {}
        self['cookies'] = {}
        self['auth'] = {
            'type': None,
            'username': None,
            'password': None
        }

    def _get_path(self) -> Path:
        return self._path

    def update_headers(self, request_headers: dict):
        """
        Update the session headers with the request ones while ignoring
        certain name prefixes.

        :type request_headers: dict

        """
        for name, value in request_headers.items():

            if value is None:
                continue  # Ignore explicitly unset headers

            value = value.decode('utf8')
            if name == 'User-Agent' and value.startswith('HTTPie/'):
                continue

            for prefix in SESSION_IGNORED_HEADER_PREFIXES:
                if name.lower().startswith(prefix.lower()):
                    break
            else:
                self['headers'][name] = value

    @property
    def headers(self) -> dict:
        return self['headers']

    @property
    def cookies(self) -> RequestsCookieJar:
        jar = RequestsCookieJar()
        for name, cookie_dict in self['cookies'].items():
            jar.set_cookie(create_cookie(
                name, cookie_dict.pop('value'), **cookie_dict))
        jar.clear_expired_cookies()
        return jar

    @cookies.setter
    def cookies(self, jar: RequestsCookieJar):
        # https://docs.python.org/2/library/cookielib.html#cookie-objects
        stored_attrs = ['value', 'path', 'secure', 'expires']
        self['cookies'] = {}
        for cookie in jar:
            self['cookies'][cookie.name] = {
                attname: getattr(cookie, attname)
                for attname in stored_attrs
            }

    @property
    def auth(self) -> Optional[AuthBase]:
        auth = self.get('auth', None)
        if not auth or not auth['type']:
            return

        plugin = plugin_manager.get_auth_plugin(auth['type'])()

        credentials = {'username': None, 'password': None}
        try:
            # New style
            plugin.raw_auth = auth['raw_auth']
        except KeyError:
            # Old style
            credentials = {
                'username': auth['username'],
                'password': auth['password'],
            }
        else:
            if plugin.auth_parse:
                from httpie.cli.argtypes import parse_auth
                parsed = parse_auth(plugin.raw_auth)
                credentials = {
                    'username': parsed.key,
                    'password': parsed.value,
                }

        return plugin.get_auth(**credentials)

    @auth.setter
    def auth(self, auth: dict):
        assert {'type', 'raw_auth'} == auth.keys()
        self['auth'] = auth
