import json

import pytest
import responses

from httpie.cli.constants import PRETTY_MAP
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


@pytest.mark.parametrize('input_json, expected_json', [
    # Examples taken from https://www.w3.org/TR/html-json-forms/
    (
        ['bottle-on-wall:=1', 'bottle-on-wall:=2', 'bottle-on-wall:=3'],
        {'bottle-on-wall': [1, 2, 3]},
    ),
    (
        ['pet[species]=Dahut', 'pet[name]:="Hypatia"', 'kids[1]=Thelma', 'kids[0]:="Ashley"'],
        {'pet': {'species': 'Dahut', 'name': 'Hypatia'}, 'kids': ['Ashley', 'Thelma']},
    ),
    (
        ['pet[0][species]=Dahut', 'pet[0][name]=Hypatia', 'pet[1][species]=Felis Stultus', 'pet[1][name]:="Billie"'],
        {'pet': [{'species': 'Dahut', 'name': 'Hypatia'}, {'species': 'Felis Stultus', 'name': 'Billie'}]},
    ),
    (
        ['wow[such][deep][3][much][power][!]=Amaze'],
        {'wow': {'such': {'deep': [None, None, None, {'much': {'power': {'!': 'Amaze'}}}]}}},
    ),
    (
        ['mix=scalar', 'mix[0]=array 1', 'mix[2]:="array 2"', 'mix[key]:="key key"', 'mix[car]=car key'],
        {'mix': {'': 'scalar', '0': 'array 1', '2': 'array 2', 'key': 'key key', 'car': 'car key'}},
    ),
    (
        ['highlander[]=one'],
        {'highlander': ['one']},
    ),
    (
        ['error[good]=BOOM!', 'error[bad:="BOOM BOOM!"'],
        {'error': {'good': 'BOOM!'}, 'error[bad': 'BOOM BOOM!'},
    ),
    (
        ['special[]:=true', 'special[]:=false', 'special[]:="true"', 'special[]:=null'],
        {'special': [True, False, 'true', None]},
    ),
    (
        [r'\[\]:=1', r'escape\[d\]:=1', r'escaped\[\]:=1', r'e\[s\][c][a][p]\[ed\][]:=1'],
        {'[]': 1, 'escape[d]': 1, 'escaped[]': 1, 'e[s]': {'c': {'a': {'p': {'[ed]': [1]}}}}},
    ),
    (
        ['[]:=1', '[]=foo'],
        {'': [1, 'foo']},
    ),
    (
        [']:=1', '[]1:=1', '[1]]:=1'],
        {']': 1, '[]1': 1, '[1]]': 1},
    ),
])
def test_nested_json_syntax(input_json, expected_json, httpbin_both):
    r = http(httpbin_both + '/post', *input_json)
    assert r.json['json'] == expected_json


def test_nested_json_sparse_array(httpbin_both):
    r = http(httpbin_both + '/post', 'test[0]:=1', 'test[100]:=1')
    assert len(r.json['json']['test']) == 101
