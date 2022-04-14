import argparse
from typing import Any, Callable, Generic, Iterator, Iterable, Optional, TypeVar

T = TypeVar('T')


class Manual(argparse.Action):
    def __init__(
        self,
        option_strings,
        dest=argparse.SUPPRESS,
        default=argparse.SUPPRESS,
        help=None
    ):
        super().__init__(
            option_strings=option_strings,
            dest=dest,
            default=default,
            nargs=0,
            help=help
        )

    def __call__(self, parser, namespace, values, option_string=None):
        parser.print_manual()
        parser.exit()


class LazyChoices(argparse.Action, Generic[T]):
    def __init__(
        self,
        *args,
        getter: Callable[[], Iterable[T]],
        help_formatter: Optional[Callable[[T, bool], str]] = None,
        sort: bool = False,
        cache: bool = True,
        isolation_mode: bool = False,
        **kwargs
    ) -> None:
        self.getter = getter
        self.help_formatter = help_formatter
        self.sort = sort
        self.cache = cache
        self.isolation_mode = isolation_mode
        self._help: Optional[str] = None
        self._obj: Optional[Iterable[T]] = None
        super().__init__(*args, **kwargs)
        self.choices = self

    def load(self) -> T:
        if self._obj is None or not self.cache:
            self._obj = self.getter()

        assert self._obj is not None
        return self._obj

    @property
    def help(self) -> str:
        if self._help is None and self.help_formatter is not None:
            self._help = self.help_formatter(
                self.load(),
                isolation_mode=self.isolation_mode
            )
        return self._help

    @help.setter
    def help(self, value: Any) -> None:
        self._help = value

    def __contains__(self, item: Any) -> bool:
        return item in self.load()

    def __iter__(self) -> Iterator[T]:
        if self.sort:
            return iter(sorted(self.load()))
        else:
            return iter(self.load())

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values)
