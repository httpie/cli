import json
import os
import sys
import unittest
from unittest.mock import patch, DEFAULT

from click.testing import CliRunner
from requests.models import Response

from .base import TempAppDirTestCase
from httpie.prompt import xdg
from httpie.prompt.context import Context
from httpie.prompt.cli import cli, execute, ExecutionListener


def run_and_exit(cli_args=None, prompt_commands=None):
    """Run http-prompt executable, execute some prompt commands, and exit."""
    if cli_args is None:
        cli_args = []

        # Make sure last command is 'exit'
    if prompt_commands is None:
        prompt_commands = ['exit']
    else:
        prompt_commands += ['exit']

    # Fool cli() so that it believes we're running from CLI instead of pytest.
    # We will restore it at the end of the function.
    orig_argv = sys.argv
    sys.argv = ['http-prompt'] + cli_args

    try:
        with patch.multiple('httpie.prompt.cli',
                            prompt=DEFAULT, execute=DEFAULT) as mocks:
            mocks['execute'].side_effect = execute

            # prompt() is mocked to return the command in 'prompt_commands' in
            # sequence, i.e., prompt() returns prompt_commands[i-1] when it is
            # called for the ith time
            mocks['prompt'].side_effect = prompt_commands

            result = CliRunner().invoke(cli, cli_args)
            context = mocks['execute'].call_args[0][1]

        return result, context
    finally:
        sys.argv = orig_argv


class TestCli(TempAppDirTestCase):

    def test_without_args(self):
        result, context = run_and_exit(['http://localhost'])
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(context.url, 'http://localhost')
        self.assertEqual(context.options, {})
        self.assertEqual(context.body_params, {})
        self.assertEqual(context.headers, {})
        self.assertEqual(context.querystring_params, {})

    def test_incomplete_url1(self):
        result, context = run_and_exit(['://example.com'])
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(context.url, 'http://example.com')
        self.assertEqual(context.options, {})
        self.assertEqual(context.body_params, {})
        self.assertEqual(context.headers, {})
        self.assertEqual(context.querystring_params, {})

    def test_incomplete_url2(self):
        result, context = run_and_exit(['//example.com'])
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(context.url, 'http://example.com')
        self.assertEqual(context.options, {})
        self.assertEqual(context.body_params, {})
        self.assertEqual(context.headers, {})
        self.assertEqual(context.querystring_params, {})

    def test_incomplete_url3(self):
        result, context = run_and_exit(['example.com'])
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(context.url, 'http://example.com')
        self.assertEqual(context.options, {})
        self.assertEqual(context.body_params, {})
        self.assertEqual(context.headers, {})
        self.assertEqual(context.querystring_params, {})

    def test_httpie_oprions(self):
        url = 'http://example.com'
        custom_args = '--auth value: name=foo'
        result, context = run_and_exit([url] + custom_args.split())
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(context.url, 'http://example.com')
        self.assertEqual(context.options, {'--auth': 'value:'})
        self.assertEqual(context.body_params, {'name': 'foo'})
        self.assertEqual(context.headers, {})
        self.assertEqual(context.querystring_params, {})

    def test_persistent_context(self):
        result, context = run_and_exit(['//example.com', 'name=bob', 'id==10'])
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(context.url, 'http://example.com')
        self.assertEqual(context.options, {})
        self.assertEqual(context.body_params, {'name': 'bob'})
        self.assertEqual(context.headers, {})
        self.assertEqual(context.querystring_params, {'id': ['10']})

        result, context = run_and_exit()
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(context.url, 'http://example.com')
        self.assertEqual(context.options, {})
        self.assertEqual(context.body_params, {'name': 'bob'})
        self.assertEqual(context.headers, {})
        self.assertEqual(context.querystring_params, {'id': ['10']})

    def test_cli_args_bypasses_persistent_context(self):
        result, context = run_and_exit(['//example.com', 'name=bob', 'id==10'])
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(context.url, 'http://example.com')
        self.assertEqual(context.options, {})
        self.assertEqual(context.body_params, {'name': 'bob'})
        self.assertEqual(context.headers, {})
        self.assertEqual(context.querystring_params, {'id': ['10']})

        result, context = run_and_exit(['//example.com', 'sex=M'])
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(context.url, 'http://example.com')
        self.assertEqual(context.options, {})
        self.assertEqual(context.body_params, {'sex': 'M'})
        self.assertEqual(context.headers, {})

    def test_config_file(self):
        # Config file is not there at the beginning
        config_path = os.path.join(xdg.get_config_dir(), 'config.py')
        self.assertFalse(os.path.exists(config_path))

        # After user runs it for the first time, a default config file should
        # be created
        result, context = run_and_exit(['//example.com'])
        self.assertEqual(result.exit_code, 0)
        self.assertTrue(os.path.exists(config_path))

    def test_cli_arguments_with_spaces(self):
        result, context = run_and_exit(['example.com', "name=John Doe",
                                        "Authorization:Bearer API KEY"])
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(context.url, 'http://example.com')
        self.assertEqual(context.options, {})
        self.assertEqual(context.querystring_params, {})
        self.assertEqual(context.body_params, {'name': 'John Doe'})
        self.assertEqual(context.headers, {'Authorization': 'Bearer API KEY'})

    def test_spec_from_local(self):
        spec_filepath = self.make_tempfile(json.dumps({
            'paths': {
                '/users': {},
                '/orgs': {}
            }
        }))
        result, context = run_and_exit(['example.com', "--spec",
                                        spec_filepath])
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(context.url, 'http://example.com')
        self.assertEqual(set([n.name for n in context.root.children]),
                         set(['users', 'orgs']))

    def test_spec_basePath(self):
        spec_filepath = self.make_tempfile(json.dumps({
            'basePath': '/api/v1',
            'paths': {
                '/users': {},
                '/orgs': {}
            }
        }))
        result, context = run_and_exit(['example.com', "--spec",
                                        spec_filepath])
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(context.url, 'http://example.com')

        lv1_names = set([node.name for node in context.root.ls()])
        lv2_names = set([node.name for node in context.root.ls('api')])
        lv3_names = set([node.name for node in context.root.ls('api', 'v1')])

        self.assertEqual(lv1_names, set(['api']))
        self.assertEqual(lv2_names, set(['v1']))
        self.assertEqual(lv3_names, set(['users', 'orgs']))

    def test_spec_from_http(self):
        spec_url = 'https://raw.githubusercontent.com/github/rest-api-description/main/descriptions/api.github.com/api.github.com.json'
        result, context = run_and_exit(['https://api.github.com', '--spec',
                                        spec_url])
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(context.url, 'https://api.github.com')

        top_level_paths = set([n.name for n in context.root.children])
        self.assertIn('repos', top_level_paths)
        self.assertIn('users', top_level_paths)

    def test_spec_from_http_only(self):
        spec_url = (
            'https://api.apis.guru/v2/specs/medium.com/1.0.0/swagger.json')
        result, context = run_and_exit(['--spec', spec_url])
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(context.url, 'https://api.medium.com/v1')

        lv1_names = set([node.name for node in context.root.ls()])
        lv2_names = set([node.name for node in context.root.ls('v1')])

        self.assertEqual(lv1_names, set(['v1']))
        self.assertEqual(lv2_names, set(['me', 'publications', 'users']))

    def test_spec_with_trailing_slash(self):
        spec_filepath = self.make_tempfile(json.dumps({
            'basePath': '/api',
            'paths': {
                '/': {},
                '/users/': {}
            }
        }))
        result, context = run_and_exit(['example.com', "--spec",
                                        spec_filepath])
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(context.url, 'http://example.com')
        lv1_names = set([node.name for node in context.root.ls()])
        lv2_names = set([node.name for node in context.root.ls('api')])
        self.assertEqual(lv1_names, set(['api']))
        self.assertEqual(lv2_names, set(['/', 'users/']))

    def test_env_only(self):
        env_filepath = self.make_tempfile(
            "cd http://example.com\nname=bob\nid==10")
        result, context = run_and_exit(["--env", env_filepath])
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(context.url, 'http://example.com')
        self.assertEqual(context.options, {})
        self.assertEqual(context.body_params, {'name': 'bob'})
        self.assertEqual(context.headers, {})
        self.assertEqual(context.querystring_params, {'id': ['10']})

    def test_env_with_url(self):
        env_filepath = self.make_tempfile(
            "cd http://example.com\nname=bob\nid==10")
        result, context = run_and_exit(["--env", env_filepath,
                                        'other_example.com'])
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(context.url, 'http://other_example.com')
        self.assertEqual(context.options, {})
        self.assertEqual(context.body_params, {'name': 'bob'})
        self.assertEqual(context.headers, {})
        self.assertEqual(context.querystring_params, {'id': ['10']})

    def test_env_with_options(self):
        env_filepath = self.make_tempfile(
            "cd http://example.com\nname=bob\nid==10")
        result, context = run_and_exit(["--env", env_filepath,
                                        'other_example.com', 'name=alice'])
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(context.url, 'http://other_example.com')
        self.assertEqual(context.options, {})
        self.assertEqual(context.body_params, {'name': 'alice'})
        self.assertEqual(context.headers, {})
        self.assertEqual(context.querystring_params, {'id': ['10']})

    @patch('httpie.prompt.cli.prompt')
    @patch('httpie.prompt.cli.execute')
    def test_press_ctrl_d(self, execute_mock, prompt_mock):
        prompt_mock.side_effect = EOFError
        execute_mock.side_effect = execute
        result = CliRunner().invoke(cli, [])
        self.assertEqual(result.exit_code, 0)


class TestExecutionListenerSetCookies(unittest.TestCase):

    def setUp(self):
        self.listener = ExecutionListener({})

        self.response = Response()
        self.response.cookies.update({
            'username': 'john',
            'sessionid': 'abcd'
        })

        self.context = Context('http://localhost')
        self.context.headers['Cookie'] = 'name="John Doe"; sessionid=xyz'

    def test_auto(self):
        self.listener.cfg['set_cookies'] = 'auto'
        self.listener.response_returned(self.context, self.response)

        self.assertEqual(self.context.headers['Cookie'],
                         'name="John Doe"; sessionid=abcd; username=john')

    @patch('httpie.prompt.cli.click.confirm')
    def test_ask_and_yes(self, confirm_mock):
        confirm_mock.return_value = True

        self.listener.cfg['set_cookies'] = 'ask'
        self.listener.response_returned(self.context, self.response)

        self.assertEqual(self.context.headers['Cookie'],
                         'name="John Doe"; sessionid=abcd; username=john')

    @patch('httpie.prompt.cli.click.confirm')
    def test_ask_and_no(self, confirm_mock):
        confirm_mock.return_value = False

        self.listener.cfg['set_cookies'] = 'ask'
        self.listener.response_returned(self.context, self.response)

        self.assertEqual(self.context.headers['Cookie'],
                         'name="John Doe"; sessionid=xyz')

    def test_off(self):
        self.listener.cfg['set_cookies'] = 'off'
        self.listener.response_returned(self.context, self.response)

        self.assertEqual(self.context.headers['Cookie'],
                         'name="John Doe"; sessionid=xyz')
