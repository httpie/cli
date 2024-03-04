import argparse
from pathlib import Path
from unittest import mock

import json
import os
import io
import warnings
from urllib.request import urlopen

import pytest
import requests
import responses

from httpie.cli.argtypes import (
    PARSED_DEFAULT_FORMAT_OPTIONS,
    parse_format_options,
)
from httpie.cli.definition import parser
from httpie.encoding import UTF8
from httpie.output.formatters.colors import get_lexer, PIE_STYLE_NAMES, BUNDLED_STYLES
from httpie.status import ExitStatus
from .fixtures import XML_DATA_RAW, XML_DATA_FORMATTED
from .utils import COLOR, CRLF, HTTP_OK, MockEnvironment, http, DUMMY_URL, strip_colors


# For ensuring test reproducibility, avoid using the unsorted
# BUNDLED_STYLES set.
SORTED_BUNDLED_STYLES = sorted(BUNDLED_STYLES)


@pytest.mark.parametrize('stdout_isatty', [True, False])
def test_output_option(tmp_path, httpbin, stdout_isatty):
    output_filename = tmp_path / 'test_output_option'
    url = httpbin + '/robots.txt'

    r = http('--output', str(output_filename), url,
             env=MockEnvironment(stdout_isatty=stdout_isatty))
    assert r == ''

    expected_body = urlopen(url).read().decode()
    actual_body = output_filename.read_text(encoding=UTF8)

    assert actual_body == expected_body


class TestQuietFlag:
    QUIET_SCENARIOS = [('--quiet',), ('-q',), ('--quiet', '--quiet'), ('-qq',)]

    @pytest.mark.parametrize('quiet_flags', QUIET_SCENARIOS)
    def test_quiet(self, httpbin, quiet_flags):
        env = MockEnvironment(
            stdin_isatty=True,
            stdout_isatty=True,
            devnull=io.BytesIO()
        )
        r = http(*quiet_flags, 'GET', httpbin + '/get', env=env)
        assert env.stdout is env.devnull
        assert env.stderr is env.devnull
        assert HTTP_OK in r.devnull
        assert r == ''
        assert r.stderr == ''

    def test_quiet_with_check_status_non_zero(self, httpbin):
        r = http(
            '--quiet', '--check-status', httpbin + '/status/500',
            tolerate_error_exit_status=True,
        )
        assert 'http: warning: HTTP 500' in r.stderr

    def test_quiet_with_check_status_non_zero_pipe(self, httpbin):
        r = http(
            '--quiet', '--check-status', httpbin + '/status/500',
            tolerate_error_exit_status=True,
            env=MockEnvironment(stdout_isatty=False)
        )
        assert 'http: warning: HTTP 500' in r.stderr

    def test_quiet_quiet_with_check_status_non_zero(self, httpbin):
        r = http(
            '--quiet', '--quiet', '--check-status', httpbin + '/status/500',
            tolerate_error_exit_status=True,
        )
        assert not r.stderr

    def test_quiet_quiet_with_check_status_non_zero_pipe(self, httpbin):
        r = http(
            '--quiet', '--quiet', '--check-status', httpbin + '/status/500',
            tolerate_error_exit_status=True,
            env=MockEnvironment(stdout_isatty=False)
        )
        assert 'http: warning: HTTP 500' in r.stderr

    @mock.patch('httpie.core.program')
    @pytest.mark.parametrize('flags, expected_warnings', [
        ([], 1),
        (['-q'], 1),
        (['-qq'], 0),
    ])
    # Might fail on Windows due to interference from other warnings.
    @pytest.mark.xfail
    def test_quiet_on_python_warnings(self, test_patch, httpbin, flags, expected_warnings):
        def warn_and_run(*args, **kwargs):
            warnings.warn('warning!!')
            return ExitStatus.SUCCESS

        test_patch.side_effect = warn_and_run
        with pytest.warns(None) as record:
            http(*flags, httpbin + '/get')

        assert len(record) == expected_warnings

    def test_double_quiet_on_error(self, httpbin):
        r = http(
            '-qq', '--check-status', '$$$this.does.not.exist$$$',
            tolerate_error_exit_status=True,
        )
        assert not r
        assert 'Couldn’t resolve the given hostname' in r.stderr

    @pytest.mark.parametrize('quiet_flags', QUIET_SCENARIOS)
    @mock.patch('httpie.cli.argtypes.AuthCredentials._getpass',
                new=lambda self, prompt: 'password')
    def test_quiet_with_password_prompt(self, httpbin, quiet_flags):
        """
        Tests whether httpie still prompts for a password when request
        requires authentication and only username is provided

        """
        env = MockEnvironment(
            stdin_isatty=True,
            stdout_isatty=True,
            devnull=io.BytesIO()
        )
        r = http(
            *quiet_flags, '--auth', 'user', 'GET',
            httpbin + '/basic-auth/user/password',
            env=env
        )
        assert env.stdout is env.devnull
        assert env.stderr is env.devnull
        assert HTTP_OK in r.devnull
        assert r == ''
        assert r.stderr == ''

    @pytest.mark.parametrize('quiet_flags', QUIET_SCENARIOS)
    @pytest.mark.parametrize('output_options', ['-h', '-b', '-v', '-p=hH'])
    def test_quiet_with_explicit_output_options(self, httpbin, quiet_flags, output_options):
        env = MockEnvironment(stdin_isatty=True, stdout_isatty=True)
        r = http(*quiet_flags, output_options, httpbin + '/get', env=env)
        assert env.stdout is env.devnull
        assert env.stderr is env.devnull
        assert r == ''
        assert r.stderr == ''

    @pytest.mark.parametrize('quiet_flags', QUIET_SCENARIOS)
    @pytest.mark.parametrize('with_download', [True, False])
    def test_quiet_with_output_redirection(self, tmp_path, httpbin, quiet_flags, with_download):
        url = httpbin + '/robots.txt'
        output_path = Path('output.txt')
        env = MockEnvironment()
        orig_cwd = os.getcwd()
        output = requests.get(url).text
        extra_args = ['--download'] if with_download else []
        os.chdir(tmp_path)
        try:
            assert os.listdir('.') == []
            r = http(
                *quiet_flags,
                '--output', str(output_path),
                *extra_args,
                url,
                env=env
            )
            assert os.listdir('.') == [str(output_path)]
            assert r == ''
            assert r.stderr == ''
            assert env.stderr is env.devnull
            if with_download:
                assert env.stdout is env.devnull
            else:
                assert env.stdout is not env.devnull  # --output swaps stdout.
            assert output_path.read_text(encoding=UTF8) == output
        finally:
            os.chdir(orig_cwd)


class TestVerboseFlag:
    def test_verbose(self, httpbin):
        r = http('--verbose',
                 'GET', httpbin + '/get', 'test-header:__test__')
        assert HTTP_OK in r
        assert r.count('__test__') == 2

    def test_verbose_raw(self, httpbin):
        r = http('--verbose', '--raw', 'foo bar',
                 'POST', httpbin + '/post')
        assert HTTP_OK in r
        assert 'foo bar' in r

    def test_verbose_form(self, httpbin):
        # https://github.com/httpie/cli/issues/53
        r = http('--verbose', '--form', 'POST', httpbin + '/post',
                 'A=B', 'C=D')
        assert HTTP_OK in r
        assert 'A=B&C=D' in r

    def test_verbose_json(self, httpbin):
        r = http('--verbose',
                 'POST', httpbin + '/post', 'foo=bar', 'baz=bar')
        assert HTTP_OK in r
        assert '"baz": "bar"' in r

    def test_verbose_implies_all(self, httpbin):
        r = http('--verbose', '--follow', httpbin + '/redirect/1')
        assert 'GET /redirect/1 HTTP/1.1' in r
        assert 'HTTP/1.1 302 FOUND' in r
        assert 'GET /get HTTP/1.1' in r
        assert HTTP_OK in r


class TestColors:

    @pytest.mark.parametrize(
        'mime, explicit_json, body, expected_lexer_name',
        [
            ('application/json', False, None, 'JSON'),
            ('application/json+foo', False, None, 'JSON'),
            ('application/foo+json', False, None, 'JSON'),
            ('application/json-foo', False, None, 'JSON'),
            ('application/x-json', False, None, 'JSON'),
            ('foo/json', False, None, 'JSON'),
            ('foo/json+bar', False, None, 'JSON'),
            ('foo/bar+json', False, None, 'JSON'),
            ('foo/json-foo', False, None, 'JSON'),
            ('foo/x-json', False, None, 'JSON'),
            ('application/vnd.comverge.grid+hal+json', False, None, 'JSON'),
            ('text/plain', True, '{}', 'JSON'),
            ('text/plain', True, 'foo', 'Text only'),
        ]
    )
    def test_get_lexer(self, mime, explicit_json, body, expected_lexer_name):
        lexer = get_lexer(mime, body=body, explicit_json=explicit_json)
        assert lexer is not None
        assert lexer.name == expected_lexer_name

    def test_get_lexer_not_found(self):
        assert get_lexer('xxx/yyy') is None


@pytest.mark.parametrize("endpoint", [
    "/encoding/utf8",
    "/html",
    "/json",
    "/xml",
])
def test_ensure_contents_colored(httpbin, endpoint):
    env = MockEnvironment(colors=256)
    r = http('--body', 'GET', httpbin + endpoint, env=env)
    assert COLOR in r


@pytest.mark.parametrize('style', PIE_STYLE_NAMES)
def test_ensure_meta_is_colored(httpbin, style):
    env = MockEnvironment(colors=256)
    r = http('--meta', '--style', style, 'GET', httpbin + '/get', env=env)
    assert COLOR in r


@pytest.mark.parametrize('style', SORTED_BUNDLED_STYLES)
@pytest.mark.parametrize('msg', [
    '',
    ' ',
    ' OK',
    ' OK ',
    ' CUSTOM ',
])
def test_ensure_status_code_is_shown_on_all_themes(http_server, style, msg):
    env = MockEnvironment(colors=256)
    r = http('--style', style,
             http_server + '/status/msg',
             '--raw', msg, env=env)

    # Trailing space is stripped away.
    assert 'HTTP/1.0 200' + msg.rstrip() in strip_colors(r)


class TestPrettyOptions:
    """Test the --pretty handling."""

    def test_pretty_enabled_by_default(self, httpbin):
        env = MockEnvironment(colors=256)
        r = http('GET', httpbin + '/get', env=env)
        assert COLOR in r

    def test_pretty_enabled_by_default_unless_stdout_redirected(self, httpbin):
        r = http('GET', httpbin + '/get')
        assert COLOR not in r

    def test_force_pretty(self, httpbin):
        env = MockEnvironment(stdout_isatty=False, colors=256)
        r = http('--pretty=all', 'GET', httpbin + '/get', env=env)
        assert COLOR in r

    def test_force_ugly(self, httpbin):
        r = http('--pretty=none', 'GET', httpbin + '/get')
        assert COLOR not in r

    def test_subtype_based_pygments_lexer_match(self, httpbin):
        """Test that media subtype is used if type/subtype doesn't
        match any lexer.

        """
        env = MockEnvironment(colors=256)
        r = http('--print=B', '--pretty=all', httpbin + '/post',
                 'Content-Type:text/foo+json', 'a=b', env=env)
        assert COLOR in r

    def test_colors_option(self, httpbin):
        env = MockEnvironment(colors=256)
        r = http('--print=B', '--pretty=colors',
                 'GET', httpbin + '/get', 'a=b',
                 env=env)
        # Tests that the JSON data isn't formatted.
        assert not r.strip().count('\n')
        assert COLOR in r

    def test_format_option(self, httpbin):
        env = MockEnvironment(colors=256)
        r = http('--print=B', '--pretty=format',
                 'GET', httpbin + '/get', 'a=b',
                 env=env)
        # Tests that the JSON data is formatted.
        assert r.strip().count('\n') == 2
        assert COLOR not in r


class TestLineEndings:
    """
    Test that CRLF is properly used in headers
    and as the headers/body separator.

    """

    def _validate_crlf(self, msg):
        lines = iter(msg.splitlines(True))
        for header in lines:
            if header == CRLF:
                break
            assert header.endswith(CRLF), repr(header)
        else:
            assert 0, f'CRLF between headers and body not found in {msg!r}'
        body = ''.join(lines)
        assert CRLF not in body
        return body

    def test_CRLF_headers_only(self, httpbin):
        r = http('--headers', 'GET', httpbin + '/get')
        body = self._validate_crlf(r)
        assert not body, f'Garbage after headers: {r!r}'

    def test_CRLF_ugly_response(self, httpbin):
        r = http('--pretty=none', 'GET', httpbin + '/get')
        self._validate_crlf(r)

    def test_CRLF_formatted_response(self, httpbin):
        r = http('--pretty=format', 'GET', httpbin + '/get')
        assert r.exit_status == ExitStatus.SUCCESS
        self._validate_crlf(r)

    def test_CRLF_ugly_request(self, httpbin):
        r = http('--pretty=none', '--print=HB', 'GET', httpbin + '/get')
        self._validate_crlf(r)

    def test_CRLF_formatted_request(self, httpbin):
        r = http('--pretty=format', '--print=HB', 'GET', httpbin + '/get')
        self._validate_crlf(r)


class TestFormatOptions:
    def test_header_formatting_options(self):
        def get_headers(sort):
            return http(
                '--offline', '--print=H',
                '--format-options', 'headers.sort:' + sort,
                'example.org', 'ZZZ:foo', 'XXX:foo',
            )

        r_sorted = get_headers('true')
        r_unsorted = get_headers('false')
        assert r_sorted != r_unsorted
        assert f'XXX: foo{CRLF}ZZZ: foo' in r_sorted
        assert f'ZZZ: foo{CRLF}XXX: foo' in r_unsorted

    @pytest.mark.parametrize(
        'options, expected_json',
        [
            # @formatter:off
            (
                'json.sort_keys:true,json.indent:4',
                json.dumps({'a': 0, 'b': 0}, indent=4),
            ),
            (
                'json.sort_keys:false,json.indent:2',
                json.dumps({'b': 0, 'a': 0}, indent=2),
            ),
            (
                'json.format:false',
                json.dumps({'b': 0, 'a': 0}),
            ),
            # @formatter:on
        ]
    )
    def test_json_formatting_options(self, options: str, expected_json: str):
        r = http(
            '--offline', '--print=B',
            '--format-options', options,
            'example.org', 'b:=0', 'a:=0',
        )
        assert expected_json in r

    @pytest.mark.parametrize(
        'defaults, options_string, expected',
        [
            # @formatter:off
            ({'foo': {'bar': 1}}, 'foo.bar:2', {'foo': {'bar': 2}}),
            ({'foo': {'bar': True}}, 'foo.bar:false', {'foo': {'bar': False}}),
            ({'foo': {'bar': 'a'}}, 'foo.bar:b', {'foo': {'bar': 'b'}}),
            # @formatter:on
        ]
    )
    def test_parse_format_options(self, defaults, options_string, expected):
        actual = parse_format_options(s=options_string, defaults=defaults)
        assert expected == actual

    @pytest.mark.parametrize(
        'options_string, expected_error',
        [
            ('foo:2', 'invalid option'),
            ('foo.baz:2', 'invalid key'),
            ('foo.bar:false', 'expected int got bool'),
        ]
    )
    def test_parse_format_options_errors(self, options_string, expected_error):
        defaults = {
            'foo': {
                'bar': 1
            }
        }
        with pytest.raises(argparse.ArgumentTypeError, match=expected_error):
            parse_format_options(s=options_string, defaults=defaults)

    @pytest.mark.parametrize(
        'args, expected_format_options',
        [
            (
                [
                    '--format-options',
                    'headers.sort:false,json.sort_keys:false',
                    '--format-options=json.indent:10'
                ],
                {
                    'headers': {
                        'sort': False
                    },
                    'json': {
                        'sort_keys': False,
                        'indent': 10,
                        'format': True
                    },
                    'xml': {
                        'format': True,
                        'indent': 2,
                    },
                }
            ),
            (
                [
                    '--unsorted'
                ],
                {
                    'headers': {
                        'sort': False
                    },
                    'json': {
                        'sort_keys': False,
                        'indent': 4,
                        'format': True
                    },
                    'xml': {
                        'format': True,
                        'indent': 2,
                    },
                }
            ),
            (
                [
                    '--format-options=headers.sort:true',
                    '--unsorted',
                    '--format-options=headers.sort:true',
                ],
                {
                    'headers': {
                        'sort': True
                    },
                    'json': {
                        'sort_keys': False,
                        'indent': 4,
                        'format': True
                    },
                    'xml': {
                        'format': True,
                        'indent': 2,
                    },
                }
            ),
            (
                [
                    '--no-format-options',  # --no-<option> anywhere resets
                    '--format-options=headers.sort:true',
                    '--unsorted',
                    '--format-options=headers.sort:true',
                ],
                PARSED_DEFAULT_FORMAT_OPTIONS,
            ),
            (
                [
                    '--format-options=json.indent:2',
                    '--format-options=xml.format:false',
                    '--format-options=xml.indent:4',
                    '--unsorted',
                    '--no-unsorted',
                ],
                {
                    'headers': {
                        'sort': True
                    },
                    'json': {
                        'sort_keys': True,
                        'indent': 2,
                        'format': True
                    },
                    'xml': {
                        'format': False,
                        'indent': 4,
                    },
                }
            ),
            (
                [
                    '--format-options=json.indent:2',
                    '--unsorted',
                    '--sorted',
                ],
                {
                    'headers': {
                        'sort': True
                    },
                    'json': {
                        'sort_keys': True,
                        'indent': 2,
                        'format': True
                    },
                    'xml': {
                        'format': True,
                        'indent': 2,
                    },
                }
            ),
            (
                [
                    '--format-options=json.indent:2',
                    '--sorted',
                    '--no-sorted',
                    '--no-unsorted',
                ],
                {
                    'headers': {
                        'sort': True
                    },
                    'json': {
                        'sort_keys': True,
                        'indent': 2,
                        'format': True
                    },
                    'xml': {
                        'format': True,
                        'indent': 2,
                    },
                }
            ),
        ],
    )
    def test_format_options_accumulation(self, args, expected_format_options):
        parsed_args = parser.parse_args(
            args=[*args, 'example.org'],
            env=MockEnvironment(),
        )
        assert parsed_args.format_options == expected_format_options


@responses.activate
def test_response_mime_overwrite():
    responses.add(
        method=responses.GET,
        url=DUMMY_URL,
        body=XML_DATA_RAW,
        content_type='text/plain',
    )
    r = http(
        '--offline',
        '--raw', XML_DATA_RAW,
        '--response-mime=application/xml', DUMMY_URL
    )
    assert XML_DATA_RAW in r  # not affecting request bodies

    r = http('--response-mime=application/xml', DUMMY_URL)
    assert XML_DATA_FORMATTED in r


@responses.activate
def test_response_mime_overwrite_incorrect():
    responses.add(
        method=responses.GET,
        url=DUMMY_URL,
        body=XML_DATA_RAW,
        content_type='text/xml',
    )
    # The provided Content-Type is simply ignored, and so no formatting is done.
    r = http('--response-mime=incorrect/type', DUMMY_URL)
    assert XML_DATA_RAW in r
