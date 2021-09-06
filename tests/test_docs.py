import os

import pytest
from httpie.compat import is_windows

from .utils import TESTS_ROOT


ROOT = TESTS_ROOT.parent
SOURCE_DIRECTORIES = [
    'docs',
    'extras',
    'httpie',
    'tests',
]


def md_filenames():
    yield from ROOT.glob('*.md')
    for directory in SOURCE_DIRECTORIES:
        yield from (ROOT / directory).glob('**/*.md')


filenames = sorted(md_filenames())
assert filenames


@pytest.mark.skipif(is_windows and 'CI' in os.environ,
                    reason='Does not pass on GitHub.')
@pytest.mark.parametrize('filename', filenames)
def test_md_file_syntax(filename):
    mdformat = pytest.importorskip('mdformat._cli')
    args = ['--end-of-line', 'lf', '--number']
    err = f'Running "python -m mdformat {" ".join(args)} {filename}; git diff" should help.'
    assert mdformat.run(args + ['--check', str(filename)]) == 0, err
