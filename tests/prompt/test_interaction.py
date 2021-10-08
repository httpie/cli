import os
import sys

import pexpect
import pytest

from .base import TempAppDirTestCase
from .utils import get_http_prompt_path
from httpie.prompt import config


class TestInteraction(TempAppDirTestCase):

    def setUp(self):
        super(TestInteraction, self).setUp()

        # Use temporary directory as user config home.
        # Will restore it in tearDown().
        self.orig_config_home = os.getenv('XDG_CONFIG_HOME')
        os.environ['XDG_CONFIG_HOME'] = self.temp_dir

        # Make sure pexpect uses the same terminal environment
        self.orig_term = os.getenv('TERM')
        os.environ['TERM'] = 'screen-256color'

    def tearDown(self):
        super(TestInteraction, self).tearDown()

        os.environ['XDG_CONFIG_HOME'] = self.orig_config_home

        if self.orig_term:
            os.environ['TERM'] = self.orig_term
        else:
            os.environ.pop('TERM', None)

    def write_config(self, content):
        config_path = config.get_user_config_path()
        with open(config_path, 'a') as f:
            f.write(content)

    @pytest.mark.skipif(sys.platform == 'win32',
                        reason="pexpect doesn't work well on Windows")
    @pytest.mark.slow
    def test_interaction(self):
        bin_path = get_http_prompt_path()
        child = pexpect.spawn(bin_path, env=os.environ)

        # TODO: Test more interaction

        child.sendline('exit')
        child.expect_exact('Goodbye!', timeout=20)
        child.close()

    @pytest.mark.skipif(sys.platform == 'win32',
                        reason="pexpect doesn't work well on Windows")
    @pytest.mark.slow
    def test_vi_mode(self):
        self.write_config('vi = True\n')

        bin_path = get_http_prompt_path()
        child = pexpect.spawn(bin_path, env=os.environ)

        child.expect_exact('http://localhost:8000>')

        # Enter 'htpie', switch to command mode (ESC),
        # move two chars left (hh), and insert (i) a 't'
        child.send('htpie')
        child.send('\x1b')
        child.sendline('hhit')

        child.expect_exact('http http://localhost:8000')

        # Enter 'exit'
        child.send('\x1b')
        child.send('i')
        child.sendline('exit')

        child.expect_exact('Goodbye!', timeout=20)
        child.close()
