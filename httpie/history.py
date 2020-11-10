from httpie.config import BaseConfigDict, get_default_config_dir
from typing import Optional
from urllib.parse import urlsplit
from pathlib import Path


HISTORY_DIR_NAME = 'history'

def get_history(config_dir: Path, host: Optional[str], url: str) -> 'History':
    hostname = host or urlsplit(url).netloc.split('@')[-1]
    if not hostname:
        hostname = 'localhost'

    path = config_dir / HISTORY_DIR_NAME / f'{hostname}.json'

    history = History(path)
    history.load()

    return history


class EntryNotFound(Exception):
    pass


class Entry(dict):

    def __init__(self, data):
        self.update(data)

    def get_args(self):
        return self['args']


class History(BaseConfigDict):

    def __init__(self, path: Path):
        super().__init__(path)
        self['entries'] = []

    def add_entry(self, **kwargs):
        self['entries'].append((Entry(kwargs)))

    def get_entry(self, index) -> Entry:
        try:
            entry_dict = self['entries'][index - 1]
        except IndexError:
            raise EntryNotFound()

        return Entry(entry_dict)

    def get_history_str(self, count):
        history = '\n'

        i = 1

        entries = self['entries']

        for entry in entries:
            history = history + f"{i}  {' '.join(entry['args'][1:])}\n"
            i += 1

        return history + '\n'

    def __str__(self):
        return self.get_history_str(len(self['entries']))
