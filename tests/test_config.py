from os import path
import sys

from httpie import __version__
from utils import MockEnvironment, http, HTTP_OK
from httpie.context import Environment
import pkg_resources
import pytest

TEST_PLUGINS_PATH = path.join(path.abspath(path.dirname(__file__)), 'test_plugins')


def test_default_options(httpbin):
    env = MockEnvironment()
    env.config['default_options'] = ['--form']
    env.config.save()
    r = http(httpbin.url + '/post', 'foo=bar', env=env)
    assert r.json['form'] == {"foo": "bar"}


def test_config_dir_not_writeable(httpbin):
    r = http(httpbin + '/get', env=MockEnvironment(
        config_dir='/',
        create_temp_config_dir=False,
    ))
    assert HTTP_OK in r


def test_default_options_overwrite(httpbin):
    env = MockEnvironment()
    env.config['default_options'] = ['--form']
    env.config.save()
    r = http('--json', httpbin.url + '/post', 'foo=bar', env=env)
    assert r.json['json'] == {"foo": "bar"}


def test_current_version():
    version = MockEnvironment().config['__meta__']['httpie']
    assert version == __version__


@pytest.fixture()
def sandbox():
    # this is based on setuptools.sandbox.setup_context
    # but it seems the kind of thing likely to break!
    saved_pkg_resources = pkg_resources.__getstate__()
    saved_modules = sys.modules.copy()
    saved_path = sys.path[:]
    try:
        yield
    finally:
        sys.path[:] = saved_path
        sys.modules.update(saved_modules)
        for mod_name in list(sys.modules.keys()):
            if mod_name not in saved_modules and not mod_name.startswith('encodings.'):
                del sys.modules[mod_name]
        pkg_resources.__setstate__(saved_pkg_resources)


def test_extra_site_dirs_plugin_loading(sandbox):
    assert TEST_PLUGINS_PATH not in sys.path
    env = MockEnvironment()
    env.config['extra_site_dirs'] = [TEST_PLUGINS_PATH]
    env.config.save()
    r = http('--debug', '--help', env=env)
    assert "Loading plugin 'foo 0.0.1' from " in r.stderr
    assert '--auth-type {basic,digest,foo}' in r
    assert TEST_PLUGINS_PATH in sys.path


def test_extra_site_dirs_plugin_works(httpbin, sandbox):
    assert TEST_PLUGINS_PATH not in sys.path
    env = MockEnvironment()
    env.config['extra_site_dirs'] = [TEST_PLUGINS_PATH]
    env.config.save()
    r = http('--auth-type=foo', '--auth=user:password',
             'GET', httpbin + '/basic-auth/user/password-foo', env=env)
    assert HTTP_OK in r
    assert r.json == {'authenticated': True, 'user': 'user'}
    assert TEST_PLUGINS_PATH in sys.path
