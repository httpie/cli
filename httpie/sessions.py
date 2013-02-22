"""Persistent, JSON-serialized sessions.

"""
import re
import os
import glob
import errno
import shutil

import requests
from requests.cookies import RequestsCookieJar, create_cookie
from requests.auth import HTTPBasicAuth, HTTPDigestAuth

from .compat import urlsplit
from .config import BaseConfigDict, DEFAULT_CONFIG_DIR


SESSIONS_DIR_NAME = 'sessions'
DEFAULT_SESSIONS_DIR = os.path.join(DEFAULT_CONFIG_DIR, SESSIONS_DIR_NAME)


def get_response(name, request_kwargs, config_dir, read_only=False):
    """Like `client.get_response`, but applies permanent
    aspects of the session to the request.

    """
    sessions_dir = os.path.join(config_dir, SESSIONS_DIR_NAME)
    host = Host(
        root_dir=sessions_dir,
        name=request_kwargs['headers'].get('Host', None)
             or urlsplit(request_kwargs['url']).netloc.split('@')[-1]
    )
    session = Session(host, name)
    session.load()

    # Update session headers with the request headers.
    session['headers'].update(request_kwargs.get('headers', {}))
    # Use the merged headers for the request
    request_kwargs['headers'] = session['headers']

    auth = request_kwargs.get('auth', None)
    if auth:
        session.auth = auth
    elif session.auth:
        request_kwargs['auth'] = session.auth

    requests_session = requests.Session()
    requests_session.cookies = session.cookies

    try:
        response = requests_session.request(**request_kwargs)
    except Exception:
        raise
    else:
        # Existing sessions with `read_only=True` don't get updated.
        if session.is_new or not read_only:
            session.cookies = requests_session.cookies
            session.save()
        return response


class Host(object):
    """A host is a per-host directory on the disk containing sessions files."""

    VALID_NAME_PATTERN = re.compile('^[a-zA-Z0-9_.:-]+$')

    def __init__(self, name, root_dir=DEFAULT_SESSIONS_DIR):
        assert self.VALID_NAME_PATTERN.match(name)
        self.name = name
        self.root_dir = root_dir

    def __iter__(self):
        """Return an iterator yielding `Session` instances."""
        for fn in sorted(glob.glob1(self.path, '*.json')):
            session_name = os.path.splitext(fn)[0]
            yield Session(host=self, name=session_name)

    @staticmethod
    def _quote_name(name):
        """host:port => host_port"""
        return name.replace(':', '_')

    @staticmethod
    def _unquote_name(name):
        """host_port => host:port"""
        return re.sub(r'_(\d+)$', r':\1', name)

    @classmethod
    def all(cls, root_dir=DEFAULT_SESSIONS_DIR):
        """Return a generator yielding a host at a time."""
        for name in sorted(glob.glob1(root_dir, '*')):
            if os.path.isdir(os.path.join(root_dir, name)):
                yield Host(cls._unquote_name(name), root_dir=root_dir)

    @property
    def verbose_name(self):
        return '%s %s' % (self.name, self.path)

    def delete(self):
        shutil.rmtree(self.path)

    @property
    def path(self):
        path = os.path.join(self.root_dir, self._quote_name(self.name))
        try:
            os.makedirs(path, mode=0o700)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise
        return path


class Session(BaseConfigDict):

    help = 'https://github.com/jkbr/httpie#sessions'
    about = 'HTTPie session file'

    VALID_NAME_PATTERN = re.compile('^[a-zA-Z0-9_.-]+$')

    def __init__(self, host, name, *args, **kwargs):
        assert self.VALID_NAME_PATTERN.match(name)
        super(Session, self).__init__(*args, **kwargs)
        self.host = host
        self.name = name
        self['headers'] = {}
        self['cookies'] = {}
        self['auth'] = {
            'type': None,
            'username': None,
            'password': None
        }

    @property
    def directory(self):
        return self.host.path

    @property
    def verbose_name(self):
        return '%s %s %s' % (self.host.name, self.name, self.path)

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
        # http://docs.python.org/2/library/cookielib.html#cookie-objects
        stored_attrs = ['value', 'path', 'secure', 'expires']
        self['cookies'] = {}
        for host in jar._cookies.values():
            for path in host.values():
                for name, cookie in path.items():
                    self['cookies'][name] = dict(
                        (attname, getattr(cookie, attname))
                        for attname in stored_attrs
                    )

    @property
    def auth(self):
        auth = self.get('auth', None)
        if not auth or not auth['type']:
            return
        Auth = {'basic': HTTPBasicAuth,
                'digest': HTTPDigestAuth}[auth['type']]
        return Auth(auth['username'], auth['password'])

    @auth.setter
    def auth(self, cred):
        self['auth'] = {
            'type': {HTTPBasicAuth: 'basic',
                     HTTPDigestAuth: 'digest'}[type(cred)],
            'username': cred.username,
            'password': cred.password,
        }
