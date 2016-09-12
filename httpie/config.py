import os
import json
import errno

from httpie import __version__
from httpie.compat import is_windows


DEFAULT_CONFIG_DIR = str(os.environ.get(
    'HTTPIE_CONFIG_DIR',
    os.path.expanduser('~/.httpie') if not is_windows else
    os.path.expandvars(r'%APPDATA%\\httpie')
))


class BaseConfigDict(dict):

    name = None
    helpurl = None
    about = None

    def __getattr__(self, item):
        return self[item]

    def _get_path(self):
        """Return the config file path without side-effects."""
        raise NotImplementedError()

    @property
    def path(self):
        """Return the config file path creating basedir, if needed."""
        path = self._get_path()
        try:
            os.makedirs(os.path.dirname(path), mode=0o700)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise
        return path

    def is_new(self):
        return not os.path.exists(self._get_path())

    def load(self):
        try:
            with open(self.path, 'rt') as f:
                try:
                    data = json.load(f)
                except ValueError as e:
                    raise ValueError(
                        'Invalid %s JSON: %s [%s]' %
                        (type(self).__name__, str(e), self.path)
                    )
                self.update(data)
        except IOError as e:
            if e.errno != errno.ENOENT:
                raise

    def save(self):
        self['__meta__'] = {
            'httpie': __version__
        }
        if self.helpurl:
            self['__meta__']['help'] = self.helpurl

        if self.about:
            self['__meta__']['about'] = self.about

        with open(self.path, 'w') as f:
            json.dump(self, f, indent=4, sort_keys=True, ensure_ascii=True)
            f.write('\n')

    def delete(self):
        try:
            os.unlink(self.path)
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise


class Config(BaseConfigDict):

    name = 'config'
    helpurl = 'https://httpie.org/docs#config'
    about = 'HTTPie configuration file'

    DEFAULTS = {
        'default_options': []
    }

    def __init__(self, directory=DEFAULT_CONFIG_DIR):
        super(Config, self).__init__()
        self.update(self.DEFAULTS)
        self.directory = directory

    def load(self):
        super(Config, self).load()
        self._migrate_implicit_content_type()

    def _get_path(self):
        return os.path.join(self.directory, self.name + '.json')

    def _migrate_implicit_content_type(self):
        """Migrate the removed implicit_content_type config option"""
        try:
            implicit_content_type = self.pop('implicit_content_type')
        except KeyError:
            pass
        else:
            if implicit_content_type == 'form':
                self['default_options'].insert(0, '--form')
            self.save()
            self.load()
