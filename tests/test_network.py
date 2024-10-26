import argparse

import pytest

from httpie.cli.ports import (
    MAX_PORT,
    MIN_PORT,
    OUTSIDE_VALID_PORT_RANGE_ERROR,
    local_port_arg_type,
    parse_local_port_arg,
)
from httpie.compat import has_ipv6_support
from .utils import HTTP_OK, http


def test_non_existent_interface_arg(httpbin):
    """We ensure that HTTPie properly wire interface by passing an interface that does not exist. thus, we expect an error."""
    r = http(
        '--interface=1.1.1.1',
        httpbin + '/get',
        tolerate_error_exit_status=True
    )
    assert r.exit_status != 0
    assert (
        'assign requested address' in r.stderr
        or 'The requested address is not valid in its context' in r.stderr
    )


@pytest.mark.parametrize(['local_port_arg', 'expected_output'], [
    # Single ports — valid
    ('0', 0),
    ('-0', 0),
    (str(MAX_PORT), MAX_PORT),
    ('8000', 8000),
    # Single ports — invalid
    (f'{MIN_PORT - 1}', OUTSIDE_VALID_PORT_RANGE_ERROR),
    (f'{MAX_PORT + 1}', OUTSIDE_VALID_PORT_RANGE_ERROR),
    ('-', 'not a number'),
    ('AAA', 'not a number'),
    (' ', 'not a number'),
    # Port ranges — valid
    (f'{MIN_PORT}-{MAX_PORT}', (MIN_PORT, MAX_PORT)),
    ('3000-8000', (3000, 8000)),
    ('-0-8000', (0, 8000)),
    ('0-0', (0, 0)),
    # Port ranges — invalid
    (f'2-1', 'not a valid port range'),
    (f'2-', 'not a number'),
    (f'2-A', 'not a number'),
    (f'A-A', 'not a number'),
    (f'A-2', 'not a number'),
    (f'-10-1', OUTSIDE_VALID_PORT_RANGE_ERROR),
    (f'1--1', OUTSIDE_VALID_PORT_RANGE_ERROR),
    (f'-10--1', OUTSIDE_VALID_PORT_RANGE_ERROR),
    (f'1-{MAX_PORT + 1}', OUTSIDE_VALID_PORT_RANGE_ERROR),
])
def test_parse_local_port_arg(local_port_arg, expected_output):
    expected_error = expected_output if isinstance(expected_output, str) else None
    if not expected_error:
        assert parse_local_port_arg(local_port_arg) == expected_output
    else:
        with pytest.raises(argparse.ArgumentTypeError, match=expected_error):
            parse_local_port_arg(local_port_arg)


def test_local_port_arg_type():
    assert local_port_arg_type('1') == 1
    assert local_port_arg_type('1-1') == 1
    assert local_port_arg_type('1-3') in {1, 2, 3}


def test_invoke_with_out_of_range_local_port_arg(httpbin):
    # An addition to the unittest tests
    r = http(
        '--local-port=70000',
        httpbin + '/get',
        tolerate_error_exit_status=True
    )
    assert r.exit_status != 0
    assert OUTSIDE_VALID_PORT_RANGE_ERROR in r.stderr


@pytest.mark.parametrize('interface_arg', [
    '',
    '-',
    '10.25.a.u',
    'abc',
    'localhost',
])
def test_invalid_interface_arg(httpbin, interface_arg):
    r = http(
        '--interface',
        interface_arg,
        httpbin + '/get',
        tolerate_error_exit_status=True,
    )
    assert f"'{interface_arg}' does not appear to be an IPv4 or IPv6" in r.stderr


def test_force_ipv6_on_unsupported_system(remote_httpbin):
    orig = has_ipv6_support()
    has_ipv6_support(False)
    try:
        r = http(
            '-6',
            remote_httpbin + '/get',
            tolerate_error_exit_status=True,
        )
    finally:
        has_ipv6_support(orig)
    assert 'Unable to force IPv6 because your system lack IPv6 support.' in r.stderr


def test_force_both_ipv6_and_ipv4(remote_httpbin):
    r = http(
        '-6',  # force IPv6
        '-4',  # force IPv4
        remote_httpbin + '/get',
        tolerate_error_exit_status=True,
    )

    assert 'Unable to force both IPv4 and IPv6, omit the flags to allow both.' in r.stderr


def test_happy_eyeballs(remote_httpbin_secure):
    r = http(
        '--heb',  # this will automatically and concurrently try IPv6 and IPv4 endpoints
        '--verify=no',
        remote_httpbin_secure + '/get',
    )

    assert r.exit_status == 0
    assert HTTP_OK in r
