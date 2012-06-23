import unittest
from argparse import Namespace
from httpie.cliparse import HTTPieArgumentParser, KeyValue


__author__ = 'vladimir'



class HTTPieArgumentParserTestCase(unittest.TestCase):
    def setUp(self):
        self.HTTPieArgumentParserStub = type(HTTPieArgumentParser.__name__, (HTTPieArgumentParser,), {})
        self.HTTPieArgumentParserStub.__init__ = lambda self: None
        self.httpie_argument_parser = self.HTTPieArgumentParserStub()

    def test_suggest_when_method_set_and_valid(self):
        args = Namespace()
        args.method = 'GET'
        args.url = 'http://example.com/'
        args.items = []

        self.httpie_argument_parser.suggest_method(args)

        self.assertEquals(args.method, 'GET')
        self.assertEquals(args.url, 'http://example.com/')
        self.assertEquals(args.items, [])

    def test_suggest_when_method_not_set(self):
        args = Namespace()
        args.method = None
        args.url = 'http://example.com/'
        args.items = []

        self.httpie_argument_parser.suggest_method(args)

        self.assertEquals(args.method, 'GET')
        self.assertEquals(args.url, 'http://example.com/')
        self.assertEquals(args.items, [])

    def test_suggest_when_method_set_but_invalid_and_data_field(self):
        args = Namespace()
        args.method = 'http://example.com/'
        args.url = 'data=field'
        args.items = []

        self.httpie_argument_parser.suggest_method(args)

        self.assertEquals(args.method, 'POST')
        self.assertEquals(args.url, 'http://example.com/')
        self.assertEquals(args.items, [KeyValue(key='data', value='field', sep='=', orig='data=field')])

    def test_suggest_when_method_set_but_invalid_and_header_field(self):
        args = Namespace()
        args.method = 'http://example.com/'
        args.url = 'test:header'
        args.items = []

        self.httpie_argument_parser.suggest_method(args)

        self.assertEquals(args.method, 'GET')
        self.assertEquals(args.url, 'http://example.com/')
        self.assertEquals(args.items, [KeyValue(key='test', value='header', sep=':', orig='test:header')])

    def test_suggest_when_method_set_but_invalid_and_item_exists(self):
        args = Namespace()
        args.method = 'http://example.com/'
        args.url = 'new_item=a'
        args.items = [KeyValue(key='old_item', value='b', sep='=', orig='old_item=b')]

        self.httpie_argument_parser.suggest_method(args)

        self.assertEquals(args.items, [
            KeyValue(key='new_item', value='a', sep='=', orig='new_item=a'),
            KeyValue(key='old_item', value='b', sep='=', orig='old_item=b'),
        ])
