import os
import sys
import time
import json
import shutil
import tempfile

from httpie import ExitStatus
from httpie.models import Environment
from httpie.core import main
from httpie.compat import bytes, str


TESTS_ROOT = os.path.abspath(os.path.dirname(__file__))
HTTPBIN_URL = os.environ.get('HTTPBIN_URL',
                             'http://httpbin.org').rstrip('/')


CRLF = '\r\n'
COLOR = '\x1b['
HTTP_OK = 'HTTP/1.1 200'
HTTP_OK_COLOR = (
    'HTTP\x1b[39m\x1b[38;5;245m/\x1b[39m\x1b'
    '[38;5;37m1.1\x1b[39m\x1b[38;5;245m \x1b[39m\x1b[38;5;37m200'
    '\x1b[39m\x1b[38;5;245m \x1b[39m\x1b[38;5;136mOK'
)


def httpbin(path):
    """
    Return a fully-qualified URL for `path`.

    >>> httpbin('/get')
    'http://httpbin.org/get'

    """
    url = HTTPBIN_URL + path
    return url


def mk_config_dir():
    return tempfile.mkdtemp(prefix='httpie_test_config_dir_')


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


class Response(object):
    stderr = None
    json = None
    exit_status = None


class BytesResponse(bytes, Response):
    pass


class StrResponse(str, Response):

    @property
    def json(self):
        if not hasattr(self, '_json'):
            self._json = None
            # De-serialize JSON body if possible.
            if COLOR in self:
                # Colorized output cannot be parsed.
                pass
            elif self.strip().startswith('{'):
                # Looks like JSON body.
                self._json = json.loads(self)
            elif self.count('Content-Type:') == 1 and 'application/json' in self:
                # Looks like a JSON HTTP message, try to extract its body.
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


def http(*args, **kwargs):
    """
    Invoke `httpie.core.main()` with `args` and `kwargs`,
    and return a unicode response.

    Return a `StrResponse`, or `BytesResponse` if unable to decode the output.
    The response has the following attributes:

        `stderr`: text written to stderr
        `exit_status`: the exit status
        `json`: decoded JSON (if possible) or `None`

    Exceptions are propagated except for SystemExit.

    """
    env = kwargs.get('env')
    if not env:
        env = kwargs['env'] = TestEnvironment()

    stdout = env.stdout
    stderr = env.stderr
    try:

        try:
            exit_status = main(args=['--traceback'] + list(args), **kwargs)
            if '--download' in args:
                # Let the progress reporter thread finish.
                time.sleep(.5)
        except Exception:
            sys.stderr.write(stderr.read())
            raise
        except SystemExit:
            exit_status = ExitStatus.ERROR

        stdout.seek(0)
        stderr.seek(0)
        output = stdout.read()
        try:
            r = StrResponse(output.decode('utf8'))
        except UnicodeDecodeError:
            r = BytesResponse(output)
        r.stderr = stderr.read()
        r.exit_status = exit_status

        return r

    finally:
        stdout.close()
        stderr.close()

