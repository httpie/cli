from __future__ import annotations

import typing
from collections import OrderedDict
from typing import Union, TypeVar

T = TypeVar("T")


class BaseMultiDictKeyView:
    """
    Basic key view for BaseMultiDict.
    """

    def __init__(self, o: BaseMultiDict) -> None:
        self._container = o

    def __iter__(self):
        for key in self._container:
            yield key

    def __contains__(self, item: str) -> bool:
        return item in self._container


class BaseMultiDict(typing.MutableMapping[str, Union[str, bytes]]):
    """
    This follow the multidict (case-insensitive) implementation but does not implement it fully.
    We scoped this class according to our needs. In the future we should be able to refactor
    HTTPie in order to use either kiss_headers.Headers or urllib3.HTTPHeaderDict.
    The main constraints are: We use bytes sometime in values, and relly on multidict specific behaviors.
    """

    def __init__(self, d: BaseMultiDict | typing.MutableMapping[str, str | bytes] | None = None, **kwargs: str | bytes) -> None:
        super().__init__()
        self._container: typing.MutableMapping[str, list[tuple[str, str | bytes]] | str] = {}

        if d is not None:
            self.update(d)

        for key, value in kwargs.items():
            self.add(key, value)

    def items(self) -> typing.Iterator[str, str | bytes | None]:
        for key_i in self._container:

            if isinstance(self._container[key_i], str):
                yield key_i, None
                continue

            for original_key, value in self._container[key_i]:
                yield original_key, value

    def keys(self) -> BaseMultiDictKeyView:
        return BaseMultiDictKeyView(self)

    def copy(self: T) -> T:
        return BaseMultiDict(self)

    def __delitem__(self, __key: str) -> None:
        del self._container[__key.lower()]

    def __len__(self) -> int:
        return len(self._container)

    def __iter__(self) -> typing.Iterator[str]:
        for key_i in self._container:
            if isinstance(self._container[key_i], list):
                yield self._container[key_i][0][0]
            else:
                yield self._container[key_i]

    def __contains__(self, item: str) -> bool:
        return item.lower() in self._container

    def update(self, __m, **kwargs) -> None:
        if hasattr(__m, "items"):
            for k in __m:
                self[k] = None
            for k, v in __m.items():
                self.add(k, v)
        else:
            for k, v in __m:
                self.add(k, v)

    def getlist(self, key: str) -> list[str | bytes]:
        key_lower = key.lower()
        values = self._container[key_lower]

        if isinstance(values, str):
            return []

        return [_[-1] for _ in self._container[key_lower]]

    def __setitem__(self, key: str | bytes, val: str | bytes | None) -> None:
        if isinstance(key, bytes):
            key = key.decode("latin-1")
        if val is not None:
            self._container[key.lower()] = [(key, val,)]
        else:
            self._container[key.lower()] = key

    def __getitem__(self, key: str) -> str | None:
        values = self._container[key.lower()]
        if isinstance(values, str):
            return None
        return ",".join([_[-1].decode() if isinstance(_[-1], bytes) else _[-1] for _ in values])

    def popone(self, key: str) -> str | bytes:
        key_lower = key.lower()

        val = self._container[key_lower].pop()

        if not self._container[key_lower]:
            self._container[key_lower] = key

        return val[-1]

    def popall(self, key: str) -> list[str]:
        key_lower = key.lower()
        values = self._container[key_lower]

        self._container[key_lower] = values[0][0]

        return [_[-1] for _ in values]

    def add(self, key: str | bytes, val: str | bytes | None) -> None:
        if isinstance(key, bytes):
            key = key.decode("latin-1")

        key_lower = key.lower()

        if val is None:
            self._container[key_lower] = key
            return

        if key_lower not in self._container or isinstance(self._container[key_lower], str):
            self._container[key_lower] = []

        self._container[key_lower].append((key, val,))

    def remove_item(self, key: str, value: str | bytes) -> None:
        """
        Remove a (key, value) pair from the dict.
        """
        key_lower = key.lower()

        to_remove = None

        for k, v in self._container[key_lower]:
            if (key == k or key == key_lower) and v == value:
                to_remove = (k, v)
                break

        if to_remove:
            self._container[key_lower].remove(to_remove)
            if not self._container[key_lower]:
                del self._container[key_lower]


class HTTPHeadersDict(BaseMultiDict):
    """
    Headers are case-insensitive and multiple values are supported
    through the `add()` API.
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
