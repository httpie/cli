# coding=utf-8
"""Utilities for HTTPie test suite."""
import re
import shlex
import sys
import time
import json
import tempfile
from io import BytesIO
from pathlib import Path
from typing import Optional, Union, List

from httpie.status import ExitStatus
from httpie.config import Config
from httpie.context import Environment
from httpie.core import main


# pytest-httpbin currently does not support chunked requests:
# <https://github.com/kevin1024/pytest-httpbin/issues/33>
# <https://github.com/kevin1024/pytest-httpbin/issues/28>
HTTPBIN_WITH_CHUNKED_SUPPORT = 'http://pie.dev'


TESTS_ROOT = Path(__file__).parent.parent
CRLF = '\r\n'
COLOR = '\x1b['
HTTP_OK = '200 OK'
# noinspection GrazieInspection
HTTP_OK_COLOR = (
    'HTTP\x1b[39m\x1b[38;5;245m/\x1b[39m\x1b'
    '[38;5;37m1.1\x1b[39m\x1b[38;5;245m \x1b[39m\x1b[38;5;37m200'
    '\x1b[39m\x1b[38;5;245m \x1b[39m\x1b[38;5;136mOK'
)


def mk_config_dir() -> Path:
    dirname = tempfile.mkdtemp(prefix='httpie_config_')
    return Path(dirname)


def add_auth(url, auth):
    proto, rest = url.split('://', 1)
    return proto + '://' + auth + '@' + rest


class StdinBytesIO(BytesIO):
    """To be used for `MockEnvironment.stdin`"""
    len = 0  # See `prepare_request_body()`


class MockEnvironment(Environment):
    """Environment subclass with reasonable defaults for testing."""
    colors = 0  # For easier debugging
    stdin_isatty = True,
    stdout_isatty = True
    is_windows = False

    def __init__(self, create_temp_config_dir=True, **kwargs):
        if 'stdout' not in kwargs:
            kwargs['stdout'] = tempfile.TemporaryFile(
                mode='w+b',
                prefix='httpie_stdout'
            )
        if 'stderr' not in kwargs:
            kwargs['stderr'] = tempfile.TemporaryFile(
                mode='w+t',
                prefix='httpie_stderr'
            )
        super().__init__(**kwargs)
        self._create_temp_config_dir = create_temp_config_dir
        self._delete_config_dir = False
        self._temp_dir = Path(tempfile.gettempdir())

    @property
    def config(self) -> Config:
        if (self._create_temp_config_dir
                and self._temp_dir not in self.config_dir.parents):
            self.create_temp_config_dir()
        return super().config

    def create_temp_config_dir(self):
        self.config_dir = mk_config_dir()
        self._delete_config_dir = True

    def cleanup(self):
        self.stdout.close()
        self.stderr.close()
        if self._delete_config_dir:
            assert self._temp_dir in self.config_dir.parents
            from shutil import rmtree
            rmtree(self.config_dir, ignore_errors=True)

    def __del__(self):
        # noinspection PyBroadException
        try:
            self.cleanup()
        except Exception:
            pass


class BaseCLIResponse:
    """
    Represents the result of simulated `$ http' invocation via `http()`.

    Holds and provides access to:

        - stdout output: print(self)
        - stderr output: print(self.stderr)
        - devnull output: print(self.devnull)
        - exit_status output: print(self.exit_status)

    """
    stderr: str = None
    devnull: str = None
    json: dict = None
    exit_status: ExitStatus = None
    command: str = None
    args: List[str] = []
    complete_args: List[str] = []

    @property
    def command(self):
        cmd = ' '.join(shlex.quote(arg) for arg in ['http', *self.args])
        # pytest-httpbin to real httpbin.
        return re.sub(r'127\.0\.0\.1:\d+', 'httpbin.org', cmd)


class BytesCLIResponse(bytes, BaseCLIResponse):
    """
    Used as a fallback when a StrCLIResponse cannot be used.

    E.g. when the output contains binary data or when it is colorized.

    `.json` will always be None.

    """


class StrCLIResponse(str, BaseCLIResponse):

    @property
    def json(self) -> Optional[dict]:
        """
        Return deserialized the request or response JSON body,
        if one (and only one) included in the output and is parsable.

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
            elif self.count('Content-Type:') == 1:
                # Looks like a HTTP message,
                # try to extract JSON from its body.
                try:
                    j = self.strip()[self.strip().rindex('\r\n\r\n'):]
                except ValueError:
                    pass
                else:
                    try:
                        # noinspection PyAttributeOutsideInit
                        self._json = json.loads(j)
                    except ValueError:
                        pass
        return self._json


class ExitStatusError(Exception):
    pass


def http(
    *args,
    program_name='http',
    tolerate_error_exit_status=False,
    **kwargs,
) -> Union[StrCLIResponse, BytesCLIResponse]:
    # noinspection PyUnresolvedReferences
    """
    Run HTTPie and capture stderr/out and exit status.
    Content writtent to devnull will be captured only if
    env.devnull is set manually.

    Invoke `httpie.core.main()` with `args` and `kwargs`,
    and return a `CLIResponse` subclass instance.

    The return value is either a `StrCLIResponse`, or `BytesCLIResponse`
    if unable to decode the output. Devnull is string when possible,
    bytes otherwise.

    The response has the following attributes:

        `stdout` is represented by the instance itself (print r)
        `stderr`: text written to stderr
        `devnull` text written to devnull.
        `exit_status`: the exit status
        `json`: decoded JSON (if possible) or `None`

    Exceptions are propagated.

    If you pass ``tolerate_error_exit_status=True``, then error exit statuses
    won't result into an exception.

    Example:

    $ http --auth=user:password GET pie.dev/basic-auth/user/password

        >>> httpbin = getfixture('httpbin')
        >>> r = http('-a', 'user:pw', httpbin.url + '/basic-auth/user/pw')
        >>> type(r) == StrCLIResponse
        True
        >>> r.exit_status
        <ExitStatus.SUCCESS: 0>
        >>> r.stderr
        ''
        >>> 'HTTP/1.1 200 OK' in r
        True
        >>> r.json == {'authenticated': True, 'user': 'user'}
        True

    """
    env = kwargs.get('env')
    if not env:
        env = kwargs['env'] = MockEnvironment()

    stdout = env.stdout
    stderr = env.stderr
    devnull = env.devnull

    args = list(args)
    args_with_config_defaults = args + env.config.default_options
    add_to_args = []
    if '--debug' not in args_with_config_defaults:
        if (not tolerate_error_exit_status
                and '--traceback' not in args_with_config_defaults):
            add_to_args.append('--traceback')
        if not any('--timeout' in arg for arg in args_with_config_defaults):
            add_to_args.append('--timeout=3')

    complete_args = [program_name, *add_to_args, *args]
    # print(' '.join(complete_args))

    def dump_stderr():
        stderr.seek(0)
        sys.stderr.write(stderr.read())

    try:
        try:
            exit_status = main(args=complete_args, **kwargs)
            if '--download' in args:
                # Let the progress reporter thread finish.
                time.sleep(.5)
        except SystemExit:
            if tolerate_error_exit_status:
                exit_status = ExitStatus.ERROR
            else:
                dump_stderr()
                raise
        except Exception:
            stderr.seek(0)
            sys.stderr.write(stderr.read())
            raise
        else:
            if (not tolerate_error_exit_status
                    and exit_status != ExitStatus.SUCCESS):
                dump_stderr()
                raise ExitStatusError(
                    'httpie.core.main() unexpectedly returned'
                    f' a non-zero exit status: {exit_status}'
                )

        stdout.seek(0)
        stderr.seek(0)
        devnull.seek(0)
        output = stdout.read()
        devnull_output = devnull.read()
        try:
            output = output.decode('utf8')
        except UnicodeDecodeError:
            r = BytesCLIResponse(output)
        else:
            r = StrCLIResponse(output)

        try:
            devnull_output = devnull_output.decode('utf8')
        except Exception:
            pass

        r.devnull = devnull_output
        r.stderr = stderr.read()
        r.exit_status = exit_status
        r.args = args
        r.complete_args = ' '.join(complete_args)

        if r.exit_status != ExitStatus.SUCCESS:
            sys.stderr.write(r.stderr)

        # print(f'\n\n$ {r.command}\n')
        return r

    finally:
        devnull.close()
        stdout.close()
        stderr.close()
        env.cleanup()
