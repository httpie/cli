from httpie.cli.opts_compiler import to_argparse
from httpie.cli.opts import options

parser = to_argparse(options)
