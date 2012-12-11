"""
Provides the `httpie' management command.

Note that the main `http' command points to `httpie.__main__.main()`.

"""
import inspect
import argparse
import functools

from . import __version__
from .input import RegexValidator
from .sessions import (Session, Host,
                       command_session_list,
                       command_session_edit,
                       command_session_show,
                       command_session_delete)


parser = argparse.ArgumentParser(
    description='The HTTPie management command.',
    version=__version__
)
subparsers = parser.add_subparsers()


#################################################################
# Session commands
#################################################################

hostname_validator = RegexValidator(
    Host.VALID_NAME_PATTERN,
    'Hostname contains invalid characters.'
)
session_name_validator = RegexValidator(
    Session.VALID_NAME_PATTERN,
    'Session name contains invalid characters.'
)


def make_command(func):
    @functools.wraps(func)
    def wrapper(parsed_args):
        """Convert parsed args to function kwargs."""
        kwargs = dict((name, getattr(parsed_args, name, None))
                      for name in inspect.getargspec(func).args)
        return func(**kwargs)
    return wrapper


def add_hostname_arg(parser, *args, **kwargs):
    parser.add_argument(
        'hostname', metavar='HOSTNAME',
        type=hostname_validator,
        *args, **kwargs
    )


def add_session_name_arg(parser, *args, **kwargs):
    parser.add_argument(
        'session_name', metavar='SESSION_NAME',
        type=session_name_validator,
        *args, **kwargs
    )


session = subparsers.add_parser('session',
    help='manipulate and inspect sessions').add_subparsers()

# List
session_list_parser = session.add_parser('list', help='list sessions')
session_list_parser.set_defaults(command=make_command(command_session_list))
add_hostname_arg(session_list_parser, nargs=argparse.OPTIONAL)


# Show
session_show_parser = session.add_parser('show', help='show a session')
session_show_parser.set_defaults(command=make_command(command_session_show))
add_hostname_arg(session_show_parser)
add_session_name_arg(session_show_parser)


# Edit
session_edit_parser = session.add_parser(
    'edit', help='edit a session in $EDITOR')
session_edit_parser.set_defaults(command=make_command(command_session_edit))
add_hostname_arg(session_edit_parser)
add_session_name_arg(session_edit_parser)

# Delete
session_delete_parser = session.add_parser('delete', help='delete a session')
session_delete_parser.set_defaults(
    command=make_command(command_session_delete))
add_hostname_arg(session_delete_parser)
add_session_name_arg(session_delete_parser, nargs=argparse.OPTIONAL,
    help='The name of the session to be deleted.'
         ' If not specified, all of the host\'s')


#################################################################
# Main
#################################################################


def main():
    args = parser.parse_args()
    args.command(args)


if __name__ == '__main__':
    main()
