import json

import pytest
import responses

from httpie.cli.constants import PRETTY_MAP
from httpie.cli.exceptions import ParseError
from httpie.compat import is_windows
from httpie.output.formatters.colors import ColorFormatter
from httpie.utils import JsonDictPreservingDuplicateKeys

from .fixtures import JSON_WITH_DUPE_KEYS_FILE_PATH
from .utils import MockEnvironment, http, DUMMY_URL

TEST_JSON_XXSI_PREFIXES = [
    r")]}',\n",
    ")]}',",
    'while(1);',
    'for(;;)',
    ')',
    ']',
    '}',
]
TEST_JSON_VALUES = [
    # FIXME: missing int & float
    {},
    {'a': 0, 'b': 0},
    [],
    ['a', 'b'],
    'foo',
    True,
    False,
    None,
]
TEST_PREFIX_TOKEN_COLOR = '\x1b[38;5;15m' if is_windows else '\x1b[04m\x1b[91m'

JSON_WITH_DUPES_RAW = '{"key": 15, "key": 15, "key": 3, "key": 7}'
JSON_WITH_DUPES_FORMATTED_SORTED = '''{
    "key": 3,
    "key": 7,
    "key": 15,
    "key": 15
}'''
JSON_WITH_DUPES_FORMATTED_UNSORTED = '''{
    "key": 15,
    "key": 15,
    "key": 3,
    "key": 7
}'''


@pytest.mark.parametrize('data_prefix', TEST_JSON_XXSI_PREFIXES)
@pytest.mark.parametrize('json_data', TEST_JSON_VALUES)
@pytest.mark.parametrize('pretty', PRETTY_MAP.keys())
@responses.activate
def test_json_formatter_with_body_preceded_by_non_json_data(data_prefix, json_data, pretty):
    """Test JSON bodies preceded by non-JSON data."""
    body = data_prefix + json.dumps(json_data)
    content_type = 'application/json;charset=utf8'
    responses.add(
        responses.GET,
        DUMMY_URL,
        body=body,
        content_type=content_type,
    )

    colored_output = pretty in {'all', 'colors'}
    env = MockEnvironment(colors=256) if colored_output else None
    r = http('--pretty', pretty, DUMMY_URL, env=env)

    indent = None if pretty in {'none', 'colors'} else 4
    expected_body = data_prefix + json.dumps(json_data, indent=indent)
    if colored_output:
        fmt = ColorFormatter(env, format_options={'json': {'format': True, 'indent': 4}})
        expected_body = fmt.format_body(expected_body, content_type)
        # Check to ensure the non-JSON data prefix is colored only one time,
        # meaning it was correctly handled as a whole.
        assert TEST_PREFIX_TOKEN_COLOR + data_prefix in expected_body, expected_body
    assert expected_body in r


@responses.activate
def test_duplicate_keys_support_from_response():
    """JSON with duplicate keys should be handled correctly."""
    responses.add(
        responses.GET,
        DUMMY_URL,
        body=JSON_WITH_DUPES_RAW,
        content_type='application/json',
    )
    args = ('--pretty', 'format', DUMMY_URL)

    # Check implicit --sorted
    if JsonDictPreservingDuplicateKeys.SUPPORTS_SORTING:
        r = http(*args)
        assert JSON_WITH_DUPES_FORMATTED_SORTED in r

    # Check --unsorted
    r = http(*args, '--unsorted')
    assert JSON_WITH_DUPES_FORMATTED_UNSORTED in r


def test_duplicate_keys_support_from_input_file():
    """JSON file with duplicate keys should be handled correctly."""
    args = (
        '--verbose',
        '--offline',
        DUMMY_URL,
        f'@{JSON_WITH_DUPE_KEYS_FILE_PATH}',
    )

    # Check implicit --sorted
    if JsonDictPreservingDuplicateKeys.SUPPORTS_SORTING:
        r = http(*args)
        assert JSON_WITH_DUPES_FORMATTED_SORTED in r

    # Check --unsorted
    r = http(*args, '--unsorted')
    assert JSON_WITH_DUPES_FORMATTED_UNSORTED in r


@pytest.mark.parametrize("value", [
    1,
    1.1,
    True,
    'some_value'
])
def test_simple_json_arguments_with_non_json(httpbin, value):
    r = http(
        '--form',
        httpbin + '/post',
        f'option:={json.dumps(value)}',
    )
    assert r.json['form'] == {'option': str(value)}


@pytest.mark.parametrize("request_type", [
    "--form",
    "--multipart",
])
@pytest.mark.parametrize("value", [
    [1, 2, 3],
    {'a': 'b'},
    None
])
def test_complex_json_arguments_with_non_json(httpbin, request_type, value):
    with pytest.raises(ParseError) as cm:
        http(
            request_type,
            httpbin + '/post',
            f'option:={json.dumps(value)}',
        )

    cm.match('Can\'t use complex JSON value types')
