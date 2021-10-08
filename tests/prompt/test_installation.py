"""Test if http-prompt is installed correctly."""

import subprocess

import pytest

from subprocess import PIPE

from .utils import get_http_prompt_path
from httpie.prompt import __version__


def run_http_prompt(args):
    """Run http-prompt from terminal."""
    bin_path = get_http_prompt_path()
    p = subprocess.Popen([bin_path] + args, stdin=PIPE, stdout=PIPE)
    return p.communicate()


@pytest.mark.slow
def test_help():
    out, err = run_http_prompt(['--help'])
    assert out.startswith(b'Usage: http-prompt')


@pytest.mark.slow
def test_version():
    out, err = run_http_prompt(['--version'])
    version = __version__
    if hasattr(version, 'encode'):
        version = version.encode('ascii')
    assert out.rstrip() == version
