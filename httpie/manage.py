"""
Provides the `httpie' management command.

Note that the main `http' command points to `httpie.__main__.main()`.

"""
import argparse
from argparse import OPTIONAL

from . import __version__
from .sessions import (command_session_list,
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

session = subparsers.add_parser('session',
    help='manipulate and inspect sessions').add_subparsers()

# List
list_ = session.add_parser('list', help='list sessions')
list_.set_defaults(command=command_session_list)
list_.add_argument('host', nargs=OPTIONAL)

# Show
show = session.add_parser('show', help='show a session')
show.set_defaults(command=command_session_show)
show.add_argument('host')
show.add_argument('name')

# Edit
edit = session.add_parser(
    'edit', help='edit a session in $EDITOR')
edit.set_defaults(command=command_session_edit)
edit.add_argument('host')
edit.add_argument('name')

# Delete
delete = session.add_parser('delete', help='delete a session')
delete.set_defaults(command=command_session_delete)
delete.add_argument('host')
delete.add_argument('name', nargs=OPTIONAL,
    help='The name of the session to be deleted.'
         ' If not specified, all host sessions are deleted.')


def main():
    args = parser.parse_args()
    args.command(args)


if __name__ == '__main__':
    main()
