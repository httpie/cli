import pytest

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


@pytest.mark.parametrize('filename', filenames)
def test_md_file_syntax(filename):
    mdformat = pytest.importorskip('mdformat._cli')
    err = f'Running "python -m mdformat --number {filename}; git diff" should help.'
    assert mdformat.run(['--check', '--number', str(filename)]) == 0, err
