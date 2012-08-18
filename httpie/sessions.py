"""Persistent, JSON-serialized sessions.

"""
import os
import sys
import json
import glob
import errno
import codecs
import subprocess

from requests import Session as RSession
from requests.cookies import RequestsCookieJar, create_cookie
from requests.auth import HTTPBasicAuth, HTTPDigestAuth

from . import __version__
from .config import CONFIG_DIR
from .output import PygmentsProcessor


SESSIONS_DIR = os.path.join(CONFIG_DIR, 'sessions')


def get_response(name, request_kwargs):

    session = Session.load(name)

    # Update session headers with the request headers.
    session['headers'].update(request_kwargs.get('headers', {}))

    auth = request_kwargs.get('auth', None)
    if auth:
        session.auth = auth
    elif session.auth:
        request_kwargs['auth'] = session.auth


    # Use the merged headers for the request
    request_kwargs['headers'] = session['headers']

    rsession = RSession(cookies=session.cookies)
    try:
        response = rsession.request(**request_kwargs)
    except Exception:
        raise
    else:
        session.cookies = rsession.cookies
        session.save()
        return response


class Session(dict):

    def __init__(self, name, *args, **kwargs):
        super(Session, self).__init__(*args, **kwargs)
        self.name = name
        self.setdefault('cookies', {})
        self.setdefault('headers', {})

    @property
    def path(self):
        return type(self).get_path(self.name)

    @property
    def cookies(self):
        jar = RequestsCookieJar()
        for name, cookie_dict in self['cookies'].items():
            cookie = create_cookie(
                name, cookie_dict.pop('value'), **cookie_dict)
            jar.set_cookie(cookie)
        jar.clear_expired_cookies()
        return jar

    @cookies.setter
    def cookies(self, jar):
        exclude = [
            '_rest', 'name', 'port_specified',
            'domain_specified', 'domain_initial_dot',
            'path_specified'
        ]
        self['cookies'] = {}
        for host in jar._cookies.values():
            for path in host.values():
                for name, cookie in path.items():
                    cookie_dict = {}
                    for k, v in cookie.__dict__.items():
                        if k not in exclude:
                            cookie_dict[k] = v
                    self['cookies'][name] = cookie_dict

    @property
    def auth(self):
        auth = self.get('auth', None)
        if not auth:
            return None
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

    def save(self):
        self['__version__'] = __version__
        with open(self.path, 'wb') as f:
            json.dump(self, f, indent=4, sort_keys=True, ensure_ascii=True)
            f.write(b'\n')

    @classmethod
    def load(cls, name):
        try:
            with open(cls.get_path(name), 'rt') as f:
                try:
                    data = json.load(f)
                except ValueError as e:
                    raise ValueError('Invalid session: %s [%s]' %
                                     (e.message, f.name))

                return cls(name, data)
        except IOError as e:
            if e.errno != errno.ENOENT:
                raise
            return cls(name)

    @classmethod
    def get_path(cls, name):
       try:
           os.makedirs(SESSIONS_DIR, mode=0o700)
       except OSError as e:
           if e.errno != errno.EEXIST:
               raise

       return os.path.join(SESSIONS_DIR, name + '.json')


def show_action(args):
    if not args.name:
        for fn in sorted(glob.glob1(SESSIONS_DIR, '*.json')):
            print(os.path.splitext(fn)[0])
        return

    path = Session.get_path(args.name)
    if not os.path.exists(path):
        sys.stderr.write('Session "%s" does not exist [%s].\n'
                          % (args.name, path))
        sys.exit(1)

    with codecs.open(path, encoding='utf8') as f:
        print(path + ':\n')
        print(PygmentsProcessor().process_body(
                f.read(), 'application/json', 'json'))
        print('')


def delete_action(args):
    if not args.name:
        for path in glob.glob(os.path.join(SESSIONS_DIR, '*.json')):
            os.unlink(path)
        return
    path = Session.get_path(args.name)
    if not os.path.exists(path):
        sys.stderr.write('Session "%s" does not exist [%s].\n'
                          % (args.name, path))
        sys.exit(1)
    else:
        os.unlink(path)


def edit_action(args):
    editor = os.environ.get('EDITOR', None)
    if not editor:
        sys.stderr.write(
            'You need to configure the environment variable EDITOR.\n')
        sys.exit(1)
    command = editor.split()
    command.append(Session.get_path(args.name))
    subprocess.call(command)


def add_actions(subparsers):

    # Show
    show = subparsers.add_parser('session-show', help='list or show sessions')
    show.set_defaults(action=show_action)
    show.add_argument('name', nargs='?',
        help='When omitted, HTTPie prints a list of existing sessions.'
             ' When specified, the session data is printed.')

    # Edit
    edit = subparsers.add_parser('session-edit', help='edit a session in $EDITOR')
    edit.set_defaults(action=edit_action)
    edit.add_argument('name')

    # Delete
    delete = subparsers.add_parser('session-delete', help='delete a session')
    delete.set_defaults(action=delete_action)
    delete_group = delete.add_mutually_exclusive_group(required=True)
    delete_group.add_argument(
        '--all', action='store_true',
        help='Delete all sessions from %s' % SESSIONS_DIR)
    delete_group.add_argument(
        'name', nargs='?',
        help='The name of the session to be deleted. ' \
             'To see a list existing sessions, run `httpie sessions show\'.')
