import errno
import json
import os
from pathlib import Path
from typing import Union

from httpie import __version__
from httpie.compat import is_windows


def get_default_config_dir() -> Path:
    """Return the path to the httpie configuration directory.

    This directory isn't guaranteed to exist, and nor are any of its
    ancestors.
    """
    env_config_dir = os.environ.get('HTTPIE_CONFIG_DIR')
    if env_config_dir:
        return Path(env_config_dir)
    if is_windows:
        return Path(os.path.expandvars(r'%APPDATA%\httpie'))
    legacy_config_dir = os.path.expanduser('~/.httpie')
    if os.path.exists(legacy_config_dir):
        return Path(legacy_config_dir)
    xdg_config_dir = os.environ.get('XDG_CONFIG_HOME')
    if not xdg_config_dir or not os.path.isabs(xdg_config_dir):
        xdg_config_dir = os.path.expanduser('~/.config')
    httpie_config_dir = os.path.join(xdg_config_dir, 'httpie')
    return Path(httpie_config_dir)


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

        try:
            with self.path.open('w') as f:
                json.dump(
                    obj=self,
                    fp=f,
                    indent=4,
                    sort_keys=True,
                    ensure_ascii=True,
                )
                f.write('\n')
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
