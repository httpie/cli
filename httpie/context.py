import argparse
import sys
import os
import warnings
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, IO, Optional, TYPE_CHECKING
from enum import Enum


try:
    import curses
except ImportError:
    curses = None  # Compiled w/o curses

from .compat import is_windows, cached_property
from .config import DEFAULT_CONFIG_DIR, Config, ConfigFileError
from .encoding import UTF8

from .utils import repr_dict
from .output.ui.palette import GenericColor

if TYPE_CHECKING:
    from rich.console import Console


class LogLevel(str, Enum):
    INFO = 'info'
    WARNING = 'warning'
    ERROR = 'error'


LOG_LEVEL_COLORS = {
    LogLevel.INFO: GenericColor.PINK,
    LogLevel.WARNING: GenericColor.ORANGE,
    LogLevel.ERROR: GenericColor.RED,
}

LOG_LEVEL_DISPLAY_THRESHOLDS = {
    LogLevel.INFO: 1,
    LogLevel.WARNING: 2,
    LogLevel.ERROR: float('inf'),  # Never hide errors.
}


class Environment:
    """
    Information about the execution context
    (standard streams, config directory, etc).

    By default, it represents the actual environment.
    All of the attributes can be overwritten though, which
    is used by the test suite to simulate various scenarios.

    """
    args = argparse.Namespace()
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
    program_name: str = 'http'

    # Whether to show progress bars / status spinners etc.
    show_displays: bool = True

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

    def __init__(self, devnull=None, **kwargs):
        """
        Use keyword arguments to overwrite
        any of the class attributes for this instance.

        """
        assert all(hasattr(type(self), attr) for attr in kwargs.keys())
        self.__dict__.update(**kwargs)

        # The original STDERR unaffected by --quiet’ing.
        self._orig_stderr = self.stderr
        self._devnull = devnull

        # Keyword arguments > stream.encoding > default UTF-8
        if self.stdin and self.stdin_encoding is None:
            self.stdin_encoding = getattr(
                self.stdin, 'encoding', None) or UTF8
        if self.stdout_encoding is None:
            actual_stdout = self.stdout
            if is_windows:
                # noinspection PyUnresolvedReferences
                from colorama import AnsiToWin32
                if isinstance(self.stdout, AnsiToWin32):
                    # noinspection PyUnresolvedReferences
                    actual_stdout = self.stdout.wrapped
            self.stdout_encoding = getattr(
                actual_stdout, 'encoding', None) or UTF8

        self.quiet = kwargs.pop('quiet', 0)

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

    _config: Config = None

    @property
    def config(self) -> Config:
        config = self._config
        if not config:
            self._config = config = Config(directory=self.config_dir)
            if not config.is_new():
                try:
                    config.load()
                except ConfigFileError as e:
                    self.log_error(e, level='warning')
        return config

    @property
    def devnull(self) -> IO:
        if self._devnull is None:
            self._devnull = open(os.devnull, 'w+')
        return self._devnull

    @contextmanager
    def as_silent(self) -> Iterator[None]:
        original_stdout = self.stdout
        original_stderr = self.stderr

        try:
            self.stdout = self.devnull
            self.stderr = self.devnull
            yield
        finally:
            self.stdout = original_stdout
            self.stderr = original_stderr

    def log_error(self, msg: str, level: LogLevel = LogLevel.ERROR) -> None:
        if self.stdout_isatty and self.quiet >= LOG_LEVEL_DISPLAY_THRESHOLDS[level]:
            stderr = self.stderr  # Not directly /dev/null, since stderr might be mocked
        else:
            stderr = self._orig_stderr
        rich_console = self._make_rich_console(file=stderr, force_terminal=stderr.isatty())
        rich_console.print(
            f'\n{self.program_name}: {level}: {msg}\n\n',
            style=LOG_LEVEL_COLORS[level],
            markup=False,
            highlight=False,
            soft_wrap=True
        )

    def apply_warnings_filter(self) -> None:
        if self.quiet >= LOG_LEVEL_DISPLAY_THRESHOLDS[LogLevel.WARNING]:
            warnings.simplefilter("ignore")

    def _make_rich_console(
        self,
        file: IO[str],
        force_terminal: bool
    ) -> 'Console':
        from rich.console import Console
        from httpie.output.ui.rich_palette import _make_rich_color_theme

        style = getattr(self.args, 'style', None)
        theme = _make_rich_color_theme(style)
        # Rich infers the rest of the knowledge (e.g encoding)
        # dynamically by looking at the file/stderr.
        return Console(
            file=file,
            force_terminal=force_terminal,
            no_color=(self.colors == 0),
            theme=theme
        )

    # Rich recommends separating the actual console (stdout) from
    # the error (stderr) console for better isolation between parts.
    # https://rich.readthedocs.io/en/stable/console.html#error-console

    @cached_property
    def rich_console(self):
        return self._make_rich_console(self.stdout, self.stdout_isatty)

    @cached_property
    def rich_error_console(self):
        return self._make_rich_console(self.stderr, self.stderr_isatty)
