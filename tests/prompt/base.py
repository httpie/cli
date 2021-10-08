import os
import shutil
import sys
import tempfile
import unittest


class TempAppDirTestCase(unittest.TestCase):
    """Set up temporary app data and config directories before every test
    method, and delete them afterwards.
    """

    def setUp(self):
        # Create a temp dir that will contain data and config directories
        self.temp_dir = tempfile.mkdtemp()

        if sys.platform == 'win32':
            self.homes = {
                # subdir_name: envvar_name
                'data': 'LOCALAPPDATA',
                'config': 'LOCALAPPDATA'
            }
        else:
            self.homes = {
                # subdir_name: envvar_name
                'data': 'XDG_DATA_HOME',
                'config': 'XDG_CONFIG_HOME'
            }

        # Used to restore
        self.orig_envvars = {}

        for subdir_name, envvar_name in self.homes.items():
            if envvar_name in os.environ:
                self.orig_envvars[envvar_name] = os.environ[envvar_name]
            os.environ[envvar_name] = os.path.join(self.temp_dir, subdir_name)

    def tearDown(self):
        # Restore envvar values
        for name in self.homes.values():
            if name in self.orig_envvars:
                os.environ[name] = self.orig_envvars[name]
            else:
                del os.environ[name]

        shutil.rmtree(self.temp_dir)

    def make_tempfile(self, data='', subdir_name=''):
        """Create a file under self.temp_dir and return the path."""
        full_tempdir = os.path.join(self.temp_dir, subdir_name)
        if not os.path.exists(full_tempdir):
            os.makedirs(full_tempdir)

        if isinstance(data, str):
            data = data.encode()

        with tempfile.NamedTemporaryFile(dir=full_tempdir, delete=False) as f:
            f.write(data)
            return f.name
