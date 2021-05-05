import os
import subprocess
from glob import glob
from pathlib import Path

import pytest

from utils import TESTS_ROOT


SOURCE_DIRECTORIES = [
    'extras',
    'docs',
    'httpie',
    'tests',
]


def has_recommonmark():
    try:
        # noinspection PyUnresolvedReferences,PyPackageRequirements
        import recommonmark
        return True
    except ImportError:
        return False


def md_filenames():
    cwd = os.getcwd()
    os.chdir(TESTS_ROOT.parent)
    try:
        yield from glob('*.md')
        for directory in SOURCE_DIRECTORIES:
            yield from glob(f'{directory}/**/*.md', recursive=True)
    finally:
        os.chdir(cwd)


filenames = list(sorted(md_filenames()))
assert filenames


# HACK: hardcoded paths, venv should be irrelevant, etc.
# TODO: simplify by using the Python API instead of a subprocess
#       then we wont’t need the paths.
VENV_BIN = Path(__file__).parent.parent / 'venv/bin'
VENV_PYTHON = VENV_BIN / 'python'
VENV_CM2PSEUDOXML = VENV_BIN / 'cm2pseudoxml'


@pytest.mark.skipif(
    not VENV_CM2PSEUDOXML.exists(),
    reason='remarkdown not installed',
)
@pytest.mark.parametrize('filename', filenames)
def test_cm_file_syntax(filename):
    p = subprocess.Popen(
        [
            VENV_PYTHON,
            VENV_CM2PSEUDOXML,
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
