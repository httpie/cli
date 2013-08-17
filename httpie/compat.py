"""
Python 2/3 compatibility.

"""
#noinspection PyUnresolvedReferences
from requests.compat import (
    is_windows,
    bytes,
    str,
    is_py3,
    is_py26,
)

try:
    #noinspection PyUnresolvedReferences,PyCompatibility
    from urllib.parse import urlsplit
except ImportError:
    #noinspection PyUnresolvedReferences,PyCompatibility
    from urlparse import urlsplit
