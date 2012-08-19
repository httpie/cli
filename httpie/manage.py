"""
Provides the `httpie' management command.

Note that the main `http' command points to `httpie.__main__.main()`.

"""
import argparse

from . import sessions
from . import __version__


parser = argparse.ArgumentParser(
    description='The HTTPie management command.',
    version=__version__
)
subparsers = parser.add_subparsers()


# Only sessions as of now.
sessions.add_commands(subparsers)


def main():
    args = parser.parse_args()
    args.command(args)


if __name__ == '__main__':
    main()
