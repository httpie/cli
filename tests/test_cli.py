"""CLI argument parsing related tests."""
import json
# noinspection PyCompatibility
import argparse

import pytest
from requests.exceptions import InvalidSchema

from httpie import input
from httpie.input import KeyValue, KeyValueArgType, DataDict
from httpie import ExitStatus
from httpie.cli import parser
from utils import TestEnvironment, http, HTTP_OK
from fixtures import (
    FILE_PATH_ARG, JSON_FILE_PATH_ARG,
    JSON_FILE_CONTENT, FILE_CONTENT, FILE_PATH
)


class TestItemParsing:

    key_value = KeyValueArgType(*input.SEP_GROUP_ALL_ITEMS)

    def test_invalid_items(self):
        items = ['no-separator']
        for item in items:
            pytest.raises(argparse.ArgumentTypeError, self.key_value, item)

    def test_escape_separator(self):
        items = input.parse_items([
            # headers
            self.key_value(r'foo\:bar:baz'),
            self.key_value(r'jack\@jill:hill'),

            # data
            self.key_value(r'baz\=bar=foo'),

            # files
            self.key_value(r'bar\@baz@%s' % FILE_PATH_ARG),
        ])
        # `requests.structures.CaseInsensitiveDict` => `dict`
        headers = dict(items.headers._store.values())

        assert headers == {
            'foo:bar': 'baz',
            'jack@jill': 'hill',
        }
        assert items.data == {'baz=bar': 'foo'}
        assert 'bar@baz' in items.files

    @pytest.mark.parametrize(('string', 'key', 'sep', 'value'), [
        ('path=c:\windows', 'path', '=', 'c:\windows'),
        ('path=c:\windows\\', 'path', '=', 'c:\windows\\'),
        ('path\==c:\windows', 'path=', '=', 'c:\windows'),
    ])
    def test_backslash_before_non_special_character_does_not_escape(
            self, string, key, sep, value):
        expected = KeyValue(orig=string, key=key, sep=sep, value=value)
        actual = self.key_value(string)
        assert actual == expected

    def test_escape_longsep(self):
        items = input.parse_items([
            self.key_value(r'bob\:==foo'),
        ])
        assert items.params == {'bob:': 'foo'}

    def test_valid_items(self):
        items = input.parse_items([
            self.key_value('string=value'),
            self.key_value('Header:value'),
            self.key_value('Unset-Header:'),
            self.key_value('Empty-Header;'),
            self.key_value('list:=["a", 1, {}, false]'),
            self.key_value('obj:={"a": "b"}'),
            self.key_value('ed='),
            self.key_value('bool:=true'),
            self.key_value('file@' + FILE_PATH_ARG),
            self.key_value('query==value'),
            self.key_value('string-embed=@' + FILE_PATH_ARG),
            self.key_value('raw-json-embed:=@' + JSON_FILE_PATH_ARG),
        ])

        # Parsed headers
        # `requests.structures.CaseInsensitiveDict` => `dict`
        headers = dict(items.headers._store.values())
        assert headers == {
            'Header': 'value',
            'Unset-Header': None,
            'Empty-Header': ''
        }

        # Parsed data
        raw_json_embed = items.data.pop('raw-json-embed')
        assert raw_json_embed == json.loads(JSON_FILE_CONTENT)
        items.data['string-embed'] = items.data['string-embed'].strip()
        assert dict(items.data) == {
            "ed": "",
            "string": "value",
            "bool": True,
            "list": ["a", 1, {}, False],
            "obj": {"a": "b"},
            "string-embed": FILE_CONTENT,
        }

        # Parsed query string parameters
        assert items.params == {'query': 'value'}

        # Parsed file fields
        assert 'file' in items.files
        assert (items.files['file'][1].read().strip().
                decode('utf8') == FILE_CONTENT)

    def test_multiple_file_fields_with_same_field_name(self):
        items = input.parse_items([
            self.key_value('file_field@' + FILE_PATH_ARG),
            self.key_value('file_field@' + FILE_PATH_ARG),
        ])
        assert len(items.files['file_field']) == 2

    def test_multiple_text_fields_with_same_field_name(self):
        items = input.parse_items(
            [self.key_value('text_field=a'),
             self.key_value('text_field=b')],
            data_class=DataDict
        )
        assert items.data['text_field'] == ['a', 'b']
        assert list(items.data.items()) == [
            ('text_field', 'a'),
            ('text_field', 'b'),
        ]


class TestQuerystring:
    def test_query_string_params_in_url(self, httpbin):
        r = http('--print=Hhb', 'GET', httpbin.url + '/get?a=1&b=2')
        path = '/get?a=1&b=2'
        url = httpbin.url + path
        assert HTTP_OK in r
        assert 'GET %s HTTP/1.1' % path in r
        assert '"url": "%s"' % url in r

    def test_query_string_params_items(self, httpbin):
        r = http('--print=Hhb', 'GET', httpbin.url + '/get', 'a==1')
        path = '/get?a=1'
        url = httpbin.url + path
        assert HTTP_OK in r
        assert 'GET %s HTTP/1.1' % path in r
        assert '"url": "%s"' % url in r

    def test_query_string_params_in_url_and_items_with_duplicates(self,
                                                                  httpbin):
        r = http('--print=Hhb', 'GET',
                 httpbin.url + '/get?a=1&a=1', 'a==1', 'a==1')
        path = '/get?a=1&a=1&a=1&a=1'
        url = httpbin.url + path
        assert HTTP_OK in r
        assert 'GET %s HTTP/1.1' % path in r
        assert '"url": "%s"' % url in r


class TestLocalhostShorthand:
    def test_expand_localhost_shorthand(self):
        args = parser.parse_args(args=[':'], env=TestEnvironment())
        assert args.url == 'http://localhost'

    def test_expand_localhost_shorthand_with_slash(self):
        args = parser.parse_args(args=[':/'], env=TestEnvironment())
        assert args.url == 'http://localhost/'

    def test_expand_localhost_shorthand_with_port(self):
        args = parser.parse_args(args=[':3000'], env=TestEnvironment())
        assert args.url == 'http://localhost:3000'

    def test_expand_localhost_shorthand_with_path(self):
        args = parser.parse_args(args=[':/path'], env=TestEnvironment())
        assert args.url == 'http://localhost/path'

    def test_expand_localhost_shorthand_with_port_and_slash(self):
        args = parser.parse_args(args=[':3000/'], env=TestEnvironment())
        assert args.url == 'http://localhost:3000/'

    def test_expand_localhost_shorthand_with_port_and_path(self):
        args = parser.parse_args(args=[':3000/path'], env=TestEnvironment())
        assert args.url == 'http://localhost:3000/path'

    def test_dont_expand_shorthand_ipv6_as_shorthand(self):
        args = parser.parse_args(args=['::1'], env=TestEnvironment())
        assert args.url == 'http://::1'

    def test_dont_expand_longer_ipv6_as_shorthand(self):
        args = parser.parse_args(
            args=['::ffff:c000:0280'],
            env=TestEnvironment()
        )
        assert args.url == 'http://::ffff:c000:0280'

    def test_dont_expand_full_ipv6_as_shorthand(self):
        args = parser.parse_args(
            args=['0000:0000:0000:0000:0000:0000:0000:0001'],
            env=TestEnvironment()
        )
        assert args.url == 'http://0000:0000:0000:0000:0000:0000:0000:0001'


class TestArgumentParser:

    def setup_method(self, method):
        self.parser = input.HTTPieArgumentParser()

    def test_guess_when_method_set_and_valid(self):
        self.parser.args = argparse.Namespace()
        self.parser.args.method = 'GET'
        self.parser.args.url = 'http://example.com/'
        self.parser.args.items = []
        self.parser.args.ignore_stdin = False

        self.parser.env = TestEnvironment()

        self.parser._guess_method()

        assert self.parser.args.method == 'GET'
        assert self.parser.args.url == 'http://example.com/'
        assert self.parser.args.items == []

    def test_guess_when_method_not_set(self):
        self.parser.args = argparse.Namespace()
        self.parser.args.method = None
        self.parser.args.url = 'http://example.com/'
        self.parser.args.items = []
        self.parser.args.ignore_stdin = False
        self.parser.env = TestEnvironment()

        self.parser._guess_method()

        assert self.parser.args.method == 'GET'
        assert self.parser.args.url == 'http://example.com/'
        assert self.parser.args.items == []

    def test_guess_when_method_set_but_invalid_and_data_field(self):
        self.parser.args = argparse.Namespace()
        self.parser.args.method = 'http://example.com/'
        self.parser.args.url = 'data=field'
        self.parser.args.items = []
        self.parser.args.ignore_stdin = False
        self.parser.env = TestEnvironment()
        self.parser._guess_method()

        assert self.parser.args.method == 'POST'
        assert self.parser.args.url == 'http://example.com/'
        assert self.parser.args.items == [
            KeyValue(key='data',
                     value='field',
                     sep='=',
                     orig='data=field')
        ]

    def test_guess_when_method_set_but_invalid_and_header_field(self):
        self.parser.args = argparse.Namespace()
        self.parser.args.method = 'http://example.com/'
        self.parser.args.url = 'test:header'
        self.parser.args.items = []
        self.parser.args.ignore_stdin = False

        self.parser.env = TestEnvironment()

        self.parser._guess_method()

        assert self.parser.args.method == 'GET'
        assert self.parser.args.url == 'http://example.com/'
        assert self.parser.args.items, [
            KeyValue(key='test',
                     value='header',
                     sep=':',
                     orig='test:header')
        ]

    def test_guess_when_method_set_but_invalid_and_item_exists(self):
        self.parser.args = argparse.Namespace()
        self.parser.args.method = 'http://example.com/'
        self.parser.args.url = 'new_item=a'
        self.parser.args.items = [
            KeyValue(
                key='old_item', value='b', sep='=', orig='old_item=b')
        ]
        self.parser.args.ignore_stdin = False

        self.parser.env = TestEnvironment()

        self.parser._guess_method()

        assert self.parser.args.items, [
            KeyValue(key='new_item', value='a', sep='=', orig='new_item=a'),
            KeyValue(
                key='old_item', value='b', sep='=', orig='old_item=b'),
        ]


class TestNoOptions:

    def test_valid_no_options(self, httpbin):
        r = http('--verbose', '--no-verbose', 'GET', httpbin.url + '/get')
        assert 'GET /get HTTP/1.1' not in r

    def test_invalid_no_options(self, httpbin):
        r = http('--no-war', 'GET', httpbin.url + '/get',
                 error_exit_ok=True)
        assert r.exit_status == 1
        assert 'unrecognized arguments: --no-war' in r.stderr
        assert 'GET /get HTTP/1.1' not in r


class TestIgnoreStdin:

    def test_ignore_stdin(self, httpbin):
        with open(FILE_PATH) as f:
            env = TestEnvironment(stdin=f, stdin_isatty=False)
            r = http('--ignore-stdin', '--verbose', httpbin.url + '/get',
                     env=env)
        assert HTTP_OK in r
        assert 'GET /get HTTP' in r, "Don't default to POST."
        assert FILE_CONTENT not in r, "Don't send stdin data."

    def test_ignore_stdin_cannot_prompt_password(self, httpbin):
        r = http('--ignore-stdin', '--auth=no-password', httpbin.url + '/get',
                 error_exit_ok=True)
        assert r.exit_status == ExitStatus.ERROR
        assert 'because --ignore-stdin' in r.stderr


class TestSchemes:

    def test_invalid_custom_scheme(self):
        # InvalidSchema is expected because HTTPie
        # shouldn't touch a formally valid scheme.
        with pytest.raises(InvalidSchema):
            http('foo+bar-BAZ.123://bah')

    def test_invalid_scheme_via_via_default_scheme(self):
        # InvalidSchema is expected because HTTPie
        # shouldn't touch a formally valid scheme.
        with pytest.raises(InvalidSchema):
            http('bah', '--default=scheme=foo+bar-BAZ.123')

    def test_default_scheme(self, httpbin_secure):
        url = '{0}:{1}'.format(httpbin_secure.host, httpbin_secure.port)
        assert HTTP_OK in http(url, '--default-scheme=https')
