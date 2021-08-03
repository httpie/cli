"""Test data"""
from pathlib import Path

from httpie.constants import UTF8


def patharg(path):
    """
    Back slashes need to be escaped in ITEM args,
    even in Windows paths.

    """
    return str(path).replace('\\', '\\\\\\')


FIXTURES_ROOT = Path(__file__).parent
FILE_PATH = FIXTURES_ROOT / 'test.txt'
JSON_FILE_PATH = FIXTURES_ROOT / 'test.json'
BIN_FILE_PATH = FIXTURES_ROOT / 'test.bin'
XML_FILES_PATH = FIXTURES_ROOT / 'xmldata'
XML_FILES_VALID = list((XML_FILES_PATH / 'valid').glob('*_raw.xml'))
XML_FILES_INVALID = list((XML_FILES_PATH / 'invalid').glob('*.xml'))

FILE_PATH_ARG = patharg(FILE_PATH)
BIN_FILE_PATH_ARG = patharg(BIN_FILE_PATH)
JSON_FILE_PATH_ARG = patharg(JSON_FILE_PATH)

# Strip because we don't want new lines in the data so that we can
# easily count occurrences also when embedded in JSON (where the new
# line would be escaped).
FILE_CONTENT = FILE_PATH.read_text(encoding=UTF8).strip()


JSON_FILE_CONTENT = JSON_FILE_PATH.read_text(encoding=UTF8)
BIN_FILE_CONTENT = BIN_FILE_PATH.read_bytes()
UNICODE = FILE_CONTENT
