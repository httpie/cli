import os

from tests import TESTS_ROOT
from httpie.compat import bytes


def patharg(path):
    """Back slashes need to be escaped in ITEM args, even in Windows paths."""
    return path.replace('\\', '\\\\\\')


### Test files
FILE_PATH = os.path.join(TESTS_ROOT, 'fixtures', 'test.txt')
JSON_FILE_PATH = os.path.join(TESTS_ROOT, 'fixtures', 'test.json')
BIN_FILE_PATH = os.path.join(TESTS_ROOT, 'fixtures', 'test.bin')

FILE_PATH_ARG = patharg(FILE_PATH)
BIN_FILE_PATH_ARG = patharg(BIN_FILE_PATH)
JSON_FILE_PATH_ARG = patharg(JSON_FILE_PATH)

with open(FILE_PATH) as f:
    # Strip because we don't want new lines in the data so that we can
    # easily count occurrences also when embedded in JSON (where the new
    # line would be escaped).
    FILE_CONTENT = f.read().strip()
    if isinstance(FILE_CONTENT, bytes):
        # Python < 3.0
        FILE_CONTENT = FILE_CONTENT.decode('utf8')
with open(BIN_FILE_PATH, 'rb') as f:
    BIN_FILE_CONTENT = f.read()
with open(JSON_FILE_PATH, 'rb') as f:
    JSON_FILE_CONTENT = f.read()
