from httpie import __version__
from utils import MockEnvironment, http, HTTP_OK
from httpie.context import Environment


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
