import argparse
import getpass
import os
import sys
from copy import deepcopy
from typing import List, Optional, Union

from .constants import DEFAULT_FORMAT_OPTIONS, SEPARATOR_CREDENTIALS
from ..sessions import VALID_SESSION_NAME_PATTERN


class KeyValueArg:
    """Base key-value pair parsed from CLI."""

    def __init__(self, key: str, value: Optional[str], sep: str, orig: str):
        self.key = key
        self.value = value
        self.sep = sep
        self.orig = orig

    def __eq__(self, other: 'KeyValueArg'):
        return self.__dict__ == other.__dict__

    def __repr__(self):
        return repr(self.__dict__)


class SessionNameValidator:

    def __init__(self, error_message: str):
        self.error_message = error_message

    def __call__(self, value: str) -> str:
        # Session name can be a path or just a name.
        if (os.path.sep not in value
                and not VALID_SESSION_NAME_PATTERN.search(value)):
            raise argparse.ArgumentError(None, self.error_message)
        return value


class Escaped(str):
    """Represents an escaped character."""

    def __repr__(self):
        return f"Escaped({repr(str(self))})"


class KeyValueArgType:
    """A key-value pair argument type used with `argparse`.

    Parses a key-value arg and constructs a `KeyValueArg` instance.
    Used for headers, form data, and other key-value pair types.

    """

    key_value_class = KeyValueArg

    def __init__(self, *separators: str):
        self.separators = separators
        self.special_characters = set()
        for separator in separators:
            self.special_characters.update(separator)

    def __call__(self, s: str) -> KeyValueArg:
        """Parse raw string arg and return `self.key_value_class` instance.

        The best of `self.separators` is determined (first found, longest).
        Back slash escaped characters aren't considered as separators
        (or parts thereof). Literal back slash characters have to be escaped
        as well (r'\\').

        """
        tokens = self.tokenize(s)

        # Sorting by length ensures that the longest one will be
        # chosen as it will overwrite any shorter ones starting
        # at the same position in the `found` dictionary.
        separators = sorted(self.separators, key=len)

        for i, token in enumerate(tokens):

            if isinstance(token, Escaped):
                continue

            found = {}
            for sep in separators:
                pos = token.find(sep)
                if pos != -1:
                    found[pos] = sep

            if found:
                # Starting first, longest separator found.
                sep = found[min(found.keys())]

                key, value = token.split(sep, 1)

                # Any preceding tokens are part of the key.
                key = ''.join(tokens[:i]) + key

                # Any following tokens are part of the value.
                value += ''.join(tokens[i + 1:])

                break

        else:
            raise argparse.ArgumentTypeError(f'{s!r} is not a valid value')

        return self.key_value_class(key=key, value=value, sep=sep, orig=s)

    def tokenize(self, s: str) -> List[Union[str, Escaped]]:
        r"""Tokenize the raw arg string

        There are only two token types - strings and escaped characters:

        >>> KeyValueArgType('=').tokenize(r'foo\=bar\\baz')
        ['foo', Escaped('='), 'bar\\\\baz']

        """
        tokens = ['']
        characters = iter(s)
        for char in characters:
            if char == '\\':
                char = next(characters, '')
                if char not in self.special_characters:
                    tokens[-1] += '\\' + char
                else:
                    tokens.extend([Escaped(char), ''])
            else:
                tokens[-1] += char
        return tokens


class PromptMixin:
    def _prompt_password(self, prompt: str) -> str:
        prompt_text = f'http: {prompt}: '
        try:
            return self._getpass(prompt_text)
        except (EOFError, KeyboardInterrupt):
            sys.stderr.write('\n')
            sys.exit(0)

    @staticmethod
    def _getpass(prompt):
        # To allow easy mocking.
        return getpass.getpass(str(prompt))


class SSLCredentials(PromptMixin):
    """Represents the passphrase for the certificate's key."""

    def __init__(self, value: Optional[str]) -> None:
        self.value = value

    def prompt_password(self, key_file: str) -> None:
        self.value = self._prompt_password(f'passphrase for {key_file}')


class AuthCredentials(KeyValueArg, PromptMixin):
    """Represents parsed credentials."""

    def has_password(self) -> bool:
        return self.value is not None

    def prompt_password(self, host: str) -> None:
        self.value = self._prompt_password(f'password for {self.key}@{host}:')


class AuthCredentialsArgType(KeyValueArgType):
    """A key-value arg type that parses credentials."""

    key_value_class = AuthCredentials

    def __call__(self, s):
        """Parse credentials from `s`.

        ("username" or "username:password").

        """
        try:
            return super().__call__(s)
        except argparse.ArgumentTypeError:
            # No password provided, will prompt for it later.
            return self.key_value_class(
                key=s,
                value=None,
                sep=SEPARATOR_CREDENTIALS,
                orig=s
            )


parse_auth = AuthCredentialsArgType(SEPARATOR_CREDENTIALS)


def readable_file_arg(filename):
    try:
        with open(filename, 'rb'):
            return filename
    except OSError as ex:
        raise argparse.ArgumentTypeError(f'{ex.filename}: {ex.strerror}')


def parse_format_options(s: str, defaults: Optional[dict]) -> dict:
    """
    Parse `s` and update `defaults` with the parsed values.

    >>> parse_format_options(
    ... defaults={'json': {'indent': 4, 'sort_keys': True}},
    ... s='json.indent:2,json.sort_keys:False',
    ... )
    {'json': {'indent': 2, 'sort_keys': False}}

    """
    value_map = {
        'true': True,
        'false': False,
    }
    options = deepcopy(defaults or {})
    for option in s.split(','):
        try:
            path, value = option.lower().split(':')
            section, key = path.split('.')
        except ValueError:
            raise argparse.ArgumentTypeError(f'invalid option {option!r}')

        if value in value_map:
            parsed_value = value_map[value]
        else:
            if value.isnumeric():
                parsed_value = int(value)
            else:
                parsed_value = value

        if defaults is None:
            options.setdefault(section, {})
        else:
            try:
                default_value = defaults[section][key]
            except KeyError:
                raise argparse.ArgumentTypeError(
                    f'invalid key {path!r}')

            default_type, parsed_type = type(default_value), type(parsed_value)
            if parsed_type is not default_type:
                raise argparse.ArgumentTypeError(
                    'invalid value'
                    f' {value!r} in {option!r}'
                    f' (expected {default_type.__name__}'
                    f' got {parsed_type.__name__})'
                )

        options[section][key] = parsed_value

    return options


PARSED_DEFAULT_FORMAT_OPTIONS = parse_format_options(
    s=','.join(DEFAULT_FORMAT_OPTIONS),
    defaults=None,
)


def response_charset_type(encoding: str) -> str:
    try:
        ''.encode(encoding)
    except LookupError:
        raise argparse.ArgumentTypeError(
            f'{encoding!r} is not a supported encoding')
    return encoding


def response_mime_type(mime_type: str) -> str:
    if mime_type.count('/') != 1:
        raise argparse.ArgumentTypeError(
            f'{mime_type!r} doesn’t look like a mime type; use type/subtype')
    return mime_type
