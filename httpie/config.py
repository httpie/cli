import errno
import json
import os
from pathlib import Path
from typing import Union

from httpie import __version__
from httpie.compat import is_windows


ENV_XDG_CONFIG_HOME = 'XDG_CONFIG_HOME'
ENV_HTTPIE_CONFIG_DIR = 'HTTPIE_CONFIG_DIR'
DEFAULT_CONFIG_DIRNAME = 'httpie'
DEFAULT_RELATIVE_XDG_CONFIG_HOME = Path('.config')
DEFAULT_RELATIVE_LEGACY_CONFIG_DIR = Path('.httpie')
DEFAULT_WINDOWS_CONFIG_DIR = Path(
    os.path.expandvars('%APPDATA%')) / DEFAULT_CONFIG_DIRNAME


def get_default_config_dir() -> Path:
    """
    Return the path to the httpie configuration directory.

    This directory isn't guaranteed to exist, and nor are any of its
    ancestors (only the legacy ~/.httpie, if returned, is guaranteed to exist).

    XDG Base Directory Specification support:

        <https://wiki.archlinux.org/index.php/XDG_Base_Directory>

        $XDG_CONFIG_HOME is supported; $XDG_CONFIG_DIRS is not

    """
    # 1. explicitly set through env
    env_config_dir = os.environ.get(ENV_HTTPIE_CONFIG_DIR)
    if env_config_dir:
        return Path(env_config_dir)

    # 2. Windows
    if is_windows:
        return DEFAULT_WINDOWS_CONFIG_DIR

    home_dir = Path.home()

    # 3. legacy ~/.httpie
    legacy_config_dir = home_dir / DEFAULT_RELATIVE_LEGACY_CONFIG_DIR
    if legacy_config_dir.exists():
        return legacy_config_dir

    # 4. XDG
    xdg_config_home_dir = os.environ.get(
        ENV_XDG_CONFIG_HOME,  # 4.1. explicit
        home_dir / DEFAULT_RELATIVE_XDG_CONFIG_HOME  # 4.2. default
    )
    return Path(xdg_config_home_dir) / DEFAULT_CONFIG_DIRNAME


DEFAULT_CONFIG_DIR = get_default_config_dir()


class ConfigFileError(Exception):
    pass


class BaseConfigDict(dict):
    name = None
    helpurl = None
    about = None

    def __init__(self, path: Path):
        super().__init__()
        self.path = path

    def ensure_directory(self):
        try:
            self.path.parent.mkdir(mode=0o700, parents=True)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

    def is_new(self) -> bool:
        return not self.path.exists()

    def load(self):
        config_type = type(self).__name__.lower()
        try:
            with self.path.open('rt') as f:
                try:
                    data = json.load(f)
                except ValueError as e:
                    raise ConfigFileError(
                        f'invalid {config_type} file: {e} [{self.path}]'
                    )
                self.update(data)
        except IOError as e:
            if e.errno != errno.ENOENT:
                raise ConfigFileError(f'cannot read {config_type} file: {e}')

    def save(self, fail_silently=False):
        self['__meta__'] = {
            'httpie': __version__
        }
        if self.helpurl:
            self['__meta__']['help'] = self.helpurl

        if self.about:
            self['__meta__']['about'] = self.about

        self.ensure_directory()

        json_string = json.dumps(
            obj=self,
            indent=4,
            sort_keys=True,
            ensure_ascii=True,
        )
        try:
            self.path.write_text(json_string + '\n')
        except IOError:
            if not fail_silently:
                raise

    def delete(self):
        try:
            self.path.unlink()
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise


class Config(BaseConfigDict):
    FILENAME = 'config.json'
    DEFAULTS = {
        'default_options': []
    }

    def __init__(self, directory: Union[str, Path] = DEFAULT_CONFIG_DIR):
        self.directory = Path(directory)
        super().__init__(path=self.directory / self.FILENAME)
        self.update(self.DEFAULTS)

    @property
    def default_options(self) -> list:
        return self['default_options']
