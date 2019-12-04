import os
import subprocess
from glob import glob

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


@pytest.mark.skipif(not has_docutils(), reason='docutils not installed')
@pytest.mark.parametrize('filename', filenames)
def test_rst_file_syntax(filename):
    print(filename)
    p = subprocess.Popen(
        ['rst2pseudoxml.py', '--report=1', '--exit-status=1', filename],
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE,
        shell=True,
    )
    err = p.communicate()[1]
    assert p.returncode == 0, err.decode('utf8')
