import os
import pickle
import errno
from requests import Session

from .config import CONFIG_DIR


SESSIONS_DIR = os.path.join(CONFIG_DIR, 'sessions')


def get_response(name, request_kwargs):
    session = load(name)
    session_kwargs, request_kwargs = split_kwargs(request_kwargs)
    headers = session_kwargs.pop('headers', None)
    if headers:
        session.headers.update(headers)
    session.__dict__.update(session_kwargs)
    try:
        response = session.request(**request_kwargs)
    except Exception:
        raise
    else:
        save(session, name)
        return response


def split_kwargs(requests_kwargs):
    session = {}
    request = {}
    session_attrs = [
        'auth', 'timeout',
        'verify', 'proxies',
        'params'
    ]

    for k, v in requests_kwargs.items():
        if v is not None:
            if k in session_attrs:
                session[k] = v
            else:
                request[k] = v
    return session, request


def get_path(name):
    try:
        os.makedirs(SESSIONS_DIR, mode=0o700)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

    return os.path.join(SESSIONS_DIR, name + '.pickle')


def load(name):
    try:
        with open(get_path(name), 'rb') as f:
            return pickle.load(f)
    except IOError as e:
        if e.errno != errno.ENOENT:
            raise
        return Session()


def save(session, name):
    with open(get_path(name), 'wb') as f:
        pickle.dump(session, f)
