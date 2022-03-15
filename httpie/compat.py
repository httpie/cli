import sys
from typing import Any, Optional, Iterable


is_windows = 'win32' in str(sys.platform).lower()


try:
    from functools import cached_property
except ImportError:
    # Can be removed once we drop Python <3.8 support.
    # Taken from `django.utils.functional.cached_property`.
    class cached_property:
        """
        Decorator that converts a method with a single self argument into a
        property cached on the instance.

        A cached property can be made out of an existing method:
        (e.g. ``url = cached_property(get_absolute_url)``).
        The optional ``name`` argument is obsolete as of Python 3.6 and will be
        deprecated in Django 4.0 (#30127).
        """
        name = None

        @staticmethod
        def func(instance):
            raise TypeError(
                'Cannot use cached_property instance without calling '
                '__set_name__() on it.'
            )

        def __init__(self, func, name=None):
            self.real_func = func
            self.__doc__ = getattr(func, '__doc__')

        def __set_name__(self, owner, name):
            if self.name is None:
                self.name = name
                self.func = self.real_func
            elif name != self.name:
                raise TypeError(
                    "Cannot assign the same cached_property to two different names "
                    "(%r and %r)." % (self.name, name)
                )

        def __get__(self, instance, cls=None):
            """
            Call the function and put the return value in instance.__dict__ so that
            subsequent attribute access on the instance returns the cached value
            instead of calling cached_property.__get__().
            """
            if instance is None:
                return self
            res = instance.__dict__[self.name] = self.func(instance)
            return res


# importlib_metadata was a provisional module, so the APIs changed quite a few times
# between 3.8-3.10. It was also not included in the standard library until 3.8, so
# we install the backport for <3.8.

if sys.version_info >= (3, 8):
    import importlib.metadata as importlib_metadata
else:
    import importlib_metadata


def find_entry_points(entry_points: Any, group: str) -> Iterable[importlib_metadata.EntryPoint]:
    if hasattr(entry_points, "select"):  # Python 3.10+ / importlib_metadata >= 3.9.0
        return entry_points.select(group=group)
    else:
        return set(entry_points.get(group, ()))


def get_dist_name(entry_point: importlib_metadata.EntryPoint) -> Optional[str]:
    dist = getattr(entry_point, "dist", None)
    if dist is not None:  # Python 3.10+
        return dist.name

    match = entry_point.pattern.match(entry_point.value)
    if not (match and match.group('module')):
        return None

    package = match.group('module').split('.')[0]
    try:
        metadata = importlib_metadata.metadata(package)
    except importlib_metadata.PackageNotFoundError:
        return None
    else:
        return metadata.get('name')


from http import cookiejar # noqa

# Requests does not carry the original policy attached to the
# cookie jar, so until it is resolved we change the global cookie
# policy.
# https://github.com/psf/requests/issues/5449

_LOCALHOST = 'localhost'
_LOCALHOST_SUFFIX = '.localhost'


class HTTPieCookiePolicy(cookiejar.DefaultCookiePolicy):
    def return_ok_secure(self, cookie, request):
        """Check whether the given cookie is sent to a secure host."""

        is_secure_protocol = super().return_ok_secure(cookie, request)
        if is_secure_protocol:
            return True

        # The original implementation of this method only takes secure protocols
        # (e.g https) into account, but the latest developments in modern browsers
        # (chrome, firefox) assume 'localhost' is also a secure location. So we
        # override it with our own strategy.
        return self._is_local_host(cookiejar.request_host(request))

    def _is_local_host(self, hostname):
        # Implements the static localhost detection algorithm in firefox.
        # https://searchfox.org/mozilla-central/rev/d4d7611ee4dd0003b492b865bc5988a4e6afc985/netwerk/dns/DNS.cpp#205-218
        return hostname == _LOCALHOST or hostname.endswith(_LOCALHOST_SUFFIX)


cookiejar.DefaultCookiePolicy = HTTPieCookiePolicy
