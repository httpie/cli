import os
import fnmatch
import subprocess
from unittest import TestCase

import pytest

from tests import TESTS_ROOT


def has_docutils():
    try:
        #noinspection PyUnresolvedReferences
        import docutils

        return True
    except ImportError:
        return False


def validate_rst(filename):
    p = subprocess.Popen(
        ['rst2pseudoxml.py', '--report=1', '--exit-status=1', filename],
         stderr=subprocess.PIPE,
         stdout=subprocess.PIPE
    )
    err = p.communicate()[1]
    assert p.returncode == 0, err


def rst_files():
    for root, dirnames, filenames in os.walk(os.path.dirname(TESTS_ROOT)):
        if '.tox' not in root:
            for filename in fnmatch.filter(filenames, '*.rst'):
                yield os.path.join(root, filename)


@pytest.mark.skipif(not has_docutils(), reason='docutils not installed')
class RSTTest(TestCase):

    def test_rst_files_syntax(self):
        paths = list(rst_files())
        assert paths, 'no .rst files found, which is weird'
        for path in paths:
            validate_rst(path)
