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
