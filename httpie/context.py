import sys
from pathlib import Path
from typing import Union, IO, Optional


try:
    import curses
except ImportError:
    curses = None  # Compiled w/o curses

from httpie.compat import is_windows
from httpie.config import DEFAULT_CONFIG_DIR, Config

from httpie.utils import repr_dict


class Environment:
    """
    Information about the execution context
    (standard streams, config directory, etc).

    By default, it represents the actual environment.
    All of the attributes can be overwritten though, which
    is used by the test suite to simulate various scenarios.

    """
    is_windows: bool = is_windows
    config_dir: Path = DEFAULT_CONFIG_DIR
    stdin: Optional[IO] = sys.stdin  # `None` when closed fd (#791)
    stdin_isatty: bool = stdin.isatty() if stdin else False
    stdin_encoding: str = None
    stdout: IO = sys.stdout
    stdout_isatty: bool = stdout.isatty()
    stdout_encoding: str = None
    stderr: IO = sys.stderr
    stderr_isatty: bool = stderr.isatty()
    colors = 256
    if not is_windows:
        if curses:
            try:
                curses.setupterm()
                colors = curses.tigetnum('colors')
            except curses.error:
                pass
    else:
        # noinspection PyUnresolvedReferences
        import colorama.initialise
        stdout = colorama.initialise.wrap_stream(
            stdout, convert=None, strip=None,
            autoreset=True, wrap=True
        )
        stderr = colorama.initialise.wrap_stream(
            stderr, convert=None, strip=None,
            autoreset=True, wrap=True
        )
        del colorama

    def __init__(self, **kwargs):
        """
        Use keyword arguments to overwrite
        any of the class attributes for this instance.

        """
        assert all(hasattr(type(self), attr) for attr in kwargs.keys())
        self.__dict__.update(**kwargs)

        # Keyword arguments > stream.encoding > default utf8
        if self.stdin and self.stdin_encoding is None:
            self.stdin_encoding = getattr(
                self.stdin, 'encoding', None) or 'utf8'
        if self.stdout_encoding is None:
            actual_stdout = self.stdout
            if is_windows:
                # noinspection PyUnresolvedReferences
                from colorama import AnsiToWin32
                if isinstance(self.stdout, AnsiToWin32):
                    # noinspection PyUnresolvedReferences
                    actual_stdout = self.stdout.wrapped
            self.stdout_encoding = getattr(
                actual_stdout, 'encoding', None) or 'utf8'

    @property
    def config(self) -> Config:
        if not hasattr(self, '_config'):
            self._config = Config(directory=self.config_dir)
            if self._config.is_new():
                self._config.save(fail_silently=True)
            else:
                self._config.load()
        return self._config

    def __str__(self):
        defaults = dict(type(self).__dict__)
        actual = dict(defaults)
        actual.update(self.__dict__)
        actual['config'] = self.config
        return repr_dict({
            key: value
            for key, value in actual.items()
            if not key.startswith('_')
        })

    def __repr__(self):
        return f'<{type(self).__name__} {self}>'
