import errno
import json
import os
from pathlib import Path
from typing import Union

from httpie import __version__
from httpie.compat import is_windows


DEFAULT_CONFIG_DIR = Path(os.environ.get(
    'HTTPIE_CONFIG_DIR',
    os.path.expanduser('~/.httpie') if not is_windows else
    os.path.expandvars(r'%APPDATA%\\httpie')
))


class BaseConfigDict(dict):
    name = None
    helpurl = None
    about = None

    def _get_path(self) -> Path:
        """Return the config file path without side-effects."""
        raise NotImplementedError()

    def path(self) -> Path:
        """Return the config file path creating basedir, if needed."""
        path = self._get_path()
        try:
            path.parent.mkdir(mode=0o700, parents=True)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise
        return path

    def is_new(self) -> bool:
        return not self._get_path().exists()

    def load(self):
        try:
            with self.path().open('rt') as f:
                try:
                    data = json.load(f)
                except ValueError as e:
                    raise ValueError(
                        'Invalid %s JSON: %s [%s]' %
                        (type(self).__name__, str(e), self.path())
                    )
                self.update(data)
        except IOError as e:
            if e.errno != errno.ENOENT:
                raise

    def save(self, fail_silently=False):
        self['__meta__'] = {
            'httpie': __version__
        }
        if self.helpurl:
            self['__meta__']['help'] = self.helpurl

        if self.about:
            self['__meta__']['about'] = self.about

        try:
            with self.path().open('w') as f:
                json.dump(self, f, indent=4, sort_keys=True, ensure_ascii=True)
                f.write('\n')
        except IOError:
            if not fail_silently:
                raise

    def delete(self):
        try:
            self.path().unlink()
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise


class Config(BaseConfigDict):
    name = 'config'
    helpurl = 'https://httpie.org/doc#config'
    about = 'HTTPie configuration file'
    DEFAULTS = {
        'default_options': [],
        'extra_site_dirs': [],
    }

    def __init__(self, directory: Union[str, Path] = DEFAULT_CONFIG_DIR):
        super().__init__()
        self.update(self.DEFAULTS)
        self.directory = Path(directory)

    def _get_path(self) -> Path:
        return self.directory / (self.name + '.json')

    @property
    def default_options(self) -> list:
        return self['default_options']

    @property
    def extra_site_dirs(self) -> list:
        return self['extra_site_dirs']
