from collections import OrderedDict

from multidict import MultiDict, CIMultiDict


class BaseMultiDict(MultiDict):
    """
    Base class for all MultiDicts.
    """


class HTTPHeadersDict(CIMultiDict, BaseMultiDict):
    """
    Headers are case-insensitive and multiple values are supported
    through the `add()` API.
    """

    def add(self, key, value):
        """
        Add or update a new header.

        If the given `value` is `None`, then all the previous
        values will be overwritten and the value will be set
        to `None`.
        """
        if value is None:
            self[key] = value
            return None

        # If the previous value for the given header is `None`
        # then discard it since we are explicitly giving a new
        # value for it.
        if key in self and self.getone(key) is None:
            self.popone(key)

        super().add(key, value)

    def remove_item(self, key, value):
        """
        Remove a (key, value) pair from the dict.
        """
        existing_values = self.popall(key)
        existing_values.remove(value)

        for value in existing_values:
            self.add(key, value)


class RequestJSONDataDict(OrderedDict):
    pass


class MultiValueOrderedDict(OrderedDict):
    """Multi-value dict for URL parameters and form data."""

    def __setitem__(self, key, value):
        """
        If `key` is assigned more than once, `self[key]` holds a
        `list` of all the values.

        This allows having multiple fields with the same name in form
        data and URL params.

        """
        assert not isinstance(value, list)
        if key not in self:
            super().__setitem__(key, value)
        else:
            if not isinstance(self[key], list):
                super().__setitem__(key, [self[key]])
            self[key].append(value)

    def items(self):
        for key, values in super().items():
            if not isinstance(values, list):
                values = [values]
            for value in values:
                yield key, value


class RequestQueryParamsDict(MultiValueOrderedDict):
    pass


class RequestDataDict(MultiValueOrderedDict):
    pass


class MultipartRequestDataDict(MultiValueOrderedDict):
    pass


class RequestFilesDict(RequestDataDict):
    pass
