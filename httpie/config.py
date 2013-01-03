import os
import json
import errno

from . import __version__
from .compat import is_windows


DEFAULT_CONFIG_DIR = os.environ.get(
    'HTTPIE_CONFIG_DIR',
    os.path.expanduser('~/.httpie') if not is_windows else
    os.path.expandvars(r'%APPDATA%\\httpie')
)


class BaseConfigDict(dict):

    name = None
    help = None
    about = None

    directory = DEFAULT_CONFIG_DIR

    def __init__(self, directory=None, *args, **kwargs):
        super(BaseConfigDict, self).__init__(*args, **kwargs)
        if directory:
            self.directory = directory

    def __getattr__(self, item):
        return self[item]

    @property
    def path(self):
        try:
            os.makedirs(self.directory, mode=0o700)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise
        return os.path.join(self.directory, self.name + '.json')

    @property
    def is_new(self):
        return not os.path.exists(self.path)

    def load(self):
        try:
            with open(self.path, 'rt') as f:
                try:
                    data = json.load(f)
                except ValueError as e:
                    raise ValueError(
                        'Invalid %s JSON: %s [%s]' %
                        (type(self).__name__, e.message, self.path)
                    )
                self.update(data)
        except IOError as e:
            if e.errno != errno.ENOENT:
                raise

    def save(self):
        self['__meta__'] = {
            'httpie': __version__
        }
        if self.help:
            self['__meta__']['help'] = self.help

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
    help = 'https://github.com/jkbr/httpie#config'
    about = 'HTTPie configuration file'

    DEFAULTS = {
        'implicit_content_type': 'json',
        'default_options': []
    }

    def __init__(self, *args, **kwargs):
        super(Config, self).__init__(*args, **kwargs)
        self.update(self.DEFAULTS)
