"""Persistent, JSON-serialized sessions.

"""
import os
import sys
import glob
import errno
import codecs
import shutil
import subprocess

import requests
from requests.compat import urlparse
from requests.cookies import RequestsCookieJar, create_cookie
from requests.auth import HTTPBasicAuth, HTTPDigestAuth
from argparse import OPTIONAL

from .config import BaseConfigDict, DEFAULT_CONFIG_DIR
from .output import PygmentsProcessor


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
             or urlparse(request_kwargs['url']).netloc.split('@')[-1]
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

    rsession = requests.Session(cookies=session.cookies)
    try:
        response = rsession.request(**request_kwargs)
    except Exception:
        raise
    else:
        # Existing sessions with `read_only=True` don't get updated.
        if session.is_new or not read_only:
            session.cookies = rsession.cookies
            session.save()
        return response


class Host(object):
    """A host is a per-host directory on the disk containing sessions files."""

    def __init__(self, name, root_dir=DEFAULT_CONFIG_DIR):
        self.name = name
        self.root_dir = root_dir

    def __iter__(self):
        """Return a iterator yielding `(session_name, session_path)`."""
        for fn in sorted(glob.glob1(self.path, '*.json')):
            yield os.path.splitext(fn)[0], os.path.join(self.path, fn)

    def delete(self):
        shutil.rmtree(self.path)

    @property
    def path(self):
        # Name will include ':' if a port is specified, which is invalid
        # on windows. DNS does not allow '_' in a domain, or for it to end
        # in a number (I think?)
        path = os.path.join(self.root_dir, self.name.replace(':', '_'))
        try:
            os.makedirs(path, mode=0o700)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise
        return path

    @classmethod
    def all(cls):
        """Return a generator yielding a host at a time."""
        for name in sorted(glob.glob1(DEFAULT_SESSIONS_DIR, '*')):
            if os.path.isdir(os.path.join(DEFAULT_SESSIONS_DIR, name)):
                yield Host(name)


class Session(BaseConfigDict):
    """"""

    def __init__(self, host, name, *args, **kwargs):
        super(Session, self).__init__(*args, **kwargs)
        self.host = host
        self.name = name
        self['headers'] = {}
        self['cookies'] = {}

    @property
    def directory(self):
        return self.host.path

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
        excluded = [
            '_rest', 'name', 'port_specified',
            'domain_specified', 'domain_initial_dot',
            'path_specified', 'comment', 'comment_url'
        ]
        self['cookies'] = {}
        for host in jar._cookies.values():
            for path in host.values():
                for name, cookie in path.items():
                    cookie_dict = {}
                    for k, v in cookie.__dict__.items():
                        if k not in excluded:
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


# The commands are disabled for now.
# TODO: write tests for the commands.

def list_command(args):
    if args.host:
        for name, path in Host(args.host):
            print(name + ' [' + path + ']')
    else:
        for host in Host.all():
            print(host.name)
            for name, path in host:
                print(' ' + name + ' [' + path + ']')


def show_command(args):
    path = Session(Host(args.host), args.name).path
    if not os.path.exists(path):
        sys.stderr.write('Session "%s" does not exist [%s].\n'
        % (args.name, path))
        sys.exit(1)

    with codecs.open(path, encoding='utf8') as f:
        print(path + ':\n')
        proc = PygmentsProcessor()
        print(proc.process_body(f.read(), 'application/json', 'json'))
        print('')


def delete_command(args):
    host = Host(args.host)
    if not args.name:
        host.delete()
    else:
        Session(host, args.name).delete()


def edit_command(args):
    editor = os.environ.get('EDITOR', None)
    if not editor:
        sys.stderr.write(
            'You need to configure the environment variable EDITOR.\n')
        sys.exit(1)
    command = editor.split()
    command.append(Session(Host(args.host), args.name).path)
    subprocess.call(command)


def add_commands(subparsers):

    # List
    list_ = subparsers.add_parser('session-list', help='list sessions')
    list_.set_defaults(command=list_command)
    list_.add_argument('host', nargs=OPTIONAL)

    # Show
    show = subparsers.add_parser('session-show', help='show a session')
    show.set_defaults(command=show_command)
    show.add_argument('host')
    show.add_argument('name')

    # Edit
    edit = subparsers.add_parser(
        'session-edit', help='edit a session in $EDITOR')
    edit.set_defaults(command=edit_command)
    edit.add_argument('host')
    edit.add_argument('name')

    # Delete
    delete = subparsers.add_parser('session-delete', help='delete a session')
    delete.set_defaults(command=delete_command)
    delete.add_argument('host')
    delete.add_argument('name', nargs=OPTIONAL,
        help='The name of the session to be deleted.'
             ' If not specified, all host sessions are deleted.')
