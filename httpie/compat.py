import sys


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
