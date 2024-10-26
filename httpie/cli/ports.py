from __future__ import annotations

import argparse
from random import randint
from typing import Tuple


MIN_PORT = 0
MAX_PORT = 65535
OUTSIDE_VALID_PORT_RANGE_ERROR = f'outside valid port range {MIN_PORT}-{MAX_PORT}'


def local_port_arg_type(port: str) -> int:
    port = parse_local_port_arg(port)
    if isinstance(port, tuple):
        port = randint(*port)
    return port


def parse_local_port_arg(port: str) -> int | Tuple[int, int]:
    if '-' in port[1:]:  # Don’t treat negative port as range.
        return _clean_port_range(port)
    return _clean_port(port)


def _clean_port_range(port_range: str) -> Tuple[int, int]:
    """
    We allow two digits separated by a hyphen to represent a port range.

    The parsing is done so that even negative numbers get parsed correctly, allowing us to
    give a more specific outside-range error message.

    """
    sep_pos = port_range.find('-', 1)
    start, end = port_range[:sep_pos], port_range[sep_pos + 1:]
    start = _clean_port(start)
    end = _clean_port(end)
    if start > end:
        raise argparse.ArgumentTypeError(f'{port_range!r} is not a valid port range')
    return start, end


def _clean_port(port: str) -> int:
    try:
        port = int(port)
    except ValueError:
        raise argparse.ArgumentTypeError(f'{port!r} is not a number')
    if not (MIN_PORT <= port <= MAX_PORT):
        raise argparse.ArgumentTypeError(
            f'{port!r} is {OUTSIDE_VALID_PORT_RANGE_ERROR}'
        )
    return port
