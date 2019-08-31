import argparse
import getpass
import os
import sys

from httpie.cli.constants import SEPARATOR_CREDENTIALS
from httpie.sessions import VALID_SESSION_NAME_PATTERN


class KeyValueArg:
    """Base key-value pair parsed from CLI."""

    def __init__(self, key, value, sep, orig):
        self.key = key
        self.value = value
        self.sep = sep
        self.orig = orig

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __repr__(self):
        return repr(self.__dict__)


class SessionNameValidator:

    def __init__(self, error_message):
        self.error_message = error_message

    def __call__(self, value):
        # Session name can be a path or just a name.
        if (os.path.sep not in value
                and not VALID_SESSION_NAME_PATTERN.search(value)):
            raise argparse.ArgumentError(None, self.error_message)
        return value


class Escaped(str):
    """Represents an escaped character."""


class KeyValueArgType:
    """A key-value pair argument type used with `argparse`.

    Parses a key-value arg and constructs a `KeyValuArge` instance.
    Used for headers, form data, and other key-value pair types.

    """

    key_value_class = KeyValueArg

    def __init__(self, *separators):
        self.separators = separators
        self.special_characters = set('\\')
        for separator in separators:
            self.special_characters.update(separator)

    def __call__(self, string) -> KeyValueArg:
        """Parse `string` and return `self.key_value_class()` instance.

        The best of `self.separators` is determined (first found, longest).
        Back slash escaped characters aren't considered as separators
        (or parts thereof). Literal back slash characters have to be escaped
        as well (r'\\').

        """

        def tokenize(string):
            r"""Tokenize `string`. There are only two token types - strings
            and escaped characters:

            tokenize(r'foo\=bar\\baz')
            => ['foo', Escaped('='), 'bar', Escaped('\\'), 'baz']

            """
            tokens = ['']
            characters = iter(string)
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

        tokens = tokenize(string)

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
            raise argparse.ArgumentTypeError(
                u'"%s" is not a valid value' % string)

        return self.key_value_class(
            key=key, value=value, sep=sep, orig=string)


class AuthCredentials(KeyValueArg):
    """Represents parsed credentials."""

    def _getpass(self, prompt):
        # To allow mocking.
        return getpass.getpass(str(prompt))

    def has_password(self):
        return self.value is not None

    def prompt_password(self, host):
        try:
            self.value = self._getpass(
                'http: password for %s@%s: ' % (self.key, host))
        except (EOFError, KeyboardInterrupt):
            sys.stderr.write('\n')
            sys.exit(0)


class AuthCredentialsArgType(KeyValueArgType):
    """A key-value arg type that parses credentials."""

    key_value_class = AuthCredentials

    def __call__(self, string):
        """Parse credentials from `string`.

        ("username" or "username:password").

        """
        try:
            return super().__call__(string)
        except argparse.ArgumentTypeError:
            # No password provided, will prompt for it later.
            return self.key_value_class(
                key=string,
                value=None,
                sep=SEPARATOR_CREDENTIALS,
                orig=string
            )


parse_auth = AuthCredentialsArgType(SEPARATOR_CREDENTIALS)


def readable_file_arg(filename):
    try:
        with open(filename, 'rb'):
            return filename
    except IOError as ex:
        raise argparse.ArgumentTypeError('%s: %s' % (filename, ex.args[1]))
