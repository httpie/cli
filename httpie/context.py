import os
import sys

from requests.compat import is_windows

from httpie.config import DEFAULT_CONFIG_DIR, Config


class Environment(object):
    """
    Information about the execution context
    (standard streams, config directory, etc).

    By default, it represents the actual environment.
    All of the attributes can be overwritten though, which
    is used by the test suite to simulate various scenarios.

    """
    is_windows = is_windows
    config_dir = DEFAULT_CONFIG_DIR
    colors = 256 if '256color' in os.environ.get('TERM', '') else 88
    stdin = sys.stdin
    stdin_isatty = stdin.isatty()
    stdin_encoding = None
    stdout = sys.stdout
    stdout_isatty = stdout.isatty()
    stdout_encoding = None
    stderr = sys.stderr
    stderr_isatty = stderr.isatty()
    if is_windows:
        # noinspection PyUnresolvedReferences
        from colorama.initialise import wrap_stream
        stdout = wrap_stream(stdout, convert=None, strip=None,
                             autoreset=True, wrap=True)
        stderr = wrap_stream(stderr, convert=None, strip=None,
                             autoreset=True, wrap=True)

    def __init__(self, **kwargs):
        """
        Use keyword arguments to overwrite
        any of the class attributes for this instance.

        """
        assert all(hasattr(type(self), attr) for attr in kwargs.keys())
        self.__dict__.update(**kwargs)

        # Keyword arguments > stream.encoding > default utf8
        if self.stdin_encoding is None:
            self.stdin_encoding = getattr(
                self.stdin, 'encoding', None) or 'utf8'
        if self.stdout_encoding is None:
            actual_stdout = self.stdout
            if is_windows:
                from colorama import AnsiToWin32
                if isinstance(self.stdout, AnsiToWin32):
                    actual_stdout = self.stdout.wrapped
            self.stdout_encoding = getattr(
                actual_stdout, 'encoding', None) or 'utf8'

    @property
    def config(self):
        if not hasattr(self, '_config'):
            self._config = Config(directory=self.config_dir)
            if self._config.is_new():
                self._config.save()
            else:
                self._config.load()
        return self._config
