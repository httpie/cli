import sys

import responses

from .fixtures import JSON_WITH_DUPE_KEYS_FILE_PATH
from .utils import http, URL_EXAMPLE

JSON_WITH_DUPES_RAW = '{"key": 15, "key": 3, "key": 7}'
JSON_WITH_DUPES_FORMATTED_SORTED = '''{
    "key": 3,
    "key": 7,
    "key": 15
}'''
JSON_WITH_DUPES_FORMATTED_UNSORTED = '''{
    "key": 15,
    "key": 3,
    "key": 7
}'''


@responses.activate
def test_duplicate_keys_support():
    """JSON with duplicate keys should be handled correctly."""
    responses.add(responses.GET, URL_EXAMPLE, body=JSON_WITH_DUPES_RAW,
                  content_type='application/json')

    # JSON keys are sorted by default.
    if sys.version_info >= (3, 8):
        r = http('--pretty', 'format', URL_EXAMPLE)
        assert JSON_WITH_DUPES_FORMATTED_SORTED in r

    # Ensure --unsorted also does a good job.
    r = http('--unsorted', '--pretty', 'format', URL_EXAMPLE)
    assert JSON_WITH_DUPES_FORMATTED_UNSORTED in r


def test_duplicate_keys_support_from_input_file(httpbin):
    """JSON file with duplicate keys should be handled correctly."""
    # JSON keys are sorted by default.
    if sys.version_info >= (3, 8):
        r = http('--verbose', httpbin.url + '/post',
                 f'@{JSON_WITH_DUPE_KEYS_FILE_PATH}')
        # FIXME: count should be 2 (1 for the request, 1 for the response)
        #        but httpbin does not support duplicate keys.
        assert r.count(JSON_WITH_DUPES_FORMATTED_SORTED) == 1

    # Ensure --unsorted also does a good job.
    r = http('--verbose', '--unsorted', httpbin.url + '/post',
             f'@{JSON_WITH_DUPE_KEYS_FILE_PATH}')
    # FIXME: count should be 2 (1 for the request, 1 for the response)
    #        but httpbin does not support duplicate keys.
    assert r.count(JSON_WITH_DUPES_FORMATTED_UNSORTED) == 1
