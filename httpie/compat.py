"""
Python 2.7, and 3.x compatibility.

"""
import sys


is_py2 = sys.version_info[0] == 2
is_py27 = sys.version_info[:2] == (2, 7)
is_py3 = sys.version_info[0] == 3
is_pypy = 'pypy' in sys.version.lower()
is_windows = 'win32' in str(sys.platform).lower()


if is_py2:
    # noinspection PyShadowingBuiltins
    bytes = str
    # noinspection PyUnresolvedReferences,PyShadowingBuiltins
    str = unicode
elif is_py3:
    # noinspection PyShadowingBuiltins
    str = str
    # noinspection PyShadowingBuiltins
    bytes = bytes


try:  # pragma: no cover
    # noinspection PyUnresolvedReferences,PyCompatibility
    from urllib.parse import urlencode
except ImportError:  # pragma: no cover
    # noinspection PyUnresolvedReferences,PyCompatibility
    from urllib import urlencode

try:  # pragma: no cover
    # noinspection PyUnresolvedReferences,PyCompatibility
    from urllib.parse import urlsplit
except ImportError:  # pragma: no cover
    # noinspection PyUnresolvedReferences,PyCompatibility
    from urlparse import urlsplit

try:  # pragma: no cover
    # noinspection PyCompatibility
    from urllib.request import urlopen
except ImportError:  # pragma: no cover
    # noinspection PyCompatibility,PyUnresolvedReferences
    from urllib2 import urlopen
