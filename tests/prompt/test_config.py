import hashlib
import os

from .base import TempAppDirTestCase
from httpie.prompt import config


def _hash_file(path):
    with open(path, 'rb') as f:
        data = f.read()
    return hashlib.sha1(data).hexdigest()


class TestConfig(TempAppDirTestCase):

    def test_initialize(self):
        # Config file doesn't exist at first
        expected_path = config.get_user_config_path()
        self.assertFalse(os.path.exists(expected_path))

        # Config file should exist after initialization
        copied, actual_path = config.initialize()
        self.assertTrue(copied)
        self.assertEqual(actual_path, expected_path)
        self.assertTrue(os.path.exists(expected_path))

        # Change config file and hash the content to see if it's changed
        with open(expected_path, 'a') as f:
            f.write('dont_care\n')
        orig_hash = _hash_file(expected_path)

        # Make sure it's fine to call config.initialize() twice
        copied, actual_path = config.initialize()
        self.assertFalse(copied)
        self.assertEqual(actual_path, expected_path)
        self.assertTrue(os.path.exists(expected_path))

        # Make sure config file is unchanged
        new_hash = _hash_file(expected_path)
        self.assertEqual(new_hash, orig_hash)

    def test_load_default(self):
        cfg = config.load_default()
        self.assertEqual(cfg['command_style'], 'solarized')
        self.assertFalse(cfg['output_style'])
        self.assertEqual(cfg['pager'], 'less')

    def test_load_user(self):
        copied, path = config.initialize()
        self.assertTrue(copied)

        with open(path, 'w') as f:
            f.write("\ngreeting = 'hello!'\n")

        cfg = config.load_user()
        self.assertEqual(cfg, {'greeting': 'hello!'})

    def test_load(self):
        copied, path = config.initialize()
        self.assertTrue(copied)

        with open(path, 'w') as f:
            f.write("pager = 'more'\n"
                    "greeting = 'hello!'\n")

        cfg = config.load()
        self.assertEqual(cfg['command_style'], 'solarized')
        self.assertFalse(cfg['output_style'])
        self.assertEqual(cfg['pager'], 'more')
        self.assertEqual(cfg['greeting'], 'hello!')
