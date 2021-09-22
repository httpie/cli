import json
import re
from typing import Tuple

from ..utils import load_json_preserve_order_and_dupe_keys
from .lexers.json import PREFIX_REGEX


def load_prefixed_json(data: str) -> Tuple[str, json.JSONDecoder]:
    """Simple JSON loading from `data`.

    """
    # First, the full data.
    try:
        return '', load_json_preserve_order_and_dupe_keys(data)
    except ValueError:
        pass

    # Then, try to find the start of the actual body.
    data_prefix, body = parse_prefixed_json(data)
    try:
        return data_prefix, load_json_preserve_order_and_dupe_keys(body)
    except ValueError:
        raise ValueError('Invalid JSON')


def parse_prefixed_json(data: str) -> Tuple[str, str]:
    """Find the potential JSON body from `data`.

    Sometimes the JSON body is prefixed with a XSSI magic string, specific to the server.
    Return a tuple (data prefix, actual JSON body).

    """
    matches = re.findall(PREFIX_REGEX, data)
    data_prefix = matches[0] if matches else ''
    body = data[len(data_prefix):]
    return data_prefix, body


def parse_header_content_type(line):
    """Parse a Content-Type like header.
    Return the main Content-Type and a dictionary of options.
        >>> parse_header_content_type('application/xml; charset=utf-8')
        ('application/xml', {'charset': 'utf-8'})
        >>> parse_header_content_type('application/xml; charset = utf-8')
        ('application/xml', {'charset': 'utf-8'})
        >>> parse_header_content_type('application/html+xml;ChArSeT="UTF-8"')
        ('application/html+xml', {'charset': 'UTF-8'})
        >>> parse_header_content_type('application/xml')
        ('application/xml', {})
        >>> parse_header_content_type(';charset=utf-8')
        ('', {'charset': 'utf-8'})
        >>> parse_header_content_type('charset=utf-8')
        ('', {'charset': 'utf-8'})
        >>> parse_header_content_type('multipart/mixed; boundary="gc0pJq0M:08jU534c0p"')
        ('multipart/mixed', {'boundary': 'gc0pJq0M:08jU534c0p'})
        >>> parse_header_content_type('Message/Partial; number=3; total=3; id="oc=jpbe0M2Yt4s@foo.com"')
        ('Message/Partial', {'number': '3', 'total': '3', 'id': 'oc=jpbe0M2Yt4s@foo.com'})
    """
    # Source: https://github.com/python/cpython/blob/bb3e0c2/Lib/cgi.py#L230

    def _parseparam(s: str):
        # Source: https://github.com/python/cpython/blob/bb3e0c2/Lib/cgi.py#L218
        while s[:1] == ';':
            s = s[1:]
            end = s.find(';')
            while end > 0 and (s.count('"', 0, end) - s.count('\\"', 0, end)) % 2:
                end = s.find(';', end + 1)
            if end < 0:
                end = len(s)
            f = s[:end]
            yield f.strip()
            s = s[end:]

    # Special case: 'key=value' only (without starting with ';').
    if ';' not in line and '=' in line:
        line = ';' + line

    parts = _parseparam(';' + line)
    key = parts.__next__()
    pdict = {}
    for p in parts:
        i = p.find('=')
        if i >= 0:
            name = p[:i].strip().lower()
            value = p[i + 1:].strip()
            if len(value) >= 2 and value[0] == value[-1] == '"':
                value = value[1:-1]
                value = value.replace('\\\\', '\\').replace('\\"', '"')
            pdict[name] = value
    return key, pdict
