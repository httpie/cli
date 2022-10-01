import json

import pytest
import responses

from httpie.cli.constants import PRETTY_MAP
from httpie.cli.exceptions import ParseError
from httpie.cli.nested_json import NestedJSONSyntaxError
from httpie.output.formatters.colors import ColorFormatter
from httpie.utils import JsonDictPreservingDuplicateKeys

from .fixtures import (
    FILE_CONTENT,
    FILE_PATH,
    JSON_FILE_CONTENT,
    JSON_FILE_PATH,
    JSON_WITH_DUPE_KEYS_FILE_PATH,
)
from .utils import DUMMY_URL, MockEnvironment, http

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
TEST_PREFIX_TOKEN_COLOR = '\x1b[04m\x1b[91m'

JSON_WITH_DUPES_RAW = '{"key": 15, "key": 15, "key": 3, "key": 7}'
JSON_WITH_DUPES_FORMATTED_SORTED = """{
    "key": 3,
    "key": 7,
    "key": 15,
    "key": 15
}"""
JSON_WITH_DUPES_FORMATTED_UNSORTED = """{
    "key": 15,
    "key": 15,
    "key": 3,
    "key": 7
}"""


@pytest.mark.parametrize('data_prefix', TEST_JSON_XXSI_PREFIXES)
@pytest.mark.parametrize('json_data', TEST_JSON_VALUES)
@pytest.mark.parametrize('pretty', PRETTY_MAP.keys())
@responses.activate
def test_json_formatter_with_body_preceded_by_non_json_data(
    data_prefix, json_data, pretty
):
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
        fmt = ColorFormatter(
            env, format_options={'json': {'format': True, 'indent': 4}}
        )
        expected_body = fmt.format_body(expected_body, content_type)
        # Check to ensure the non-JSON data prefix is colored only one time,
        # meaning it was correctly handled as a whole.
        assert (
            TEST_PREFIX_TOKEN_COLOR + data_prefix in expected_body
        ), expected_body
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


@pytest.mark.parametrize('value', [1, 1.1, True, 'some_value'])
def test_simple_json_arguments_with_non_json(httpbin, value):
    r = http(
        '--form',
        httpbin + '/post',
        f'option:={json.dumps(value)}',
    )
    assert r.json['form'] == {'option': str(value)}


@pytest.mark.parametrize(
    'request_type',
    [
        '--form',
        '--multipart',
    ],
)
@pytest.mark.parametrize('value', [[1, 2, 3], {'a': 'b'}, None])
def test_complex_json_arguments_with_non_json(httpbin, request_type, value):
    with pytest.raises(ParseError) as cm:
        http(
            request_type,
            httpbin + '/post',
            f'option:={json.dumps(value)}',
        )

    cm.match('Cannot use complex JSON value types')


@pytest.mark.parametrize(
    'input_json, expected_json',
    [
        # Examples taken from https://www.w3.org/TR/html-json-forms/
        (
            [
                'bottle-on-wall[]:=1',
                'bottle-on-wall[]:=2',
                'bottle-on-wall[]:=3',
            ],
            {'bottle-on-wall': [1, 2, 3]},
        ),
        (
            [
                'pet[species]=Dahut',
                'pet[name]:="Hypatia"',
                'kids[1]=Thelma',
                'kids[0]:="Ashley"',
            ],
            {
                'pet': {'species': 'Dahut', 'name': 'Hypatia'},
                'kids': ['Ashley', 'Thelma'],
            },
        ),
        (
            [
                'pet[0][species]=Dahut',
                'pet[0][name]=Hypatia',
                'pet[1][species]=Felis Stultus',
                'pet[1][name]:="Billie"',
            ],
            {
                'pet': [
                    {'species': 'Dahut', 'name': 'Hypatia'},
                    {'species': 'Felis Stultus', 'name': 'Billie'},
                ]
            },
        ),
        (
            ['wow[such][deep][3][much][power][!]=Amaze'],
            {
                'wow': {
                    'such': {
                        'deep': [
                            None,
                            None,
                            None,
                            {'much': {'power': {'!': 'Amaze'}}},
                        ]
                    }
                }
            },
        ),
        (
            ['mix[]=scalar', 'mix[2]=something', 'mix[4]:="something 2"'],
            {'mix': ['scalar', None, 'something', None, 'something 2']},
        ),
        (
            ['highlander[]=one'],
            {'highlander': ['one']},
        ),
        (
            ['error[good]=BOOM!', r'error\[bad:="BOOM BOOM!"'],
            {'error': {'good': 'BOOM!'}, 'error[bad': 'BOOM BOOM!'},
        ),
        (
            [
                'special[]:=true',
                'special[]:=false',
                'special[]:="true"',
                'special[]:=null',
            ],
            {'special': [True, False, 'true', None]},
        ),
        (
            [
                r'\[\]:=1',
                r'escape\[d\]:=1',
                r'escaped\[\]:=1',
                r'e\[s\][c][a][p][\[ed\]][]:=1',
            ],
            {
                '[]': 1,
                'escape[d]': 1,
                'escaped[]': 1,
                'e[s]': {'c': {'a': {'p': {'[ed]': [1]}}}},
            },
        ),
        (
            ['[]:=1', '[]=foo'],
            [1, 'foo'],
        ),
        (
            [r'\]:=1', r'\[\]1:=1', r'\[1\]\]:=1'],
            {']': 1, '[]1': 1, '[1]]': 1},
        ),
        (
            [
                r'foo\[bar\][baz]:=1',
                r'foo\[bar\]\[baz\]:=3',
                r'foo[bar][\[baz\]]:=4',
            ],
            {
                'foo[bar]': {'baz': 1},
                'foo[bar][baz]': 3,
                'foo': {'bar': {'[baz]': 4}},
            },
        ),
        (
            ['key[]:=1', 'key[][]:=2', 'key[][][]:=3', 'key[][][]:=4'],
            {'key': [1, [2], [[3]], [[4]]]},
        ),
        (
            ['x[0]:=1', 'x[]:=2', 'x[]:=3', 'x[][]:=4', 'x[][]:=5'],
            {'x': [1, 2, 3, [4], [5]]},
        ),
        (
            [
                f'x=@{FILE_PATH}',
                f'y[z]=@{FILE_PATH}',
                f'q[u][]:=@{JSON_FILE_PATH}',
            ],
            {
                'x': FILE_CONTENT,
                'y': {'z': FILE_CONTENT},
                'q': {'u': [json.loads(JSON_FILE_CONTENT)]},
            },
        ),
        (
            [
                'foo[bar][5][]:=5',
                'foo[bar][]:=6',
                'foo[bar][][]:=7',
                'foo[bar][][x]=dfasfdas',
                'foo[baz]:=[1, 2, 3]',
                'foo[baz][]:=4',
            ],
            {
                'foo': {
                    'bar': [
                        None,
                        None,
                        None,
                        None,
                        None,
                        [5],
                        6,
                        [7],
                        {'x': 'dfasfdas'},
                    ],
                    'baz': [1, 2, 3, 4],
                }
            },
        ),
        (
            [
                'foo[]:=1',
                'foo[]:=2',
                'foo[][key]=value',
                'foo[2][key 2]=value 2',
                r'foo[2][key \[]=value 3',
                r'bar[nesting][under][!][empty][?][\\key]:=4',
            ],
            {
                'foo': [
                    1,
                    2,
                    {'key': 'value', 'key 2': 'value 2', 'key [': 'value 3'},
                ],
                'bar': {
                    'nesting': {'under': {'!': {'empty': {'?': {'\\key': 4}}}}}
                },
            },
        ),
        (
            [
                r'foo\[key\]:=1',
                r'bar\[1\]:=2',
                r'baz\[\]:3',
                r'quux[key\[escape\]]:=4',
                r'quux[key 2][\\][\\\\][\\\[\]\\\]\\\[\n\\]:=5',
            ],
            {
                'foo[key]': 1,
                'bar[1]': 2,
                'quux': {
                    'key[escape]': 4,
                    'key 2': {'\\': {'\\\\': {'\\[]\\]\\[\\n\\': 5}}},
                },
            },
        ),
        (
            [r'A[B\\]=C', r'A[B\\\\]=C', r'A[\B\\]=C'],
            {'A': {'B\\': 'C', 'B\\\\': 'C', '\\B\\': 'C'}},
        ),
        (
            [
                'name=python',
                'version:=3',
                'date[year]:=2021',
                'date[month]=December',
                'systems[]=Linux',
                'systems[]=Mac',
                'systems[]=Windows',
                'people[known_ids][1]:=1000',
                'people[known_ids][5]:=5000',
            ],
            {
                'name': 'python',
                'version': 3,
                'date': {'year': 2021, 'month': 'December'},
                'systems': ['Linux', 'Mac', 'Windows'],
                'people': {'known_ids': [None, 1000, None, None, None, 5000]},
            },
        ),
        (
            [
                r'foo[\1][type]=migration',
                r'foo[\2][type]=migration',
                r'foo[\dates]:=[2012, 2013]',
                r'foo[\dates][0]:=2014',
                r'foo[\2012 bleh]:=2013',
                r'foo[bleh \2012]:=2014',
                r'\2012[x]:=2',
                r'\2012[\[3\]]:=4',
            ],
            {
                'foo': {
                    '1': {'type': 'migration'},
                    '2': {'type': 'migration'},
                    '\\dates': [2014, 2013],
                    '\\2012 bleh': 2013,
                    'bleh \\2012': 2014,
                },
                '2012': {'x': 2, '[3]': 4},
            },
        ),
        (
            [
                r'a[\0]:=0',
                r'a[\\1]:=1',
                r'a[\\\2]:=2',
                r'a[\\\\\3]:=3',
                r'a[-1\\]:=-1',
                r'a[-2\\\\]:=-2',
                r'a[\\-3\\\\]:=-3',
            ],
            {
                'a': {
                    '0': 0,
                    r'\1': 1,
                    r'\\2': 2,
                    r'\\\3': 3,
                    '-1\\': -1,
                    '-2\\\\': -2,
                    '\\-3\\\\': -3,
                }
            },
        ),
        (
            ['[]:=0', '[]:=1', '[5]:=5', '[]:=6', '[9]:=9'],
            [0, 1, None, None, None, 5, 6, None, None, 9],
        ),
        (
            ['=empty', 'foo=bar', 'bar[baz][quux]=tuut'],
            {'': 'empty', 'foo': 'bar', 'bar': {'baz': {'quux': 'tuut'}}},
        ),
        (
            [
                r'\1=top level int',
                r'\\1=escaped top level int',
                r'\2[\3][\4]:=5',
            ],
            {
                '1': 'top level int',
                '\\1': 'escaped top level int',
                '2': {'3': {'4': 5}},
            },
        ),
        (
            [':={"foo": {"bar": "baz"}}', 'top=val'],
            {'': {'foo': {'bar': 'baz'}}, 'top': 'val'},
        ),
        (
            ['[][a][b][]:=1', '[0][a][b][]:=2', '[][]:=2'],
            [{'a': {'b': [1, 2]}}, [2]],
        ),
        ([':=[1,2,3]'], {'': [1, 2, 3]}),
        ([':=[1,2,3]', 'foo=bar'], {'': [1, 2, 3], 'foo': 'bar'}),
    ],
)
def test_nested_json_syntax(input_json, expected_json, httpbin):
    r = http(httpbin + '/post', *input_json)
    assert r.json['json'] == expected_json


@pytest.mark.parametrize(
    'input_json, expected_error',
    [
        (
            ['A[:=1'],
            "HTTPie Syntax Error: Expecting a text, a number or ']'\nA[\n  ^",
        ),
        (['A[1:=1'], "HTTPie Syntax Error: Expecting ']'\nA[1\n   ^"),
        (['A[text:=1'], "HTTPie Syntax Error: Expecting ']'\nA[text\n      ^"),
        (
            ['A[text][:=1'],
            "HTTPie Syntax Error: Expecting a text, a number or ']'\nA[text][\n        ^",
        ),
        (
            ['A[key]=value', 'B[something]=u', 'A[text][:=1', 'C[key]=value'],
            "HTTPie Syntax Error: Expecting a text, a number or ']'\nA[text][\n        ^",
        ),
        (
            ['A[text]1:=1'],
            "HTTPie Syntax Error: Expecting '['\nA[text]1\n       ^",
        ),
        (['A\\[]:=1'], "HTTPie Syntax Error: Expecting '['\nA\\[]\n   ^"),
        (
            ['A[something\\]:=1'],
            "HTTPie Syntax Error: Expecting ']'\nA[something\\]\n             ^",
        ),
        (
            ['foo\\[bar\\]\\\\[   bleh:=1'],
            "HTTPie Syntax Error: Expecting ']'\nfoo\\[bar\\]\\\\[   bleh\n                    ^",
        ),
        (
            ['foo\\[bar\\]\\\\[   bleh   :=1'],
            "HTTPie Syntax Error: Expecting ']'\nfoo\\[bar\\]\\\\[   bleh   \n                       ^",
        ),
        (
            ['foo[bar][1]][]:=2'],
            "HTTPie Syntax Error: Expecting '['\nfoo[bar][1]][]\n           ^",
        ),
        (
            ['foo[bar][1]something[]:=2'],
            "HTTPie Syntax Error: Expecting '['\nfoo[bar][1]something[]\n           ^^^^^^^^^",
        ),
        (
            ['foo[bar][1][142241[]:=2'],
            "HTTPie Syntax Error: Expecting ']'\nfoo[bar][1][142241[]\n                  ^",
        ),
        (
            ['foo[bar][1]\\[142241[]:=2'],
            "HTTPie Syntax Error: Expecting '['\nfoo[bar][1]\\[142241[]\n           ^^^^^^^^",
        ),
        (
            ['foo=1', 'foo[key]:=2'],
            "HTTPie Type Error: Cannot perform 'key' based access on 'foo' which has a type of 'string' but this operation requires a type of 'object'.\nfoo[key]\n   ^^^^^",
        ),
        (
            ['foo=1', 'foo[0]:=2'],
            "HTTPie Type Error: Cannot perform 'index' based access on 'foo' which has a type of 'string' but this operation requires a type of 'array'.\nfoo[0]\n   ^^^",
        ),
        (
            ['foo=1', 'foo[]:=2'],
            "HTTPie Type Error: Cannot perform 'append' based access on 'foo' which has a type of 'string' but this operation requires a type of 'array'.\nfoo[]\n   ^^",
        ),
        (
            ['data[key]=value', 'data[key 2]=value 2', 'data[0]=value'],
            "HTTPie Type Error: Cannot perform 'index' based access on 'data' which has a type of 'object' but this operation requires a type of 'array'.\ndata[0]\n    ^^^",
        ),
        (
            ['data[key]=value', 'data[key 2]=value 2', 'data[]=value'],
            "HTTPie Type Error: Cannot perform 'append' based access on 'data' which has a type of 'object' but this operation requires a type of 'array'.\ndata[]\n    ^^",
        ),
        (
            [
                'foo[bar][baz][5]:=[1,2,3]',
                'foo[bar][baz][5][]:=4',
                'foo[bar][baz][key][]:=5',
            ],
            "HTTPie Type Error: Cannot perform 'key' based access on 'foo[bar][baz]' which has a type of 'array' but this operation requires a type of 'object'.\nfoo[bar][baz][key][]\n             ^^^^^",
        ),
        (
            ['foo[-10]:=[1,2]'],
            'HTTPie Value Error: Negative indexes are not supported.\nfoo[-10]\n    ^^^',
        ),
        (
            ['foo[0]:=1', 'foo[]:=2', 'foo[\\2]:=3'],
            "HTTPie Type Error: Cannot perform 'key' based access on 'foo' which has a type of 'array' but this operation requires a type of 'object'.\nfoo[\\2]\n   ^^^^",
        ),
        (
            ['foo[\\1]:=2', 'foo[5]:=3'],
            "HTTPie Type Error: Cannot perform 'index' based access on 'foo' which has a type of 'object' but this operation requires a type of 'array'.\nfoo[5]\n   ^^^",
        ),
        (
            ['x=y', '[]:=2'],
            "HTTPie Type Error: Cannot perform 'append' based access on '' which has a type of 'object' but this operation requires a type of 'array'.",
        ),
        (
            ['[]:=2', 'x=y'],
            "HTTPie Type Error: Cannot perform 'key' based access on '' which has a type of 'array' but this operation requires a type of 'object'.",
        ),
        (
            [':=[1,2,3]', '[]:=4'],
            "HTTPie Type Error: Cannot perform 'append' based access on '' which has a type of 'object' but this operation requires a type of 'array'.",
        ),
        (
            ['[]:=4', ':=[1,2,3]'],
            "HTTPie Type Error: Cannot perform 'key' based access on '' which has a type of 'array' but this operation requires a type of 'object'.",
        ),
    ],
)
def test_nested_json_errors(input_json, expected_error, httpbin):
    with pytest.raises(NestedJSONSyntaxError) as exc:
        http(httpbin + '/post', *input_json)

    exc_lines = str(exc.value).splitlines()
    expected_lines = expected_error.splitlines()
    if len(expected_lines) == 1:
        # When the error offsets are not important, we'll just compare the actual
        # error message.
        exc_lines = exc_lines[:1]

    assert expected_lines == exc_lines


def test_nested_json_sparse_array(httpbin_both):
    r = http(httpbin_both + '/post', 'test[0]:=1', 'test[100]:=1')
    assert len(r.json['json']['test']) == 101
