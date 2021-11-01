from httpie.cli.argparser import BaseHTTPieArgumentParser

COMMANDS = {
    "plugins": {
        "install": [
            {
                "dest": "targets",
                "nargs": "+",
                "help": "targets to install"
            }
        ],
        "uninstall": [
            {
                "dest": "targets",
                "nargs": "+",
                "help": "targets to install"
            }
        ],
        "list": []
    },
}


def generate_subparsers(parent_parser, definitions):
    action_dest = "_".join(parent_parser.prog.split()[1:] + ["action"])
    actions = parent_parser.add_subparsers(
        dest=action_dest
    )
    for command, properties in definitions.items():
        command_parser = actions.add_parser(command)
        if isinstance(properties, dict):
            generate_subparsers(command_parser, properties)
            continue

        for argument in properties:
            command_parser.add_argument(**argument)


parser = BaseHTTPieArgumentParser(
    prog="httpie"
)
parser.add_argument(
    '--debug',
    action='store_true',
    default=False,
    help='''
    Prints the exception traceback should one occur, as well as other
    information useful for debugging HTTPie itself and for reporting bugs.

    '''
)
parser.add_argument(
    '--traceback',
    action='store_true',
    default=False,
    help='''
    Prints the exception traceback should one occur.

    '''
)

generate_subparsers(parser, COMMANDS)
