import os
import fnmatch
import subprocess

import pytest

from utils import TESTS_ROOT


def has_docutils():
    try:
        # noinspection PyUnresolvedReferences,PyPackageRequirements
        import docutils
        return True
    except ImportError:
        return False


def rst_filenames():
    # noinspection PyShadowingNames
    for root, dirnames, filenames in os.walk(os.path.dirname(TESTS_ROOT)):
        if '.tox' not in root:
            for filename in fnmatch.filter(filenames, '*.rst'):
                yield os.path.join(root, filename)


filenames = list(rst_filenames())
assert filenames


@pytest.mark.skipif(not has_docutils(), reason='docutils not installed')
@pytest.mark.parametrize('filename', filenames)
def test_rst_file_syntax(filename):
    p = subprocess.Popen(
        ['rst2pseudoxml.py', '--report=1', '--exit-status=1', filename],
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE
    )
    err = p.communicate()[1]
    assert p.returncode == 0, err.decode('utf8')
