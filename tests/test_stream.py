import json

import pytest
import responses
from unittest.mock import Mock

from httpie.compat import is_windows
from httpie.cli.constants import PRETTY_MAP
from httpie.output.streams import BINARY_SUPPRESSED_NOTICE
from httpie.plugins import ConverterPlugin
from httpie.plugins.registry import plugin_manager

from .utils import StdinBytesIO, http, MockEnvironment, DUMMY_URL
from .fixtures import (
    ASCII_FILE_CONTENT,
    BIN_FILE_CONTENT,
    BIN_FILE_PATH,
    FILE_CONTENT as UNICODE_FILE_CONTENT
)

PRETTY_OPTIONS = list(PRETTY_MAP.keys())


class SortJSONConverterPlugin(ConverterPlugin):
    @classmethod
    def supports(cls, mime):
        return mime == 'json/bytes'

    def convert(self, body):
        body = body.lstrip(b'\x00')
        data = json.loads(body)
        return 'application/json', json.dumps(data, sort_keys=True)


# GET because httpbin 500s with binary POST body.


@pytest.mark.skipif(is_windows,
                    reason='Pretty redirect not supported under Windows')
def test_pretty_redirected_stream(httpbin):
    """Test that --stream works with prettified redirected output."""
    env = MockEnvironment(
        colors=256,
        stdin=StdinBytesIO(BIN_FILE_PATH.read_bytes()),
        stdin_isatty=False,
        stdout_isatty=False,
    )
    r = http('--verbose', '--pretty=all', '--stream', 'GET',
             httpbin + '/get', env=env)
    assert BINARY_SUPPRESSED_NOTICE.decode() in r


def test_pretty_stream_ensure_full_stream_is_retrieved(httpbin):
    env = MockEnvironment(
        stdin=StdinBytesIO(),
        stdin_isatty=False,
        stdout_isatty=False,
    )
    r = http('--pretty=format', '--stream', 'GET',
             httpbin + '/stream/3', env=env)
    assert r.count('/stream/3') == 3


@pytest.mark.parametrize('pretty', PRETTY_OPTIONS)
@pytest.mark.parametrize('stream', [True, False])
@responses.activate
def test_pretty_options_with_and_without_stream_with_converter(pretty, stream):
    plugin_manager.register(SortJSONConverterPlugin)
    try:
        # Cover PluginManager.__repr__()
        assert 'SortJSONConverterPlugin' in str(plugin_manager)

        body = b'\x00{"foo":42,\n"bar":"baz"}'
        responses.add(responses.GET, DUMMY_URL, body=body,
                      stream=True, content_type='json/bytes')

        args = ['--pretty=' + pretty, 'GET', DUMMY_URL]
        if stream:
            args.insert(0, '--stream')
        r = http(*args)

        assert 'json/bytes' in r
        if pretty == 'none':
            assert BINARY_SUPPRESSED_NOTICE.decode() in r
        else:
            # Ensure the plugin was effectively used and the resulting JSON is sorted
            assert '"bar": "baz",' in r
            assert '"foo": 42' in r
    finally:
        plugin_manager.unregister(SortJSONConverterPlugin)


def test_encoded_stream(httpbin):
    """Test that --stream works with non-prettified
    redirected terminal output."""
    env = MockEnvironment(
        stdin=StdinBytesIO(BIN_FILE_PATH.read_bytes()),
        stdin_isatty=False,
    )
    r = http('--pretty=none', '--stream', '--verbose', 'GET',
             httpbin + '/get', env=env)
    assert BINARY_SUPPRESSED_NOTICE.decode() in r


def test_redirected_stream(httpbin):
    """Test that --stream works with non-prettified
    redirected terminal output."""
    env = MockEnvironment(
        stdout_isatty=False,
        stdin_isatty=False,
        stdin=StdinBytesIO(BIN_FILE_PATH.read_bytes()),
    )
    r = http('--pretty=none', '--stream', '--verbose', 'GET',
             httpbin + '/get', env=env)
    assert BIN_FILE_CONTENT in r


# /drip endpoint produces 3 individual lines,
# if we set text/event-stream HTTPie should stream
# it by default. Otherwise, it will buffer and then
# print.
@pytest.mark.parametrize('extras, expected', [
    (
        ['Accept:text/event-stream'],
        3
    ),
    (
        ['Accept:text/event-stream; charset=utf-8'],
        3
    ),
    (
        ['Accept:text/plain'],
        1
    )
])
def test_auto_streaming(http_server, extras, expected):
    env = MockEnvironment()
    env.stdout.write = Mock()
    http(http_server + '/drip', *extras, env=env)
    assert len([
        call_arg
        for call_arg in env.stdout.write.call_args_list
        if 'test' in call_arg[0][0]
    ]) == expected


def test_streaming_encoding_detection(http_server):
    r = http('--stream', http_server + '/stream/encoding/random')
    assert ASCII_FILE_CONTENT in r
    assert UNICODE_FILE_CONTENT in r
