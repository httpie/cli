from collections import Iterable

from requests.structures import CaseInsensitiveDict

from httpie.compat import OrderedDict, is_pypy, is_py27


class RequestHeadersDict(CaseInsensitiveDict):
    """
    Headers are case-insensitive and multiple values are currently not supported.

    """


class RequestJSONDataDict(OrderedDict):
    pass


class MultiValueOrderedDict(OrderedDict):
    """Multi-value dict for URL parameters and form data."""

    if is_pypy and is_py27:
        # Manually set keys when initialized with an iterable as PyPy
        # doesn't call __setitem__ in such case (pypy3 does).
        def __init__(self, *args, **kwargs):
            if len(args) == 1 and isinstance(args[0], Iterable):
                super(MultiValueOrderedDict, self).__init__(**kwargs)
                for k, v in args[0]:
                    self[k] = v
            else:
                super(MultiValueOrderedDict, self).__init__(*args, **kwargs)

    # noinspection PyMethodOverriding
    def __setitem__(self, key, value):
        """
        If `key` is assigned more than once, `self[key]` holds a
        `list` of all the values.

        This allows having multiple fields with the same name in form
        data and URL params.

        """
        assert not isinstance(value, list)
        if key not in self:
            super(MultiValueOrderedDict, self).__setitem__(key, value)
        else:
            if not isinstance(self[key], list):
                super(MultiValueOrderedDict, self).__setitem__(key, [self[key]])
            self[key].append(value)


class RequestQueryParamsDict(MultiValueOrderedDict):
    pass


class RequestDataDict(MultiValueOrderedDict):

    def items(self):
        for key, values in super(MultiValueOrderedDict, self).items():
            if not isinstance(values, list):
                values = [values]
            for value in values:
                yield key, value


class RequestFilesDict(RequestDataDict):
    pass
