# -*- coding: utf-8 -*-
import unittest

from prompt_toolkit.document import Document

from httpie.prompt.completer import HttpPromptCompleter
from httpie.prompt.context import Context


class TestCompleter(unittest.TestCase):

    def setUp(self):
        self.context = Context('http://localhost', spec={
            'paths': {
                '/users': {},
                '/users/{username}': {},
                '/users/{username}/events': {},
                '/users/{username}/orgs': {},
                '/orgs': {},
                '/orgs/{org}': {},
                '/orgs/{org}/events': {},
                '/orgs/{org}/members': {}
            }
        })
        self.completer = HttpPromptCompleter(self.context)
        self.completer_event = None

    def get_completions(self, command):
        if not isinstance(command, str):
            command = command.decode()
        position = len(command)
        completions = self.completer.get_completions(
            Document(text=command, cursor_position=position),
            self.completer_event)
        return [c.text for c in completions]

    def test_header_name(self):
        result = self.get_completions('ctype')
        self.assertEqual(result[0], 'Content-Type')

    def test_header_value(self):
        result = self.get_completions('Content-Type:json')
        self.assertEqual(result[0], 'application/json')

    def test_verify_option(self):
        result = self.get_completions('--vfy')
        self.assertEqual(result[0], '--verify')

    def test_preview_then_action(self):
        result = self.get_completions('httpie po')
        self.assertEqual(result[0], 'post')

    def test_rm_body_param(self):
        self.context.body_params['my_name'] = 'dont_care'
        result = self.get_completions('rm -b ')
        self.assertEqual(result[0], 'my_name')

    def test_rm_body_json_param(self):
        self.context.body_json_params['number'] = 2
        result = self.get_completions('rm -b ')
        self.assertEqual(result[0], 'number')

    def test_rm_querystring_param(self):
        self.context.querystring_params['my_name'] = 'dont_care'
        result = self.get_completions('rm -q ')
        self.assertEqual(result[0], 'my_name')

    def test_rm_header(self):
        self.context.headers['Accept'] = 'dont_care'
        result = self.get_completions('rm -h ')
        self.assertEqual(result[0], 'Accept')

    def test_rm_option(self):
        self.context.options['--form'] = None
        result = self.get_completions('rm -o ')
        self.assertEqual(result[0], '--form')

    def test_querystring_with_chinese(self):
        result = self.get_completions('name==王')
        self.assertFalse(result)

    def test_header_with_spanish(self):
        result = self.get_completions('X-Custom-Header:Jesú')
        self.assertFalse(result)

    def test_options_method(self):
        result = self.get_completions('opt')
        self.assertEqual(result[0], 'options')

    def test_ls_no_path(self):
        result = self.get_completions('ls ')
        self.assertEqual(result, ['orgs', 'users'])

    def test_ls_no_path_substring(self):
        result = self.get_completions('ls o')
        self.assertEqual(result, ['orgs'])

    def test_ls_absolute_path(self):
        result = self.get_completions('ls /users/1/')
        self.assertEqual(result, ['events', 'orgs'])

    def test_ls_absolute_path_substring(self):
        result = self.get_completions('ls /users/1/e')
        self.assertEqual(result, ['events'])

    def test_ls_relative_path(self):
        self.context.url = 'http://localhost/orgs'
        result = self.get_completions('ls 1/')
        self.assertEqual(result, ['events', 'members'])

    def test_cd_no_path(self):
        result = self.get_completions('cd ')
        self.assertEqual(result, ['orgs', 'users'])

    def test_cd_no_path_substring(self):
        result = self.get_completions('cd o')
        self.assertEqual(result, ['orgs'])

    def test_cd_absolute_path(self):
        result = self.get_completions('cd /users/1/')
        self.assertEqual(result, ['events', 'orgs'])

    def test_cd_absolute_path_substring(self):
        result = self.get_completions('cd /users/1/e')
        self.assertEqual(result, ['events'])

    def test_cd_relative_path(self):
        self.context.url = 'http://localhost/orgs'
        result = self.get_completions('cd 1/')
        self.assertEqual(result, ['events', 'members'])
