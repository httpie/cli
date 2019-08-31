from collections import OrderedDict

from requests.structures import CaseInsensitiveDict


class RequestHeadersDict(CaseInsensitiveDict):
    """
    Headers are case-insensitive and multiple values are currently not supported.

    """


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
