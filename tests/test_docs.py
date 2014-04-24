import os
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


def get_readme_errors():
    p = subprocess.Popen([
        'rst2pseudoxml.py',
        '--report=1',
        '--exit-status=1',
        os.path.join(TESTS_ROOT, '..', 'README.rst')
    ], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    err = p.communicate()[1]
    if p.returncode:
        return err


class READMETest(TestCase):

    @pytest.mark.skipif(not has_docutils(), reason='docutils not installed')
    def test_README_reStructuredText_valid(self):
        errors = get_readme_errors()
        assert not errors, errors
