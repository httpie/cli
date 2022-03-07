from textwrap import dedent
from httpie.cli.argparser import HTTPieManagerArgumentParser
from httpie import __version__

CLI_SESSION_UPGRADE_FLAGS = [
    {
        'flags': ['--bind-cookies'],
        'action': 'store_true',
        'default': False,
        'help': 'Bind domainless cookies to the host that session belongs.'
    }
]

COMMANDS = {
    'plugins': {
        'help': 'Manage HTTPie plugins.',
        'install': [
            'Install the given targets from PyPI '
            'or from a local paths.',
            {
                'dest': 'targets',
                'nargs': '+',
                'help': 'targets to install'
            }
        ],
        'upgrade': [
            'Upgrade the given plugins',
            {
                'dest': 'targets',
                'nargs': '+',
                'help': 'targets to upgrade'
            }
        ],
        'uninstall': [
            'Uninstall the given HTTPie plugins.',
            {
                'dest': 'targets',
                'nargs': '+',
                'help': 'targets to install'
            }
        ],
        'list': [
            'List all installed HTTPie plugins.'
        ],
    },
    'cli': {
        'help': 'Manage HTTPie for Terminal',
        'export-args': [
            'Export available options for the CLI',
            {
                'flags': ['-f', '--format'],
                'choices': ['json'],
                'default': 'json'
            }
        ],
        'sessions': {
            'help': 'Manage HTTPie sessions',
            'upgrade': [
                'Upgrade the given HTTPie session with the latest '
                'layout. A list of changes between different session versions '
                'can be found in the official documentation.',
                {
                    'dest': 'hostname',
                    'metavar': 'HOSTNAME',
                    'help': 'The host this session belongs.'
                },
                {
                    'dest': 'session',
                    'metavar': 'SESSION_NAME_OR_PATH',
                    'help': 'The name or the path for the session that will be upgraded.'
                },
                *CLI_SESSION_UPGRADE_FLAGS
            ],
            'upgrade-all': [
                'Upgrade all named sessions with the latest layout. A list of '
                'changes between different session versions can be found in the official '
                'documentation.',
                *CLI_SESSION_UPGRADE_FLAGS
            ],
        }
    }
}


def missing_subcommand(*args) -> str:
    base = COMMANDS
    for arg in args:
        base = base[arg]

    assert isinstance(base, dict)
    subcommands = ', '.join(map(repr, base.keys()))
    return f'Please specify one of these: {subcommands}'


def generate_subparsers(root, parent_parser, definitions):
    action_dest = '_'.join(parent_parser.prog.split()[1:] + ['action'])
    actions = parent_parser.add_subparsers(
        dest=action_dest
    )
    for command, properties in definitions.items():
        is_subparser = isinstance(properties, dict)
        properties = properties.copy()

        descr = properties.pop('help', None) if is_subparser else properties.pop(0)
        command_parser = actions.add_parser(command, description=descr)
        command_parser.root = root
        if is_subparser:
            generate_subparsers(root, command_parser, properties)
            continue

        for argument in properties:
            argument = argument.copy()
            flags = argument.pop('flags', [])
            command_parser.add_argument(*flags, **argument)


parser = HTTPieManagerArgumentParser(
    prog='httpie',
    description=dedent(
        '''
        Managing interface for the HTTPie itself. <https://httpie.io/docs#manager>

        Be aware that you might be looking for http/https commands for sending
        HTTP requests. This command is only available for managing the HTTTPie
        plugins and the configuration around it.
        '''
    ),
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

parser.add_argument(
    '--version',
    action='version',
    version=__version__,
    help='''
    Show version and exit.

    '''
)

generate_subparsers(parser, parser, COMMANDS)
