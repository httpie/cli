# -*- coding: utf-8 -*-
import hashlib
import io
import json
import shutil
import os
import sys

import pytest

from collections import namedtuple

from unittest.mock import patch

from httpie.prompt.context import Context
from httpie.prompt.executionimport execute, HTTPIE_PROGRAM_NAME

from .base import TempAppDirTestCase


class ExecutionTestCase(TempAppDirTestCase):

    def setUp(self):
        super(ExecutionTestCase, self).setUp()
        self.patchers = [
            ('httpie_main', patch('http_prompt.execution.httpie_main')),
            ('echo_via_pager',
             patch('http_prompt.output.click.echo_via_pager')),
            ('secho', patch('http_prompt.execution.click.secho')),
            ('get_terminal_size', patch('http_prompt.utils.get_terminal_size'))
        ]
        for attr_name, patcher in self.patchers:
            setattr(self, attr_name, patcher.start())

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

        # pytest mocks to capture stdout so we can't really get_terminal_size()
        Size = namedtuple('Size', ['columns', 'rows'])
        self.get_terminal_size.return_value = Size(80, 30)

    def tearDown(self):
        super(ExecutionTestCase, self).tearDown()
        for _, patcher in self.patchers:
            patcher.stop()

    def assert_httpie_main_called_with(self, args):
        self.assertEqual(self.httpie_main.call_args[0][0], [
                         HTTPIE_PROGRAM_NAME, *args])

    def assert_stdout(self, expected_msg):
        # Append '\n' to simulate behavior of click.echo_via_pager(),
        # which we use whenever we want to output anything to stdout
        printed_msg = self.echo_via_pager.call_args[0][0] + '\n'
        self.assertEqual(printed_msg, expected_msg)

    def assert_stdout_startswith(self, expected_prefix):
        printed_msg = self.echo_via_pager.call_args[0][0]
        self.assertTrue(printed_msg.startswith(expected_prefix))

    def get_stdout(self):
        return self.echo_via_pager.call_args[0][0]

    def assert_stderr(self, expected_msg):
        printed_msg = self.secho.call_args[0][0]
        print_options = self.secho.call_args[1]
        self.assertEqual(printed_msg, expected_msg)
        self.assertEqual(print_options, {'err': True, 'fg': 'red'})


class TestExecution_noop(ExecutionTestCase):

    def test_empty_string(self):
        execute('', self.context)
        self.assertEqual(self.context.url, 'http://localhost')
        self.assertFalse(self.context.options)
        self.assertFalse(self.context.headers)
        self.assertFalse(self.context.querystring_params)
        self.assertFalse(self.context.body_params)
        self.assertFalse(self.context.should_exit)

    def test_spaces(self):
        execute('  \t \t  ', self.context)
        self.assertEqual(self.context.url, 'http://localhost')
        self.assertFalse(self.context.options)
        self.assertFalse(self.context.headers)
        self.assertFalse(self.context.querystring_params)
        self.assertFalse(self.context.body_params)
        self.assertFalse(self.context.should_exit)


class TestExecution_env(ExecutionTestCase):

    def setUp(self):
        super(TestExecution_env, self).setUp()

        self.context.url = 'http://localhost:8000/api'
        self.context.headers.update({
            'Accept': 'text/csv',
            'Authorization': 'ApiKey 1234'
        })
        self.context.querystring_params.update({
            'page': ['1'],
            'limit': ['50']
        })
        self.context.body_params.update({
            'name': 'John Doe'
        })
        self.context.options.update({
            '--verify': 'no',
            '--form': None
        })

    def test_env(self):
        execute('env', self.context)
        self.assert_stdout("--form\n--verify=no\n"
                           "cd http://localhost:8000/api\n"
                           "limit==50\npage==1\n"
                           "'name=John Doe'\n"
                           "Accept:text/csv\n"
                           "'Authorization:ApiKey 1234'\n")

    def test_env_with_spaces(self):
        execute('  env   ', self.context)
        self.assert_stdout("--form\n--verify=no\n"
                           "cd http://localhost:8000/api\n"
                           "limit==50\npage==1\n"
                           "'name=John Doe'\n"
                           "Accept:text/csv\n"
                           "'Authorization:ApiKey 1234'\n")

    def test_env_non_ascii(self):
        self.context.body_params['name'] = '許 功蓋'
        execute('env', self.context)
        self.assert_stdout("--form\n--verify=no\n"
                           "cd http://localhost:8000/api\n"
                           "limit==50\npage==1\n"
                           "'name=許 功蓋'\n"
                           "Accept:text/csv\n"
                           "'Authorization:ApiKey 1234'\n")

    def test_env_write_to_file(self):
        filename = self.make_tempfile()

        # write something first to make sure it's a full overwrite
        with open(filename, 'w') as f:
            f.write('hello world\n')

        execute('env > %s' % filename, self.context)

        with open(filename) as f:
            content = f.read()

        self.assertEqual(content,
                         "--form\n--verify=no\n"
                         "cd http://localhost:8000/api\n"
                         "limit==50\npage==1\n"
                         "'name=John Doe'\n"
                         "Accept:text/csv\n"
                         "'Authorization:ApiKey 1234'\n")

    def test_env_write_to_file_with_env_vars(self):
        filename = self.make_tempfile('hello world\n', 'testenvvar')
        filename_with_var = filename.replace("testenvvar", "${MYPRIVATEVAR}")

        os.environ['MYPRIVATEVAR'] = 'testenvvar'
        execute('env > %s' % filename_with_var, self.context)
        os.environ['MYPRIVATEVAR'] = ''

        with open(filename) as f:
            content = f.read()

        self.assertEqual(content,
                         "--form\n--verify=no\n"
                         "cd http://localhost:8000/api\n"
                         "limit==50\npage==1\n"
                         "'name=John Doe'\n"
                         "Accept:text/csv\n"
                         "'Authorization:ApiKey 1234'\n")

    def test_env_non_ascii_and_write_to_file(self):
        filename = self.make_tempfile()

        # write something first to make sure it's a full overwrite
        with open(filename, 'w') as f:
            f.write('hello world\n')

        self.context.body_params['name'] = '許 功蓋'
        execute('env > %s' % filename, self.context)

        with open(filename, encoding='utf-8') as f:
            content = f.read()

        self.assertEqual(content,
                         "--form\n--verify=no\n"
                         "cd http://localhost:8000/api\n"
                         "limit==50\npage==1\n"
                         "'name=許 功蓋'\n"
                         "Accept:text/csv\n"
                         "'Authorization:ApiKey 1234'\n")

    def test_env_write_to_quoted_filename(self):
        filename = self.make_tempfile()

        # Write something first to make sure it's a full overwrite
        with open(filename, 'w') as f:
            f.write('hello world\n')

        execute("env > '%s'" % filename, self.context)

        with open(filename) as f:
            content = f.read()

        self.assertEqual(content,
                         "--form\n--verify=no\n"
                         "cd http://localhost:8000/api\n"
                         "limit==50\npage==1\n"
                         "'name=John Doe'\n"
                         "Accept:text/csv\n"
                         "'Authorization:ApiKey 1234'\n")

    def test_env_append_to_file(self):
        filename = self.make_tempfile()

        # Write something first to make sure it's an append
        with open(filename, 'w') as f:
            f.write('hello world\n')

        execute('env >> %s' % filename, self.context)

        with open(filename) as f:
            content = f.read()

        self.assertEqual(content,
                         "hello world\n"
                         "--form\n--verify=no\n"
                         "cd http://localhost:8000/api\n"
                         "limit==50\npage==1\n"
                         "'name=John Doe'\n"
                         "Accept:text/csv\n"
                         "'Authorization:ApiKey 1234'\n")


class TestExecution_source_and_exec(ExecutionTestCase):

    def setUp(self):
        super(TestExecution_source_and_exec, self).setUp()

        self.context.url = 'http://localhost:8000/api'
        self.context.headers.update({
            'Accept': 'text/csv',
            'Authorization': 'ApiKey 1234'
        })
        self.context.querystring_params.update({
            'page': ['1'],
            'limit': ['50']
        })
        self.context.body_params.update({
            'name': 'John Doe'
        })
        self.context.options.update({
            '--verify': 'no',
            '--form': None
        })

        # The file that is about to be sourced/exec'd
        self.filename = self.make_tempfile(
            "Language:en Authorization:'ApiKey 5678'\n"
            "name='Jane Doe'  username=jane   limit==25\n"
            "rm -o --form\n"
            "cd v2/user\n")

    def test_source(self):
        execute('source %s' % self.filename, self.context)

        self.assertEqual(self.context.url,
                         'http://localhost:8000/api/v2/user')
        self.assertEqual(self.context.headers, {
            'Accept': 'text/csv',
            'Authorization': 'ApiKey 5678',
            'Language': 'en'
        })
        self.assertEqual(self.context.querystring_params, {
            'page': ['1'],
            'limit': ['25']
        })
        self.assertEqual(self.context.body_params, {
            'name': 'Jane Doe',
            'username': 'jane'
        })
        self.assertEqual(self.context.options, {
            '--verify': 'no'
        })

    def test_source_with_spaces(self):
        execute(' source       %s   ' % self.filename, self.context)

        self.assertEqual(self.context.url,
                         'http://localhost:8000/api/v2/user')
        self.assertEqual(self.context.headers, {
            'Accept': 'text/csv',
            'Authorization': 'ApiKey 5678',
            'Language': 'en'
        })
        self.assertEqual(self.context.querystring_params, {
            'page': ['1'],
            'limit': ['25']
        })
        self.assertEqual(self.context.body_params, {
            'name': 'Jane Doe',
            'username': 'jane'
        })
        self.assertEqual(self.context.options, {
            '--verify': 'no'
        })

    def test_source_non_existing_file(self):
        c = self.context.copy()
        execute('source no_such_file.txt', self.context)
        self.assertEqual(self.context, c)

        # Expect the error message would be the same as when we open the
        # non-existing file
        try:
            with open('no_such_file.txt'):
                pass
        except OSError as err:
            err_msg = str(err)
        else:
            assert False, 'what?! no_such_file.txt exists!'

        self.assert_stderr(err_msg)

    def test_source_quoted_filename(self):
        execute('source "%s"' % self.filename, self.context)

        self.assertEqual(self.context.url,
                         'http://localhost:8000/api/v2/user')
        self.assertEqual(self.context.headers, {
            'Accept': 'text/csv',
            'Authorization': 'ApiKey 5678',
            'Language': 'en'
        })
        self.assertEqual(self.context.querystring_params, {
            'page': ['1'],
            'limit': ['25']
        })
        self.assertEqual(self.context.body_params, {
            'name': 'Jane Doe',
            'username': 'jane'
        })
        self.assertEqual(self.context.options, {
            '--verify': 'no'
        })

    @pytest.mark.skipif(sys.platform == 'win32',
                        reason="Windows doesn't use backslashes to escape")
    def test_source_escaped_filename(self):
        new_filename = self.filename + r' copy'
        shutil.copyfile(self.filename, new_filename)

        new_filename = new_filename.replace(' ', r'\ ')

        execute('source %s' % new_filename, self.context)

        self.assertEqual(self.context.url,
                         'http://localhost:8000/api/v2/user')
        self.assertEqual(self.context.headers, {
            'Accept': 'text/csv',
            'Authorization': 'ApiKey 5678',
            'Language': 'en'
        })
        self.assertEqual(self.context.querystring_params, {
            'page': ['1'],
            'limit': ['25']
        })
        self.assertEqual(self.context.body_params, {
            'name': 'Jane Doe',
            'username': 'jane'
        })
        self.assertEqual(self.context.options, {
            '--verify': 'no'
        })

    def test_exec(self):
        execute('exec %s' % self.filename, self.context)

        self.assertEqual(self.context.url,
                         'http://localhost:8000/api/v2/user')
        self.assertEqual(self.context.headers, {
            'Authorization': 'ApiKey 5678',
            'Language': 'en'
        })
        self.assertEqual(self.context.querystring_params, {
            'limit': ['25']
        })
        self.assertEqual(self.context.body_params, {
            'name': 'Jane Doe',
            'username': 'jane'
        })

    def test_exec_with_spaces(self):
        execute('  exec    %s   ' % self.filename, self.context)

        self.assertEqual(self.context.url,
                         'http://localhost:8000/api/v2/user')
        self.assertEqual(self.context.headers, {
            'Authorization': 'ApiKey 5678',
            'Language': 'en'
        })
        self.assertEqual(self.context.querystring_params, {
            'limit': ['25']
        })
        self.assertEqual(self.context.body_params, {
            'name': 'Jane Doe',
            'username': 'jane'
        })

    def test_exec_non_existing_file(self):
        c = self.context.copy()
        execute('exec no_such_file.txt', self.context)
        self.assertEqual(self.context, c)

        # Try to get the error message when opening a non-existing file
        try:
            with open('no_such_file.txt'):
                pass
        except OSError as err:
            err_msg = str(err)
        else:
            assert False, 'what?! no_such_file.txt exists!'

        self.assert_stderr(err_msg)

    def test_exec_quoted_filename(self):
        execute("exec '%s'" % self.filename, self.context)

        self.assertEqual(self.context.url,
                         'http://localhost:8000/api/v2/user')
        self.assertEqual(self.context.headers, {
            'Authorization': 'ApiKey 5678',
            'Language': 'en'
        })
        self.assertEqual(self.context.querystring_params, {
            'limit': ['25']
        })
        self.assertEqual(self.context.body_params, {
            'name': 'Jane Doe',
            'username': 'jane'
        })

    @pytest.mark.skipif(sys.platform == 'win32',
                        reason="Windows doesn't use backslashes to escape")
    def test_exec_escaped_filename(self):
        new_filename = self.filename + r' copy'
        shutil.copyfile(self.filename, new_filename)

        new_filename = new_filename.replace(' ', r'\ ')

        execute('exec %s' % new_filename, self.context)
        self.assertEqual(self.context.url,
                         'http://localhost:8000/api/v2/user')
        self.assertEqual(self.context.headers, {
            'Authorization': 'ApiKey 5678',
            'Language': 'en'
        })
        self.assertEqual(self.context.querystring_params, {
            'limit': ['25']
        })
        self.assertEqual(self.context.body_params, {
            'name': 'Jane Doe',
            'username': 'jane'
        })


class TestExecution_env_and_source(ExecutionTestCase):

    def test_env_and_source(self):
        c = Context()
        c.url = 'http://localhost:8000/api'
        c.headers.update({
            'Accept': 'text/csv',
            'Authorization': 'ApiKey 1234'
        })
        c.querystring_params.update({
            'page': ['1'],
            'limit': ['50']
        })
        c.body_params.update({
            'name': 'John Doe'
        })
        c.options.update({
            '--verify': 'no',
            '--form': None
        })

        c2 = c.copy()

        filename = self.make_tempfile()
        execute('env > %s' % filename, c)
        execute('rm *', c)

        self.assertFalse(c.headers)
        self.assertFalse(c.querystring_params)
        self.assertFalse(c.body_params)
        self.assertFalse(c.options)

        execute('source %s' % filename, c)

        self.assertEqual(c, c2)

    def test_env_and_source_non_ascii(self):
        c = Context()
        c.url = 'http://localhost:8000/api'
        c.headers.update({
            'Accept': 'text/csv',
            'Authorization': 'ApiKey 1234'
        })
        c.querystring_params.update({
            'page': ['1'],
            'limit': ['50']
        })
        c.body_params.update({
            'name': '許 功蓋'
        })
        c.options.update({
            '--verify': 'no',
            '--form': None
        })

        c2 = c.copy()

        filename = self.make_tempfile()
        execute('env > %s' % filename, c)
        execute('rm *', c)

        self.assertFalse(c.headers)
        self.assertFalse(c.querystring_params)
        self.assertFalse(c.body_params)
        self.assertFalse(c.options)

        execute('source %s' % filename, c)

        self.assertEqual(c, c2)


class TestExecution_help(ExecutionTestCase):

    def test_help(self):
        execute('help', self.context)
        self.assert_stdout_startswith('Commands:\n\tcd')

    def test_help_with_spaces(self):
        execute('  help   ', self.context)
        self.assert_stdout_startswith('Commands:\n\tcd')


class TestExecution_exit(ExecutionTestCase):

    def test_exit(self):
        execute('exit', self.context)
        self.assertTrue(self.context.should_exit)

    def test_exit_with_spaces(self):
        execute('   exit  ', self.context)
        self.assertTrue(self.context.should_exit)


class TestExecution_cd(ExecutionTestCase):

    def test_single_level(self):
        execute('cd api', self.context)
        self.assertEqual(self.context.url, 'http://localhost/api')

    def test_many_levels(self):
        execute('cd api/v2/movie/50', self.context)
        self.assertEqual(self.context.url, 'http://localhost/api/v2/movie/50')

    def test_change_base(self):
        execute('cd //example.com/api', self.context)
        self.assertEqual(self.context.url, 'http://example.com/api')

    def test_root(self):
        execute('cd /api/v2', self.context)
        self.assertEqual(self.context.url, 'http://localhost/api/v2')

        execute('cd /index.html', self.context)
        self.assertEqual(self.context.url, 'http://localhost/index.html')

    def test_dot_dot(self):
        execute('cd api/v1', self.context)
        self.assertEqual(self.context.url, 'http://localhost/api/v1')

        execute('cd ..', self.context)
        self.assertEqual(self.context.url, 'http://localhost/api')

        # If dot-dot has a trailing slash, the resulting URL should have a
        # trailing slash
        execute('cd ../rest/api/', self.context)
        self.assertEqual(self.context.url, 'http://localhost/rest/api/')

    def test_url_with_trailing_slash(self):
        self.context.url = 'http://localhost/'
        execute('cd api', self.context)
        self.assertEqual(self.context.url, 'http://localhost/api')

        execute('cd v2/', self.context)
        self.assertEqual(self.context.url, 'http://localhost/api/v2/')

        execute('cd /objects/', self.context)
        self.assertEqual(self.context.url, 'http://localhost/objects/')

    def test_path_with_trailing_slash(self):
        execute('cd api/', self.context)
        self.assertEqual(self.context.url, 'http://localhost/api/')

        execute('cd movie/1/', self.context)
        self.assertEqual(self.context.url, 'http://localhost/api/movie/1/')

    def test_without_url(self):
        execute('cd api/', self.context)
        self.assertEqual(self.context.url, 'http://localhost/api/')

        execute('cd', self.context)
        self.assertEqual(self.context.url, 'http://localhost')


class TestExecution_rm(ExecutionTestCase):

    def test_header(self):
        self.context.headers['Content-Type'] = 'text/html'
        execute('rm -h Content-Type', self.context)
        self.assertFalse(self.context.headers)

    def test_option(self):
        self.context.options['--form'] = None
        execute('rm -o --form', self.context)
        self.assertFalse(self.context.options)

    def test_querystring(self):
        self.context.querystring_params['page'] = '1'
        execute('rm -q page', self.context)
        self.assertFalse(self.context.querystring_params)

    def test_body_param(self):
        self.context.body_params['name'] = 'alice'
        execute('rm -b name', self.context)
        self.assertFalse(self.context.body_params)

    def test_body_json_param(self):
        self.context.body_json_params['name'] = 'bob'
        execute('rm -b name', self.context)
        self.assertFalse(self.context.body_json_params)

    def test_header_single_quoted(self):
        self.context.headers['Content-Type'] = 'text/html'
        execute("rm -h 'Content-Type'", self.context)
        self.assertFalse(self.context.headers)

    def test_option_double_quoted(self):
        self.context.options['--form'] = None
        execute('rm -o "--form"', self.context)
        self.assertFalse(self.context.options)

    def test_querystring_double_quoted(self):
        self.context.querystring_params['page size'] = '10'
        execute('rm -q "page size"', self.context)
        self.assertFalse(self.context.querystring_params)

    def test_body_param_double_quoted(self):
        self.context.body_params['family name'] = 'Doe Doe'
        execute('rm -b "family name"', self.context)
        self.assertFalse(self.context.body_params)

    def test_body_param_escaped(self):
        self.context.body_params['family name'] = 'Doe Doe'
        execute(r'rm -b family\ name', self.context)
        self.assertFalse(self.context.body_params)

    def test_body_json_param_escaped_colon(self):
        self.context.body_json_params[r'where[id\:gt]'] = 2
        execute(r'rm -b where[id\:gt]', self.context)
        self.assertFalse(self.context.body_json_params)

    def test_body_param_escaped_equal(self):
        self.context.body_params[r'foo\=bar'] = 'hello'
        execute(r'rm -b foo\=bar', self.context)
        self.assertFalse(self.context.body_params)

    def test_non_existing_key(self):
        execute('rm -q abcd', self.context)
        self.assert_stderr("Key 'abcd' not found")

    def test_non_existing_key_unicode(self):  # See #25
        execute(u'rm -q abcd', self.context)
        self.assert_stderr("Key 'abcd' not found")

    def test_body_reset(self):
        self.context.body_params.update({
            'first_name': 'alice',
            'last_name': 'bryne'
        })
        execute('rm -b *', self.context)
        self.assertFalse(self.context.body_params)

    def test_querystring_reset(self):
        self.context.querystring_params.update({
            'first_name': 'alice',
            'last_name': 'bryne'
        })
        execute('rm -q *', self.context)
        self.assertFalse(self.context.querystring_params)

    def test_headers_reset(self):
        self.context.headers.update({
            'Content-Type': 'text/html',
            'Accept': 'application/json'
        })
        execute('rm -h *', self.context)
        self.assertFalse(self.context.headers)

    def test_options_reset(self):
        self.context.options.update({
            '--form': None,
            '--body': None
        })
        execute('rm -o *', self.context)
        self.assertFalse(self.context.options)

    def test_reset(self):
        self.context.options.update({
            '--form': None,
            '--verify': 'no'
        })
        self.context.headers.update({
            'Accept': 'dontcare',
            'Content-Type': 'dontcare'
        })
        self.context.querystring_params.update({
            'name': 'dontcare',
            'email': 'dontcare'
        })
        self.context.body_params.update({
            'name': 'dontcare',
            'email': 'dontcare'
        })
        self.context.body_json_params.update({
            'name': 'dontcare'
        })

        execute('rm *', self.context)

        self.assertFalse(self.context.options)
        self.assertFalse(self.context.headers)
        self.assertFalse(self.context.querystring_params)
        self.assertFalse(self.context.body_params)
        self.assertFalse(self.context.body_json_params)


class TestExecution_ls(ExecutionTestCase):

    def test_root(self):
        execute('ls', self.context)
        self.assert_stdout('orgs  users\n')

    def test_relative_path(self):
        self.context.url = 'http://localhost/users'
        execute('ls 101', self.context)
        self.assert_stdout('events orgs\n')

    def test_absolute_path(self):
        self.context.url = 'http://localhost/users'
        execute('ls /orgs/1', self.context)
        self.assert_stdout('events  members\n')

    def test_redirect_write(self):
        filename = self.make_tempfile()

        # Write something first to make sure it's a full overwrite
        with open(filename, 'w') as f:
            f.write('hello world\n')

        execute('ls > %s' % filename, self.context)

        with open(filename) as f:
            content = f.read()
        self.assertEqual(content, 'orgs\nusers')

    def test_redirect_append(self):
        filename = self.make_tempfile()

        # Write something first to make sure it's an append
        with open(filename, 'w') as f:
            f.write('hello world\n')

        execute('ls >> %s' % filename, self.context)

        with open(filename) as f:
            content = f.read()
        self.assertEqual(content, 'hello world\norgs\nusers')

    def test_grep(self):
        execute('ls | grep users', self.context)
        self.assert_stdout('users\n')


class TestMutation(ExecutionTestCase):

    def test_simple_headers(self):
        execute('Accept:text/html User-Agent:HttpPrompt', self.context)
        self.assertEqual(self.context.headers, {
            'Accept': 'text/html',
            'User-Agent': 'HttpPrompt'
        })

    def test_header_value_with_double_quotes(self):
        execute('Accept:text/html User-Agent:"HTTP Prompt"', self.context)
        self.assertEqual(self.context.headers, {
            'Accept': 'text/html',
            'User-Agent': 'HTTP Prompt'
        })

    def test_header_value_with_single_quotes(self):
        execute("Accept:text/html User-Agent:'HTTP Prompt'", self.context)
        self.assertEqual(self.context.headers, {
            'Accept': 'text/html',
            'User-Agent': 'HTTP Prompt'
        })

    def test_header_with_double_quotes(self):
        execute('Accept:text/html "User-Agent:HTTP Prompt"', self.context)
        self.assertEqual(self.context.headers, {
            'Accept': 'text/html',
            'User-Agent': 'HTTP Prompt'
        })

    def test_header_with_single_quotes(self):
        execute("Accept:text/html 'User-Agent:HTTP Prompt'", self.context)
        self.assertEqual(self.context.headers, {
            'Accept': 'text/html',
            'User-Agent': 'HTTP Prompt'
        })

    def test_header_escaped_chars(self):
        execute(r'X-Name:John\'s\ Doe', self.context)
        self.assertEqual(self.context.headers, {
            'X-Name': "John's Doe"
        })

    def test_header_value_escaped_quote(self):
        execute(r"'X-Name:John\'s Doe'", self.context)
        self.assertEqual(self.context.headers, {
            'X-Name': "John's Doe"
        })

    def test_simple_querystring(self):
        execute('page==1 limit==20', self.context)
        self.assertEqual(self.context.querystring_params, {
            'page': ['1'],
            'limit': ['20']
        })

    def test_querystring_with_double_quotes(self):
        execute('page==1 name=="John Doe"', self.context)
        self.assertEqual(self.context.querystring_params, {
            'page': ['1'],
            'name': ['John Doe']
        })

    def test_querystring_with_single_quotes(self):
        execute("page==1 name=='John Doe'", self.context)
        self.assertEqual(self.context.querystring_params, {
            'page': ['1'],
            'name': ['John Doe']
        })

    def test_querystring_with_chinese(self):
        execute("name==王小明", self.context)
        self.assertEqual(self.context.querystring_params, {
            'name': ['王小明']
        })

    def test_querystring_escaped_chars(self):
        execute(r'name==John\'s\ Doe', self.context)
        self.assertEqual(self.context.querystring_params, {
            'name': ["John's Doe"]
        })

    def test_querytstring_value_escaped_quote(self):
        execute(r"'name==John\'s Doe'", self.context)
        self.assertEqual(self.context.querystring_params, {
            'name': ["John's Doe"]
        })

    def test_querystring_key_escaped_quote(self):
        execute(r"'john\'s last name==Doe'", self.context)
        self.assertEqual(self.context.querystring_params, {
            "john's last name": ['Doe']
        })

    def test_simple_body_params(self):
        execute('username=john password=123', self.context)
        self.assertEqual(self.context.body_params, {
            'username': 'john',
            'password': '123'
        })

    def test_body_param_value_with_double_quotes(self):
        execute('name="John Doe" password=123', self.context)
        self.assertEqual(self.context.body_params, {
            'name': 'John Doe',
            'password': '123'
        })

    def test_body_param_value_with_single_quotes(self):
        execute("name='John Doe' password=123", self.context)
        self.assertEqual(self.context.body_params, {
            'name': 'John Doe',
            'password': '123'
        })

    def test_body_param_with_double_quotes(self):
        execute('"name=John Doe" password=123', self.context)
        self.assertEqual(self.context.body_params, {
            'name': 'John Doe',
            'password': '123'
        })

    def test_body_param_with_spanish(self):
        execute('name=Jesús', self.context)
        self.assertEqual(self.context.body_params, {
            'name': 'Jesús'
        })

    def test_body_param_escaped_chars(self):
        execute(r'name=John\'s\ Doe', self.context)
        self.assertEqual(self.context.body_params, {
            'name': "John's Doe"
        })

    def test_body_param_value_escaped_quote(self):
        execute(r"'name=John\'s Doe'", self.context)
        self.assertEqual(self.context.body_params, {
            'name': "John's Doe"
        })

    def test_body_param_key_escaped_quote(self):
        execute(r"'john\'s last name=Doe'", self.context)
        self.assertEqual(self.context.body_params, {
            "john's last name": 'Doe'
        })

    def test_long_option_names(self):
        execute('--auth user:pass --form', self.context)
        self.assertEqual(self.context.options, {
            '--form': None,
            '--auth': 'user:pass'
        })

    def test_long_option_names_with_its_prefix(self):
        execute('--auth-type basic --auth user:pass --session user '
                '--session-read-only user', self.context)
        self.assertEqual(self.context.options, {
            '--auth-type': 'basic',
            '--auth': 'user:pass',
            '--session-read-only': 'user',
            '--session': 'user'
        })

    def test_long_short_option_names_mixed(self):
        execute('--style=default -j --stream', self.context)
        self.assertEqual(self.context.options, {
            '-j': None,
            '--stream': None,
            '--style': 'default'
        })

    def test_option_and_body_param(self):
        execute('--form name="John Doe"', self.context)
        self.assertEqual(self.context.options, {
            '--form': None
        })
        self.assertEqual(self.context.body_params, {
            'name': 'John Doe'
        })

    def test_mixed(self):
        execute('   --form  name="John Doe"   password=1234\\ 5678    '
                'User-Agent:HTTP\\ Prompt  -a   \'john:1234 5678\'  '
                '"Accept:text/html"  ', self.context)
        self.assertEqual(self.context.options, {
            '--form': None,
            '-a': 'john:1234 5678'
        })
        self.assertEqual(self.context.headers, {
            'User-Agent': 'HTTP Prompt',
            'Accept': 'text/html'
        })
        self.assertEqual(self.context.options, {
            '--form': None,
            '-a': 'john:1234 5678'
        })
        self.assertEqual(self.context.body_params, {
            'name': 'John Doe',
            'password': '1234 5678'
        })

    def test_multi_querystring(self):
        execute('name==john name==doe', self.context)
        self.assertEqual(self.context.querystring_params, {
            'name': ['john', 'doe']
        })

        execute('name==jane', self.context)
        self.assertEqual(self.context.querystring_params, {
            'name': ['jane']
        })

    def test_raw_json_object(self):
        execute("""definition:={"id":819,"name":"ML"}""", self.context)
        self.assertEqual(self.context.body_json_params, {
            'definition': {
                'id': 819,
                'name': 'ML'
            }
        })

    def test_raw_json_object_quoted(self):
        execute("""definition:='{"id": 819, "name": "ML"}'""", self.context)
        self.assertEqual(self.context.body_json_params, {
            'definition': {
                'id': 819,
                'name': 'ML'
            }
        })

    def test_raw_json_array(self):
        execute("""names:=["foo","bar"]""", self.context)
        self.assertEqual(self.context.body_json_params, {
            'names': ["foo", "bar"]
        })

    def test_raw_json_array_quoted(self):
        execute("""names:='["foo", "bar"]'""", self.context)
        self.assertEqual(self.context.body_json_params, {
            'names': ["foo", "bar"]
        })

    def test_raw_json_integer(self):
        execute('number:=999', self.context)
        self.assertEqual(self.context.body_json_params, {'number': 999})

    def test_raw_json_string(self):
        execute("""name:='"john doe"'""", self.context)
        self.assertEqual(self.context.body_json_params, {'name': 'john doe'})

    def test_escape_colon(self):
        execute(r'where[id\:gt]:=2', self.context)
        self.assertEqual(self.context.body_json_params, {
            r'where[id\:gt]': 2
        })

    def test_escape_equal(self):
        execute(r'foo\=bar=hello', self.context)
        self.assertEqual(self.context.body_params, {
            r'foo\=bar': 'hello'
        })


class TestHttpAction(ExecutionTestCase):

    def test_get(self):
        execute('get', self.context)
        self.assert_httpie_main_called_with(['GET', 'http://localhost'])

    def test_get_uppercase(self):
        execute('GET', self.context)
        self.assert_httpie_main_called_with(['GET', 'http://localhost'])

    def test_get_multi_querystring(self):
        execute('get foo==1 foo==2 foo==3', self.context)
        self.assert_httpie_main_called_with([
            'GET', 'http://localhost', 'foo==1', 'foo==2', 'foo==3'])

    def test_post(self):
        execute('post page==1', self.context)
        self.assert_httpie_main_called_with(['POST', 'http://localhost',
                                             'page==1'])
        self.assertFalse(self.context.querystring_params)

    def test_post_with_absolute_path(self):
        execute('post /api/v3 name=bob', self.context)
        self.assert_httpie_main_called_with(['POST', 'http://localhost/api/v3',
                                             'name=bob'])
        self.assertFalse(self.context.body_params)
        self.assertEqual(self.context.url, 'http://localhost')

    def test_post_with_relative_path(self):
        self.context.url = 'http://localhost/api/v3'
        execute('post ../v2/movie id=8', self.context)
        self.assert_httpie_main_called_with([
            'POST', 'http://localhost/api/v2/movie', 'id=8'])
        self.assertFalse(self.context.body_params)
        self.assertEqual(self.context.url, 'http://localhost/api/v3')

    def test_post_with_full_url(self):
        execute('post http://httpbin.org/post id=9', self.context)
        self.assert_httpie_main_called_with([
            'POST', 'http://httpbin.org/post', 'id=9'])
        self.assertFalse(self.context.body_params)
        self.assertEqual(self.context.url, 'http://localhost')

    def test_post_with_full_https_url(self):
        execute('post https://httpbin.org/post id=9', self.context)
        self.assert_httpie_main_called_with([
            'POST', 'https://httpbin.org/post', 'id=9'])
        self.assertFalse(self.context.body_params)
        self.assertEqual(self.context.url, 'http://localhost')

    def test_post_uppercase(self):
        execute('POST content=text', self.context)
        self.assert_httpie_main_called_with(['POST', 'http://localhost',
                                             'content=text'])
        self.assertFalse(self.context.body_params)

    def test_post_raw_json_object(self):
        execute("""post definition:={"id":819,"name":"ML"}""",
                self.context)
        self.assert_httpie_main_called_with([
            'POST', 'http://localhost',
            """definition:={"id": 819, "name": "ML"}"""])
        self.assertFalse(self.context.body_json_params)

    def test_post_raw_json_object_quoted(self):
        execute("""post definition:='{"id": 819, "name": "ML"}'""",
                self.context)
        self.assert_httpie_main_called_with([
            'POST', 'http://localhost',
            'definition:={"id": 819, "name": "ML"}'])
        self.assertFalse(self.context.body_json_params)

    def test_post_raw_json_array(self):
        execute("""post hobbies:=["foo","bar"]""",
                self.context)
        self.assert_httpie_main_called_with([
            'POST', 'http://localhost',
            'hobbies:=["foo", "bar"]'])
        self.assertFalse(self.context.body_json_params)

    def test_post_raw_json_array_quoted(self):
        execute("""post hobbies:='["foo", "bar"]'""",
                self.context)
        self.assert_httpie_main_called_with([
            'POST', 'http://localhost',
            'hobbies:=["foo", "bar"]'])
        self.assertFalse(self.context.body_json_params)

    def test_post_raw_json_integer(self):
        execute('post number:=123',
                self.context)
        self.assert_httpie_main_called_with([
            'POST', 'http://localhost', 'number:=123'])
        self.assertFalse(self.context.body_json_params)

    def test_post_raw_json_boolean(self):
        execute('post foo:=true',
                self.context)
        self.assert_httpie_main_called_with([
            'POST', 'http://localhost', 'foo:=true'])
        self.assertFalse(self.context.body_json_params)

    def test_delete(self):
        execute('delete', self.context)
        self.assert_httpie_main_called_with(['DELETE', 'http://localhost'])

    def test_delete_uppercase(self):
        execute('DELETE', self.context)
        self.assert_httpie_main_called_with(['DELETE', 'http://localhost'])

    def test_patch(self):
        execute('patch', self.context)
        self.assert_httpie_main_called_with(['PATCH', 'http://localhost'])

    def test_patch_uppercase(self):
        execute('PATCH', self.context)
        self.assert_httpie_main_called_with(['PATCH', 'http://localhost'])

    def test_head(self):
        execute('head', self.context)
        self.assert_httpie_main_called_with(['HEAD', 'http://localhost'])

    def test_head_uppercase(self):
        execute('HEAD', self.context)
        self.assert_httpie_main_called_with(['HEAD', 'http://localhost'])

    def test_options(self):
        execute('options', self.context)
        self.assert_httpie_main_called_with(['OPTIONS', 'http://localhost'])


class TestHttpActionRedirection(ExecutionTestCase):

    def test_get(self):
        execute('get > data.json', self.context)
        self.assert_httpie_main_called_with(['GET', 'http://localhost'])

        env = self.httpie_main.call_args[1]['env']
        self.assertFalse(env.stdout_isatty)
        self.assertEqual(env.stdout.fp.name, 'data.json')


@pytest.mark.slow
class TestHttpBin(TempAppDirTestCase):
    """Send real requests to http://httpbin.org, save the responses to files,
    and asserts on the file content.
    """

    def setUp(self):
        super(TestHttpBin, self).setUp()

        # XXX: pytest doesn't allow HTTPie to read stdin while it's capturing
        # stdout, so we replace stdin with a file temporarily during the test.
        class MockStdin(object):
            def __init__(self, fp):
                self.fp = fp

            def isatty(self):
                return True

            def __getattr__(self, name):
                if name == 'isatty':
                    return self.isatty
                return getattr(self.fp, name)

        self.orig_stdin = sys.stdin
        filename = self.make_tempfile()
        sys.stdin = MockStdin(open(filename, 'rb'))
        sys.stdin.isatty = lambda: True

        # Mock echo_via_pager() so that we can catch data fed to stdout
        self.patcher = patch('http_prompt.output.click.echo_via_pager')
        self.echo_via_pager = self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

        sys.stdin.close()
        sys.stdin = self.orig_stdin

        super(TestHttpBin, self).tearDown()

    def get_stdout(self):
        return self.echo_via_pager.call_args[0][0]

    def execute_redirection(self, command):
        context = Context('http://httpbin.org')
        filename = self.make_tempfile()
        execute('%s > %s' % (command, filename), context)

        with open(filename, 'rb') as f:
            return f.read()

    def execute_pipe(self, command):
        context = Context('http://httpbin.org')
        execute(command, context)

    def test_get_image(self):
        data = self.execute_redirection('get /image/png')
        self.assertTrue(data)
        self.assertEqual(hashlib.sha1(data).hexdigest(),
                         '379f5137831350c900e757b39e525b9db1426d53')

    def test_get_querystring(self):
        data = self.execute_redirection(
            'get /get id==1234 X-Custom-Header:5678')
        data = json.loads(data.decode())
        self.assertEqual(data['args'], {
            'id': '1234'
        })
        self.assertEqual(data['headers']['X-Custom-Header'], '5678')

    def test_post_json(self):
        data = self.execute_redirection(
            'post /post id=1234 X-Custom-Header:5678')
        data = json.loads(data.decode())
        self.assertEqual(data['json'], {
            'id': '1234'
        })
        self.assertEqual(data['headers']['X-Custom-Header'], '5678')

    def test_post_form(self):
        data = self.execute_redirection(
            'post /post --form id=1234 X-Custom-Header:5678')
        data = json.loads(data.decode())
        self.assertEqual(data['form'], {
            'id': '1234'
        })
        self.assertEqual(data['headers']['X-Custom-Header'], '5678')

    @pytest.mark.skipif(sys.platform == 'win32', reason="Unix only")
    def test_get_and_tee(self):
        filename = self.make_tempfile()
        self.execute_pipe('get /get hello==world | tee %s' % filename)

        with open(filename) as f:
            data = json.load(f)
        self.assertEqual(data['args'], {'hello': 'world'})

        printed_msg = self.get_stdout()
        data = json.loads(printed_msg)
        self.assertEqual(data['args'], {'hello': 'world'})


class TestCommandPreview(ExecutionTestCase):

    def test_httpie_without_args(self):
        execute('httpie', self.context)
        self.assert_stdout('http http://localhost\n')

    def test_httpie_with_post(self):
        execute('httpie post name=alice', self.context)
        self.assert_stdout('http POST http://localhost name=alice\n')
        self.assertFalse(self.context.body_params)

    def test_httpie_with_absolute_path(self):
        execute('httpie post /api name=alice', self.context)
        self.assert_stdout('http POST http://localhost/api name=alice\n')
        self.assertFalse(self.context.body_params)

    def test_httpie_with_full_url(self):
        execute('httpie POST http://httpbin.org/post name=alice', self.context)
        self.assert_stdout('http POST http://httpbin.org/post name=alice\n')
        self.assertEqual(self.context.url, 'http://localhost')
        self.assertFalse(self.context.body_params)

    def test_httpie_with_full_https_url(self):
        execute('httpie post https://httpbin.org/post name=alice',
                self.context)
        self.assert_stdout('http POST https://httpbin.org/post name=alice\n')
        self.assertEqual(self.context.url, 'http://localhost')
        self.assertFalse(self.context.body_params)

    def test_httpie_with_quotes(self):
        execute(r'httpie post http://httpbin.org/post name="john doe" '
                r"apikey==abc\ 123 'Authorization:ApiKey 1234'",
                self.context)
        self.assert_stdout(
            "http POST http://httpbin.org/post 'apikey==abc 123' "
            "'name=john doe' 'Authorization:ApiKey 1234'\n")
        self.assertEqual(self.context.url, 'http://localhost')
        self.assertFalse(self.context.body_params)
        self.assertFalse(self.context.querystring_params)
        self.assertFalse(self.context.headers)

    def test_httpie_with_multi_querystring(self):
        execute('httpie get foo==1 foo==2 foo==3', self.context)
        self.assert_stdout('http GET http://localhost foo==1 foo==2 foo==3\n')
        self.assertEqual(self.context.url, 'http://localhost')
        self.assertFalse(self.context.querystring_params)


class TestPipe(ExecutionTestCase):

    @pytest.mark.skipif(sys.platform == 'win32', reason="Unix only")
    def test_httpie_sed(self):
        execute("httpie get some==data | sed 's/data$/input/'", self.context)
        self.assert_stdout('http GET http://localhost some==input\n')

    @pytest.mark.skipif(sys.platform == 'win32', reason="Unix only")
    def test_httpie_sed_with_echo(self):
        execute("httpie post | `echo \"sed 's/localhost$/127.0.0.1/'\"`",
                self.context)
        self.assert_stdout("http POST http://127.0.0.1\n")

    @pytest.mark.skipif(sys.platform == 'win32', reason="Unix only")
    def test_env_grep(self):
        self.context.body_params = {
            'username': 'jane',
            'name': 'Jane',
            'password': '1234'
        }
        execute('env | grep name', self.context)
        self.assert_stdout('name=Jane\nusername=jane\n')


class TestShellSubstitution(ExecutionTestCase):

    def test_unquoted_option(self):
        execute("--auth `echo user:pass`", self.context)
        self.assertEqual(self.context.options, {
            '--auth': 'user:pass'
        })

    def test_partial_unquoted_option(self):
        execute("--auth user:`echo pass`", self.context)
        self.assertEqual(self.context.options, {
            '--auth': 'user:pass'
        })

    def test_partial_squoted_option(self):
        execute("--auth='user:`echo pass`'", self.context)
        self.assertEqual(self.context.options, {
            '--auth': 'user:pass'
        })

    def test_partial_dquoted_option(self):
        execute('--auth="user:`echo pass`"', self.context)
        self.assertEqual(self.context.options, {
            '--auth': 'user:pass'
        })

    def test_unquoted_header(self):
        execute("`echo 'X-Greeting'`:`echo 'hello world'`", self.context)
        if sys.platform == 'win32':
            expected_key = "'X-Greeting'"
            expected_value = "'hello world'"
        else:
            expected_key = 'X-Greeting'
            expected_value = 'hello world'

        self.assertEqual(self.context.headers, {
            expected_key: expected_value
        })

    def test_full_squoted_header(self):
        execute("'`echo X-Greeting`:`echo hello`'", self.context)
        self.assertEqual(self.context.headers, {
            'X-Greeting': 'hello'
        })

    def test_full_dquoted_header(self):
        execute('"`echo X-Greeting`:`echo hello`"', self.context)
        self.assertEqual(self.context.headers, {
            'X-Greeting': 'hello'
        })

    def test_value_squoted_header(self):
        execute("`echo X-Greeting`:'`echo hello`'", self.context)
        self.assertEqual(self.context.headers, {
            'X-Greeting': 'hello'
        })

    def test_value_dquoted_header(self):
        execute('`echo X-Greeting`:"`echo hello`"', self.context)
        self.assertEqual(self.context.headers, {
            'X-Greeting': 'hello'
        })

    def test_partial_value_dquoted_header(self):
        execute('Authorization:"Bearer `echo OAUTH TOKEN`"', self.context)
        self.assertEqual(self.context.headers, {
            'Authorization': 'Bearer OAUTH TOKEN'
        })

    def test_partial_full_dquoted_header(self):
        execute('"Authorization:Bearer `echo OAUTH TOKEN`"', self.context)
        self.assertEqual(self.context.headers, {
            'Authorization': 'Bearer OAUTH TOKEN'
        })

    def test_unquoted_querystring(self):
        execute("`echo greeting`==`echo 'hello world'`", self.context)
        expected = ("'hello world'"
                    if sys.platform == 'win32' else 'hello world')
        self.assertEqual(self.context.querystring_params, {
            'greeting': [expected]
        })

    def test_full_squoted_querystring(self):
        execute("'`echo greeting`==`echo hello`'", self.context)
        self.assertEqual(self.context.querystring_params, {
            'greeting': ['hello']
        })

    def test_value_squoted_querystring(self):
        execute("`echo greeting`=='`echo hello`'", self.context)
        self.assertEqual(self.context.querystring_params, {
            'greeting': ['hello']
        })

    def test_value_dquoted_querystring(self):
        execute('`echo greeting`=="`echo hello`"', self.context)
        self.assertEqual(self.context.querystring_params, {
            'greeting': ['hello']
        })

    def test_unquoted_body_param(self):
        execute("`echo greeting`=`echo 'hello world'`", self.context)
        expected = ("'hello world'"
                    if sys.platform == 'win32' else 'hello world')
        self.assertEqual(self.context.body_params, {
            'greeting': expected
        })

    def test_full_squoted_body_param(self):
        execute("'`echo greeting`=`echo hello`'", self.context)
        self.assertEqual(self.context.body_params, {
            'greeting': 'hello'
        })

    def test_value_squoted_body_param(self):
        execute("`echo greeting`='`echo hello`'", self.context)
        self.assertEqual(self.context.body_params, {
            'greeting': 'hello'
        })

    def test_full_dquoted_body_param(self):
        execute('"`echo greeting`=`echo hello`"', self.context)
        self.assertEqual(self.context.body_params, {
            'greeting': 'hello'
        })

    def test_bad_command(self):
        execute("name=`bad command test`", self.context)
        self.assertEqual(self.context.body_params, {'name': ''})

    @pytest.mark.skipif(sys.platform == 'win32', reason="Unix only")
    def test_pipe_and_grep(self):
        execute("greeting=`echo 'hello world\nhihi\n' | grep hello`",
                self.context)
        self.assertEqual(self.context.body_params, {
            'greeting': 'hello world'
        })


class TestCommandPreviewRedirection(ExecutionTestCase):

    def test_httpie_redirect_write(self):
        filename = self.make_tempfile()

        # Write something first to make sure it's a full overwrite
        with open(filename, 'w') as f:
            f.write('hello world\n')

        execute('httpie > %s' % filename, self.context)

        with open(filename) as f:
            content = f.read()
        self.assertEqual(content, 'http http://localhost\n')

    def test_httpie_redirect_write_quoted_filename(self):
        filename = self.make_tempfile()

        # Write something first to make sure it's a full overwrite
        with open(filename, 'w') as f:
            f.write('hello world\n')

        execute('httpie > "%s"' % filename, self.context)

        with open(filename) as f:
            content = f.read()
        self.assertEqual(content, 'http http://localhost\n')

    @pytest.mark.skipif(sys.platform == 'win32',
                        reason="Windows doesn't use backslashes to escape")
    def test_httpie_redirect_write_escaped_filename(self):
        filename = self.make_tempfile()
        filename += r' copy'

        # Write something first to make sure it's a full overwrite
        with open(filename, 'w') as f:
            f.write('hello world\n')

        execute('httpie > %s' % filename.replace(' ', r'\ '), self.context)

        with open(filename) as f:
            content = f.read()
        self.assertEqual(content, 'http http://localhost\n')

    def test_httpie_redirect_write_with_args(self):
        filename = self.make_tempfile()

        # Write something first to make sure it's a full overwrite
        with open(filename, 'w') as f:
            f.write('hello world\n')

        execute('httpie post http://example.org name=john > %s' % filename,
                self.context)

        with open(filename) as f:
            content = f.read()
        self.assertEqual(content, 'http POST http://example.org name=john\n')

    def test_httpie_redirect_append(self):
        filename = self.make_tempfile()

        # Write something first to make sure it's an append
        with open(filename, 'w') as f:
            f.write('hello world\n')

        execute('httpie >> %s' % filename, self.context)

        with open(filename) as f:
            content = f.read()
        self.assertEqual(content, 'hello world\nhttp http://localhost\n')

    def test_httpie_redirect_append_without_spaces(self):
        filename = self.make_tempfile()

        # Write something first to make sure it's an append
        with open(filename, 'w') as f:
            f.write('hello world\n')

        execute('httpie>>%s' % filename, self.context)

        with open(filename) as f:
            content = f.read()
        self.assertEqual(content, 'hello world\nhttp http://localhost\n')

    def test_httpie_redirect_append_quoted_filename(self):
        filename = self.make_tempfile()

        # Write something first to make sure it's an append
        with open(filename, 'w') as f:
            f.write('hello world\n')

        execute("httpie >> '%s'" % filename, self.context)

        with open(filename) as f:
            content = f.read()
        self.assertEqual(content, 'hello world\nhttp http://localhost\n')
