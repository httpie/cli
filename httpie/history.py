from httpie.config import BaseConfigDict, get_default_config_dir
from typing import Optional
from urllib.parse import urlsplit


def get_history(host: Optional[str], url: str) -> 'History':
    hostname = host or urlsplit(url).netloc.split('@')[-1]
    if not hostname:
        hostname = 'localhost'

    history = History(f'{hostname}.json')
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

    def __init__(self, filename):
        super().__init__(self.get_history_path(filename))
        self['entries'] = []

    def add_entry(self, entry: Entry):
        self['entries'].append(entry)

    def add_entry(self, **kwargs):
        self['entries'].append((Entry(kwargs)))

    def get_entry(self, index) -> Entry:
        entries = self['entries']
        entry_dict = entries[index]
        return Entry(entry_dict)

    def get_history_str(self, count):
        history = '\n'

        i = len(self['entries']) - count

        entries = self['entries'][-count:]

        for entry in entries:
            history = history + f"{i}  {' '.join(entry['args'])}\n"
            i += 1

        return history + '\n'

    def get_history_path(self, filename):
        return get_default_config_dir() / 'history' / filename

    def __str__(self):
        return self.get_history_str(len(self['entries']))
