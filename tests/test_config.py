import pytest

from httpie.compat import is_windows
from httpie.config import Config
from utils import HTTP_OK, MockEnvironment, http


def test_default_options(httpbin):
    env = MockEnvironment()
    env.config['default_options'] = ['--form']
    env.config.save()
    r = http(httpbin.url + '/post', 'foo=bar', env=env)
    assert r.json['form'] == {
        "foo": "bar"
    }


def test_config_file_not_valid(httpbin):
    env = MockEnvironment()
    env.create_temp_config_dir()
    with (env.config_dir / Config.FILENAME).open('w') as f:
        f.write('{invalid json}')
    r = http(httpbin + '/get', env=env)
    assert HTTP_OK in r
    assert 'http: warning' in r.stderr
    assert 'invalid config file' in r.stderr


@pytest.mark.skipif(is_windows, reason='cannot chmod 000 on Windows')
def test_config_file_inaccessible(httpbin):
    env = MockEnvironment()
    env.create_temp_config_dir()
    config_path = env.config_dir / Config.FILENAME
    assert not config_path.exists()
    config_path.touch(0o000)
    assert config_path.exists()
    r = http(httpbin + '/get', env=env)
    assert HTTP_OK in r
    assert 'http: warning' in r.stderr
    assert 'cannot read config file' in r.stderr


def test_default_options_overwrite(httpbin):
    env = MockEnvironment()
    env.config['default_options'] = ['--form']
    env.config.save()
    r = http('--json', httpbin.url + '/post', 'foo=bar', env=env)
    assert r.json['json'] == {
        "foo": "bar"
    }
