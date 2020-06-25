import os
import subprocess
from glob import glob
from pathlib import Path

import pytest

from utils import TESTS_ROOT


SOURCE_DIRECTORIES = [
    'extras',
    'httpie',
    'tests',
]


def has_docutils():
    try:
        # noinspection PyUnresolvedReferences,PyPackageRequirements
        import docutils
        return True
    except ImportError:
        return False


def rst_filenames():
    cwd = os.getcwd()
    os.chdir(TESTS_ROOT.parent)
    try:
        yield from glob('*.rst')
        for directory in SOURCE_DIRECTORIES:
            yield from glob(f'{directory}/**/*.rst', recursive=True)
    finally:
        os.chdir(cwd)


filenames = list(sorted(rst_filenames()))
assert filenames


# HACK: hardcoded paths, venv should be irrelevant, etc.
# TODO: simplify by using the Python API instead of a subprocess
#       then we wont’t need the paths.
VENV_BIN = Path(__file__).parent.parent / 'venv/bin'
VENV_PYTHON = VENV_BIN / 'python'
VENV_RST2PSEUDOXML = VENV_BIN / 'rst2pseudoxml.py'


@pytest.mark.skipif(
    not VENV_RST2PSEUDOXML.exists(),
    reason='docutils not installed',
)
@pytest.mark.parametrize('filename', filenames)
def test_rst_file_syntax(filename):
    p = subprocess.Popen(
        [
            VENV_PYTHON,
            VENV_RST2PSEUDOXML,
            '--report=1',
            '--exit-status=1',
            filename,
        ],
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE,
        shell=True,
    )
    err = p.communicate()[1]
    assert p.returncode == 0, err.decode('utf8')
