import json

import pytest
import responses

from httpie.cli.constants import PRETTY_MAP
from httpie.output.formatters.colors import ColorFormatter

from .utils import MockEnvironment, http, URL_EXAMPLE

TEST_JSON_XXSI_PREFIXES = (r")]}',\n", ")]}',", 'while(1);', 'for(;;)', ')', ']', '}')
TEST_JSON_VALUES = ({}, {'a': 0, 'b': 0}, [], ['a', 'b'], 'foo', True, False, None)  # FIX: missing int & float
TEST_PREFIX_TOKEN_COLOR = '\x1b[04m\x1b[91m'


@pytest.mark.parametrize('data_prefix', TEST_JSON_XXSI_PREFIXES)
@pytest.mark.parametrize('json_data', TEST_JSON_VALUES)
@pytest.mark.parametrize('pretty', PRETTY_MAP.keys())
@responses.activate
def test_json_formatter_with_body_preceded_by_non_json_data(data_prefix, json_data, pretty):
    """Test JSON bodies preceded by non-JSON data."""
    body = data_prefix + json.dumps(json_data)
    content_type = 'application/json'
    responses.add(responses.GET, URL_EXAMPLE, body=body,
                  content_type=content_type)

    colored_output = pretty in ('all', 'colors')
    env = MockEnvironment(colors=256) if colored_output else None
    r = http('--pretty=' + pretty, URL_EXAMPLE, env=env)

    indent = None if pretty in ('none', 'colors') else 4
    expected_body = data_prefix + json.dumps(json_data, indent=indent)
    if colored_output:
        fmt = ColorFormatter(env, format_options={'json': {'format': True, 'indent': 4}})
        expected_body = fmt.format_body(expected_body, content_type)
        # Check to ensure the non-JSON data prefix is colored only one time,
        # meaning it was correctly handled as a whole.
        assert TEST_PREFIX_TOKEN_COLOR + data_prefix in expected_body, expected_body
    assert expected_body in r
