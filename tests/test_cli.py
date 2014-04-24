"""CLI argument parsing related tests."""
import json

# noinspection PyCompatibility
import argparse

from tests import (
    BaseTestCase, TestEnvironment, http, httpbin,
    FILE_PATH_ARG, JSON_FILE_PATH_ARG,
    JSON_FILE_CONTENT, FILE_CONTENT, OK, FILE_PATH
)
from httpie import input
from httpie import ExitStatus
from httpie.cli import parser


class ItemParsingTest(BaseTestCase):

    def setUp(self):
        self.key_value_type = input.KeyValueArgType(
            *input.SEP_GROUP_ALL_ITEMS
        )

    def test_invalid_items(self):
        items = ['no-separator']
        for item in items:
            self.assertRaises(argparse.ArgumentTypeError,
                              lambda: self.key_value_type(item))

    def test_escape(self):
        headers, data, files, params = input.parse_items([
            # headers
            self.key_value_type('foo\\:bar:baz'),
            self.key_value_type('jack\\@jill:hill'),
            # data
            self.key_value_type('baz\\=bar=foo'),
            # files
            self.key_value_type('bar\\@baz@%s' % FILE_PATH_ARG)
        ])
        # `requests.structures.CaseInsensitiveDict` => `dict`
        headers = dict(headers._store.values())
        self.assertDictEqual(headers, {
            'foo:bar': 'baz',
            'jack@jill': 'hill',
        })
        self.assertDictEqual(data, {
            'baz=bar': 'foo',
        })
        self.assertIn('bar@baz', files)

    def test_escape_longsep(self):
        headers, data, files, params = input.parse_items([
            self.key_value_type('bob\\:==foo'),
        ])
        self.assertDictEqual(params, {
            'bob:': 'foo',
        })

    def test_valid_items(self):
        headers, data, files, params = input.parse_items([
            self.key_value_type('string=value'),
            self.key_value_type('header:value'),
            self.key_value_type('list:=["a", 1, {}, false]'),
            self.key_value_type('obj:={"a": "b"}'),
            self.key_value_type('eh:'),
            self.key_value_type('ed='),
            self.key_value_type('bool:=true'),
            self.key_value_type('file@' + FILE_PATH_ARG),
            self.key_value_type('query==value'),
            self.key_value_type('string-embed=@' + FILE_PATH_ARG),
            self.key_value_type('raw-json-embed:=@' + JSON_FILE_PATH_ARG),
        ])

        # Parsed headers
        # `requests.structures.CaseInsensitiveDict` => `dict`
        headers = dict(headers._store.values())
        self.assertDictEqual(headers, {
            'header': 'value',
            'eh': ''
        })

        # Parsed data
        raw_json_embed = data.pop('raw-json-embed')
        self.assertDictEqual(raw_json_embed, json.loads(
            JSON_FILE_CONTENT.decode('utf8')))
        data['string-embed'] = data['string-embed'].strip()
        self.assertDictEqual(dict(data), {
            "ed": "",
            "string": "value",
            "bool": True,
            "list": ["a", 1, {}, False],
            "obj": {"a": "b"},
            "string-embed": FILE_CONTENT,
        })

        # Parsed query string parameters
        self.assertDictEqual(params, {
            'query': 'value',
        })

        # Parsed file fields
        self.assertIn('file', files)
        self.assertEqual(files['file'][1].read().strip().decode('utf8'),
                         FILE_CONTENT)


class QuerystringTest(BaseTestCase):

    def test_query_string_params_in_url(self):
        r = http(
            '--print=Hhb',
            'GET',
            httpbin('/get?a=1&b=2')
        )

        path = '/get?a=1&b=2'
        url = httpbin(path)

        self.assertIn(OK, r)
        self.assertIn('GET %s HTTP/1.1' % path, r)
        self.assertIn('"url": "%s"' % url, r)

    def test_query_string_params_items(self):
        r = http(
            '--print=Hhb',
            'GET',
            httpbin('/get'),
            'a==1',
            'b==2'
        )

        path = '/get?a=1&b=2'
        url = httpbin(path)

        self.assertIn(OK, r)
        self.assertIn('GET %s HTTP/1.1' % path, r)
        self.assertIn('"url": "%s"' % url, r)

    def test_query_string_params_in_url_and_items_with_duplicates(self):
        r = http(
            '--print=Hhb',
            'GET',
            httpbin('/get?a=1&a=1'),
            'a==1',
            'a==1',
            'b==2',
        )

        path = '/get?a=1&a=1&a=1&a=1&b=2'
        url = httpbin(path)

        self.assertIn(OK, r)
        self.assertIn('GET %s HTTP/1.1' % path, r)
        self.assertIn('"url": "%s"' % url, r)


class CLIParserTestCase(BaseTestCase):

    def test_expand_localhost_shorthand(self):
        args = parser.parse_args(args=[':'], env=TestEnvironment())

        self.assertEqual(args.url, 'http://localhost')

    def test_expand_localhost_shorthand_with_slash(self):
        args = parser.parse_args(args=[':/'], env=TestEnvironment())

        self.assertEqual(args.url, 'http://localhost/')

    def test_expand_localhost_shorthand_with_port(self):
        args = parser.parse_args(args=[':3000'], env=TestEnvironment())

        self.assertEqual(args.url, 'http://localhost:3000')

    def test_expand_localhost_shorthand_with_path(self):
        args = parser.parse_args(args=[':/path'], env=TestEnvironment())

        self.assertEqual(args.url, 'http://localhost/path')

    def test_expand_localhost_shorthand_with_port_and_slash(self):
        args = parser.parse_args(args=[':3000/'], env=TestEnvironment())

        self.assertEqual(args.url, 'http://localhost:3000/')

    def test_expand_localhost_shorthand_with_port_and_path(self):
        args = parser.parse_args(args=[':3000/path'], env=TestEnvironment())

        self.assertEqual(args.url, 'http://localhost:3000/path')

    def test_dont_expand_shorthand_ipv6_as_shorthand(self):
        args = parser.parse_args(args=['::1'], env=TestEnvironment())

        self.assertEqual(args.url, 'http://::1')

    def test_dont_expand_longer_ipv6_as_shorthand(self):
        args = parser.parse_args(
            args=['::ffff:c000:0280'],
            env=TestEnvironment()
        )
        self.assertEqual(args.url, 'http://::ffff:c000:0280')

    def test_dont_expand_full_ipv6_as_shorthand(self):
        args = parser.parse_args(
            args=['0000:0000:0000:0000:0000:0000:0000:0001'],
            env=TestEnvironment()
        )

        self.assertEqual(
            args.url,
            'http://0000:0000:0000:0000:0000:0000:0000:0001'
        )


class ArgumentParserTestCase(BaseTestCase):

    def setUp(self):
        self.parser = input.Parser()

    def test_guess_when_method_set_and_valid(self):
        self.parser.args = argparse.Namespace()
        self.parser.args.method = 'GET'
        self.parser.args.url = 'http://example.com/'
        self.parser.args.items = []
        self.parser.args.ignore_stdin = False

        self.parser.env = TestEnvironment()

        self.parser._guess_method()

        self.assertEqual(self.parser.args.method, 'GET')
        self.assertEqual(self.parser.args.url, 'http://example.com/')
        self.assertEqual(self.parser.args.items, [])

    def test_guess_when_method_not_set(self):

        self.parser.args = argparse.Namespace()
        self.parser.args.method = None
        self.parser.args.url = 'http://example.com/'
        self.parser.args.items = []
        self.parser.args.ignore_stdin = False
        self.parser.env = TestEnvironment()

        self.parser._guess_method()

        self.assertEqual(self.parser.args.method, 'GET')
        self.assertEqual(self.parser.args.url, 'http://example.com/')
        self.assertEqual(self.parser.args.items, [])

    def test_guess_when_method_set_but_invalid_and_data_field(self):
        self.parser.args = argparse.Namespace()
        self.parser.args.method = 'http://example.com/'
        self.parser.args.url = 'data=field'
        self.parser.args.items = []
        self.parser.args.ignore_stdin = False
        self.parser.env = TestEnvironment()
        self.parser._guess_method()

        self.assertEqual(self.parser.args.method, 'POST')
        self.assertEqual(self.parser.args.url, 'http://example.com/')
        self.assertEqual(
            self.parser.args.items,
            [input.KeyValue(
                key='data', value='field', sep='=', orig='data=field')])

    def test_guess_when_method_set_but_invalid_and_header_field(self):
        self.parser.args = argparse.Namespace()
        self.parser.args.method = 'http://example.com/'
        self.parser.args.url = 'test:header'
        self.parser.args.items = []
        self.parser.args.ignore_stdin = False

        self.parser.env = TestEnvironment()

        self.parser._guess_method()

        self.assertEqual(self.parser.args.method, 'GET')
        self.assertEqual(self.parser.args.url, 'http://example.com/')
        self.assertEqual(
            self.parser.args.items,
            [input.KeyValue(
                key='test', value='header', sep=':', orig='test:header')])

    def test_guess_when_method_set_but_invalid_and_item_exists(self):
        self.parser.args = argparse.Namespace()
        self.parser.args.method = 'http://example.com/'
        self.parser.args.url = 'new_item=a'
        self.parser.args.items = [
            input.KeyValue(
                key='old_item', value='b', sep='=', orig='old_item=b')
        ]
        self.parser.args.ignore_stdin = False

        self.parser.env = TestEnvironment()

        self.parser._guess_method()

        self.assertEqual(self.parser.args.items, [
            input.KeyValue(
                key='new_item', value='a', sep='=', orig='new_item=a'),
            input.KeyValue(
                key='old_item', value='b', sep='=', orig='old_item=b'),
        ])


class TestNoOptions(BaseTestCase):

    def test_valid_no_options(self):
        r = http(
            '--verbose',
            '--no-verbose',
            'GET',
            httpbin('/get')
        )
        self.assertNotIn('GET /get HTTP/1.1', r)

    def test_invalid_no_options(self):
        r = http(
            '--no-war',
            'GET',
            httpbin('/get')
        )
        self.assertEqual(r.exit_status, 1)
        self.assertIn('unrecognized arguments: --no-war', r.stderr)
        self.assertNotIn('GET /get HTTP/1.1', r)


class IgnoreStdinTest(BaseTestCase):

    def test_ignore_stdin(self):
        with open(FILE_PATH) as f:
            r = http(
                '--ignore-stdin',
                '--verbose',
                httpbin('/get'),
                env=TestEnvironment(stdin=f, stdin_isatty=False)
            )
        self.assertIn(OK, r)
        self.assertIn('GET /get HTTP', r)  # Don't default to POST.
        self.assertNotIn(FILE_CONTENT, r)  # Don't send stdin data.

    def test_ignore_stdin_cannot_prompt_password(self):
        r = http(
            '--ignore-stdin',
            '--auth=username-without-password',
            httpbin('/get'),
        )
        self.assertEqual(r.exit_status, ExitStatus.ERROR)
        self.assertIn('because --ignore-stdin', r.stderr)
