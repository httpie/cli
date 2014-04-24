import os
import sys
import time
import json
import shutil
import tempfile
try:
    from unittest import skipIf, skip
except ImportError:
    skip = lambda msg: lambda self: None

    # noinspection PyUnusedLocal
    def skipIf(cond, reason):
        def decorator(test_method):
            if cond:
                return lambda self: None
            return test_method
        return decorator

from requests.structures import CaseInsensitiveDict

TESTS_ROOT = os.path.abspath(os.path.dirname(__file__))
# HACK: Prepend ../ to PYTHONPATH so that we can import httpie form there.
sys.path.insert(0, os.path.realpath(os.path.join(TESTS_ROOT, '..')))
from httpie import ExitStatus
from httpie.models import Environment
from httpie.core import main
from httpie.compat import bytes, str


HTTPBIN_URL = os.environ.get('HTTPBIN_URL',
                             'http://httpbin.org').rstrip('/')


CRLF = '\r\n'
HTTP_OK = 'HTTP/1.1 200'
OK_COLOR = (
    'HTTP\x1b[39m\x1b[38;5;245m/\x1b[39m\x1b'
    '[38;5;37m1.1\x1b[39m\x1b[38;5;245m \x1b[39m\x1b[38;5;37m200'
    '\x1b[39m\x1b[38;5;245m \x1b[39m\x1b[38;5;136mOK'
)
COLOR = '\x1b['


def httpbin(path):
    url = HTTPBIN_URL + path
    return url


def mk_config_dir():
    return tempfile.mkdtemp(prefix='httpie_test_config_dir_')


class Response(object):

    # noinspection PyDefaultArgument
    def __init__(self, url, headers={}, status_code=200):
        self.url = url
        self.headers = CaseInsensitiveDict(headers)
        self.status_code = status_code


class TestEnvironment(Environment):
    colors = 0
    stdin_isatty = True,
    stdout_isatty = True
    is_windows = False
    _shutil = shutil  # we need it in __del__ (would get gc'd)

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


class BytesResponse(bytes):
    stderr = json = exit_status = None


class StrResponse(str):
    stderr = json = exit_status = None


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
        else:
            if COLOR not in r:
                # De-serialize JSON body if possible.
                if r.strip().startswith('{'):
                    #noinspection PyTypeChecker
                    r.json = json.loads(r)
                elif r.count('Content-Type:') == 1 and 'application/json' in r:
                    try:
                        j = r.strip()[r.strip().rindex('\r\n\r\n'):]
                    except ValueError:
                        pass
                    else:
                        try:
                            r.json = json.loads(j)
                        except ValueError:
                            pass

        r.stderr = stderr.read()
        r.exit_status = exit_status

        return r

    finally:
        stdout.close()
        stderr.close()
