# coding=utf-8
"""Utilities used by HTTPie tests.

"""
import os
import sys
import time
import json
import shutil
import tempfile

import httpie
from httpie.context import Environment
from httpie.core import main
from httpie.compat import bytes, str


TESTS_ROOT = os.path.abspath(os.path.dirname(__file__))


CRLF = '\r\n'
COLOR = '\x1b['
HTTP_OK = '200 OK'
HTTP_OK_COLOR = (
    'HTTP\x1b[39m\x1b[38;5;245m/\x1b[39m\x1b'
    '[38;5;37m1.1\x1b[39m\x1b[38;5;245m \x1b[39m\x1b[38;5;37m200'
    '\x1b[39m\x1b[38;5;245m \x1b[39m\x1b[38;5;136mOK'
)


def no_content_type(headers):
    return (
        'Content-Type' not in headers
        # We need to do also this because of this issue:
        # <https://github.com/kevin1024/pytest-httpbin/issues/5>
        # TODO: remove this function once the issue is if fixed
        or headers['Content-Type'] == 'text/plain'
    )


def add_auth(url, auth):
    proto, rest = url.split('://', 1)
    return proto + '://' + auth + '@' + rest


class TestEnvironment(Environment):
    """
    Environment subclass with reasonable defaults suitable for testing.

    """
    colors = 0
    stdin_isatty = True,
    stdout_isatty = True
    is_windows = False

    _shutil = shutil  # needed by __del__ (would get gc'd)

    def __init__(self, **kwargs):

        if 'stdout' not in kwargs:
            kwargs['stdout'] = tempfile.TemporaryFile('w+b')

        if 'stderr' not in kwargs:
            kwargs['stderr'] = tempfile.TemporaryFile('w+t')

        self.delete_config_dir = False
        if 'config_dir' not in kwargs:
            kwargs['config_dir'] = mk_config_dir()
            self.delete_config_dir = True

        super(TestEnvironment, self).__init__(**kwargs)

    def __del__(self):
        if self.delete_config_dir:
            self._shutil.rmtree(self.config_dir)


def http(*args, **kwargs):
    """
    Run HTTPie and capture stderr/out and exit status.

    Invoke `httpie.core.main()` with `args` and `kwargs`,
    and return a `CLIResponse` subclass instance.

    The return value is either a `StrCLIResponse`, or `BytesCLIResponse`
    if unable to decode the output.

    The response has the following attributes:

        `stdout` is represented by the instance itself (print r)
        `stderr`: text written to stderr
        `exit_status`: the exit status
        `json`: decoded JSON (if possible) or `None`

    Exceptions are propagated.

    If you pass ``error_exit_ok=True``, then error exit statuses
    won't result into an exception.

    Example:

    $ http --auth=user:password GET httpbin.org/basic-auth/user/password

        >>> r = http('-a', 'user:pw', 'httpbin.org/basic-auth/user/pw')
        >>> type(r) == StrCLIResponse
        True
        >>> r.exit_status
        0
        >>> r.stderr
        ''
        >>> 'HTTP/1.1 200 OK' in r
        True
        >>> r.json == {'authenticated': True, 'user': 'user'}
        True


    """
    error_exit_ok = kwargs.pop('error_exit_ok', False)
    env = kwargs.get('env')
    if not env:
        env = kwargs['env'] = TestEnvironment()

    stdout = env.stdout
    stderr = env.stderr

    args = list(args)
    if '--debug' not in args and '--traceback' not in args:
        args = ['--traceback'] + args

    def dump_stderr():
        stderr.seek(0)
        sys.stderr.write(stderr.read())

    try:
        try:
            exit_status = main(args=args, **kwargs)
            if '--download' in args:
                # Let the progress reporter thread finish.
                time.sleep(.5)
        except SystemExit:
            if error_exit_ok:
                exit_status = httpie.ExitStatus.ERROR
            else:
                dump_stderr()
                raise
        except Exception:
            stderr.seek(0)
            sys.stderr.write(stderr.read())
            raise
        else:
            if exit_status != httpie.ExitStatus.OK and not error_exit_ok:
                dump_stderr()
                raise Exception('Unexpected exit status: %s', exit_status)

        stdout.seek(0)
        stderr.seek(0)
        output = stdout.read()
        try:
            output = output.decode('utf8')
        except UnicodeDecodeError:
            # noinspection PyArgumentList
            r = BytesCLIResponse(output)
        else:
            # noinspection PyArgumentList
            r = StrCLIResponse(output)
        r.stderr = stderr.read()
        r.exit_status = exit_status

        if r.exit_status != httpie.ExitStatus.OK:
            sys.stderr.write(r.stderr)

        return r

    finally:
        stdout.close()
        stderr.close()


class BaseCLIResponse(object):
    """
    Represents the result of simulated `$ http' invocation  via `http()`.

    Holds and provides access to:

        - stdout output: print(self)
        - stderr output: print(self.stderr)
        - exit_status output: print(self.exit_status)

    """
    stderr = None
    json = None
    exit_status = None


class BytesCLIResponse(bytes, BaseCLIResponse):
    """
    Used as a fallback when a StrCLIResponse cannot be used.

    E.g. when the output contains binary data or when it is colorized.

    `.json` will always be None.

    """


class StrCLIResponse(str, BaseCLIResponse):

    @property
    def json(self):
        """
        Return deserialized JSON body, if one included in the output
        and is parseable.

        """
        if not hasattr(self, '_json'):
            self._json = None
            # De-serialize JSON body if possible.
            if COLOR in self:
                # Colorized output cannot be parsed.
                pass
            elif self.strip().startswith('{'):
                # Looks like JSON body.
                self._json = json.loads(self)
            elif (self.count('Content-Type:') == 1
                    and 'application/json' in self):
                # Looks like a whole JSON HTTP message,
                # try to extract its body.
                try:
                    j = self.strip()[self.strip().rindex('\r\n\r\n'):]
                except ValueError:
                    pass
                else:
                    try:
                        self._json = json.loads(j)
                    except ValueError:
                        pass
        return self._json


def mk_config_dir():
    return tempfile.mkdtemp(prefix='httpie_test_config_dir_')
